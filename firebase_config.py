import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import streamlit as st


def init_firebase():
    """Khởi tạo Firebase Admin SDK (chỉ một lần). Trả về Firestore client."""
    if not firebase_admin._apps:
        # Ưu tiên biến môi trường (Streamlit Cloud secrets)
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
        if raw:
            cred = credentials.Certificate(json.loads(raw))
        elif os.path.exists("firebase_service_account.json"):
            cred = credentials.Certificate("firebase_service_account.json")
        else:
            st.error(
                "⚠️ Chưa cấu hình Firebase Service Account cho project **nhacheocon**.\n\n"
                "**Cách 1 — Streamlit Cloud secrets:**\n"
                "Thêm key `FIREBASE_SERVICE_ACCOUNT` = nội dung file JSON service account.\n\n"
                "**Cách 2 — Local:**\n"
                "Đặt file `firebase_service_account.json` vào thư mục gốc."
            )
            st.stop()
        firebase_admin.initialize_app(cred)
    return firestore.client()
