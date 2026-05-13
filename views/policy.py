import streamlit as st
from views._nav import render as nav

nav()

st.markdown("# 📜 Chính Sách & Điều Khoản")
st.markdown("*Cập nhật lần cuối: tháng 5 năm 2026*")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔒 Chính Sách Bảo Mật", "📋 Điều Khoản Dịch Vụ", "↩️ Chính Sách Hoàn Tiền"])

# ── Tab 1: Privacy Policy ─────────────────────────────────────────────────────
with tab1:
    st.markdown("## 🔒 Chính Sách Bảo Mật")
    st.markdown("""
    ### 1. Thông Tin Chúng Tôi Thu Thập

    Khi bạn sử dụng **nhacheocon**, chúng tôi thu thập:

    - **Thông tin tài khoản Google**: tên, địa chỉ email và ảnh đại diện (thông qua Google Sign-In)
    - **Dữ liệu sử dụng**: lịch sử tạo nhạc (chủ đề, thể loại, số bài) — lưu 72 giờ rồi tự xóa
    - **Thông tin thanh toán**: chúng tôi **không** lưu trữ thông tin thẻ — toàn bộ thanh toán xử lý qua PayPal

    ### 2. Cách Chúng Tôi Sử Dụng Thông Tin

    - Xác thực danh tính và quản lý tài khoản
    - Kiểm tra trạng thái đăng ký và kích hoạt gói dịch vụ
    - Hiển thị lịch sử tạo nhạc trong phiên làm việc
    - Cải thiện chất lượng dịch vụ

    ### 3. Chia Sẻ Thông Tin

    Chúng tôi **không bán, cho thuê hoặc chia sẻ** thông tin cá nhân của bạn với bên thứ ba, ngoại trừ:

    - **Firebase (Google)**: lưu trữ thông tin tài khoản và dữ liệu ứng dụng
    - **PayPal**: xử lý thanh toán (tuân theo chính sách bảo mật của PayPal)
    - **Anthropic, Suno, Google**: API keys do bạn tự cung cấp — chúng tôi không lưu trữ

    ### 4. Bảo Mật Dữ Liệu

    - Dữ liệu được lưu trữ trên **Firebase (Google Cloud)** với mã hóa tiêu chuẩn
    - API keys của bạn được lưu trong **cookie trình duyệt** và không gửi lên server của chúng tôi
    - Session đăng nhập sử dụng **Firebase ID Token** và refresh token bảo mật

    ### 5. Cookie

    Chúng tôi sử dụng cookie trình duyệt để:

    - Duy trì phiên đăng nhập (30 ngày)
    - Lưu API keys để tự điền khi quay lại (365 ngày)

    Bạn có thể xóa cookie bất kỳ lúc nào bằng cách đăng xuất hoặc xóa cookie trình duyệt.

    ### 6. Quyền Của Bạn

    Bạn có quyền:
    - **Xóa tài khoản**: liên hệ để yêu cầu xóa toàn bộ dữ liệu
    - **Truy cập dữ liệu**: yêu cầu bản sao thông tin của bạn
    - **Đăng xuất**: xóa phiên làm việc bất kỳ lúc nào

    ### 7. Liên Hệ

    Mọi thắc mắc về bảo mật, vui lòng liên hệ qua tài khoản PayPal của chúng tôi.
    """)

