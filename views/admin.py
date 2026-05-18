import streamlit as st
from datetime import datetime, timezone, timedelta
from auth import (
    is_admin,
    get_all_users,
    admin_update_user,
    admin_set_plan,
    admin_extend_plan,
    admin_remove_plan,
    admin_delete_user_data,
    admin_get_user_history,
    admin_delete_history_item,
    admin_update_history_item,
    PLAN_DURATION,
)
from views._nav import render as _nav

_nav()

# ── Access guard ──────────────────────────────────────────────────────────────
user = st.session_state.get("user")
if not user or not st.session_state.get("is_admin"):
    st.error("🚫 Bạn không có quyền truy cập trang này.")
    st.stop()

# ── Helpers ───────────────────────────────────────────────────────────────────
_PLANS = ["Ngày", "Tuần", "Tháng", "Năm"]
_PLAN_COLORS = {"Ngày": "#3b82f6", "Tuần": "#8b5cf6", "Tháng": "#f59e0b", "Năm": "#10b981"}

def _fmt_dt(dt) -> str:
    if not dt:
        return "—"
    if hasattr(dt, "tzinfo") and dt.tzinfo:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%d/%m/%Y %H:%M")

def _days_left(expires_at) -> int | None:
    if not expires_at:
        return None
    now = datetime.now(timezone.utc)
    if hasattr(expires_at, "tzinfo") and not expires_at.tzinfo:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - now
    return max(0, delta.days)

def _plan_badge(plan, is_paid) -> str:
    if not plan or not is_paid:
        return '<span style="background:#374151;color:#9ca3af;padding:2px 8px;border-radius:9999px;font-size:0.75rem;">Free</span>'
    color = _PLAN_COLORS.get(plan, "#6b7280")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:9999px;font-size:0.75rem;font-weight:600;">{plan}</span>'

def _status_badge(is_paid, expires_at) -> str:
    if not is_paid:
        return '<span style="background:#1f2937;color:#6b7280;padding:2px 8px;border-radius:9999px;font-size:0.75rem;">Không hoạt động</span>'
    days = _days_left(expires_at)
    if days is None or days <= 0:
        return '<span style="background:#7f1d1d;color:#fca5a5;padding:2px 8px;border-radius:9999px;font-size:0.75rem;">Hết hạn</span>'
    if days <= 3:
        return f'<span style="background:#78350f;color:#fcd34d;padding:2px 8px;border-radius:9999px;font-size:0.75rem;">Còn {days}d</span>'
    return f'<span style="background:#14532d;color:#86efac;padding:2px 8px;border-radius:9999px;font-size:0.75rem;">Còn {days}d</span>'


# ── Dialogs ───────────────────────────────────────────────────────────────────
@st.dialog("✏️ Chỉnh sửa người dùng", width="large")
def _edit_dialog(u: dict):
    uid = u["uid"]
    st.caption(f"UID: `{uid}`")

    col_a, col_b = st.columns(2)
    new_name = col_a.text_input("Tên hiển thị", value=u["name"])
    roles = ["user", "admin"]
    new_role = col_b.selectbox(
        "Vai trò", roles,
        index=roles.index(u.get("role", "user")),
    )

    st.divider()
    st.write("**Gói dịch vụ**")
    plan_opts = ["Giữ nguyên", "Cấp gói mới", "Gia hạn (ngày)", "Thu hồi gói"]
    plan_action = st.radio("Thao tác", plan_opts, horizontal=True)

    new_plan = None
    extra_days = 0
    if plan_action == "Cấp gói mới":
        new_plan = st.selectbox("Chọn gói", _PLANS)
    elif plan_action == "Gia hạn (ngày)":
        extra_days = st.number_input("Số ngày gia hạn", min_value=1, max_value=3650, value=30)

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("💾 Lưu thay đổi", type="primary", use_container_width=True):
        updates = {}
        if new_name.strip() and new_name != u["name"]:
            updates["name"] = new_name.strip()
        if new_role != u.get("role", "user"):
            updates["role"] = new_role
        if updates:
            admin_update_user(uid, updates)
        if plan_action == "Cấp gói mới" and new_plan:
            admin_set_plan(uid, new_plan)
        elif plan_action == "Gia hạn (ngày)" and extra_days:
            admin_extend_plan(uid, int(extra_days))
        elif plan_action == "Thu hồi gói":
            admin_remove_plan(uid)
        st.success("Đã lưu!")
        st.session_state["_admin_refresh"] = True
        st.rerun()
    if col2.button("Hủy", use_container_width=True):
        st.rerun()


