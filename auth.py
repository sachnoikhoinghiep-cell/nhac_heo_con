import streamlit as st
import streamlit.components.v1 as components
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

# Firebase REST API key (public — dùng cho client-side auth)
FIREBASE_API_KEY = "AIzaSyBl3BYwj_E3v4ppfFUHXY1WpWx7r_6H5bA"
FIREBASE_REST    = "https://identitytoolkit.googleapis.com/v1/accounts"

def _google_client_id() -> str:
    """Đọc Google OAuth Web Client ID từ secrets hoặc env."""
    try:
        return st.secrets["GOOGLE_CLIENT_ID"]
    except Exception:
        return os.environ.get("GOOGLE_CLIENT_ID", "")

def _redirect_uri() -> str:
    """URL callback sau khi Google xác thực — phải khớp với cấu hình OAuth."""
    try:
        return st.secrets["REDIRECT_URI"]
    except Exception:
        return os.environ.get("REDIRECT_URI", "http://localhost:8501")


# ---------------------------------------------------------------------------
# Google OAuth 2.0 — Implicit flow (redirect window.top, bypass iframe sandbox)
# ---------------------------------------------------------------------------
def _build_google_auth_url() -> str:
    client_id    = _google_client_id()
    redirect_uri = _redirect_uri()
    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={urllib.parse.quote(client_id)}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        "&response_type=token"
        "&scope=openid%20email%20profile"
        "&prompt=select_account"
    )


def render_google_signin_button():
    """Render nút Google Sign-In dưới dạng thẻ <a> thật — click trực tiếp điều hướng trình duyệt."""
    if not _google_client_id():
        st.info("💡 Thêm `GOOGLE_CLIENT_ID` và `REDIRECT_URI` vào Streamlit secrets để bật Google Sign-In.")
        return

    auth_url = _build_google_auth_url()
    st.markdown(
        f"""
        <a href="{auth_url}" target="_top" style="
            display:flex; align-items:center; justify-content:center; gap:10px;
            width:100%; padding:11px 0; margin-bottom:4px;
            background:#fff; border:1.5px solid #dadce0; border-radius:8px;
            font-size:15px; font-weight:600; color:#3c4043;
            text-decoration:none; box-shadow:0 1px 3px rgba(0,0,0,.12);
        ">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="20"/>
            Đăng nhập bằng Google
        </a>
        """,
        unsafe_allow_html=True,
    )


def handle_google_hash_fragment():
    """
    Đọc #access_token từ URL hash (Google trả về sau OAuth) và chuyển sang query param.
    Phải render trên mỗi lần load trang để bắt được callback.
    """
    components.html("""
    <script>
    (function() {
        const hash = window.parent.location.hash;
        if (!hash || !hash.includes('access_token')) return;
        const params = new URLSearchParams(hash.slice(1));
        const token  = params.get('access_token');
        if (!token) return;
        // Xóa hash, thêm token vào query string để Python đọc được
        const url = new URL(window.parent.location.href);
        url.hash = '';
        url.searchParams.set('google_access_token', token);
        window.parent.location.replace(url.toString());
    })();
    </script>
    """, height=0)


