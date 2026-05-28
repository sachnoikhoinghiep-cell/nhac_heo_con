import streamlit as st
from auth import try_restore_session, handle_google_callback, process_pending_rt, is_admin

st.set_page_config(
    page_title="Sonicflowai — AI Music Producer",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 1. Ghi pending refresh token vào cookie (trước session restore)
process_pending_rt()

# 2. Khôi phục session từ cookie (cần biết user trước khi build navigation)
if "user" not in st.session_state:
    st.session_state.user = None
try_restore_session()

# 3. Kiểm tra quyền admin (cache trong session_state)
_user = st.session_state.get("user")
if _user and "is_admin" not in st.session_state:
    st.session_state["is_admin"] = is_admin(_user["uid"])
elif not _user:
    st.session_state["is_admin"] = False

# 4. Xây dựng navigation (phải trước st.switch_page)
_pages = [
    st.Page("views/home.py",           title="Trang chủ",   icon="🏠", default=True),
    st.Page("views/app_music.py",      title="Ứng dụng",    icon="🎵"),
    st.Page("views/user_dashboard.py", title="Tài khoản",   icon="👤"),
    st.Page("views/about.py",          title="Giới thiệu",  icon="ℹ️"),
    st.Page("views/guide.py",          title="Hướng dẫn",   icon="📋"),
    st.Page("views/policy.py",         title="Chính sách",  icon="📜"),
    st.Page("views/privacy.py",        title="Privacy Policy",  icon="🔒"),
    st.Page("views/terms.py",          title="Terms of Use",    icon="📋"),
    st.Page("views/refund.py",         title="Refund Policy",   icon="↩️"),
]
if st.session_state.get("is_admin"):
    _pages.append(st.Page("views/admin.py", title="Quản trị", icon="⚙️"))

pg = st.navigation(_pages, position="hidden")

# 5. Xử lý Google OAuth callback (?code=...) — redirect về app sau khi login
if handle_google_callback():
    st.switch_page("views/app_music.py")

# 6. Xử lý PayPal subscription callback (?subscription_id=...)
_pp_sub_id = st.query_params.get("subscription_id")
if _pp_sub_id and st.session_state.get("user"):
    st.query_params.clear()
    _PLAN_ID_TO_NAME = {
        "P-48U172572M537580PNICAPDY": "Ngày",
        "P-12862804M08177324NICAPSI": "Tuần",
        "P-5AV04190G6017082ENICAOVA": "Tháng",
        "P-055284903H354632FNICAN7I": "Năm",
    }
    def _pp_client_id():
        try:    return st.secrets["PAYPAL_CLIENT_ID"]
        except: return ""
    def _pp_secret():
        try:    return st.secrets["PAYPAL_SECRET"]
        except: return ""
    with st.spinner("Đang xác nhận đăng ký PayPal…"):
        try:
            from paypal import get_subscription
            from auth import activate_plan
            _sub = get_subscription(_pp_client_id(), _pp_secret(), _pp_sub_id)
            if _sub.get("status") == "ACTIVE":
                _plan = _PLAN_ID_TO_NAME.get(_sub.get("plan_id", ""), "Tháng")
                activate_plan(st.session_state.user["uid"], _plan)
                st.session_state.user["is_paid"] = True
                st.session_state.user["plan"]    = _plan
                st.success(f"Đăng ký thành công! Gói **{_plan}** đã được kích hoạt.")
            else:
                st.error(f"PayPal: subscription chưa kích hoạt (status: {_sub.get('status')})")
        except Exception as _e:
            st.error(f"Lỗi xác nhận PayPal: {_e}")
    st.switch_page("views/app_music.py")
elif st.query_params.get("ba_token") and not _pp_sub_id:
    st.query_params.clear()
    st.warning("Bạn đã hủy đăng ký PayPal.")

pg.run()