@st.dialog("📋 Lịch sử nhạc của người dùng", width="large")
def _history_dialog(uid: str, email: str):
    st.caption(f"**{email}**")
    items = admin_get_user_history(uid, limit=50)
    if not items:
        st.info("Chưa có project nào.")
        return

    for item in items:
        created = _fmt_dt(item.get("created_at"))
        name = item.get("project_name") or item.get("topic", "—")
        genre = item.get("genre", "")
        tracks = item.get("num_tracks", 0)

        with st.expander(f"🎵 {name}  ·  {genre}  ·  {created}"):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**Topic:** {item.get('topic','')}")
            c2.write(f"**Số bài:** {tracks}")
            c3.write(f"**MV:** {'Có' if item.get('create_mv') else 'Không'}")

            # Edit project name
            new_pname = st.text_input(
                "Đổi tên project", value=name, key=f"adm_pname_{item['id']}"
            )
            col_s, col_d = st.columns(2)
            if col_s.button("💾 Lưu tên", key=f"adm_save_{item['id']}"):
                admin_update_history_item(uid, item["id"], {"project_name": new_pname.strip()})
                st.success("Đã lưu!")
                st.rerun()
            if col_d.button("🗑️ Xóa project", key=f"adm_del_{item['id']}", type="secondary"):
                admin_delete_history_item(uid, item["id"])
                st.warning("Đã xóa.")
                st.rerun()


@st.dialog("⚠️ Xác nhận xóa tài khoản", width="small")
def _delete_dialog(uid: str, email: str):
    st.warning(f"Bạn sắp xóa **toàn bộ dữ liệu** của:\n\n`{email}`\n\nHành động này **không thể hoàn tác**!")
    st.caption("(Chỉ xóa dữ liệu Firestore, không xóa tài khoản Firebase Auth)")
    col1, col2 = st.columns(2)
    if col1.button("🗑️ Xóa", type="primary", use_container_width=True):
        admin_delete_user_data(uid)
        st.success("Đã xóa dữ liệu người dùng.")
        st.session_state["_admin_refresh"] = True
        st.rerun()
    if col2.button("Hủy", use_container_width=True):
        st.rerun()


# ── Page header ───────────────────────────────────────────────────────────────
st.title("⚙️ Quản trị hệ thống")

# ── Load users ────────────────────────────────────────────────────────────────
if "admin_users" not in st.session_state or st.session_state.pop("_admin_refresh", False):
    st.session_state["admin_users"] = get_all_users()

all_users: list = st.session_state["admin_users"]
now = datetime.now(timezone.utc)

# ── Stats row ─────────────────────────────────────────────────────────────────
total   = len(all_users)
paid    = sum(1 for u in all_users if u["is_paid"])
admins  = sum(1 for u in all_users if u.get("role") == "admin")
expiring = sum(
    1 for u in all_users
    if u["is_paid"] and (_days_left(u.get("expires_at")) or 999) <= 3
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Tổng users", total)
m2.metric("Đang trả phí", paid)
m3.metric("Free / Hết hạn", total - paid)
m4.metric("Sắp hết hạn (≤3d)", expiring)
m5.metric("Admin", admins)

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([3, 1.5, 1])
search    = fc1.text_input("🔍 Tìm email / tên", placeholder="Nhập để lọc…", label_visibility="collapsed")
plan_filt = fc2.selectbox("Lọc gói", ["Tất cả", "Đang hoạt động", "Free/Hết hạn"] + _PLANS, label_visibility="collapsed")
if fc3.button("🔄 Làm mới", use_container_width=True):
    st.session_state.pop("admin_users", None)
    st.rerun()

# Filter logic
users = all_users
if search:
    q = search.lower()
    users = [u for u in users if q in u["email"].lower() or q in u["name"].lower()]
if plan_filt == "Đang hoạt động":
    users = [u for u in users if u["is_paid"]]
elif plan_filt == "Free/Hết hạn":
    users = [u for u in users if not u["is_paid"]]
elif plan_filt in _PLANS:
    users = [u for u in users if u.get("plan") == plan_filt and u["is_paid"]]

st.caption(f"Hiển thị **{len(users)}** / {total} người dùng")
st.divider()

# ── User list ─────────────────────────────────────────────────────────────────
if not users:
    st.info("Không tìm thấy người dùng nào.")
else:
    for u in users:
        uid   = u["uid"]
        email = u["email"]
        name  = u["name"] or email.split("@")[0]
        plan  = u.get("plan")
        is_paid = u["is_paid"]

        with st.container(border=True):
            c_info, c_plan, c_status, c_exp, c_role, c_acts = st.columns(
                [3, 1.2, 1.4, 1.6, 1, 2.2]
            )

            # Info
            with c_info:
                st.write(f"**{name}**")
                st.caption(email)

            # Plan badge
            c_plan.markdown(_plan_badge(plan, is_paid), unsafe_allow_html=True)

            # Status badge
            c_status.markdown(_status_badge(is_paid, u.get("expires_at")), unsafe_allow_html=True)

            # Expires
            c_exp.caption(_fmt_dt(u.get("expires_at")))

            # Role
            if u.get("role") == "admin":
                c_role.markdown(
                    '<span style="color:#f59e0b;font-size:0.75rem;font-weight:700;">⚡ Admin</span>',
                    unsafe_allow_html=True,
                )
            else:
                c_role.caption("User")

            # Action buttons
            with c_acts:
                b1, b2, b3 = st.columns(3)
                if b1.button("✏️", key=f"edit_{uid}", help="Chỉnh sửa"):
                    _edit_dialog(u)
                if b2.button("📋", key=f"hist_{uid}", help="Xem lịch sử nhạc"):
                    _history_dialog(uid, email)
                if b3.button("🗑️", key=f"del_{uid}", help="Xóa tài khoản"):
                    _delete_dialog(uid, email)
