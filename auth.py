import streamlit as st
import requests
import urllib.parse
import os
import json
from firebase_admin import auth, firestore as fs
from firebase_config import init_firebase
from datetime import datetime, timezone, timedelta
import extra_streamlit_components as stx

_COOKIE_KEY  = "nhacheocon_rt"
_COOKIE_DAYS = 30

def _cookie_mgr():
    return stx.CookieManager(key="nhacheocon_cm")

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
_APIKEY_COOKIE = "nhacheocon_ak"

def save_api_keys(anthropic: str, google: str, suno: str, fal: str = ""):
    """Lưu API keys vào cookie (fallback cho user chưa login)."""
    data = json.dumps({"a": anthropic, "g": google, "s": suno, "f": fal})
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
                "anthropic": d.get("a", ""), "google": d.get("g", ""),
                "suno": d.get("s", ""), "fal": d.get("f", ""),
            }
    except Exception:
        pass
    return {}

def save_user_api_keys(uid: str, anthropic: str, google: str, suno: str, fal: str = ""):
    """Lưu API keys vào Firestore gắn với tài khoản user."""
    db = init_firebase()
    db.collection("users").document(uid).update({
        "api_keys": {"anthropic": anthropic, "google": google, "suno": suno, "fal": fal},
    })

def load_user_api_keys(uid: str) -> dict:
    """Đọc API keys từ Firestore của user. Trả về dict rỗng nếu chưa lưu."""
    try:
        db  = init_firebase()
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            return doc.to_dict().get("api_keys") or {}
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------------------
# Preset persistence
# ---------------------------------------------------------------------------
_PRESETS_COOKIE = "nhacheocon_presets"
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
# Token verification & Firestore
# ---------------------------------------------------------------------------
def verify_and_load_user(token: str, email: str = "", name: str = "", photo: str = "") -> dict | None:
    db = init_firebase()
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        return None

    uid   = decoded["uid"]
    email = decoded.get("email", "") or email
    name  = decoded.get("name",  "") or name
    photo = decoded.get("picture", "") or photo
    now   = datetime.now(timezone.utc)

    user_ref = db.collection("users").document(uid)
    doc      = user_ref.get()

    if not doc.exists:
        user_ref.set({
            "email": email, "name": name, "photo_url": photo,
            "created_at": now, "plan": None, "is_paid": False, "expires_at": None,
        })
        return {"uid": uid, "email": email, "name": name, "photo": photo,
                "is_paid": False, "plan": None}

    data       = doc.to_dict()
    expires_at = data.get("expires_at")
    is_paid    = data.get("is_paid", False)

    if is_paid and expires_at and expires_at < now:
        user_ref.update({"is_paid": False})
        is_paid = False

    if name and not data.get("name"):
        user_ref.update({"name": name})

    return {
        "uid":     uid,
        "email":   email or data.get("email", ""),
        "name":    name  or data.get("name", email.split("@")[0] if email else "User"),
        "photo":   photo or data.get("photo_url", ""),
        "is_paid": is_paid,
        "plan":    data.get("plan"),
    }


# ---------------------------------------------------------------------------
# Activate plan / History / Sign-out
# ---------------------------------------------------------------------------
def activate_plan(uid: str, plan: str):
    db      = init_firebase()
    now     = datetime.now(timezone.utc)
    expires = now + PLAN_DURATION[plan]
    db.collection("users").document(uid).update({
        "is_paid": True, "plan": plan, "paid_at": now, "expires_at": expires,
    })


def save_music_history(uid: str, topic: str, genre: str, num_tracks: int,
                       result: dict, create_mv: bool = False) -> str:
    """Save a generation project to Firestore. Returns doc_id for later Suno updates."""
    db           = init_firebase()
    now          = datetime.now(timezone.utc)
    project_name = result.get("title") or topic   # Claude-generated title as project name
    _, doc_ref   = db.collection("users").document(uid).collection("music_history").add({
        "project_name": project_name,
        "topic":        topic,
        "genre":        genre,
        "num_tracks":   num_tracks,
        "create_mv":    create_mv,
        "created_at":   now,
        "expire_at":    now + timedelta(hours=72),
        "result":       result,
        "suno_results": {},
    })
    return doc_ref.id


def update_history_suno(uid: str, doc_id: str, suno_results: dict):
    """Patch a history doc with Suno audio URLs after generation completes."""
    if not doc_id:
        return
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").document(doc_id).update({
        "suno_results": suno_results,
    })


