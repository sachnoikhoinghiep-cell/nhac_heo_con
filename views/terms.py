import streamlit as st
from views._nav import render as nav

nav()

_, col, _ = st.columns([1, 4, 1])
with col:
    st.markdown("# 📋 Điều Khoản Sử Dụng")
    st.caption("Terms of Use · Cập nhật: tháng 5 năm 2026 · [sonicflowai.click](https://sonicflowai.click)")
    st.divider()

    st.markdown("""
## 1. Chấp Nhận Điều Khoản

Bằng cách truy cập hoặc sử dụng **SonicFlow AI** tại [sonicflowai.click](https://sonicflowai.click),
bạn xác nhận đã đọc, hiểu và đồng ý bị ràng buộc bởi các điều khoản này.

Nếu bạn **không đồng ý** với bất kỳ điều khoản nào, vui lòng ngừng sử dụng dịch vụ ngay lập tức.

---

## 2. Mô Tả Dịch Vụ

SonicFlow AI là nền tảng tạo nhạc bằng trí tuệ nhân tạo, kết hợp:

- **Claude AI (Anthropic)** — tạo lời nhạc, gợi ý phong cách, nội dung sáng tạo
- **Suno API** — chuyển lyrics và style tags thành file âm nhạc MP3
- **fal.ai** — tạo ảnh thumbnail và clip video
- **Google Gemini** — hỗ trợ tạo nội dung đa phương tiện

> Người dùng **tự chịu trách nhiệm** về API keys của riêng mình và mọi chi phí phát sinh
> với các nhà cung cấp API bên thứ ba.

---

## 3. Tài Khoản Người Dùng

**Điều kiện sử dụng:**
- Bạn cần tài khoản Google hợp lệ để đăng ký và đăng nhập
- Mỗi người dùng chỉ được sở hữu **một tài khoản**
- Nghiêm cấm chia sẻ tài khoản cho người khác sử dụng
- Bạn có trách nhiệm bảo mật thông tin đăng nhập của mình

**Tắt/xóa tài khoản:**
- Bạn có thể yêu cầu xóa tài khoản bất kỳ lúc nào
- SonicFlow AI có quyền tạm ngừng hoặc xóa tài khoản vi phạm

---

## 4. Gói Dịch Vụ & Thanh Toán

| Gói | Giá | Thời hạn |
|-----|-----|----------|
| Ngày | $0.99 | 24 giờ |
| Tuần | $4.99 | 7 ngày |
| Tháng | $14.99 | 30 ngày |
| Năm | $99.99 | 365 ngày |

**Quy định thanh toán:**
- Thanh toán xử lý qua **PayPal** — an toàn và bảo mật
- Gói **không tự động gia hạn** — bạn phải chủ động đăng ký lại khi hết hạn
- Giá có thể thay đổi với thông báo trước 30 ngày
- Giá đã bao gồm mọi chi phí nền tảng — không có phí ẩn

---

## 5. Sử Dụng Được Chấp Nhận

Bạn đồng ý **chỉ** sử dụng dịch vụ cho mục đích hợp pháp và không:

- Tạo nội dung vi phạm bản quyền, nhãn hiệu hoặc quyền sở hữu trí tuệ
- Tạo nội dung phỉ báng, quấy rối, thù hận hoặc kích động bạo lực
- Tạo nội dung khiêu dâm, liên quan đến trẻ em không phù hợp
- Spam, lạm dụng hoặc tấn công từ chối dịch vụ (DDoS)
- Cố gắng reverse engineer, decompile hoặc sao chép hệ thống
- Bán lại hoặc cấp phép lại quyền truy cập tài khoản của mình

---

## 6. Quyền Sở Hữu Nội Dung

**Nội dung bạn tạo ra:**
- Lời nhạc, ảnh thumbnail và nội dung sáng tạo do Claude AI tạo thuộc về bạn
- SonicFlow AI không yêu cầu bản quyền đối với output bạn tạo ra trên nền tảng

**Nội dung từ Suno AI:**
- File âm nhạc MP3 tuân theo [Điều khoản dịch vụ của Suno AI](https://suno.com/terms)
- Bạn chịu trách nhiệm tuân thủ điều khoản Suno khi phát hành hoặc kiếm tiền từ nhạc

**Nội dung của SonicFlow AI:**
- Giao diện, logo, thiết kế và code nền tảng là tài sản của SonicFlow AI
- Nghiêm cấm sao chép, phân phối hoặc tạo sản phẩm phái sinh mà không có sự đồng ý bằng văn bản

---

## 7. Tuyên Bố Miễn Trừ Trách Nhiệm

**Dịch vụ được cung cấp "nguyên trạng" (AS-IS):**
- Chúng tôi không đảm bảo tính liên tục 100% của dịch vụ
- Chúng tôi không chịu trách nhiệm về gián đoạn, lỗi hoặc ngừng hoạt động của API bên thứ ba (Suno, Google, Anthropic, fal.ai)
- Kết quả tạo nhạc và hình ảnh mang tính ngẫu nhiên theo đặc tính của AI — không đảm bảo đầu ra cụ thể

**Giới hạn bồi thường:**
- Trách nhiệm tối đa của SonicFlow AI không vượt quá số tiền bạn đã thanh toán trong 30 ngày gần nhất

---

## 8. Thay Đổi Điều Khoản

Chúng tôi có quyền cập nhật điều khoản này bất kỳ lúc nào. Thay đổi có hiệu lực ngay khi đăng tải lên website. Việc tiếp tục sử dụng dịch vụ sau khi điều khoản thay đổi đồng nghĩa với việc bạn chấp nhận điều khoản mới.

---

## 9. Luật Áp Dụng

Các điều khoản này được điều chỉnh theo pháp luật Việt Nam. Mọi tranh chấp sẽ được giải quyết thông qua thương lượng thiện chí trước khi đưa ra tòa án có thẩm quyền.

---

## 10. Liên Hệ

Câu hỏi về điều khoản sử dụng:

🌐 **Website:** [sonicflowai.click](https://sonicflowai.click)
📧 Liên hệ qua tài khoản PayPal đã thanh toán
""")

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.page_link("views/home.py",    label="🏠 Trang chủ")
    c2.page_link("views/privacy.py", label="🔒 Bảo mật")
    c3.page_link("views/refund.py",  label="↩️ Hoàn tiền")
    c4.page_link("views/policy.py",  label="📜 Chính sách")
    st.caption("© 2026 SonicFlow AI · sonicflowai.click")
