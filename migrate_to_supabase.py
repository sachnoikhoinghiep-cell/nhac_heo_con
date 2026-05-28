"""
migrate_to_supabase.py
======================
Migrate toàn bộ dữ liệu từ Firebase Firestore sang Supabase Postgres.

Chạy:
    python migrate_to_supabase.py              # migrate thật
    python migrate_to_supabase.py --dry-run    # chỉ đọc, không ghi
    python migrate_to_supabase.py --uid <UID>  # migrate 1 user cụ thể

Yêu cầu:
    - .streamlit/secrets.toml có đủ SUPABASE_URL, SUPABASE_SERVICE_KEY, ENCRYPTION_KEY
    - firebase_service_account.json hợp lệ
    - pip install supabase cryptography
"""

import sys
import os
import argparse
import traceback
from datetime import datetime, timezone

# Encode stdout UTF-8 (Windows terminal)
if hasattr(sys.stdout, "buffer"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Bootstrap Streamlit secrets (cho môi trường non-Streamlit)
# ---------------------------------------------------------------------------
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
try:
    import streamlit as st
    # Kích hoạt secrets từ file nếu chưa load
    _ = st.secrets._secrets
except Exception:
    pass

from firebase_config import init_firebase
from firebase_admin import firestore as fs
import supabase_db as sdb

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ts_to_dt(ts) -> datetime | None:
    """Chuyển Firestore Timestamp / datetime → datetime UTC."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
    try:
        return ts.astimezone(timezone.utc)
    except Exception:
        return None


def dt_to_iso(dt) -> str | None:
    return dt.isoformat() if dt else None


class Stats:
    def __init__(self):
        self.users_ok = self.users_err = 0
        self.subs_ok  = self.subs_err  = 0
        self.keys_ok  = self.keys_err  = 0
        self.proj_ok  = self.proj_err  = 0
        self.audio_ok = self.audio_err = 0

    def print(self):
        print("\n" + "=" * 50)
        print("KẾT QUẢ MIGRATION")
        print("=" * 50)
        print(f"  Profiles  : {self.users_ok} OK  /  {self.users_err} lỗi")
        print(f"  Subs      : {self.subs_ok} OK  /  {self.subs_err} lỗi")
        print(f"  API keys  : {self.keys_ok} OK  /  {self.keys_err} lỗi")
        print(f"  Projects  : {self.proj_ok} OK  /  {self.proj_err} lỗi")
        print(f"  Audio rows: {self.audio_ok} OK  /  {self.audio_err} lỗi")


# ---------------------------------------------------------------------------
# Migrate 1 user
# ---------------------------------------------------------------------------
def migrate_user(db_fire, uid: str, data: dict,
                 dry_run: bool, stats: Stats, plan_id_map: dict):

    email     = data.get("email", "")
    name      = data.get("name", "") or ""
    photo     = data.get("photo_url", "") or ""
    role      = data.get("role", "user") or "user"
    is_paid   = data.get("is_paid", False)
    plan_name = data.get("plan")
    expires_at = ts_to_dt(data.get("expires_at"))
    paid_at    = ts_to_dt(data.get("paid_at"))
    created_at = ts_to_dt(data.get("created_at"))

    print(f"\n→ [{uid[:8]}] {email}  role={role}  plan={plan_name}  is_paid={is_paid}")

    # ── 1. Profile ────────────────────────────────────────────────────────
    try:
        if not dry_run:
            sb = sdb.get_supabase()
            row = {
                "id":         uid,
                "email":      email,
                "full_name":  name,
                "avatar_url": photo,
                "role":       role if role in ("admin", "user") else "user",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if created_at:
                row["created_at"] = created_at.isoformat()
            sb.table("profiles").upsert(row, on_conflict="id").execute()
        print(f"  ✅ profile upserted")
        stats.users_ok += 1
    except Exception as e:
        print(f"  ❌ profile lỗi: {e}")
        stats.users_err += 1
        return  # Không thể tiếp tục nếu profile lỗi

    # ── 2. Subscription ───────────────────────────────────────────────────
    if is_paid and plan_name and expires_at:
        try:
            plan_id = plan_id_map.get(plan_name)
            if plan_id is None:
                print(f"  ⚠️  plan '{plan_name}' không tìm thấy trong Supabase, bỏ qua sub")
            else:
                if not dry_run:
                    sb = sdb.get_supabase()
                    # Xóa subs cũ (idempotent)
                    sb.table("user_subscriptions").delete().eq(
                        "user_id", uid
                    ).eq("status", "active").execute()

                    sb.table("user_subscriptions").insert({
                        "user_id":           uid,
                        "plan_id":           plan_id,
                        "status":            "active" if expires_at > datetime.now(timezone.utc) else "expired",
                        "started_at":        dt_to_iso(paid_at),
                        "expires_at":        dt_to_iso(expires_at),
                        "paid_at":           dt_to_iso(paid_at),
                        "payment_provider":  "paypal",
                    }).execute()
                print(f"  ✅ subscription: {plan_name} → hết hạn {expires_at.date()}")
                stats.subs_ok += 1
        except Exception as e:
            print(f"  ❌ subscription lỗi: {e}")
            stats.subs_err += 1

    # ── 3. API Keys ───────────────────────────────────────────────────────
    api_keys = data.get("api_keys") or {}
    if any(api_keys.values()):
        try:
            if not dry_run:
                sdb.save_api_keys(
                    uid,
                    anthropic = api_keys.get("anthropic", ""),
                    google    = api_keys.get("google", ""),
                    suno      = api_keys.get("suno", ""),
                    fal       = api_keys.get("fal", ""),
                )
            providers = [k for k, v in api_keys.items() if v]
            print(f"  ✅ api_keys: {providers}")
            stats.keys_ok += 1
        except Exception as e:
            print(f"  ❌ api_keys lỗi: {e}")
            stats.keys_err += 1

    # ── 4. Music History → Projects ───────────────────────────────────────
    hist_ref = db_fire.collection("users").document(uid).collection("music_history")
    hist_docs = list(hist_ref.order_by(
        "created_at", direction=fs.Query.DESCENDING
    ).stream())

    print(f"  📂 {len(hist_docs)} project(s) trong history")

    for doc in hist_docs:
        migrate_history(uid, doc, dry_run, stats)


# ---------------------------------------------------------------------------
# Migrate 1 history document → project + tracks + audio
# ---------------------------------------------------------------------------
def migrate_history(uid: str, doc, dry_run: bool, stats: Stats):
    h          = doc.to_dict()
    name       = h.get("project_name") or h.get("topic") or "Untitled"
    topic      = h.get("topic", "")
    genre      = h.get("genre", "")
    num_tracks = h.get("num_tracks", 1)
    create_mv  = h.get("create_mv", False)
    result     = h.get("result") or {}
    suno_res   = h.get("suno_results") or {}
    created_at = ts_to_dt(h.get("created_at"))
    expire_at  = ts_to_dt(h.get("expire_at"))

    print(f"    → project: {name[:40]}  genre={genre}  tracks={num_tracks}")

    try:
        if not dry_run:
            sb = sdb.get_supabase()

            # Extract SEO
            seo = {k: result.get(k) for k in
                   ("youtube_title", "youtube_description", "hashtags",
                    "thumbnail_idea", "bgm_suggestion") if result.get(k)}

            proj_row = {
                "user_id":       uid,
                "name":          name[:200],
                "topic":         topic[:500] if topic else None,
                "genre":         genre,
                "num_tracks":    num_tracks,
                "create_mv":     create_mv,
                "status":        "completed" if suno_res else "generating",
                "claude_result": result or None,
                "seo_metadata":  seo or None,
                "expires_at":    dt_to_iso(expire_at),
            }
            if created_at:
                proj_row["created_at"] = created_at.isoformat()

            proj_res   = sb.table("projects").insert(proj_row).execute()
            project_id = proj_res.data[0]["id"]

            # Tạo project_tracks từ Claude result
            tracks = result.get("tracks") or []
            track_id_map: dict[int, str] = {}  # track_number → UUID

            if tracks:
                track_rows = [
                    {
                        "project_id":   project_id,
                        "track_number": i + 1,
                        "title":        t.get("title", f"Track {i+1}")[:200],
                        "lyrics":       t.get("lyrics", ""),
                        "style_tags":   t.get("style_tags", "")[:500],
                        "status":       "pending",
                    }
                    for i, t in enumerate(tracks)
                ]
                tr_res = sb.table("project_tracks").insert(track_rows).execute()
                for row in tr_res.data:
                    track_id_map[row["track_number"]] = row["id"]
            else:
                # Không có tracks trong Claude result → tạo placeholder
                placeholder_rows = [
                    {"project_id": project_id, "track_number": i + 1,
                     "title": f"Track {i+1}", "status": "pending"}
                    for i in range(num_tracks)
                ]
                tr_res = sb.table("project_tracks").insert(placeholder_rows).execute()
                for row in tr_res.data:
                    track_id_map[row["track_number"]] = row["id"]

            # Lưu audio từ suno_results
            # format: {"track_1": [trackA, trackB], "track_2": [...], ...}
            audio_rows = []
            for key, suno_list in suno_res.items():
                # key = "track_N" (N từ 1)
                try:
                    track_num = int(key.replace("track_", ""))
                except ValueError:
                    continue

                track_id = track_id_map.get(track_num)
                if not track_id:
                    continue

                for vi, suno_track in enumerate(suno_list if isinstance(suno_list, list) else [suno_list]):
                    if not isinstance(suno_track, dict):
                        continue
                    version = "AB"[vi] if vi < 2 else str(vi)
                    audio_rows.append({
                        "track_id":     track_id,
                        "version":      version,
                        "suno_id":      suno_track.get("id", ""),
                        "audio_url":    suno_track.get("audioUrl", ""),
                        "stream_url":   suno_track.get("streamAudioUrl", ""),
                        "image_url":    suno_track.get("imageUrl", ""),
                        "duration_secs": suno_track.get("duration"),
                    })
                # Đánh dấu track done
                sb.table("project_tracks").update({"status": "done"}).eq(
                    "id", track_id
                ).execute()

            if audio_rows:
                sb.table("track_audio").insert(audio_rows).execute()
                stats.audio_ok += len(audio_rows)

        print(f"      ✅ project OK  ({len(suno_res)} track audio groups)")
        stats.proj_ok += 1

    except Exception as e:
        print(f"      ❌ project lỗi: {e}")
        if "--debug" in sys.argv:
            traceback.print_exc()
        stats.proj_err += 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Migrate Firestore → Supabase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ đọc Firestore, không ghi vào Supabase")
    parser.add_argument("--uid", default=None,
                        help="Chỉ migrate 1 user theo UID")
    parser.add_argument("--debug", action="store_true",
                        help="In stack trace đầy đủ khi lỗi")
    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY-RUN mode — không ghi gì vào Supabase\n")

    db_fire = init_firebase()
    stats   = Stats()

    # Load plan_id map từ Supabase
    plan_id_map: dict = {}
    if not args.dry_run:
        try:
            sb  = sdb.get_supabase()
            res = sb.table("subscription_plans").select("id, name").execute()
            plan_id_map = {r["name"]: r["id"] for r in (res.data or [])}
            print(f"Loaded {len(plan_id_map)} plans từ Supabase: {list(plan_id_map.keys())}\n")
        except Exception as e:
            print(f"❌ Không kết nối được Supabase: {e}")
            sys.exit(1)

    # Lấy danh sách users cần migrate
    if args.uid:
        doc = db_fire.collection("users").document(args.uid).get()
        if not doc.exists:
            print(f"❌ UID {args.uid} không tồn tại trong Firestore")
            sys.exit(1)
        user_docs = [doc]
    else:
        user_docs = list(db_fire.collection("users").stream())

    total = len(user_docs)
    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Bắt đầu migrate {total} user(s)...\n")

    for i, doc in enumerate(user_docs, 1):
        print(f"[{i}/{total}]", end="")
        try:
            migrate_user(
                db_fire, doc.id, doc.to_dict(),
                dry_run=args.dry_run,
                stats=stats,
                plan_id_map=plan_id_map,
            )
        except Exception as e:
            print(f"  ❌ FATAL user {doc.id}: {e}")
            if args.debug:
                traceback.print_exc()
            stats.users_err += 1

    stats.print()

    if stats.users_err or stats.proj_err:
        print("\n⚠️  Có lỗi xảy ra. Chạy lại với --debug để xem chi tiết.")
    else:
        print("\n✅ Migration hoàn thành không có lỗi!")


if __name__ == "__main__":
    main()
