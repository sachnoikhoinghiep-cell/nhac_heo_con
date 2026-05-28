import streamlit as st
from views._nav import render as nav

nav()

_, col, _ = st.columns([1, 4, 1])
with col:
    st.markdown("# 🔒 Chính Sách Bảo Mật")
    st.caption("Privacy Policy · Cập nhật: tháng 5 năm 2026 · [sonicflowai.click](https://sonicflowai.click)")
    st.divider()

    st.markdown("""
## 1. Thông Tin Chúng Tôi Thu Thập

Khi bạn sử dụng **SonicFlow AI**, chúng tôi thu thập các loại thông tin sau:

**Thông tin tài khoản (qua Google Sign-In)**
- Tên hiển thị, địa chỉ email, ảnh đại diện
- Được cung cấp bởi Google OAuth 2.0 — chúng tôi không lưu mật khẩu Google của bạn

**Dữ liệu sử dụng**
- Lịch sử tạo nhạc: chủ đề, thể loại, số lượng bài
- Trạng thái đăng ký và gói dịch vụ đang dùng
- Dữ liệu project được lưu trong cơ sở dữ liệu an toàn

**API Keys (do bạn cung cấp)**
- Anthropic, Suno, Google, fal.ai API keys
- Được **mã hóa** trước khi lưu trữ — không ai đọc được giá trị thật
- Bạn có thể xóa bất kỳ lúc nào

**Thông tin thanh toán**
- Chúng tôi **không** lưu số thẻ, thông tin ngân hàng
- Toàn bộ thanh toán xử lý qua PayPal theo tiêu chuẩn PCI DSS

---

## 2. Mục Đích Sử Dụng Thông Tin

- Xác thực danh tính và quản lý phiên đăng nhập
- Kiểm tra trạng thái gói dịch vụ khi bạn truy cập
- Lưu và hiển thị lịch sử các project của bạn
- Cải thiện chất lượng dịch vụ thông qua phân tích tổng hợp (không cá nhân hóa)

---

## 3. Chia Sẻ Thông Tin Với Bên Thứ Ba

Chúng tôi **không bán, cho thuê hoặc chia sẻ** thông tin cá nhân của bạn, ngoại trừ các đối tác vận hành dịch vụ:

| Đối tác | Mục đích | Chính sách |
|---------|----------|------------|
| **Firebase / Google Cloud** | Xác thực tài khoản | [privacy.google.com](https://privacy.google.com) |
| **Supabase** | Lưu trữ dữ liệu | [supabase.com/privacy](https://supabase.com/privacy) |
| **PayPal** | Xử lý thanh toán | [paypal.com/privacy](https://www.paypal.com/privacy) |

API keys bạn nhập (Anthropic, Suno, Google) được truyền **trực tiếp** đến các nhà cung cấp tương ứng — SonicFlow AI không lưu trữ hay chia sẻ keys này theo dạng có thể đọc được.

---

## 4. Bảo Mật Dữ Liệu

- Dữ liệu lưu trữ trên **Supabase (PostgreSQL)** với mã hóa at-rest
- API keys mã hóa bằng **Fernet symmetric encryption** (AES-128-CBC)
- Kết nối HTTPS bắt buộc cho toàn bộ traffic
- Session token có thời hạn 30 ngày, tự động làm mới
- Quyền truy cập dữ liệu được kiểm soát theo từng user (Row Level Security)

---

## 5. Cookie & Local Storage

Chúng tôi sử dụng cookie trình duyệt cho:

| Cookie | Nội dung | Thời hạn |
|--------|----------|----------|
| `sonicflowai_rt` | Refresh token (đăng nhập tự động) | 30 ngày |
| `sonicflowai_ak` | API keys (tự điền) | 365 ngày |
| `sonicflowai_presets` | Preset tạo nhạc của bạn | 365 ngày |

Bạn có thể xóa toàn bộ cookie bằng cách **Đăng xuất** hoặc xóa cookie trong cài đặt trình duyệt.

---

## 6. Quyền Của Bạn

Bạn có đầy đủ quyền đối với dữ liệu của mình:

- **Truy cập**: xem tất cả dữ liệu của bạn trong trang Tài khoản
- **Chỉnh sửa**: cập nhật thông tin, đổi tên project bất kỳ lúc nào
- **Xóa**: xóa từng project hoặc toàn bộ tài khoản theo yêu cầu
- **Xuất**: yêu cầu bản sao dữ liệu của bạn qua email

---

## 7. Lưu Giữ Dữ Liệu

- **Tài khoản đang hoạt động**: dữ liệu lưu giữ vô thời hạn
- **Project hết hạn** (free tier): tự động xóa sau 72 giờ
- **Yêu cầu xóa tài khoản**: xóa toàn bộ trong vòng 7 ngày làm việc

---

## 8. Liên Hệ

Mọi câu hỏi hoặc yêu cầu liên quan đến dữ liệu cá nhân, vui lòng liên hệ qua:

📧 **Email:** liên hệ qua tài khoản PayPal thanh toán
🌐 **Website:** [sonicflowai.click](https://sonicflowai.click)
""")

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.page_link("views/home.py",   label="🏠 Trang chủ")
    c2.page_link("views/terms.py",  label="📋 Điều khoản")
    c3.page_link("views/refund.py", label="↩️ Hoàn tiền")
    c4.page_link("views/policy.py", label="📜 Chính sách")
    st.caption("© 2026 SonicFlow AI · sonicflowai.click")
