import streamlit as st
from datetime import datetime, timezone
from auth import (
    get_all_user_history,
    delete_history_item,
    update_history_item,
    sign_out,
    PLAN_DURATION,
)
from views._nav import render as _nav

_nav()

# ── Auth guard ────────────────────────────────────────────────────────────────
user = st.session_state.get("user")
if not user:
    st.warning("Vui lòng đăng nhập để xem trang này.")
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        st.page_link("views/app_music.py", label="🔵 Đăng nhập", use_container_width=True)
    st.stop()

uid = user["uid"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def _fmt_dt(dt) -> str:
    if not dt:
        return "Không xác định"
    if hasattr(dt, "tzinfo") and dt.tzinfo:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%d/%m/%Y %H:%M")

def _days_left(expires_at) -> int | None:
    if not expires_at:
        return None
    now = datetime.now(timezone.utc)
    if hasattr(expires_at, "tzinfo") and not expires_at.tzinfo:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return max(0, (expires_at - now).days)

_PLAN_ICONS = {"Ngày": "☀️", "Tuần": "📅", "Tháng": "🗓️", "Năm": "⭐"}
_PLAN_COLORS = {"Ngày": "#3b82f6", "Tuần": "#8b5cf6", "Tháng": "#f59e0b", "Năm": "#10b981"}
_GENRE_ICONS = {
    "Pop":        "🎤", "Rock":       "🎸", "Hip Hop":    "🎧",
    "R&B/Soul":   "🎶", "Electronic": "🎛️", "Jazz":       "🎺",
    "Classical":  "🎻", "Country":    "🤠", "Bolero":     "🌹",
    "Indie/Folk": "🪕",
}


# ── Dialogs ───────────────────────────────────────────────────────────────────
@st.dialog("🎵 Chi tiết project", width="large")
def _view_project_dialog(item: dict):
    name  = item.get("project_name") or item.get("topic", "—")
    genre = item.get("genre", "")
    icon  = _GENRE_ICONS.get(genre, "🎵")
    st.subheader(f"{icon} {name}")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Thể loại", genre or "—")
    col_b.metric("Số bài", item.get("num_tracks", 0))
    col_c.metric("MV", "Có" if item.get("create_mv") else "Không")

    result = item.get("result") or {}

    # Lyrics / tracks
    tracks = result.get("tracks") or []
    if tracks:
        st.divider()
        st.write("**Lời nhạc & Style tags**")
        for i, t in enumerate(tracks, 1):
            with st.expander(f"Bài {i}: {t.get('title', '')}"):
                if t.get("style_tags"):
                    st.caption(f"🎨 Style: `{t['style_tags']}`")
                if t.get("lyrics"):
                    st.text(t["lyrics"])

    # MV script
    if result.get("mv_script"):
        st.divider()
        with st.expander("🎬 Script MV"):
            st.text(result["mv_script"])

    # SEO
    if result.get("youtube_title") or result.get("youtube_description"):
        st.divider()
        with st.expander("📊 SEO YouTube"):
            if result.get("youtube_title"):
                st.write(f"**Tiêu đề:** {result['youtube_title']}")
            if result.get("youtube_description"):
                st.write("**Mô tả:**")
                st.text(result["youtube_description"])
            if result.get("hashtags"):
                st.write(f"**Hashtags:** {result['hashtags']}")

    # Suno audio
    suno = item.get("suno_results") or {}
    if suno:
        st.divider()
        st.write("**Audio từ Suno**")
        for track_idx, track_data in suno.items():
            urls = []
            if isinstance(track_data, dict):
                urls = track_data.get("audio_urls") or []
            elif isinstance(track_data, list):
                urls = track_data
            for j, url in enumerate(urls):
                if url:
                    st.audio(url)


@st.dialog("✏️ Đổi tên project", width="small")
def _rename_dialog(item: dict):
    current = item.get("project_name") or item.get("topic", "")
    new_name = st.text_input("Tên mới", value=current, max_chars=120)
    col1, col2 = st.columns(2)
    if col1.button("💾 Lưu", type="primary", use_container_width=True):
        if new_name.strip():
            update_history_item(uid, item["id"], {"project_name": new_name.strip()})
            st.session_state["_dash_refresh"] = True
            st.success("Đã lưu!")
            st.rerun()
    if col2.button("Hủy", use_container_width=True):
        st.rerun()


@st.dialog("⚠️ Xóa project", width="small")
def _delete_dialog(item: dict):
    name = item.get("project_name") or item.get("topic", "Project")
    st.warning(f"Bạn chắc chắn muốn xóa **{name}**?\n\nHành động này không thể hoàn tác.")
    col1, col2 = st.columns(2)
    if col1.button("🗑️ Xóa", type="primary", use_container_width=True):
        delete_history_item(uid, item["id"])
        st.session_state["_dash_refresh"] = True
        st.success("Đã xóa!")
        st.rerun()
    if col2.button("Hủy", use_container_width=True):
        st.rerun()


# ── Page ──────────────────────────────────────────────────────────────────────
st.title("👤 Tài khoản của tôi")

tab_plan, tab_projects = st.tabs(["📦 Gói dịch vụ", "🎵 Projects của tôi"])

# ─── Tab 1: Plan ──────────────────────────────────────────────────────────────
with tab_plan:
    plan     = user.get("plan")
    is_paid  = user.get("is_paid", False)
    icon     = _PLAN_ICONS.get(plan, "🆓")
    color    = _PLAN_COLORS.get(plan, "#6b7280")

    col_card, col_info = st.columns([1, 2])

    with col_card:
        if is_paid and plan:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, {color}22, {color}44);
                    border: 2px solid {color};
                    border-radius: 16px;
                    padding: 1.5rem;
                    text-align: center;
                ">
                    <div style="font-size: 2.5rem;">{icon}</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: {color};">Gói {plan}</div>
                    <div style="color: rgba(255,255,255,0.7); font-size: 0.85rem; margin-top: 0.3rem;">Đang hoạt động</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="
                    background: rgba(55,65,81,0.4);
                    border: 2px solid #374151;
                    border-radius: 16px;
                    padding: 1.5rem;
                    text-align: center;
                ">
                    <div style="font-size: 2.5rem;">🆓</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: #9ca3af;">Chưa có gói</div>
                    <div style="color: rgba(255,255,255,0.4); font-size: 0.85rem; margin-top: 0.3rem;">Free tier</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_info:
        st.write(f"**Tên:** {user.get('name', '')}  ·  {user.get('email', '')}")
        st.divider()

        if is_paid and plan:
            from supabase_db import get_active_subscription
            _sub = get_active_subscription(uid) or {}

            paid_at    = _from_iso(_sub.get("paid_at") or _sub.get("started_at"))
            expires_at = _from_iso(_sub.get("expires_at"))
            days       = _days_left(expires_at)

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Gói hiện tại", plan)
            col_m2.metric("Ngày kích hoạt", _fmt_dt(paid_at).split(" ")[0] if paid_at else "—")
            col_m3.metric("Hết hạn", _fmt_dt(expires_at).split(" ")[0] if expires_at else "—")

            # Progress bar
            if paid_at and expires_at:
                total_days = PLAN_DURATION.get(plan)
                if total_days:
                    total_s = total_days.total_seconds()
                    if hasattr(paid_at, "tzinfo") and not paid_at.tzinfo:
                        paid_at = paid_at.replace(tzinfo=timezone.utc)
                    elapsed_s = (datetime.now(timezone.utc) - paid_at).total_seconds()
                    pct = max(0.0, min(1.0, elapsed_s / total_s))
                    remaining = 1.0 - pct
                    color_bar = "#10b981" if remaining > 0.3 else ("#f59e0b" if remaining > 0.1 else "#ef4444")
                    st.markdown(
                        f'<p style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin-bottom:2px;">Thời gian còn lại: {days} ngày</p>',
                        unsafe_allow_html=True,
                    )
                    st.progress(remaining, text="")
        else:
            st.info("Bạn chưa có gói dịch vụ nào. Hãy mua gói để bắt đầu tạo nhạc AI!")
            st.page_link(
                "views/app_music.py",
                label="💳 Mua gói ngay",
                use_container_width=False,
            )

    st.divider()
    col_lo, _ = st.columns([1, 4])
    if col_lo.button("🚪 Đăng xuất", use_container_width=True):
        sign_out()

