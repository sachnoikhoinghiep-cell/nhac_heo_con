import streamlit as st
from views._nav import render as nav

nav()

st.markdown("# ℹ️ Giới thiệu về Sonicflowai")
st.markdown("---")

# ── Sứ mệnh ──────────────────────────────────────────────────────────────────
st.markdown("## 🎯 Sứ Mệnh")
st.markdown("""
**Sonicflowai** ra đời với mục tiêu giúp các nhà sáng tạo nội dung — từ người mới bắt đầu đến
producer chuyên nghiệp — **tạo ra âm nhạc chất lượng cao mà không cần kiến thức âm nhạc chuyên sâu**.

Chúng tôi tin rằng mỗi ý tưởng đều xứng đáng được nghe. AI chỉ là công cụ — bạn mới là người sáng tạo.
""")

st.markdown("---")

# ── Công nghệ ─────────────────────────────────────────────────────────────────
st.markdown("## 🤖 Công Nghệ Sử Dụng")

t1, t2, t3 = st.columns(3, gap="large")
with t1:
    st.markdown("### Claude AI (Anthropic)")
    st.markdown("""
    - Viết lời bài hát chuyên nghiệp
    - Tạo cấu trúc âm nhạc theo thể loại
    - Style tags tối ưu cho Suno
    - Kịch bản MV chi tiết
    - Nội dung SEO cho YouTube
    """)
with t2:
    st.markdown("### Suno API")
    st.markdown("""
    - Tạo nhạc AI chất lượng cao
    - 5 models: V4, V4.5, V4.5+, V5, V5.5
    - 2 phiên bản mỗi bài hát
    - Thời lượng đến 8 phút
    - Tải MP3 trực tiếp
    """)
with t3:
    st.markdown("### Google Gemini")
    st.markdown("""
    - Tạo ảnh thumbnail 16:9
    - Chất lượng 8K resolution
    - Phong cách theo thể loại nhạc
    - Sẵn sàng đăng YouTube
    - Xoay vòng API key tự động
    """)

st.markdown("---")

# ── Thể loại ─────────────────────────────────────────────────────────────────
st.markdown("## 🎸 10 Thể Loại Âm Nhạc")

genres = [
    ("🎵", "Thiếu Nhi (Nursery)", "100-110 BPM", "Acoustic, Sweet, Playful — dành cho kênh YouTube thiếu nhi"),
    ("💃", "Nhạc Sàn (EDM)", "128 BPM", "Big Room, Deep Bass, Synthesizer — năng lượng cao"),
    ("🔥", "Vinahouse Remix", "140-145 BPM", "Vietnamese Hard House, Thumping Bass — phong cách Việt"),
    ("🌀", "Nonstop Mix", "138 BPM", "Continuous flow, seamless transitions — mix không ngừng"),
    ("🔊", "Bass-Boosted", "128-130 BPM", "Heavy Bass, Sub-woofer — cực mạnh, rung lắc"),
    ("🕶️", "G-House (Gangsta House)", "124-126 BPM", "Deep Bass, Hip-hop vocals — phong cách đường phố"),
    ("🌀", "Psytrance", "140-150 BPM", "Rolling Bassline, Psychedelic — ảo giác, trance"),
    ("🤠", "Brazilian Phonk", "130-140 BPM", "Cowbell, Distorted Bass — drift, bí ẩn"),
    ("⚙️", "Techno (Peak Time)", "128-135 BPM", "Industrial Kick, Hypnotic — underground rave"),
    ("💥", "Hardstyle", "150-155 BPM", "Hardkick, Euphoric Melody — năng lượng tối đa"),
]

for icon, name, bpm, desc in genres:
    with st.expander(f"{icon} **{name}** — {bpm}"):
        st.markdown(desc)

st.markdown("---")

# ── Liên hệ ───────────────────────────────────────────────────────────────────
st.markdown("## 📬 Liên Hệ & Hỗ Trợ")
st.info("Mọi thắc mắc hoặc yêu cầu hỗ trợ, vui lòng liên hệ qua PayPal hoặc để lại feedback trong ứng dụng.")

st.markdown("---")
ft = st.columns([3, 1, 1, 1, 1])
ft[0].markdown("🎵 **Sonicflowai** © 2026")
ft[1].page_link("views/home.py",   label="Trang chủ")
ft[2].page_link("views/guide.py",  label="Hướng dẫn")
ft[3].page_link("views/policy.py", label="Chính sách")
ft[4].markdown('<a href="https://t.me/+Jm4a8vReOgA3N2E1" target="_blank" style="color:#229ED9;text-decoration:none;">💬 Hỗ trợ</a>', unsafe_allow_html=True)
