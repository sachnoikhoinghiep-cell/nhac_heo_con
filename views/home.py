import streamlit as st
from views._nav import render as nav

nav()

st.markdown("""
<style>
.hero {
    text-align: center;
    padding: 4rem 2rem 3rem;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px;
    margin-bottom: 2.5rem;
    border: 1px solid rgba(102,126,234,0.3);
}
.hero h1 { font-size: 2.8rem; font-weight: 900; margin-bottom: 0.6rem; }
.hero p  { font-size: 1.15rem; color: rgba(255,255,255,0.75); max-width: 620px; margin: 0 auto 2rem; line-height: 1.7; }
.feat-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.6rem 1.2rem;
    text-align: center;
    height: 100%;
    transition: border 0.2s;
}
.feat-icon { font-size: 2.2rem; margin-bottom: 0.6rem; }
.feat-card h4 { margin: 0.4rem 0; font-size: 1rem; }
.feat-card p  { font-size: 0.85rem; color: rgba(255,255,255,0.6); margin: 0; line-height: 1.5; }
.price-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 2rem 1.5rem;
    text-align: center;
    height: 100%;
}
.price-card.hot {
    background: linear-gradient(160deg, rgba(102,126,234,0.18) 0%, rgba(118,75,162,0.18) 100%);
    border: 2px solid #667eea;
}
.price-amount { font-size: 2.4rem; font-weight: 900; color: #818cf8; }
.price-period { color: rgba(255,255,255,0.45); font-size: 0.85rem; margin-bottom: 1.2rem; }
.price-list   { text-align: left; padding-left: 1.2rem; color: rgba(255,255,255,0.7); font-size: 0.88rem; line-height: 2; }
.badge {
    display: inline-block;
    background: rgba(102,126,234,0.18);
    border: 1px solid rgba(102,126,234,0.35);
    border-radius: 20px;
    padding: 0.35rem 0.95rem;
    margin: 0.3rem;
    font-size: 0.88rem;
}
.step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 2.2rem; height: 2.2rem; border-radius: 50%;
    background: #667eea; color: white; font-weight: 700; font-size: 1rem;
    margin-bottom: 0.7rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎵 AI Music Producer</h1>
  <p>Tạo nhạc chuyên nghiệp từ ý tưởng đến bài hát hoàn chỉnh chỉ trong vài phút —<br>
     nhờ sức mạnh của <b>Claude AI</b>, <b>Suno</b> và <b>Google Gemini</b>.</p>
</div>
""", unsafe_allow_html=True)

ca, cb, cc = st.columns([3, 2, 3])
with cb:
    st.page_link("views/app_music.py", label="🚀 Bắt đầu tạo nhạc ngay", use_container_width=True)

# ── Stats ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
s1, s2, s3, s4 = st.columns(4)
s1.metric("Thể loại nhạc", "10+")
s2.metric("Bài mỗi lần tạo", "20")
s3.metric("Suno Models", "5")
s4.metric("Ngôn ngữ", "3")

# ── Features ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ✨ Tính năng nổi bật")
f1, f2, f3, f4 = st.columns(4, gap="medium")

