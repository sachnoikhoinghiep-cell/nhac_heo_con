import streamlit as st
import requests
import urllib.parse
import os
import json
from firebase_admin import auth as fb_auth
from firebase_config import init_firebase   # cần để init Firebase SDK (dùng cho verify_id_token)
import supabase_db as sdb
from datetime import datetime, timezone, timedelta
import extra_streamlit_components as stx

_COOKIE_KEY  = "sonicflowai_rt"
_COOKIE_DAYS = 30

def _cookie_mgr():
    return stx.CookieManager(key="sonicflowai_cm")

def _ctx_cookie(name: str) -> str:
    """Đọc cookie từ HTTP request headers — hoạt động ngay lần render đầu tiên.
    st.context.cookies khả dụng từ Streamlit 1.37+."""
    try:
        return st.context.cookies.get(name, "") or ""
    except Exception:
        return ""

def _save_rt(refresh_token: str):
    # Lưu tạm vào session_state; process_pending_rt() trong app.py sẽ ghi cookie
    # sau khi CookieManager được render đầy đủ (tránh race với st.switch_page)
    st.session_state["_pending_rt"] = refresh_token

def _load_rt() -> str:
    # Đọc trực tiếp từ HTTP Cookie header — synchronous, không cần React init
    return _ctx_cookie(_COOKIE_KEY) or ""

def process_pending_rt():
    """Gọi ở đầu app.py mỗi render để ghi/xóa cookie refresh token.
    Tách khỏi handle_google_callback / sign_out để CookieManager được mount trước."""
    # Xóa cookie sau sign_out (deferred vì switch_page không chờ JS chạy)
    if st.session_state.pop("_pending_logout", False):
        try:
            _cookie_mgr().delete(_COOKIE_KEY)
        except Exception:
            pass
        return

    # Lưu cookie sau đăng nhập thành công
    pending = st.session_state.pop("_pending_rt", None)
    if pending:
        try:
            _cookie_mgr().set(
                _COOKIE_KEY, pending,
                expires_at=datetime.now() + timedelta(days=_COOKIE_DAYS),
            )
        except Exception:
            pass

def _clear_rt():
    try:
        _cookie_mgr().delete(_COOKIE_KEY)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# API key persistence
# ---------------------------------------------------------------------------
_APIKEY_COOKIE = "sonicflowai_ak"

def save_api_keys(anthropic: str, google: str, suno: str, fal: str = "", xai: str = "", openrouter: str = ""):
    """Lưu API keys vào cookie (fallback cho user chưa login)."""
    data = json.dumps({"a": anthropic, "g": google, "s": suno, "f": fal, "x": xai, "o": openrouter})
    try:
        _cookie_mgr().set(
            _APIKEY_COOKIE, data,
            expires_at=datetime.now() + timedelta(days=365),
        )
    except Exception:
        pass

def load_api_keys() -> dict:
    """Đọc API keys từ cookie."""
    try:
        raw = _ctx_cookie(_APIKEY_COOKIE) or _cookie_mgr().get(_APIKEY_COOKIE) or ""
        if raw:
            d = json.loads(raw)
            return {
                "anthropic":  d.get("a", ""), "google":     d.get("g", ""),
                "suno":       d.get("s", ""), "fal":        d.get("f", ""),
                "xai":        d.get("x", ""), "openrouter": d.get("o", ""),
            }
    except Exception:
        pass
    return {}

_VIDEOPREF_COOKIE = "sonicflowai_vp"

def save_video_prefs(prefs: dict):
    """Lưu Grok video preferences vào cookie."""
    try:
        _cookie_mgr().set(
            _VIDEOPREF_COOKIE, json.dumps(prefs),
            expires_at=datetime.now() + timedelta(days=365),
        )
    except Exception:
        pass

def load_video_prefs() -> dict:
    """Đọc Grok video preferences từ cookie."""
    try:
        raw = _ctx_cookie(_VIDEOPREF_COOKIE) or _cookie_mgr().get(_VIDEOPREF_COOKIE) or ""
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return {}


