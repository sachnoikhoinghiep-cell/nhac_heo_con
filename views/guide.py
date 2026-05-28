import streamlit as st
from views._nav import render as nav

nav()

st.markdown("# 📋 Hướng Dẫn Sử Dụng")
st.markdown("---")

# ── Bắt đầu ──────────────────────────────────────────────────────────────────
st.markdown("## 🚀 Bắt Đầu Nhanh (5 phút)")

with st.expander("**Bước 1 — Đăng nhập & Chọn gói**", expanded=True):
    st.markdown("""
    1. Nhấn **Đăng nhập bằng Google** — chọn tài khoản Google của bạn
    2. Sau khi đăng nhập, chọn **gói dịch vụ** phù hợp (Ngày / Tuần / Tháng / Năm)
    3. Thanh toán qua **PayPal** — an toàn và bảo mật
    4. Gói được kích hoạt ngay lập tức sau khi thanh toán thành công
    """)

with st.expander("**Bước 2 — Chuẩn bị API Keys**", expanded=True):
    st.markdown("Bạn cần 4 loại API key để dùng đầy đủ tính năng. Nhấn link bên dưới để lấy từng key:")

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
**🖼️ fal.ai API** — tạo ảnh thumbnail *(dùng chung key với Video bên dưới)*
- Dùng model **Nano Banana Pro** (fal-ai/nano-banana-pro)
- Tạo ảnh thumbnail YouTube 16:9 chất lượng cao
- Key fal.ai dùng chung cho cả ảnh và video — chỉ cần nhập 1 lần

> Xem hướng dẫn lấy fal.ai key ở cột bên phải.
""")

    with ak2:
        st.markdown("""
**🎵 Suno API** — tạo file nhạc MP3
1. Vào [sunoapi.org](https://sunoapi.org)
2. Đăng ký tài khoản
3. Vào **Dashboard** → **API Key**
4. Copy key và dán vào ô **Suno API Key** ở sidebar
5. Kiểm tra credit tại [sunoapi.org/dashboard](https://sunoapi.org/dashboard)

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

with st.expander("**Bước 3 — Tạo nhạc đầu tiên**", expanded=True):
    st.markdown("""
    1. **Chọn thể loại nhạc** ở sidebar (ví dụ: Thiếu Nhi, Bass-Boosted, Techno...)
    2. **Nhập chủ đề** bài hát (ví dụ: "Chú vịt con lông vàng") hoặc nhấn **💡 Gợi ý chủ đề**
    3. Chọn **số lượng bài** (1 single hoặc 2–20 album)
    4. Chọn **ngôn ngữ** đầu ra
    5. Nhấn **🚀 Bắt đầu sản xuất** — Claude AI sẽ tạo toàn bộ nội dung
    """)

with st.expander("**Bước 4 — Tạo nhạc Suno & Tải về**", expanded=True):
    st.markdown("""
    Sau khi Claude tạo xong lyrics và style tags:

    - **Single**: Nhấn **🎵 Tạo nhạc Suno** — chờ 2-3 phút
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
    - Không cần key Suno riêng nếu dùng key mặc định (điền vào sidebar)
    """)
    st.markdown("### 📊 SEO & Upload")
    st.markdown("""
    - Copy block **SEO** (có nút copy) → paste vào YouTube Studio
    - Dùng **hashtags** được gợi ý sẵn theo thể loại
    - Tích ✅ **Tạo kịch bản MV** để có thêm ý tưởng video
    - Lịch sử tạo nhạc lưu **72 giờ** — xem lại ở sidebar
    """)

st.markdown("---")

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.markdown("## ❓ Câu Hỏi Thường Gặp")

faqs = [
    ("Tôi có thể dùng nhạc tạo ra để kiếm tiền không?",
     "Nhạc được tạo qua Suno tuân theo chính sách của Suno AI. Với gói trả phí của Suno, bạn có quyền thương mại. Kiểm tra thêm tại suno.ai/blog/terms."),
    ("Tại sao tạo nhạc mất 2-3 phút?",
     "Suno cần thời gian để sinh âm nhạc từ lyrics. Đây là thời gian bình thường. Bạn có thể nghe preview stream trong lúc chờ."),
    ("Có thể tạo bao nhiêu bài mỗi lần?",
     "Tối đa 20 bài/lần. Với album >10 bài, Claude sẽ tự chia batch để đảm bảo chất lượng."),
    ("Lịch sử tạo nhạc lưu bao lâu?",
     "72 giờ kể từ khi tạo. Sau đó tự động xóa. Hãy tải MP3 về máy ngay sau khi tạo."),
    ("Tại sao tạo ảnh thumbnail bị lỗi?",
     "Kiểm tra fal.ai API Key ở sidebar. Nếu hết credit, nạp thêm tại fal.ai/dashboard. Mỗi ảnh tốn khoảng $0.02–0.05 credit."),
    ("Session đăng nhập kéo dài bao lâu?",
     "30 ngày. Sau 30 ngày cần đăng nhập lại bằng Google."),
]

for q, a in faqs:
    with st.expander(f"**{q}**"):
        st.markdown(a)

st.markdown("---")
ft = st.columns([3, 1, 1, 1])
ft[0].markdown("🎵 **Sonicflowai** © 2026")
ft[1].page_link("views/home.py",   label="Trang chủ")
ft[2].page_link("views/about.py",  label="Giới thiệu")
ft[3].page_link("views/policy.py", label="Chính sách")
