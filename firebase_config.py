import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import streamlit as st


def init_firebase():
    """Khởi tạo Firebase Admin SDK (chỉ một lần). Trả về Firestore client."""
    if not firebase_admin._apps:
        sa_info = None

        # 1. st.secrets (VPS tự host với secrets.toml + Streamlit Cloud)
        try:
            raw = st.secrets.get("FIREBASE_SERVICE_ACCOUNT", "")
            if raw:
                sa_info = json.loads(raw)
        except Exception:
            pass

        # 2. Biến môi trường (Streamlit Cloud tự inject env var)
        if sa_info is None:
            raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
            if raw:
                try:
                    sa_info = json.loads(raw)
                except Exception:
                    pass

        if sa_info is not None:
            cred = credentials.Certificate(sa_info)
        elif os.path.exists("firebase_service_account.json"):
            cred = credentials.Certificate("firebase_service_account.json")
        else:
            st.error(
                "⚠️ Chưa cấu hình Firebase Service Account cho project **nhacheocon**.\n\n"
                "**Cách 1 — Streamlit Cloud secrets:**\n"
                "Thêm key `FIREBASE_SERVICE_ACCOUNT` = nội dung file JSON service account.\n\n"
                "**Cách 2 — Local / VPS:**\n"
                "Đặt file `firebase_service_account.json` vào thư mục gốc."
            )
            st.stop()
            return

        firebase_admin.initialize_app(cred)
    return firestore.client()