def firebase_signin_with_google(access_token: str) -> str:
    """Đổi Google access token lấy Firebase ID token qua signInWithIdp."""
    redirect_uri = _redirect_uri()
    resp = requests.post(
        f"{FIREBASE_REST}:signInWithIdp?key={FIREBASE_API_KEY}",
        json={
            "postBody":             f"access_token={access_token}&providerId=google.com",
            "requestUri":           redirect_uri,
            "returnIdpCredential":  True,
            "returnSecureToken":    True,
        },
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"]["message"])
    return data["idToken"]


# ---------------------------------------------------------------------------
# Firebase REST API — Email/Password (không dùng JS SDK, không lỗi iframe)
# ---------------------------------------------------------------------------
def firebase_email_login(email: str, password: str) -> str:
    """Đăng nhập, trả về idToken."""
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
    """Đăng ký tài khoản mới, trả về idToken."""
    resp = requests.post(
        f"{FIREBASE_REST}:signUp?key={FIREBASE_API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        msg = data["error"]["message"]
        friendly = {
            "EMAIL_EXISTS":              "Email này đã được đăng ký.",
            "WEAK_PASSWORD":             "Mật khẩu phải có ít nhất 6 ký tự.",
            "INVALID_EMAIL":             "Địa chỉ email không hợp lệ.",
        }
        raise ValueError(friendly.get(msg, msg))
    return data["idToken"]


def firebase_reset_password(email: str):
    """Gửi email đặt lại mật khẩu."""
    resp = requests.post(
        f"{FIREBASE_REST}:sendOobCode?key={FIREBASE_API_KEY}",
        json={"requestType": "PASSWORD_RESET", "email": email},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"]["message"])


# ---------------------------------------------------------------------------
# Streamlit login / register UI
# ---------------------------------------------------------------------------
def show_auth_ui():
    """Hiển thị form đăng nhập / đăng ký — không dùng iframe, không lỗi môi trường."""
    st.markdown("### 👤 Đăng nhập để tiếp tục")

    # ── Bắt callback Google OAuth (access_token trong URL hash → query param) ──
    handle_google_hash_fragment()
    g_token = st.query_params.get("google_access_token")
    if g_token:
        st.query_params.clear()
        with st.spinner("Đang xác thực Google…"):
            try:
                id_token = firebase_signin_with_google(g_token)
                user     = verify_and_load_user(id_token)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Không thể xác thực. Thử lại.")
            except Exception as e:
                st.error(f"Lỗi Google Sign-In: {e}")

    # ── Nút Google Sign-In (anchor tag thật, không qua iframe) ─────────────
    render_google_signin_button()
    st.divider()

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
                    else:
                        st.error("Không thể xác thực tài khoản. Thử lại.")
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
                        # Cập nhật displayName sau khi đăng ký
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
# Token verification & user loading
# ---------------------------------------------------------------------------
def verify_and_load_user(token: str, email: str = "", name: str = "", photo: str = "") -> dict | None:
    """Xác minh Firebase ID token, tạo/load user trên Firestore."""
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
            "email":      email,
            "name":       name,
            "photo_url":  photo,
            "created_at": now,
            "plan":       None,
            "is_paid":    False,
            "expires_at": None,
        })
        return {"uid": uid, "email": email, "name": name, "photo": photo,
                "is_paid": False, "plan": None}

    data       = doc.to_dict()
    expires_at = data.get("expires_at")
    is_paid    = data.get("is_paid", False)

    if is_paid and expires_at and expires_at < now:
        user_ref.update({"is_paid": False})
        is_paid = False

    # Cập nhật name nếu lần đầu đăng ký có tên
    if name and not data.get("name"):
        user_ref.update({"name": name})

    return {
        "uid":     uid,
        "email":   email or data.get("email", ""),
        "name":    name  or data.get("name", email.split("@")[0]),
        "photo":   photo or data.get("photo_url", ""),
        "is_paid": is_paid,
        "plan":    data.get("plan"),
    }


# ---------------------------------------------------------------------------
# Activate plan after payment
# ---------------------------------------------------------------------------
def activate_plan(uid: str, plan: str):
    db      = init_firebase()
    now     = datetime.now(timezone.utc)
    expires = now + PLAN_DURATION[plan]
    db.collection("users").document(uid).update({
        "is_paid":    True,
        "plan":       plan,
        "paid_at":    now,
        "expires_at": expires,
    })


# ---------------------------------------------------------------------------
# Music history
# ---------------------------------------------------------------------------
def save_music_history(uid: str, topic: str, genre: str, num_tracks: int, result: dict):
    db = init_firebase()
    db.collection("users").document(uid).collection("music_history").add({
        "topic":      topic,
        "genre":      genre,
        "num_tracks": num_tracks,
        "created_at": datetime.now(timezone.utc),
        "result":     result,
    })


def get_music_history(uid: str) -> list:
    db   = init_firebase()
    docs = (
        db.collection("users").document(uid)
          .collection("music_history")
          .order_by("created_at", direction=fs.Query.DESCENDING)
          .limit(20)
          .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]


# ---------------------------------------------------------------------------
# Sign-out
# ---------------------------------------------------------------------------
def sign_out():
    st.session_state.user = None
    st.rerun()
