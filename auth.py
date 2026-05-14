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

def _save_rt(refresh_token: str):
    try:
        _cookie_mgr().set(
            _COOKIE_KEY, refresh_token,
            expires_at=datetime.now() + timedelta(days=_COOKIE_DAYS),
        )
    except Exception:
        pass

def _load_rt() -> str:
    try:
        return _cookie_mgr().get(_COOKIE_KEY) or ""
    except Exception:
        return ""

def _clear_rt():
    try:
        _cookie_mgr().delete(_COOKIE_KEY)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# API key persistence
# ---------------------------------------------------------------------------
_APIKEY_COOKIE = "nhacheocon_ak"

def save_api_keys(anthropic: str, google: str, suno: str):
    data = json.dumps({"a": anthropic, "g": google, "s": suno})
    try:
        _cookie_mgr().set(
            _APIKEY_COOKIE, data,
            expires_at=datetime.now() + timedelta(days=365),
        )
    except Exception:
        pass

def load_api_keys() -> dict:
    try:
        raw = _cookie_mgr().get(_APIKEY_COOKIE) or ""
        if raw:
            d = json.loads(raw)
            return {"anthropic": d.get("a", ""), "google": d.get("g", ""), "suno": d.get("s", "")}
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
        raw = _cookie_mgr().get(_PRESETS_COOKIE) or "[]"
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


def save_music_history(uid: str, topic: str, genre: str, num_tracks: int, result: dict):
    db  = init_firebase()
    now = datetime.now(timezone.utc)
    db.collection("users").document(uid).collection("music_history").add({
        "topic": topic, "genre": genre, "num_tracks": num_tracks,
        "created_at": now,
        "expire_at":  now + timedelta(hours=72),
        "result": result,
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
    _clear_rt()
    st.session_state.user = None
    st.rerun()