def save_user_api_keys(uid: str, anthropic: str, google: str, suno: str, fal: str = "", xai: str = "", openrouter: str = ""):
    """Lưu API keys vào Supabase (mã hoá Fernet). Raises nếu lỗi."""
    sdb.save_api_keys(uid, anthropic=anthropic, google=google, suno=suno, fal=fal, xai=xai, openrouter=openrouter)

def load_user_api_keys(uid: str) -> dict:
    """Đọc API keys từ Supabase và giải mã. Trả về dict rỗng nếu chưa lưu."""
    try:
        return sdb.get_api_keys(uid)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Preset persistence
# ---------------------------------------------------------------------------
_PRESETS_COOKIE = "sonicflowai_presets"
_PRESETS_MAX    = 10

def save_presets(presets: list):
    try:
        _cookie_mgr().set(
            _PRESETS_COOKIE, json.dumps(presets[-_PRESETS_MAX:]),
            expires_at=datetime.now() + timedelta(days=365),
        )
    except Exception:
        pass

def load_presets() -> list:
    try:
        raw = _ctx_cookie(_PRESETS_COOKIE) or _cookie_mgr().get(_PRESETS_COOKIE) or "[]"
        return json.loads(raw)
    except Exception:
        return []

PLAN_DURATION = {
    # Các gói mới (credit-based)
    "Trải Nghiệm":     timedelta(days=1),
    "Content Creator": timedelta(days=30),
    "Agency / VIP":    timedelta(days=30),
    # Các gói cũ (giữ lại để tương thích ngược với dữ liệu lịch sử)
    "Ngày":  timedelta(days=1),
    "Tuần":  timedelta(weeks=1),
    "Tháng": timedelta(days=30),
    "Năm":   timedelta(days=365),
}

FIREBASE_API_KEY = "AIzaSyBl3BYwj_E3v4ppfFUHXY1WpWx7r_6H5bA"
FIREBASE_REST    = "https://identitytoolkit.googleapis.com/v1/accounts"


def _google_client_id() -> str:
    try:    return st.secrets["GOOGLE_CLIENT_ID"]
    except Exception: return os.environ.get("GOOGLE_CLIENT_ID", "")

def _google_client_secret() -> str:
    try:    return st.secrets["GOOGLE_CLIENT_SECRET"]
    except Exception: return os.environ.get("GOOGLE_CLIENT_SECRET", "")

def _redirect_uri() -> str:
    try:    return st.secrets["REDIRECT_URI"].rstrip("/")
    except Exception: return os.environ.get("REDIRECT_URI", "http://localhost:8501")


# ---------------------------------------------------------------------------
# Google OAuth — Authorization Code flow (query param, Python-readable)
# ---------------------------------------------------------------------------
def _build_google_auth_url() -> str:
    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={urllib.parse.quote(_google_client_id())}"
        f"&redirect_uri={urllib.parse.quote(_redirect_uri())}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&prompt=select_account"
        "&access_type=online"
    )


