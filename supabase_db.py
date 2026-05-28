"""
supabase_db.py — Toàn bộ DB operations cho nhacheocon dùng Supabase.

Chiến lược:
  - Firebase Auth giữ nguyên (Google OAuth, session token)
  - Supabase thay thế Firestore làm database chính
  - profiles.id = Firebase UID (text)
  - Dùng service_role key → bypass RLS, bảo mật ở tầng ứng dụng

Secrets cần thêm vào .streamlit/secrets.toml:
  SUPABASE_URL        = "https://xxxx.supabase.co"
  SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIs..."
  ENCRYPTION_KEY       = "chuỗi bí mật bất kỳ dùng để mã hoá API keys"
"""

import os
import base64
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from supabase_config import get_supabase

# ---------------------------------------------------------------------------
# Mã hoá API keys (Fernet symmetric)
# ---------------------------------------------------------------------------
def _fernet():
    try:
        import streamlit as st
        secret = st.secrets.get("ENCRYPTION_KEY", "")
    except Exception:
        secret = os.environ.get("ENCRYPTION_KEY", "")

    if not secret:
        raise RuntimeError("ENCRYPTION_KEY chưa được cấu hình trong secrets.")

    from cryptography.fernet import Fernet
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def _encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def _decrypt(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode()).decode()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _from_iso(s) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


# ===========================================================================
# USER / PROFILE
# ===========================================================================

def upsert_profile(uid: str, email: str, name: str = "", photo_url: str = "") -> dict:
    """Tạo mới hoặc cập nhật profile. Trả về dict profile."""
    db = get_supabase()
    data = {
        "id":         uid,
        "email":      email,
        "full_name":  name,
        "avatar_url": photo_url,
        "updated_at": _now(),
    }
    result = (
        db.table("profiles")
        .upsert(data, on_conflict="id", ignore_duplicates=False)
        .execute()
    )
    return result.data[0] if result.data else data


def get_profile(uid: str) -> Optional[dict]:
    """Lấy profile theo UID. Trả về None nếu chưa tồn tại."""
    db = get_supabase()
    result = db.table("profiles").select("*").eq("id", uid).maybe_single().execute()
    return result.data


def update_profile(uid: str, updates: dict):
    """Cập nhật một số trường trong profile."""
    updates["updated_at"] = _now()
    get_supabase().table("profiles").update(updates).eq("id", uid).execute()


# ===========================================================================
# SUBSCRIPTION / PLAN
# ===========================================================================

PLAN_NAME_TO_DAYS = {
    "Ngày": 1, "Tuần": 7, "Tháng": 30, "Năm": 365,
}