# ─── Tab 2: Projects ──────────────────────────────────────────────────────────
with tab_projects:
    if st.session_state.pop("_dash_refresh", False) or "dash_history" not in st.session_state:
        st.session_state["dash_history"] = get_all_user_history(uid)

    history: list = st.session_state["dash_history"]

    col_hdr, col_refresh = st.columns([4, 1])
    col_hdr.write(f"**{len(history)} project** đã tạo")
    if col_refresh.button("🔄 Làm mới", use_container_width=True):
        st.session_state.pop("dash_history", None)
        st.rerun()

    if not history:
        st.info("Bạn chưa tạo project nào. Hãy vào **Ứng dụng** để bắt đầu!")
        st.page_link("views/app_music.py", label="🎵 Tạo nhạc ngay", use_container_width=False)
    else:
        # Search
        search_q = st.text_input(
            "🔍 Tìm project",
            placeholder="Nhập tên hoặc chủ đề…",
            label_visibility="collapsed",
        )
        items = history
        if search_q:
            q = search_q.lower()
            items = [
                h for h in history
                if q in (h.get("project_name") or "").lower()
                or q in (h.get("topic") or "").lower()
                or q in (h.get("genre") or "").lower()
            ]

        now = datetime.now(timezone.utc)

        # Grid: 3 cards per row
        for row_start in range(0, len(items), 3):
            cols = st.columns(3)
            for col_i, item in enumerate(items[row_start: row_start + 3]):
                name    = item.get("project_name") or item.get("topic", "Untitled")
                genre   = item.get("genre", "")
                icon    = _GENRE_ICONS.get(genre, "🎵")
                created = _fmt_dt(item.get("created_at"))
                tracks  = item.get("num_tracks", 0)
                has_audio = bool(item.get("suno_results"))

                expire_at = item.get("expire_at")
                if expire_at:
                    if hasattr(expire_at, "tzinfo") and not expire_at.tzinfo:
                        expire_at = expire_at.replace(tzinfo=timezone.utc)
                    expired = expire_at < now
                else:
                    expired = False

                with cols[col_i]:
                    with st.container(border=True):
                        st.markdown(f"**{icon} {name[:40]}{'…' if len(name) > 40 else ''}**")
                        st.caption(f"{genre}  ·  {tracks} bài  ·  {created}")

                        badges = []
                        if has_audio:
                            badges.append('<span style="background:#14532d;color:#86efac;padding:1px 6px;border-radius:9999px;font-size:0.7rem;">🎵 Có audio</span>')
                        if item.get("create_mv"):
                            badges.append('<span style="background:#1e3a5f;color:#93c5fd;padding:1px 6px;border-radius:9999px;font-size:0.7rem;">🎬 MV</span>')
                        if expired:
                            badges.append('<span style="background:#7f1d1d;color:#fca5a5;padding:1px 6px;border-radius:9999px;font-size:0.7rem;">⏰ Hết hạn</span>')
                        if badges:
                            st.markdown(" ".join(badges), unsafe_allow_html=True)

                        b1, b2, b3 = st.columns(3)
                        if b1.button("👁️", key=f"view_{item['id']}", help="Xem chi tiết"):
                            _view_project_dialog(item)
                        if b2.button("✏️", key=f"ren_{item['id']}", help="Đổi tên"):
                            _rename_dialog(item)
                        if b3.button("🗑️", key=f"del_{item['id']}", help="Xóa"):
                            _delete_dialog(item)
