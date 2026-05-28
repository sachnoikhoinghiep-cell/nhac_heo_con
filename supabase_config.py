import os
import streamlit as st
from supabase import create_client, Client

_client: Client | None = None


def get_supabase() -> Client:
    """Singleton Supabase client dùng service_role key (server-side only)."""
    global _client
    if _client is not None:
        return _client

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")

    if not url or not key:
        raise RuntimeError(
            "Thiếu SUPABASE_URL hoặc SUPABASE_SERVICE_KEY trong secrets."
        )

    _client = create_client(url, key)
    return _client
