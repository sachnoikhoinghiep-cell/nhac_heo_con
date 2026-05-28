import streamlit as st
from views._nav import render as nav

nav()

st.markdown("# 📋 Hướng Dẫn Sử Dụng")
st.markdown("---")

# ── Bắt đầu ──────────────────────────────────────────────────────────────────
st.markdown("## 🚀 Bắt Đầu Nhanh (5 phút)")

with st.expander("**Bước 1 — Đăng nhập**", expanded=True):
    st.markdown("""
    1. Nhấn **Đăng nhập bằng Google** — chọn tài khoản Google của bạn
    2. Hệ thống tự lưu phiên đăng nhập **30 ngày** — không cần đăng nhập lại
    3. Sau khi đăng nhập, chọn **gói dịch vụ** và thanh toán để bắt đầu sử dụng
    """)

with st.expander("**Bước 2 — Chọn gói & Thanh toán (Chuyển khoản VNĐ)**", expanded=True):
    st.markdown("""
    **Sonicflowai** hỗ trợ thanh toán **chuyển khoản ngân hàng nội địa** qua cổng SePay — không cần thẻ quốc tế.

    #### Bảng giá
    | Gói | Giá | Thời hạn |
    |-----|-----|----------|
    | ☀️ Ngày | 19.000 ₫ | 1 ngày |
    | 📅 Tuần | 69.000 ₫ | 7 ngày |
    | 🗓️ Tháng | 199.000 ₫ | 30 ngày |
    | ⭐ Năm | 1.490.000 ₫ | 365 ngày |

    #### Các bước thanh toán
    1. Chọn gói → nhấn **📱 Tạo QR & Mã Thanh Toán**
    2. Quét mã QR bằng app ngân hàng **hoặc** chuyển khoản thủ công
    3. **Bắt buộc**: ghi đúng nội dung chuyển khoản (mã `SONIC...` hiển thị trên màn hình)
    4. Gói được **tự động kích hoạt** trong vòng 5–30 giây sau khi nhận tiền
    5. Nhấn **✅ Tôi đã chuyển khoản** để kiểm tra ngay

    > ⚠️ **Nội dung chuyển khoản phải chứa đúng mã SONIC...** — hệ thống tự nhận dạng và kích hoạt. Sai mã sẽ không được ghi nhận tự động.
    """)

with st.expander("**Bước 3 — Chuẩn bị API Keys**", expanded=True):
    st.markdown("Bạn cần các API key sau để dùng đầy đủ tính năng. Nhấn link để lấy từng key:")

    ak1, ak2 = st.columns(2)

    with ak1:
        st.markdown("""
**🤖 Anthropic API** — viết lời & cấu trúc nhạc
1. Vào [console.anthropic.com](https://console.anthropic.com)
2. Đăng ký / Đăng nhập
3. Chọn **API Keys** → **Create Key**
4. Copy key bắt đầu bằng `sk-ant-...`
5. Dán vào ô **Anthropic API Key** ở sidebar

> Free tier: $5 credit khi đăng ký lần đầu.
""")

        st.markdown("""
**🖼️ fal.ai API** — tạo ảnh thumbnail & video MV
- Dùng model **Nano Banana Pro** cho ảnh thumbnail 16:9
- Key fal.ai dùng chung cho cả ảnh và video — chỉ cần nhập 1 lần

> Xem hướng dẫn lấy key ở cột bên phải.
""")

    with ak2:
        st.markdown("""
**🎵 Suno API** — tạo file nhạc MP3
1. Vào [sunoapi.org](https://sunoapi.org)
2. Đăng ký tài khoản
3. Vào **Dashboard** → **API Key**
4. Copy key và dán vào ô **Suno API Key** ở sidebar

> Mỗi bài nhạc tốn ~2 credits. Nạp thêm credit khi cần.
""")

        st.markdown("""
**🎬 fal.ai API** — tạo video từ kịch bản MV
1. Vào [fal.ai/dashboard](https://fal.ai/dashboard)
2. Đăng ký / Đăng nhập
3. Chọn **Keys** → **Add Key**
4. Copy key bắt đầu bằng `fal-...`
5. Dán vào ô **fal.ai API Key** ở sidebar

> Dùng Seedance 2.0: text-to-video, image-to-video, reference-to-video.
""")

    st.info("💡 Nhập xong nhấn **💾 Lưu API Keys** — keys được lưu vào tài khoản, tự điền ở mọi thiết bị khi đăng nhập.")

with st.expander("**Bước 4 — Tạo nhạc đầu tiên**", expanded=True):
    st.markdown("""
    1. **Chọn thể loại nhạc** ở sidebar (ví dụ: Thiếu Nhi, Bass-Boosted, Techno...)
    2. **Nhập chủ đề** bài hát (ví dụ: "Chú vịt con lông vàng") hoặc nhấn **💡 Gợi ý chủ đề**
    3. Chọn **số lượng bài** (1 single hoặc 2–20 album)
    4. Chọn **ngôn ngữ** đầu ra
    5. Nhấn **🚀 Bắt đầu sản xuất** — Claude AI sẽ tạo toàn bộ nội dung
    """)