def exchange_google_code(code: str) -> tuple[str, str]:
    """Đổi authorization code → Firebase ID token + refresh token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code":          code,
            "client_id":     _google_client_id(),
            "client_secret": _google_client_secret(),
            "redirect_uri":  _redirect_uri(),
            "grant_type":    "authorization_code",
        },
        timeout=10,
    )
    token_data = resp.json()
    if "error" in token_data:
        raise ValueError(token_data.get("error_description", token_data["error"]))

    access_token = token_data.get("access_token", "")
    id_token     = token_data.get("id_token", "")

    post_body = f"access_token={access_token}&providerId=google.com"
    if id_token:
        post_body = f"id_token={id_token}&access_token={access_token}&providerId=google.com"

    resp2 = requests.post(
        f"{FIREBASE_REST}:signInWithIdp?key={FIREBASE_API_KEY}",
        json={
            "postBody":            post_body,
            "requestUri":          _redirect_uri(),
            "returnIdpCredential": True,
            "returnSecureToken":   True,
        },
        timeout=10,
    )
    data2 = resp2.json()
    if "error" in data2:
        raise ValueError(data2["error"]["message"])
    return data2["idToken"], data2.get("refreshToken", "")


def firebase_refresh(refresh_token: str) -> str:
    """Dùng refresh token lấy ID token mới."""
    resp = requests.post(
        f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data.get("error", {}).get("message", "Token refresh failed"))
    return data["id_token"]


def render_google_signin_button():
    """Nút Google Sign-In dùng st.link_button — không iframe, không sandbox."""
    if not _google_client_id() or not _google_client_secret():
        st.info("💡 Thêm `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `REDIRECT_URI` vào Streamlit secrets.")
        return
    auth_url = _build_google_auth_url()
    st.link_button(
        "🔵  Đăng nhập bằng Google",
        auth_url,
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Firebase REST — Email/Password
# ---------------------------------------------------------------------------
def firebase_email_login(email: str, password: str) -> str:
    resp = requests.post(
        f"{FIREBASE_REST}:signInWithPassword?key={FIREBASE_API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        msg = data["error"]["message"]
        friendly = {
            "INVALID_LOGIN_CREDENTIALS": "Email hoặc mật khẩu không đúng.",
            "EMAIL_NOT_FOUND":           "Email chưa được đăng ký.",
            "INVALID_PASSWORD":          "Mật khẩu không đúng.",
            "USER_DISABLED":             "Tài khoản đã bị vô hiệu hóa.",
        }
        raise ValueError(friendly.get(msg, msg))
    return data["idToken"]


def firebase_email_register(email: str, password: str) -> str:
    resp = requests.post(
        f"{FIREBASE_REST}:signUp?key={FIREBASE_API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        msg = data["error"]["message"]
        friendly = {
            "EMAIL_EXISTS":  "Email này đã được đăng ký.",
            "WEAK_PASSWORD": "Mật khẩu phải có ít nhất 6 ký tự.",
            "INVALID_EMAIL": "Địa chỉ email không hợp lệ.",
        }
        raise ValueError(friendly.get(msg, msg))
    return data["idToken"]


def firebase_reset_password(email: str):
    resp = requests.post(
        f"{FIREBASE_REST}:sendOobCode?key={FIREBASE_API_KEY}",
        json={"requestType": "PASSWORD_RESET", "email": email},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"]["message"])


# ---------------------------------------------------------------------------
# Auth UI
# ---------------------------------------------------------------------------
def try_restore_session() -> bool:
    """Khôi phục session từ cookie. Trả về True nếu thành công."""
    # Flag được set bởi sign_out() để ngăn restore ngay sau logout
    if st.session_state.pop("_signed_out", False):
        return False
    if st.session_state.get("user"):
        return True
    rt = _load_rt()
    if rt:
        try:
            new_token = firebase_refresh(rt)
            user = verify_and_load_user(new_token)
            if user:
                st.session_state.user = user
                return True
        except Exception:
            _clear_rt()
    return False


def handle_google_callback() -> bool:
    """Xử lý ?code= OAuth callback. Trả về True nếu đăng nhập thành công."""
    google_code = st.query_params.get("code")
    if not google_code or st.session_state.get("user"):
        return False
    st.query_params.clear()
    with st.spinner("Đang xác thực với Google…"):
        try:
            firebase_token, refresh_token = exchange_google_code(google_code)
            user = verify_and_load_user(firebase_token)
            if user:
                _save_rt(refresh_token)
                st.session_state.user = user
                return True
            st.error("Không thể xác thực tài khoản. Thử lại.")
        except Exception as e:
            st.error(f"Lỗi Google Sign-In: {e}")
    return False


def show_auth_ui():
    """Hiển thị UI đăng nhập (session restore & OAuth được xử lý ở router)."""
    st.markdown("### 👤 Đăng nhập để tiếp tục")
    render_google_signin_button()


# ---------------------------------------------------------------------------
# Token verification → Supabase profile sync
# ---------------------------------------------------------------------------
def verify_and_load_user(token: str, email: str = "", name: str = "", photo: str = "") -> dict | None:
    init_firebase()   # khởi tạo Firebase SDK để verify_id_token hoạt động
    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception:
        return None

    uid   = decoded["uid"]
    email = decoded.get("email",   "") or email
    name  = decoded.get("name",    "") or name
    photo = decoded.get("picture", "") or photo

    try:
        sdb.upsert_profile(uid, email, name, photo)
        user = sdb.load_user_with_subscription(uid)
        if user:
            return user
    except Exception:
        pass

    # Fallback nếu Supabase lỗi
    return {"uid": uid, "email": email, "name": name or email.split("@")[0],
            "photo": photo, "is_paid": False, "plan": None, "role": "user"}


# ---------------------------------------------------------------------------
# Activate plan / History / Sign-out
# ---------------------------------------------------------------------------
def activate_plan(uid: str, plan: str):
    sdb.activate_subscription(uid, plan, payment_provider="paypal")


def save_music_history(uid: str, topic: str, genre: str, num_tracks: int,
                       result: dict, create_mv: bool = False) -> str:
    """Tạo project mới trong Supabase. Trả về project_id."""
    name = result.get("title") or topic
    return sdb.create_project(
        uid, name, topic, genre, num_tracks, result,
        create_mv=create_mv, auto_expire_hours=72,
    )


def update_history_suno(uid: str, project_id: str, suno_results: dict):
    """Lưu Suno audio URLs vào project (track_audio table)."""
    if not project_id:
        return
    try:
        sdb.save_suno_results(project_id, suno_results)
    except Exception:
        pass


def _parse_dt(s) -> datetime | None:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _project_to_history(proj: dict) -> dict:
    """Chuyển Supabase project dict → format tương thích với session_state.suno_tracks."""
    suno_results: dict = {}
    is_single = proj.get("num_tracks", 1) == 1
    for track in (proj.get("project_tracks") or []):
        track_num = track.get("track_number", 1)
        # Single-track dùng key "single_track" để khớp với music_widget()
        # Multi-track dùng "track_N" (1-indexed)
        key = "single_track" if is_single else f"track_{track_num}"
        audios = sorted(
            track.get("track_audio") or [],
            key=lambda x: x.get("version", "A"),
        )
        if audios:
            suno_results[key] = [
                {
                    "audioUrl":       a.get("audio_url", ""),
                    "streamAudioUrl": a.get("stream_url", ""),
                    "imageUrl":       a.get("image_url", ""),
                    "duration":       float(a.get("duration_secs") or 0),
                    "id":             a.get("suno_id", ""),
                }
                for a in audios
            ]

    return {
        "id":           proj["id"],
        "project_name": proj.get("name", ""),
        "topic":        proj.get("topic", ""),
        "genre":        proj.get("genre", ""),
        "num_tracks":   proj.get("num_tracks", 1),
        "create_mv":    proj.get("create_mv", False),
        "created_at":   _parse_dt(proj.get("created_at")),
        "expire_at":    _parse_dt(proj.get("expires_at")),
        "result":       proj.get("claude_result") or {},
        "suno_results": suno_results,
    }


def get_music_history(uid: str) -> list:
    """Lấy 20 project gần nhất (chưa hết hạn)."""
    try:
        projects = sdb.get_projects(uid, limit=20, include_expired=False)
        return [_project_to_history(p) for p in projects]
    except Exception:
        return []


def sign_out():
    st.session_state.user = None
    st.session_state.pop("is_admin", None)
    st.session_state["_signed_out"]    = True  # chặn try_restore_session() 1 render
    st.session_state["_pending_logout"] = True  # xóa cookie ở render kế (process_pending_rt)
    st.switch_page("views/home.py")


# ---------------------------------------------------------------------------
# Admin — role checks & user management  (Supabase)
# ---------------------------------------------------------------------------
def is_admin(uid: str) -> bool:
    try:
        profile = sdb.get_profile(uid)
        return bool(profile and profile.get("role") == "admin")
    except Exception:
        return False


def get_all_users(limit: int = 200) -> list:
    try:
        return sdb.admin_get_all_users(limit)
    except Exception:
        return []


def admin_update_user(uid: str, updates: dict):
    # Map legacy field names → Supabase field names
    mapped = {}
    if "name" in updates:
        mapped["full_name"] = updates["name"]
    if "role" in updates:
        mapped["role"] = updates["role"]
    if "email" in updates:
        mapped["email"] = updates["email"]
    if mapped:
        sdb.admin_update_user(uid, mapped)


def admin_set_plan(uid: str, plan: str):
    sdb.admin_set_plan(uid, plan)


def admin_extend_plan(uid: str, extra_days: int):
    sdb.admin_extend_plan(uid, extra_days)


def admin_remove_plan(uid: str):
    sdb.admin_remove_plan(uid)


def admin_delete_user_data(uid: str):
    sdb.admin_delete_user_data(uid)


def admin_get_user_history(uid: str, limit: int = 100) -> list:
    projects = sdb.admin_get_user_projects(uid, limit)
    return [_project_to_history(p) for p in projects]


def admin_delete_history_item(uid: str, project_id: str):
    sdb.admin_delete_project(project_id)


def admin_update_history_item(uid: str, project_id: str, updates: dict):
    # Map project_name → name
    mapped = {}
    if "project_name" in updates:
        mapped["name"] = updates["project_name"]
    for k in ("topic", "genre", "status"):
        if k in updates:
            mapped[k] = updates[k]
    if mapped:
        sdb.admin_update_project(project_id, mapped)


# ---------------------------------------------------------------------------
# User self-management — projects / history  (Supabase)
# ---------------------------------------------------------------------------
def get_all_user_history(uid: str, limit: int = 100) -> list:
    """Lấy toàn bộ project (không lọc hết hạn) cho trang Tài khoản."""
    projects = sdb.get_projects(uid, limit=limit, include_expired=True)
    return [_project_to_history(p) for p in projects]


def delete_history_item(uid: str, project_id: str):
    sdb.delete_project(project_id)


def update_history_item(uid: str, project_id: str, updates: dict):
    mapped = {}
    if "project_name" in updates:
        mapped["name"] = updates["project_name"]
    for k in ("topic", "genre"):
        if k in updates:
            mapped[k] = updates[k]
    if mapped:
        sdb.update_project(project_id, mapped)


# ---------------------------------------------------------------------------
# Admin — payment / refund
# ---------------------------------------------------------------------------
def admin_get_payments(status: str = "completed", limit: int = 100) -> list:
    try:
        return sdb.admin_get_payments(status=status, limit=limit)
    except Exception:
        return []


def admin_process_refund(payment_id: str, user_id: str, reason: str = "") -> bool:
    try:
        return sdb.admin_process_refund(payment_id, user_id, reason)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Credits / Coins
# ---------------------------------------------------------------------------
def deduct_coins(uid: str, amount: int = 1,
                 action: str = "deduct", description: str = "") -> int:
    """Trừ `amount` Xu và ghi log. Trả về số Xu còn lại."""
    try:
        return sdb.deduct_coins(uid, amount, action=action, description=description)
    except Exception:
        return 0


def deduct_credit(uid: str) -> int:
    """Alias — trừ 1 Xu (tương thích ngược)."""
    return deduct_coins(uid, 1)


def add_credits_topup(uid: str, credits_to_add: int) -> dict:
    try:
        return sdb.add_credits_topup(uid, credits_to_add)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Support tickets (user-facing)
# ---------------------------------------------------------------------------
def create_support_ticket(uid: str, issue_type: str, description: str,
                          bank_details: str = "", payment_id: str = "") -> dict:
    try:
        return sdb.create_support_ticket(uid, issue_type, description, bank_details, payment_id)
    except Exception:
        return {}


def get_user_tickets(uid: str) -> list:
    try:
        return sdb.get_user_tickets(uid)
    except Exception:
        return []


def get_user_completed_payments(uid: str) -> list:
    try:
        return sdb.get_user_completed_payments(uid)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Support tickets (admin-facing)
# ---------------------------------------------------------------------------
def admin_get_tickets(status: str = "pending", limit: int = 100) -> list:
    try:
        return sdb.admin_get_tickets(status=status, limit=limit)
    except Exception:
        return []


def admin_resolve_ticket(ticket_id: str, note: str = "", status: str = "resolved"):
    try:
        sdb.admin_resolve_ticket(ticket_id, note, status)
    except Exception:
        pass
