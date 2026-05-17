import streamlit as st
from auth import try_restore_session, handle_google_callback, process_pending_rt

st.set_page_config(
    page_title="nhacheocon — AI Music Producer",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Navigation phải được khởi tạo TRƯỚC st.switch_page để page registry tồn tại
pg = st.navigation(
    [
        st.Page("views/home.py",       title="Trang chủ",  icon="🏠", default=True),
        st.Page("views/app_music.py",  title="Ứng dụng",   icon="🎵"),
        st.Page("views/about.py",      title="Giới thiệu", icon="ℹ️"),
        st.Page("views/guide.py",      title="Hướng dẫn",  icon="📋"),
        st.Page("views/policy.py",     title="Chính sách", icon="📜"),
    ],
    position="hidden",
)

# Ghi pending refresh token (từ OAuth callback render trước) vào cookie
process_pending_rt()

# Session restore từ cookie (chạy trên mọi trang)
if "user" not in st.session_state:
    st.session_state.user = None
try_restore_session()

# Xử lý Google OAuth callback (?code=...) — redirect về app sau khi login
if handle_google_callback():
    st.switch_page("views/app_music.py")

# Xử lý PayPal subscription callback (?subscription_id=...) ở đây
# để mọi trang đều bắt được callback từ PayPal redirect về root URL
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
