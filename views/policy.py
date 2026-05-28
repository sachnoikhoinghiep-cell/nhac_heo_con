import streamlit as st
from views._nav import render as nav

nav()

_, col, _ = st.columns([1, 4, 1])
with col:
    st.markdown("# 📜 Chính Sách & Điều Khoản")
    st.caption("Cập nhật: tháng 5 năm 2026 · sonicflowai.click")
    st.divider()

    st.markdown("Chọn tài liệu bạn muốn đọc:")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div style="
            background: rgba(99,102,241,0.12);
            border: 1px solid rgba(99,102,241,0.35);
            border-radius: 14px;
            padding: 1.4rem 1.2rem;
            text-align: center;
            height: 100%;
        ">
            <div style="font-size:2.2rem;">🔒</div>
            <div style="font-weight:700;font-size:1rem;margin:0.5rem 0;">Chính Sách Bảo Mật</div>
            <div style="color:rgba(255,255,255,0.55);font-size:0.82rem;line-height:1.5;">
                Thông tin thu thập, cách sử dụng, bảo mật dữ liệu và quyền của bạn.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("views/privacy.py", label="Xem Privacy Policy →",
                     use_container_width=True)

    with c2:
        st.markdown("""
        <div style="
            background: rgba(16,185,129,0.12);
            border: 1px solid rgba(16,185,129,0.35);
            border-radius: 14px;
            padding: 1.4rem 1.2rem;
            text-align: center;
            height: 100%;
        ">
            <div style="font-size:2.2rem;">📋</div>
            <div style="font-weight:700;font-size:1rem;margin:0.5rem 0;">Điều Khoản Sử Dụng</div>
            <div style="color:rgba(255,255,255,0.55);font-size:0.82rem;line-height:1.5;">
                Quy định sử dụng, quyền sở hữu nội dung, giới hạn trách nhiệm.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("views/terms.py", label="Xem Terms of Use →",
                     use_container_width=True)

    with c3:
        st.markdown("""
        <div style="
            background: rgba(245,158,11,0.12);
            border: 1px solid rgba(245,158,11,0.35);
            border-radius: 14px;
            padding: 1.4rem 1.2rem;
            text-align: center;
            height: 100%;
        ">
            <div style="font-size:2.2rem;">↩️</div>
            <div style="font-weight:700;font-size:1rem;margin:0.5rem 0;">Chính Sách Hoàn Tiền</div>
            <div style="color:rgba(255,255,255,0.55);font-size:0.82rem;line-height:1.5;">
                Điều kiện hoàn tiền, quy trình yêu cầu và câu hỏi thường gặp.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("views/refund.py", label="Xem Refund Policy →",
                     use_container_width=True)

    st.divider()
    st.caption("© 2026 SonicFlow AI · sonicflowai.click · Mọi quyền được bảo lưu.")
