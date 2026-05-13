import streamlit as st


def render():
    st.markdown("""
    <style>
    [data-testid="stPageLink"] a {
        color: rgba(250,250,250,0.85) !important;
        text-decoration: none !important;
        font-weight: 500;
        padding: 0.35rem 0.75rem;
        border-radius: 8px;
        transition: background 0.2s;
    }
    [data-testid="stPageLink"] a:hover {
        color: #fff !important;
        background: rgba(255,255,255,0.12);
    }
    header[data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    c0, c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1, 1, 1, 1, 1, 1.6])

    c0.markdown("#### 🎵 **nhacheocon**")
    c1.page_link("views/home.py",    label="Trang chủ")
    c2.page_link("views/app_music.py", label="Ứng dụng")
    c3.page_link("views/about.py",   label="Giới thiệu")
    c4.page_link("views/guide.py",   label="Hướng dẫn")
    c5.page_link("views/policy.py",  label="Chính sách")

    user = st.session_state.get("user")
    if user:
        with c6:
            name = (user.get("name") or "User")[:14]
            if st.button(f"👤 {name}", use_container_width=True, key="nav_user_btn"):
                st.switch_page("views/app_music.py")
    else:
        c6.page_link("views/app_music.py", label="🔵 Đăng nhập")

    st.divider()
