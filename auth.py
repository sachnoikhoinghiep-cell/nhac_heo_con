import streamlit as st
import streamlit.components.v1 as components
from firebase_admin import auth, firestore as fs
from firebase_config import init_firebase
from datetime import datetime, timezone, timedelta

PLAN_DURATION = {
    "Ngày":  timedelta(days=1),
    "Tuần":  timedelta(weeks=1),
    "Tháng": timedelta(days=30),
    "Năm":   timedelta(days=365),
}


# ---------------------------------------------------------------------------
# Google Sign-In component (Firebase JS SDK)
# ---------------------------------------------------------------------------
FIREBASE_WEB_CONFIG = {
    "apiKey":            "AIzaSyBl3BYwj_E3v4ppfFUHXY1WpWx7r_6H5bA",
    "authDomain":        "nhacheocon.firebaseapp.com",
    "projectId":         "nhacheocon",
    "storageBucket":     "nhacheocon.firebasestorage.app",
    "messagingSenderId": "551560059881",
    "appId":             "1:551560059881:web:863e343e5f273c8532c978",
}


def google_signin_component():
    """Hiển thị nút Google Sign-In; sau khi đăng nhập trả token về qua URL param."""
    import json
    cfg_json = json.dumps(FIREBASE_WEB_CONFIG)
    html = f"""
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
    <style>
      body {{ margin:0; font-family: sans-serif; background: transparent; }}
      #btn {{
        display:flex; align-items:center; gap:12px; padding:12px 24px;
        background:#fff; border:1px solid #ddd; border-radius:8px;
        cursor:pointer; font-size:16px; font-weight:600; color:#333;
        box-shadow: 0 2px 8px rgba(0,0,0,.12);
      }}
      #btn:hover {{ background:#f5f5f5; }}
      #btn img {{ width:24px; }}
      #err {{ color:red; margin-top:10px; font-size:13px; }}
    </style>
    <button id="btn" onclick="signIn()">
      <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"/>
      Đăng nhập bằng Google
    </button>
    <div id="err"></div>
    <script>
      const cfg = {cfg_json};
      if (!firebase.apps.length) firebase.initializeApp(cfg);
      const fbAuth = firebase.auth();

      function signIn() {{
        const btn = document.getElementById('btn');
        btn.disabled = true;
        btn.innerText = 'Đang đăng nhập…';
        const provider = new firebase.auth.GoogleAuthProvider();
        fbAuth.signInWithPopup(provider)
          .then(result => result.user.getIdToken())
          .then(token => {{
            const url = new URL(window.parent.location.href);
            url.searchParams.set('firebase_token', token);
            window.parent.location.href = url.toString();
          }})
          .catch(err => {{
            document.getElementById('err').innerText = 'Lỗi: ' + err.message;
            btn.disabled = false;
            btn.innerHTML =
              '<img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"/> Đăng nhập bằng Google';
          }});
      }}
    </script>
    """
    components.html(html, height=110)


# ---------------------------------------------------------------------------
# Token verification & user loading
# ---------------------------------------------------------------------------
def verify_and_load_user(token: str) -> dict | None:
    """Xác minh Firebase ID token, tạo/load user trên Firestore."""
    db = init_firebase()
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        return None

    uid        = decoded["uid"]
    email      = decoded.get("email", "")
    name       = decoded.get("name", "")
    photo      = decoded.get("picture", "")
    now        = datetime.now(timezone.utc)
    user_ref   = db.collection("users").document(uid)
    doc        = user_ref.get()

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

    # Tự động hết hạn
    if is_paid and expires_at and expires_at < now:
        user_ref.update({"is_paid": False})
        is_paid = False

    return {
        "uid":     uid,
        "email":   email or data.get("email", ""),
        "name":    name  or data.get("name", ""),
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
    st.query_params.clear()
    st.rerun()
