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
| **Chuyển khoản nhầm / trùng lặp** | Bị trừ tiền 2 lần hoặc chuyển sai mã thanh toán | **100%** |
| **Gói không được kích hoạt** | Đã chuyển khoản thành công nhưng tài khoản không mở khóa sau 1 giờ | **100%** |
| **Yêu cầu trong 24 giờ đầu** | Chưa sử dụng bất kỳ tính năng nào (chưa tạo nhạc, ảnh) | **100%** |
| **Lỗi một phần** | Một số tính năng không hoạt động, còn tính năng khác hoạt động bình thường | **Một phần** (theo thỏa thuận) |

---

## ❌ Các Trường Hợp Không Hoàn Tiền

- **Đã sử dụng dịch vụ** — đã tạo nhạc, ảnh thumbnail, script video, hoặc bất kỳ nội dung nào
- **Hết hạn tự nhiên** — gói Ngày/Tuần/Tháng/Năm hết thời hạn đăng ký
- **Đổi ý** — thay đổi quyết định sau khi đã sử dụng dịch vụ
- **Lỗi API bên thứ ba** — Suno, Anthropic Claude, Google, fal.ai là dịch vụ độc lập; SonicFlow AI không kiểm soát tính khả dụng của họ
- **Chi phí API** — phí bạn tự trả cho Anthropic, Suno, Google không thuộc phạm vi hoàn tiền
- **Tài khoản bị tạm ngừng** do vi phạm [Điều Khoản Sử Dụng](https://sonicflowai.click/terms)

---

## 📋 Quy Trình Yêu Cầu Hoàn Tiền

Toàn bộ quy trình được xử lý **trực tiếp trong ứng dụng** — không cần email hay liên hệ ngoài.

### Bước 1 — Gửi yêu cầu qua form trong app

1. Đăng nhập vào tài khoản SonicFlow AI
2. Vào **Tài khoản** → Tab **🎧 Hỗ trợ**
3. Bấm **Gửi yêu cầu hỗ trợ mới**
4. Chọn loại yêu cầu: **"Yêu cầu Hoàn tiền (Lỗi giao dịch)"**
5. Chọn giao dịch liên quan trong danh sách, mô tả chi tiết vấn đề
6. Nhập **đầy đủ thông tin ngân hàng** để nhận tiền:
   `Ngân hàng — Số tài khoản — Tên chủ thẻ`
7. Bấm **🚀 Gửi yêu cầu**

> ⏰ Gửi yêu cầu trong vòng **72 giờ** kể từ thời điểm thanh toán.

### Bước 2 — Admin xét duyệt & chuyển khoản

- Chúng tôi phản hồi trong vòng **24 giờ làm việc**
- Nếu yêu cầu hợp lệ, Admin chuyển khoản trực tiếp vào tài khoản ngân hàng bạn đã cung cấp
- Hoàn tiền thực hiện qua **chuyển khoản ngân hàng nội địa** (MB Bank / VCB), thường trong **1 ngày làm việc**

### Bước 3 — Cập nhật trạng thái trong app

- Ticket chuyển sang trạng thái **✅ Đã Giải Quyết**
- Gói cước của bạn bị thu hồi ngay lập tức
- Bạn có thể xem lại toàn bộ lịch sử trong Tab **🎧 Hỗ trợ**

---

## ❓ Câu Hỏi Thường Gặp

**Tôi không thấy Tab Hỗ trợ ở đâu?**

Đăng nhập → Bấm vào tên hoặc avatar của bạn → Trang **Tài khoản của tôi** → Chọn tab **🎧 Hỗ trợ**.

**Tôi chưa đăng nhập, làm sao liên hệ?**

Nếu không thể đăng nhập, hãy nhắn vào nhóm Telegram hỗ trợ (link ở góc phải trang chủ) kèm mã giao dịch và email đăng ký.

**Tôi có thể yêu cầu hoàn tiền nhiều lần không?**

Mỗi tài khoản chỉ được hoàn tiền tối đa **1 lần**. Các yêu cầu tiếp theo sẽ bị từ chối.

**Quá 72 giờ mới phát hiện lỗi, có được không?**

Chúng tôi xem xét từng trường hợp cụ thể. Sau 72 giờ, đặc biệt nếu đã sử dụng dịch vụ, khả năng chấp thuận sẽ thấp hơn.

**Gói Năm (1.490.000₫) có hoàn tiền theo tỷ lệ không?**

Không. Các gói thanh toán theo thời hạn cố định không áp dụng hoàn tiền theo tỷ lệ ngày còn lại.

**Suno API lỗi, tôi không tạo được nhạc — có hoàn tiền không?**

Suno là dịch vụ độc lập. Nếu **toàn bộ tính năng** (Claude AI tạo lyrics, tạo ảnh) vẫn hoạt động, chúng tôi không hoàn tiền vì lý do Suno lỗi riêng lẻ. Nếu lỗi kéo dài và ảnh hưởng nghiêm trọng, hãy gửi ticket để được xem xét.

---

> ⚠️ **Lưu ý quan trọng:** Chi phí API (Anthropic, Suno, Google, fal.ai) là khoản bạn **tự thanh toán**
> trực tiếp cho các nhà cung cấp tương ứng. SonicFlow AI không thu và không chịu trách nhiệm
> hoàn lại các khoản chi phí API này.
""")

    # CTA box
    user = st.session_state.get("user")
    st.divider()
    if user:
        st.info("Bạn đang đăng nhập. Gửi yêu cầu hoàn tiền trực tiếp từ trang Tài khoản.")
        st.page_link("views/user_dashboard.py", label="🎧 Đến Tab Hỗ trợ →", use_container_width=False)
    else:
        st.info("Đăng nhập để gửi yêu cầu hoàn tiền nhanh chóng ngay trong ứng dụng.")
        st.page_link("views/app_music.py", label="🔵 Đăng nhập", use_container_width=False)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.page_link("views/home.py",    label="🏠 Trang chủ")
    c2.page_link("views/privacy.py", label="🔒 Bảo mật")
    c3.page_link("views/terms.py",   label="📋 Điều khoản")
    c4.page_link("views/policy.py",  label="📜 Chính sách")
    st.caption("© 2026 SonicFlow AI · sonicflowai.click")
