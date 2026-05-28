import streamlit as st
from views._nav import render as nav

nav()

_, col, _ = st.columns([1, 4, 1])
with col:
    st.markdown("# ↩️ Chính Sách Hoàn Tiền")
    st.caption("Refund Policy · Cập nhật: tháng 5 năm 2026 · [sonicflowai.click](https://sonicflowai.click)")
    st.divider()

    st.markdown("""
## Cam Kết Của Chúng Tôi

Sự hài lòng của bạn là ưu tiên hàng đầu. Chúng tôi cung cấp chính sách hoàn tiền **rõ ràng,
công bằng và minh bạch** để bạn yên tâm khi đăng ký dịch vụ.

---

## ✅ Các Trường Hợp Được Hoàn Tiền

| Tình huống | Điều kiện | Mức hoàn trả |
|-----------|-----------|-------------|
| **Lỗi kỹ thuật nghiêm trọng** | Nền tảng không hoạt động liên tục trên 24 giờ | **100%** |
| **Thanh toán trùng lặp** | Bị charge 2 lần cho cùng một gói | **100%** |
| **Gói không được kích hoạt** | Đã thanh toán thành công nhưng không truy cập được sau 1 giờ | **100%** |
| **Yêu cầu trong 24 giờ đầu** | Chưa sử dụng bất kỳ tính năng nào (chưa tạo nhạc, ảnh) | **100%** |
| **Lỗi một phần** | Một số tính năng không hoạt động, còn tính năng khác hoạt động bình thường | **Một phần** (theo thỏa thuận) |

---

## ❌ Các Trường Hợp Không Hoàn Tiền

- **Đã sử dụng dịch vụ** — đã tạo nhạc, ảnh thumbnail, script video, hoặc bất kỳ nội dung nào
- **Hết hạn tự nhiên** — gói Ngày/Tuần/Tháng/Năm hết thời hạn đăng ký
- **Đổi ý** — thay đổi quyết định sau khi đã sử dụng dịch vụ
- **Lỗi API bên thứ ba** — Suno, Anthropic Claude, Google, fal.ai là các dịch vụ độc lập; SonicFlow AI không kiểm soát tính khả dụng của họ
- **Chi phí API** — phí Anthropic, Suno, Google bạn tự trả cho nhà cung cấp không thuộc phạm vi hoàn tiền của chúng tôi
- **Tài khoản bị tạm ngừng** do vi phạm [Điều Khoản Sử Dụng](https://sonicflowai.click/terms)

---

## 📋 Quy Trình Yêu Cầu Hoàn Tiền

**Bước 1 — Liên hệ trong vòng 72 giờ**

Gửi yêu cầu trong vòng **72 giờ** kể từ thời điểm thanh toán.

**Bước 2 — Cung cấp thông tin**

- Email tài khoản Google đã đăng ký
- Mã giao dịch PayPal (Transaction ID)
- Mô tả chi tiết vấn đề gặp phải
- Screenshot hoặc bằng chứng lỗi (nếu có)

**Bước 3 — Xử lý**

- Chúng tôi phản hồi trong vòng **24 giờ làm việc**
- Nếu đủ điều kiện, hoàn tiền thực hiện trong **3–5 ngày làm việc** qua PayPal
- Tiền hoàn vào đúng tài khoản PayPal bạn đã dùng để thanh toán

---

## 💬 Cách Liên Hệ Yêu Cầu Hoàn Tiền

**Cách 1 — PayPal Resolution Center (Khuyên dùng)**

1. Đăng nhập vào tài khoản PayPal của bạn
2. Vào **Activity** → tìm giao dịch thanh toán cho SonicFlow AI
3. Chọn **"Report a problem"** → **"I want a refund"**
4. Mô tả lý do và gửi yêu cầu

**Cách 2 — Liên hệ trực tiếp**

Nhắn tin trực tiếp đến tài khoản PayPal mà bạn đã chuyển tiền, kèm theo
email đăng ký và mô tả vấn đề.

---

## ❓ Câu Hỏi Thường Gặp

**Tôi có thể yêu cầu hoàn tiền nhiều lần không?**

Mỗi tài khoản chỉ được hoàn tiền tối đa **1 lần**. Hoàn tiền nhiều lần sẽ bị từ chối.

**Tôi quên yêu cầu trong 72 giờ, có được không?**

Chúng tôi xem xét từng trường hợp cụ thể. Tuy nhiên sau 72 giờ, đặc biệt nếu đã sử dụng dịch vụ, việc hoàn tiền sẽ khó được chấp thuận.

**Gói Năm ($99.99) có hoàn tiền theo tỷ lệ không?**

Không. Các gói thanh toán theo thời hạn cố định không hoàn tiền theo tỷ lệ ngày còn lại.

**Suno API lỗi, tôi không tạo được nhạc — có hoàn tiền không?**

Suno là dịch vụ độc lập. Nếu **toàn bộ tính năng** (bao gồm Claude AI tạo lyrics, tạo ảnh) vẫn hoạt động, chúng tôi không hoàn tiền vì lý do Suno lỗi riêng lẻ. Tuy nhiên nếu lỗi kéo dài và ảnh hưởng nghiêm trọng, hãy liên hệ để được xem xét.

---

> ⚠️ **Lưu ý quan trọng:** Chi phí API (Anthropic, Suno, Google, fal.ai) là khoản bạn **tự thanh toán**
> trực tiếp cho các nhà cung cấp tương ứng. SonicFlow AI không thu và không chịu trách nhiệm
> hoàn lại các khoản chi phí API này.
""")

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.page_link("views/home.py",    label="🏠 Trang chủ")
    c2.page_link("views/privacy.py", label="🔒 Bảo mật")
    c3.page_link("views/terms.py",   label="📋 Điều khoản")
    c4.page_link("views/policy.py",  label="📜 Chính sách")
    st.caption("© 2026 SonicFlow AI · sonicflowai.click")