with st.expander("**Bước 5 — Tạo nhạc Suno & Tải về**", expanded=True):
    st.markdown("""
    Sau khi Claude tạo xong lyrics và style tags:

    - **Single**: Nhấn **🎵 Tạo nhạc Suno** — chờ 2–3 phút
    - **Album**: Nhấn **🚀 Tạo tất cả nhạc** — xử lý song song tất cả bài
    - Mỗi bài có **2 phiên bản** (Version A và B)
    - Nhấn **⬇️ Tải MP3** để lưu về máy

    > 🎧 Có preview stream trong lúc chờ — nghe thử ngay khi track đầu tiên hoàn thành!
    """)

st.markdown("---")

# ── Tips ──────────────────────────────────────────────────────────────────────
st.markdown("## 💡 Mẹo Để Có Kết Quả Tốt Nhất")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🎵 Viết Lời Tốt Hơn")
    st.markdown("""
    - Chủ đề **càng cụ thể** càng tốt (không phải "bài về xe", mà là "xe cứu hỏa cứu rừng")
    - Kết hợp với **gợi ý chủ đề hot** để đúng xu hướng
    - Chọn **thể loại phù hợp** với kênh YouTube của bạn
    - Thử **Tiếng Anh** nếu muốn reach thêm audience quốc tế
    """)
    st.markdown("### 🖼️ Ảnh Thumbnail")
    st.markdown("""
    - Dùng **fal.ai API Key** (Nano Banana Pro model)
    - Nhấn **🔄 Tạo lại ảnh** nếu kết quả chưa ưng
    - Tải ảnh PNG và chỉnh thêm text bằng Canva nếu cần
    """)

with c2:
    st.markdown("### 🎶 Tạo Nhạc Suno")
    st.markdown("""
    - **V4.5** là model cân bằng nhất (chất lượng cao, nhanh)
    - **V5/V5.5** cho bài dài hơn (đến 8 phút)
    - Nếu 1 version không hay, dùng **Version B** — Suno luôn tạo 2 phiên bản
    """)
    st.markdown("### 📊 SEO & Upload")
    st.markdown("""
    - Copy block **SEO** (có nút copy) → paste vào YouTube Studio
    - Dùng **hashtags** được gợi ý sẵn theo thể loại
    - Tích ✅ **Tạo kịch bản MV** để có thêm ý tưởng video
    - Xem lại lịch sử projects trong **👤 Tài khoản của tôi**
    """)

st.markdown("---")

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.markdown("## ❓ Câu Hỏi Thường Gặp")

faqs = [
    ("Thanh toán bằng hình thức nào?",
     "Sonicflowai dùng cổng SePay — chuyển khoản ngân hàng nội địa Việt Nam (BIDV, Vietcombank, MB Bank, Techcombank...). Không cần thẻ quốc tế. Sau khi chuyển khoản đúng nội dung SONIC..., hệ thống tự kích hoạt gói trong 5–30 giây."),
    ("Chuyển khoản xong nhưng chưa được kích hoạt?",
     "Kiểm tra nội dung chuyển khoản có chứa đúng mã SONIC... không. Nếu đúng mã, nhấn '✅ Tôi đã chuyển khoản' để hệ thống kiểm tra lại. Nếu vẫn chưa kích hoạt sau 2 phút, liên hệ hỗ trợ qua Telegram (nút 💬 góc phải màn hình)."),
    ("Mã thanh toán SONIC... có thời hạn bao lâu?",
     "30 phút kể từ khi tạo. Nếu hết hạn, nhấn '🔄 Tạo mã mới' để tạo lại. Tiền đã chuyển trước khi hết hạn vẫn được ghi nhận."),
    ("Tôi có thể dùng nhạc tạo ra để kiếm tiền không?",
     "Nhạc được tạo qua Suno tuân theo chính sách của Suno AI. Với gói trả phí của Suno, bạn có quyền thương mại. Kiểm tra thêm tại suno.ai/blog/terms."),
    ("Tại sao tạo nhạc mất 2–3 phút?",
     "Suno cần thời gian để sinh âm nhạc từ lyrics. Đây là thời gian bình thường. Bạn có thể nghe preview stream trong lúc chờ."),
    ("Có thể tạo bao nhiêu bài mỗi lần?",
     "Tối đa 20 bài/lần. Với album >10 bài, Claude sẽ tự chia batch để đảm bảo chất lượng."),
    ("Tại sao tạo ảnh thumbnail bị lỗi?",
     "Kiểm tra fal.ai API Key ở sidebar. Nếu hết credit, nạp thêm tại fal.ai/dashboard. Mỗi ảnh tốn khoảng $0.02–0.05 credit."),
    ("Liên hệ hỗ trợ ở đâu?",
     "Nhấn nút 💬 Hỗ trợ (màu xanh Telegram, góc phải màn hình) hoặc link 💬 Hỗ trợ ở footer để vào nhóm hỗ trợ Telegram."),
]

for q, a in faqs:
    with st.expander(f"**{q}**"):
        st.markdown(a)

st.markdown("---")
ft = st.columns([3, 1, 1, 1, 1])
ft[0].markdown("🎵 **Sonicflowai** © 2026")
ft[1].page_link("views/home.py",   label="Trang chủ")
ft[2].page_link("views/about.py",  label="Giới thiệu")
ft[3].page_link("views/policy.py", label="Chính sách")
ft[4].markdown('<a href="https://t.me/+Jm4a8vReOgA3N2E1" target="_blank" title="Nhóm hỗ trợ Telegram"><img src="/qr-telegram.jpg" width="72" style="border-radius:6px;display:block;"/><span style="font-size:0.7rem;color:#229ED9;">💬 Hỗ trợ Telegram</span></a>', unsafe_allow_html=True)