# ── Tab 2: Terms of Service ───────────────────────────────────────────────────
with tab2:
    st.markdown("## 📋 Điều Khoản Dịch Vụ")
    st.markdown("""
    ### 1. Chấp Nhận Điều Khoản

    Bằng cách sử dụng **nhacheocon**, bạn đồng ý với các điều khoản này. Nếu không đồng ý, vui lòng không sử dụng dịch vụ.

    ### 2. Mô Tả Dịch Vụ

    nhacheocon cung cấp nền tảng tạo nhạc AI sử dụng:
    - Claude AI (Anthropic) để tạo nội dung âm nhạc
    - Suno API để tạo file âm nhạc
    - Google Gemini để tạo hình ảnh

    Người dùng **tự chịu trách nhiệm** về API keys của riêng mình và chi phí phát sinh với các nhà cung cấp API.

    ### 3. Tài Khoản Người Dùng

    - Bạn cần tài khoản Google hợp lệ để sử dụng dịch vụ
    - Một người dùng chỉ được tạo một tài khoản
    - Nghiêm cấm chia sẻ tài khoản cho người khác sử dụng

    ### 4. Gói Dịch Vụ & Thanh Toán

    - Các gói dịch vụ được tính theo thời hạn: Ngày / Tuần / Tháng / Năm
    - Thanh toán thực hiện qua PayPal — an toàn và bảo mật
    - Gói tự động hết hạn sau thời hạn đăng ký
    - Không tự động gia hạn — bạn phải đăng ký lại khi hết hạn

    ### 5. Sử Dụng Hợp Lệ

    Nghiêm cấm sử dụng dịch vụ để:
    - Tạo nội dung vi phạm bản quyền, phỉ báng hoặc bất hợp pháp
    - Tạo nội dung thù hận, bạo lực, hoặc nội dung người lớn không phù hợp
    - Spam hoặc lạm dụng hệ thống API
    - Reverse engineer hoặc sao chép hệ thống

    ### 6. Quyền Sở Hữu Nội Dung

    - Nội dung lyrics và ảnh tạo ra thuộc về bạn trong phạm vi cho phép của các API liên quan
    - Âm nhạc tạo qua Suno tuân theo [Điều khoản của Suno AI](https://suno.ai)
    - nhacheocon không yêu cầu bản quyền đối với nội dung bạn tạo ra

    ### 7. Giới Hạn Trách Nhiệm

    - Dịch vụ được cung cấp "nguyên trạng" (as-is)
    - Chúng tôi không đảm bảo tính liên tục của dịch vụ API bên thứ ba
    - Không chịu trách nhiệm về gián đoạn do Suno, Google, hoặc Anthropic

    ### 8. Chấm Dứt Dịch Vụ

    Chúng tôi có quyền tạm ngừng hoặc chấm dứt tài khoản nếu phát hiện vi phạm điều khoản mà không cần báo trước.
    """)

# ── Tab 3: Refund Policy ──────────────────────────────────────────────────────
with tab3:
    st.markdown("## ↩️ Chính Sách Hoàn Tiền")
    st.markdown("""
    ### Cam Kết Của Chúng Tôi

    Chúng tôi muốn bạn hài lòng với dịch vụ. Đây là chính sách hoàn tiền rõ ràng và công bằng:

    ### ✅ Được Hoàn Tiền

    | Tình huống | Điều kiện | Mức hoàn |
    |-----------|-----------|---------|
    | Lỗi kỹ thuật nghiêm trọng | Hệ thống không hoạt động >24h liên tục | 100% |
    | Thanh toán trùng lặp | Bị charge 2 lần cùng gói | 100% |
    | Gói chưa kích hoạt sau 1h | Đã thanh toán nhưng không truy cập được | 100% |
    | Trong vòng 24h đầu | Chưa sử dụng bất kỳ tính năng nào | 100% |

    ### ❌ Không Hoàn Tiền

    - Đã sử dụng dịch vụ (đã tạo nhạc, ảnh, hoặc nội dung)
    - Hết hạn tự nhiên (gói Ngày/Tuần/Tháng/Năm hết thời hạn)
    - Lỗi từ API bên thứ ba (Suno, Google, Anthropic) — đây là dịch vụ độc lập
    - Đổi ý sau khi đã sử dụng

    ### 📞 Quy Trình Yêu Cầu Hoàn Tiền

    1. Liên hệ trong vòng **72 giờ** kể từ khi thanh toán
    2. Cung cấp email tài khoản Google đã đăng ký
    3. Mô tả vấn đề gặp phải
    4. Hoàn tiền xử lý trong **3-5 ngày làm việc** qua PayPal

    ### 💬 Liên Hệ Hỗ Trợ

    Gửi yêu cầu hoàn tiền qua PayPal Resolution Center hoặc liên hệ trực tiếp với tài khoản PayPal
    mà bạn đã thanh toán.

    > ⚠️ **Lưu ý**: Chi phí API (Anthropic, Suno, Google) do bạn tự trả cho các nhà cung cấp —
    > nhacheocon không chịu trách nhiệm hoàn lại các khoản này.
    """)

st.markdown("---")
ft = st.columns([3, 1, 1, 1])
ft[0].markdown("🎵 **nhacheocon** © 2026")
ft[1].page_link("views/home.py",  label="Trang chủ")
ft[2].page_link("views/about.py", label="Giới thiệu")
ft[3].page_link("views/guide.py", label="Hướng dẫn")