for col, icon, title, desc in [
    (f1, "🤖", "AI Viết Lời & Cấu Trúc",
     "Claude AI tạo lời bài hát, cấu trúc âm nhạc và style tags chuyên nghiệp theo từng thể loại."),
    (f2, "🎶", "Tạo Nhạc Với Suno",
     "Gửi thẳng lên Suno API, nhận file MP3 chất lượng cao — 2 phiên bản cho mỗi bài, tải về trực tiếp."),
    (f3, "🖼️", "Ảnh Thumbnail AI",
     "Gemini tự tạo thumbnail và ảnh bìa 16:9 đẹp, 8K resolution, sẵn sàng đăng YouTube."),
    (f4, "📊", "SEO Tối Ưu",
     "Title, description, tags và hashtags được tối ưu cho thuật toán YouTube, TikTok."),
]:
    with col:
        st.markdown(f"""
        <div class="feat-card">
          <div class="feat-icon">{icon}</div>
          <h4>{title}</h4>
          <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⚡ Chỉ 3 bước đơn giản")
h1, h2, h3 = st.columns(3, gap="large")
for col, num, title, desc in [
    (h1, "1", "Chọn thể loại & chủ đề",
     "Chọn 1 trong 10 thể loại nhạc, nhập chủ đề bài hát hoặc dùng AI gợi ý chủ đề trending."),
    (h2, "2", "Claude AI sản xuất nội dung",
     "Hệ thống tự động viết lời, tạo style tags, kịch bản MV và toàn bộ metadata SEO."),
    (h3, "3", "Tải nhạc & đăng lên YouTube",
     "Nhấn 'Tạo nhạc Suno' — MP3 sẵn sàng trong vài phút. Tải về và đăng lên ngay!"),
]:
    with col:
        st.markdown(f"<div class='step-num'>{num}</div>", unsafe_allow_html=True)
        st.markdown(f"**{title}**")
        st.caption(desc)

# ── Genres ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🎸 10 Thể Loại Nhạc")
genres_html = "".join(f'<span class="badge">{g}</span>' for g in [
    "🎵 Thiếu Nhi", "💃 Nhạc Sàn EDM", "🔥 Vinahouse Remix", "🌀 Nonstop Mix",
    "🔊 Bass-Boosted", "🕶️ G-House", "🌀 Psytrance", "🤠 Brazilian Phonk",
    "⚙️ Techno", "💥 Hardstyle",
])
st.markdown(f'<div style="text-align:center;padding:1.2rem 0;">{genres_html}</div>',
            unsafe_allow_html=True)

# ── Pricing ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💰 Bảng Giá — Đơn giản & Minh bạch")

p1, p2, p3, p4 = st.columns(4, gap="medium")
pricing = [
    ("Ngày",  "$0.99",  "/ 24 giờ",  ["Dùng thử không giới hạn", "Tất cả thể loại nhạc", "Tối đa 20 bài/lần"], False),
    ("Tuần",  "$4.99",  "/ 7 ngày",  ["Tiết kiệm 30% so với ngày", "Tất cả thể loại nhạc", "Tối đa 20 bài/lần"], False),
    ("Tháng", "$14.99", "/ 30 ngày", ["⭐ Phổ biến nhất!", "Tất cả thể loại nhạc", "Tối đa 20 bài/lần"], True),
    ("Năm",   "$99.99", "/ 365 ngày",["Gói chuyên nghiệp VIP", "Tất cả thể loại nhạc", "Tối đa 20 bài/lần"], False),
]
for col, (name, price, period, features, is_hot) in zip([p1, p2, p3, p4], pricing):
    with col:
        hot_class = "hot" if is_hot else ""
        items = "".join(f"<li>{f}</li>" for f in features)
        st.markdown(f"""
        <div class="price-card {hot_class}">
          <h3>{name}</h3>
          <div class="price-amount">{price}</div>
          <div class="price-period">{period}</div>
          <ul class="price-list">{items}</ul>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

cta1, cta2, cta3 = st.columns([3, 2, 3])
with cta2:
    st.page_link("views/app_music.py", label="💳 Đăng ký ngay", use_container_width=True)

# ── CTA banner ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding: 2.5rem 1rem;">
  <h2>Sẵn sàng tạo nhạc của bạn? 🎵</h2>
  <p style="color: rgba(255,255,255,0.55); margin-bottom: 1.5rem;">
    Đăng nhập bằng Google — miễn phí, không cần thẻ ngay lập tức.
  </p>
</div>
""", unsafe_allow_html=True)
ca2, cb2, cc2 = st.columns([3, 2, 3])
with cb2:
    st.page_link("views/app_music.py", label="🚀 Bắt đầu ngay", use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
ft = st.columns([3, 1, 1, 1, 1])
ft[0].markdown("🎵 **nhacheocon** © 2026 — AI Music Producer Automation")
ft[1].page_link("views/about.py",  label="Giới thiệu")
ft[2].page_link("views/guide.py",  label="Hướng dẫn")
ft[3].page_link("views/policy.py", label="Chính sách")
ft[4].page_link("views/policy.py", label="Điều khoản")