def get_music_history(uid: str) -> list:
    db      = init_firebase()
    now     = datetime.now(timezone.utc)
    cutoff  = now - timedelta(hours=72)
    col     = db.collection("users").document(uid).collection("music_history")

    # Lấy 20 bài gần nhất, lọc & xóa bài đã hết hạn
    docs    = list(col.order_by("created_at", direction=fs.Query.DESCENDING).limit(20).stream())
    valid, to_delete = [], []
    for doc in docs:
        d       = doc.to_dict()
        created = d.get("created_at")
        if created and created < cutoff:
            to_delete.append(doc.reference)
        else:
            valid.append({"id": doc.id, **d})

    if to_delete:
        batch = db.batch()
        for ref in to_delete:
            batch.delete(ref)
        batch.commit()

    return valid


def sign_out():
    st.session_state.user = None
    st.session_state.pop("is_admin", None)
    st.session_state["_signed_out"]    = True  # chặn try_restore_session() 1 render
    st.session_state["_pending_logout"] = True  # xóa cookie ở render kế (process_pending_rt)
    st.switch_page("views/home.py")


# ---------------------------------------------------------------------------
# Admin — role checks & user management
# ---------------------------------------------------------------------------
def is_admin(uid: str) -> bool:
    db = init_firebase()
    try:
        doc = db.collection("users").document(uid).get()
        return doc.exists and doc.to_dict().get("role") == "admin"
    except Exception:
        return False


def get_all_users(limit: int = 200) -> list:
    db = init_firebase()
    now = datetime.now(timezone.utc)
    try:
        docs = (
            db.collection("users")
            .order_by("created_at", direction=fs.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        result = []
        for doc in docs:
            data = doc.to_dict()
            expires_at = data.get("expires_at")
            is_paid = data.get("is_paid", False)
            if is_paid and expires_at and expires_at < now:
                is_paid = False
            result.append({
                "uid":        doc.id,
                "email":      data.get("email", ""),
                "name":       data.get("name", ""),
                "photo_url":  data.get("photo_url", ""),
                "plan":       data.get("plan"),
                "is_paid":    is_paid,
                "paid_at":    data.get("paid_at"),
                "expires_at": expires_at,
                "created_at": data.get("created_at"),
                "role":       data.get("role", "user"),
            })
        return result
    except Exception:
        return []


def admin_update_user(uid: str, updates: dict):
    db = init_firebase()
    db.collection("users").document(uid).update(updates)


def admin_set_plan(uid: str, plan: str):
    activate_plan(uid, plan)


def admin_extend_plan(uid: str, extra_days: int):
    db = init_firebase()
    now = datetime.now(timezone.utc)
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        current_expires = doc.to_dict().get("expires_at")
        base = max(current_expires, now) if current_expires and current_expires > now else now
        db.collection("users").document(uid).update({
            "is_paid":    True,
            "expires_at": base + timedelta(days=extra_days),
        })


def admin_remove_plan(uid: str):
    db = init_firebase()
    db.collection("users").document(uid).update({
        "is_paid":    False,
        "plan":       None,
        "expires_at": None,
    })


def admin_delete_user_data(uid: str):
    """Xóa toàn bộ dữ liệu user khỏi Firestore (không xóa Firebase Auth account)."""
    db = init_firebase()
    history_ref = db.collection("users").document(uid).collection("music_history")
    batch = db.batch()
    for doc in history_ref.stream():
        batch.delete(doc.reference)
    batch.commit()
    db.collection("users").document(uid).delete()


def admin_get_user_history(uid: str, limit: int = 100) -> list:
    db = init_firebase()
    col = db.collection("users").document(uid).collection("music_history")
    docs = list(
        col.order_by("created_at", direction=fs.Query.DESCENDING).limit(limit).stream()
    )
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def admin_delete_history_item(uid: str, doc_id: str):
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").document(doc_id).delete()


def admin_update_history_item(uid: str, doc_id: str, updates: dict):
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").document(doc_id).update(updates)


# ---------------------------------------------------------------------------
# User self-management — projects / history
# ---------------------------------------------------------------------------
def get_all_user_history(uid: str, limit: int = 100) -> list:
    """Lấy toàn bộ lịch sử (không lọc 72h) cho trang Tài khoản."""
    db = init_firebase()
    col = db.collection("users").document(uid).collection("music_history")
    docs = list(
        col.order_by("created_at", direction=fs.Query.DESCENDING).limit(limit).stream()
    )
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def delete_history_item(uid: str, doc_id: str):
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").document(doc_id).delete()


def update_history_item(uid: str, doc_id: str, updates: dict):
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").document(doc_id).update(updates)