def get_plan_id(plan_name: str) -> Optional[int]:
    """Trả về subscription_plans.id theo tên gói."""
    db = get_supabase()
    result = (
        db.table("subscription_plans")
        .select("id")
        .eq("name", plan_name)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    return result.data["id"] if result.data else None


def activate_subscription(uid: str, plan_name: str,
                          payment_provider: str = "paypal",
                          payment_reference: str = "") -> dict:
    """
    Hủy gói cũ (nếu có) + tạo subscription mới active.
    Trả về dict subscription vừa tạo.
    """
    db   = get_supabase()
    now  = datetime.now(timezone.utc)
    days = PLAN_NAME_TO_DAYS.get(plan_name, 30)

    # Hủy gói active cũ
    db.table("user_subscriptions").update({"status": "cancelled"}).eq(
        "user_id", uid
    ).eq("status", "active").execute()

    plan_id = get_plan_id(plan_name)
    if plan_id is None:
        raise ValueError(f"Gói '{plan_name}' không tồn tại trong subscription_plans.")

    row = {
        "user_id":            uid,
        "plan_id":            plan_id,
        "status":             "active",
        "started_at":         now.isoformat(),
        "expires_at":         (now + timedelta(days=days)).isoformat(),
        "paid_at":            now.isoformat(),
        "payment_provider":   payment_provider,
        "payment_reference":  payment_reference,
    }
    result = db.table("user_subscriptions").insert(row).execute()
    return result.data[0]


def get_active_subscription(uid: str) -> Optional[dict]:
    """
    Trả về dict subscription đang active của user,
    bao gồm plan_name và expires_at. None nếu không có.
    """
    db = get_supabase()
    result = (
        db.table("active_subscriptions")
        .select("*")
        .eq("user_id", uid)
        .maybe_single()
        .execute()
    )
    return result.data


def deactivate_subscription(uid: str):
    """Thu hồi gói — đặt tất cả active subs thành cancelled."""
    get_supabase().table("user_subscriptions").update(
        {"status": "cancelled"}
    ).eq("user_id", uid).eq("status", "active").execute()


def extend_subscription(uid: str, extra_days: int):
    """Gia hạn gói đang active thêm N ngày."""
    db  = get_supabase()
    now = datetime.now(timezone.utc)

    # Lấy expires_at hiện tại
    result = (
        db.table("user_subscriptions")
        .select("id, expires_at")
        .eq("user_id", uid)
        .eq("status", "active")
        .order("expires_at", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return

    current = _from_iso(result.data["expires_at"])
    base    = max(current, now) if current else now
    new_exp = (base + timedelta(days=extra_days)).isoformat()

    db.table("user_subscriptions").update({"expires_at": new_exp}).eq(
        "id", result.data["id"]
    ).execute()


def load_user_with_subscription(uid: str) -> dict:
    """
    Lấy profile + subscription active, trả về dict
    tương thích với st.session_state.user hiện tại.
    """
    profile = get_profile(uid)
    if not profile:
        return {}

    sub = get_active_subscription(uid)
    is_paid = sub is not None

    return {
        "uid":     uid,
        "email":   profile.get("email", ""),
        "name":    profile.get("full_name", ""),
        "photo":   profile.get("avatar_url", ""),
        "role":    profile.get("role", "user"),
        "is_paid": is_paid,
        "plan":    sub["plan_name"] if sub else None,
    }


# ===========================================================================
# API KEYS
# ===========================================================================

def save_api_keys(uid: str, anthropic: str = "", google: str = "",
                  suno: str = "", fal: str = ""):
    """Lưu (upsert) API keys — mã hoá từng key trước khi ghi."""
    db  = get_supabase()
    rows = []
    for provider, value in [("anthropic", anthropic), ("google", google),
                             ("suno", suno), ("fal", fal)]:
        if value:
            rows.append({
                "user_id":       uid,
                "provider":      provider,
                "encrypted_key": _encrypt(value),
                "updated_at":    _now(),
            })
    if rows:
        db.table("user_api_keys").upsert(
            rows, on_conflict="user_id,provider"
        ).execute()


def get_api_keys(uid: str) -> dict:
    """Trả về dict {provider: plain_key} sau khi giải mã."""
    db = get_supabase()
    result = (
        db.table("user_api_keys")
        .select("provider, encrypted_key")
        .eq("user_id", uid)
        .execute()
    )
    keys: dict = {}
    for row in result.data or []:
        keys[row["provider"]] = _decrypt(row["encrypted_key"])
    return keys


# ===========================================================================
# PROJECTS
# ===========================================================================

def create_project(uid: str, name: str, topic: str, genre: str,
                   num_tracks: int, claude_result: dict,
                   create_mv: bool = False,
                   language: str = "vi",
                   auto_expire_hours: Optional[int] = None) -> str:
    """
    Tạo project mới. Trả về project UUID.
    auto_expire_hours: nếu set, thêm expires_at (dùng cho free-tier).
    """
    db = get_supabase()

    seo = {k: claude_result.get(k) for k in
           ("youtube_title", "youtube_description", "hashtags",
            "thumbnail_idea", "bgm_suggestion") if claude_result.get(k)}

    row: dict = {
        "user_id":       uid,
        "name":          name,
        "topic":         topic,
        "genre":         genre,
        "language":      language,
        "num_tracks":    num_tracks,
        "create_mv":     create_mv,
        "status":        "generating",
        "claude_result": claude_result,
        "seo_metadata":  seo or None,
    }
    if auto_expire_hours:
        row["expires_at"] = (
            datetime.now(timezone.utc) + timedelta(hours=auto_expire_hours)
        ).isoformat()

    result = db.table("projects").insert(row).execute()
    project_id = result.data[0]["id"]

    # Tạo các track rows
    tracks = claude_result.get("tracks") or []
    if tracks:
        track_rows = [
            {
                "project_id":   project_id,
                "track_number": i + 1,
                "title":        t.get("title", f"Track {i+1}"),
                "lyrics":       t.get("lyrics", ""),
                "style_tags":   t.get("style_tags", ""),
                "status":       "pending",
            }
            for i, t in enumerate(tracks)
        ]
        db.table("project_tracks").insert(track_rows).execute()

    return project_id


def get_projects(uid: str, limit: int = 100,
                 include_expired: bool = True) -> list:
    """Trả về list project của user, mới nhất trước."""
    db    = get_supabase()
    query = (
        db.table("projects")
        .select("*, project_tracks(id, track_number, title, status, suno_task_id,"
                "track_audio(id, version, audio_url, stream_url, image_url, duration_secs, suno_id)),"
                "project_images(id, image_url, aspect_ratio)")
        .eq("user_id", uid)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if not include_expired:
        now = datetime.now(timezone.utc).isoformat()
        query = query.or_(f"expires_at.is.null,expires_at.gt.{now}")

    result = query.execute()
    return result.data or []


def get_project(project_id: str) -> Optional[dict]:
    """Lấy 1 project theo ID, bao gồm tracks và audio."""
    db = get_supabase()
    result = (
        db.table("projects")
        .select("*, project_tracks(*, track_audio(*)), project_images(*)")
        .eq("id", project_id)
        .maybe_single()
        .execute()
    )
    return result.data


def update_project(project_id: str, updates: dict):
    """Cập nhật trường trong project."""
    updates["updated_at"] = _now()
    get_supabase().table("projects").update(updates).eq("id", project_id).execute()


def delete_project(project_id: str):
    """Xóa project (cascade xóa tracks, audio, images)."""
    get_supabase().table("projects").delete().eq("id", project_id).execute()


# ===========================================================================
# TRACKS & AUDIO  (cập nhật sau khi Suno trả kết quả)
# ===========================================================================

def update_track(project_id: str, track_number: int, updates: dict):
    """Cập nhật track theo project_id + track_number."""
    updates["updated_at"] = _now()
    get_supabase().table("project_tracks").update(updates).eq(
        "project_id", project_id
    ).eq("track_number", track_number).execute()


def upsert_track_audio(project_id: str, track_number: int,
                       version: str, suno_data: dict):
    """
    Lưu (upsert) audio cho 1 version (A/B) của track.
    suno_data: dict từ Suno response — audioUrl, streamAudioUrl, imageUrl, duration
    """
    db = get_supabase()

    # Lấy track_id
    result = (
        db.table("project_tracks")
        .select("id")
        .eq("project_id", project_id)
        .eq("track_number", track_number)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return

    track_id = result.data["id"]
    row = {
        "track_id":     track_id,
        "version":      version,
        "suno_id":      suno_data.get("id", ""),
        "audio_url":    suno_data.get("audioUrl", ""),
        "stream_url":   suno_data.get("streamAudioUrl", ""),
        "image_url":    suno_data.get("imageUrl", ""),
        "duration_secs": suno_data.get("duration"),
    }
    db.table("track_audio").upsert(
        row, on_conflict="track_id,version"
    ).execute()


def save_suno_results(project_id: str, suno_results: dict):
    """
    Lưu toàn bộ kết quả Suno vào DB.
    suno_results format: {track_number: [suno_track_A, suno_track_B], ...}
    Đồng thời cập nhật project status = 'completed'.
    """
    db = get_supabase()
    for track_num_str, tracks in suno_results.items():
        track_num = int(track_num_str) + 1  # 0-indexed → 1-indexed
        for vi, suno_track in enumerate(tracks if isinstance(tracks, list) else [tracks]):
            version = "AB"[vi] if vi < 2 else str(vi)
            upsert_track_audio(project_id, track_num, version, suno_track)

        # Đánh dấu track done
        update_track(project_id, track_num, {"status": "done"})

    update_project(project_id, {"status": "completed"})


# ===========================================================================
# PROJECT IMAGES
# ===========================================================================

def save_project_image(project_id: str, prompt: str, image_url: str = "",
                       aspect_ratio: str = "16:9", resolution: str = "1K") -> str:
    """Lưu ảnh vào project. Trả về UUID ảnh."""
    db = get_supabase()
    result = db.table("project_images").insert({
        "project_id":   project_id,
        "prompt":       prompt,
        "image_url":    image_url,
        "aspect_ratio": aspect_ratio,
        "resolution":   resolution,
    }).execute()
    return result.data[0]["id"]


# ===========================================================================
# ADMIN FUNCTIONS
# ===========================================================================

def admin_get_all_users(limit: int = 500) -> list:
    """Lấy tất cả users kèm subscription active."""
    db = get_supabase()

    profiles_res = (
        db.table("profiles")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    profiles = profiles_res.data or []

    # Lấy all active subscriptions 1 lần
    subs_res = db.table("active_subscriptions").select("*").execute()
    sub_map  = {s["user_id"]: s for s in (subs_res.data or [])}

    result = []
    now    = datetime.now(timezone.utc)
    for p in profiles:
        sub = sub_map.get(p["id"])
        expires_at = _from_iso(sub["expires_at"]) if sub else None
        days_left  = max(0, (expires_at - now).days) if expires_at else None

        result.append({
            "uid":        p["id"],
            "email":      p.get("email", ""),
            "name":       p.get("full_name", ""),
            "photo_url":  p.get("avatar_url", ""),
            "role":       p.get("role", "user"),
            "created_at": p.get("created_at"),
            "is_paid":    sub is not None,
            "plan":       sub["plan_name"] if sub else None,
            "expires_at": expires_at,
            "days_left":  days_left,
        })
    return result


def admin_update_user(uid: str, updates: dict):
    """Cập nhật profile (full_name, role, v.v.)."""
    allowed = {"full_name", "avatar_url", "role", "email"}
    safe    = {k: v for k, v in updates.items() if k in allowed}
    if safe:
        update_profile(uid, safe)


def admin_set_plan(uid: str, plan_name: str):
    activate_subscription(uid, plan_name, payment_provider="manual")


def admin_extend_plan(uid: str, extra_days: int):
    extend_subscription(uid, extra_days)


def admin_remove_plan(uid: str):
    deactivate_subscription(uid)


def admin_set_role(uid: str, role: str):
    """role: 'admin' | 'user'"""
    update_profile(uid, {"role": role})


def admin_delete_user_data(uid: str):
    """Xóa toàn bộ data Supabase của user (profile + cascade)."""
    get_supabase().table("profiles").delete().eq("id", uid).execute()


def admin_get_user_projects(uid: str, limit: int = 100) -> list:
    """Lấy tất cả projects của user (admin view, không filter expires)."""
    return get_projects(uid, limit=limit, include_expired=True)


def admin_delete_project(project_id: str):
    delete_project(project_id)


def admin_update_project(project_id: str, updates: dict):
    update_project(project_id, updates)
