import streamlit as st
import requests
import urllib.parse
import os
from firebase_admin import auth, firestore as fs
from firebase_config import init_firebase
from datetime import datetime, timezone, timedelta

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


def exchange_google_code(code: str) -> str:
    """Đổi authorization code → Google tokens → Firebase ID token."""
    # Bước 1: đổi code lấy Google token
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

    # Bước 2: đổi Google token lấy Firebase ID token
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
    return data2["idToken"]


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
def show_auth_ui():
    st.markdown("### 👤 Đăng nhập để tiếp tục")

    # ── Xử lý callback Google OAuth (?code=...) ────────────────────────────
    google_code = st.query_params.get("code")
    if google_code and not st.session_state.get("user"):
        st.query_params.clear()
        with st.spinner("Đang xác thực với Google…"):
            try:
                firebase_token = exchange_google_code(google_code)
                user = verify_and_load_user(firebase_token)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Không thể xác thực tài khoản. Thử lại.")
            except Exception as e:
                st.error(f"Lỗi Google Sign-In: {e}")

    # ── Nút Google (dùng st.link_button — không cần iframe) ────────────────
    render_google_signin_button()
    st.divider()

    # ── Form email/password ─────────────────────────────────────────────────
    tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])

    with tab_login:
        with st.form("login_form"):
            email    = st.text_input("Email", placeholder="you@gmail.com")
            password = st.text_input("Mật khẩu", type="password")
            col1, col2 = st.columns([2, 1])
            submitted = col1.form_submit_button("Đăng nhập", use_container_width=True, type="primary")
            reset_btn = col2.form_submit_button("Quên mật khẩu?", use_container_width=True)

        if submitted and email and password:
            with st.spinner("Đang xác thực…"):
                try:
                    token = firebase_email_login(email, password)
                    user  = verify_and_load_user(token, email=email)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                except ValueError as e:
                    st.error(str(e))

        if reset_btn and email:
            try:
                firebase_reset_password(email)
                st.success(f"Đã gửi email đặt lại mật khẩu tới **{email}**")
            except Exception as e:
                st.error(str(e))
        elif reset_btn and not email:
            st.warning("Nhập email trước rồi bấm 'Quên mật khẩu?'")

    with tab_register:
        with st.form("register_form"):
            r_name     = st.text_input("Tên hiển thị", placeholder="Nguyễn Văn A")
            r_email    = st.text_input("Email", placeholder="you@gmail.com")
            r_password = st.text_input("Mật khẩu (tối thiểu 6 ký tự)", type="password")
            r_confirm  = st.text_input("Xác nhận mật khẩu", type="password")
            r_submit   = st.form_submit_button("Tạo tài khoản", use_container_width=True, type="primary")

        if r_submit:
            if not all([r_name, r_email, r_password, r_confirm]):
                st.warning("Vui lòng điền đầy đủ thông tin.")
            elif r_password != r_confirm:
                st.error("Mật khẩu xác nhận không khớp.")
            else:
                with st.spinner("Đang tạo tài khoản…"):
                    try:
                        token = firebase_email_register(r_email, r_password)
                        try:
                            fb_user = auth.get_user_by_email(r_email)
                            auth.update_user(fb_user.uid, display_name=r_name)
                        except Exception:
                            pass
                        user = verify_and_load_user(token, email=r_email, name=r_name)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                    except ValueError as e:
                        st.error(str(e))


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
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").add({
        "topic": topic, "genre": genre, "num_tracks": num_tracks,
        "created_at": datetime.now(timezone.utc), "result": result,
    })


def get_music_history(uid: str) -> list:
    db   = init_firebase()
    docs = (
        db.collection("users").document(uid)
          .collection("music_history")
          .order_by("created_at", direction=fs.Query.DESCENDING)
          .limit(20).stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]


def sign_out():
    st.session_state.user = None
    st.rerun()
