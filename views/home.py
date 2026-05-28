import streamlit as st
from views._nav import render as nav

nav()

st.markdown("""
<style>
/* ── Hero ── */
.hero-wrap {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
    align-items: center;
    padding: 3.5rem 0 4rem;
}
@media (max-width: 768px) { .hero-wrap { grid-template-columns: 1fr; } }

.hero-tag {
    display: inline-block;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.30);
    border-radius: 20px;
    padding: 0.28rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #4ade80;
    margin-bottom: 1.2rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.hero-title {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1.1;
    color: #ffffff;
    margin: 0 0 1.1rem;
    letter-spacing: -1px;
}
.hero-title .accent { color: #22c55e; }
.hero-sub {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.68);
    line-height: 1.75;
    margin-bottom: 2rem;
    max-width: 480px;
}
.hero-btns { display: flex; gap: 0.9rem; flex-wrap: wrap; }
.btn-primary {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #22c55e;
    color: #000 !important;
    font-weight: 800;
    font-size: 0.95rem;
    padding: 0.7rem 1.6rem;
    border-radius: 9px;
    text-decoration: none !important;
    transition: background 0.18s, transform 0.14s, box-shadow 0.18s;
}
.btn-primary:hover {
    background: #16a34a;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(34,197,94,0.40);
}
.btn-outline {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: transparent;
    color: rgba(255,255,255,0.88) !important;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.68rem 1.5rem;
    border-radius: 9px;
    border: 1px solid rgba(255,255,255,0.22);
    text-decoration: none !important;
    transition: border-color 0.18s, color 0.18s, background 0.18s;
}
.btn-outline:hover {
    border-color: #22c55e;
    color: #22c55e !important;
    background: rgba(34,197,94,0.06);
}

/* ── Demo panel (right side of hero) ── */
.demo-win {
    background: #0d0d0d;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 24px 60px rgba(0,0,0,0.60), 0 0 0 1px rgba(34,197,94,0.08);
}
.demo-chrome {
    background: #141414;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding: 0.7rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.demo-chrome .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.demo-chrome .dot.r { background: #ff5f57; }
.demo-chrome .dot.y { background: #febc2e; }
.demo-chrome .dot.g { background: #28c840; }
.demo-chrome .label {
    margin-left: 10px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.40);
    font-family: monospace;
}
.demo-body { padding: 1.2rem 1.3rem 1rem; font-family: 'Courier New', monospace; font-size: 0.82rem; }
.demo-kv   { margin-bottom: 0.25rem; }
.demo-key  { color: #7dd3fc; }
.demo-val  { color: #a3e635; }
.demo-num  { color: #fb923c; }
.demo-sep  { height: 1px; background: rgba(255,255,255,0.07); margin: 0.7rem 0; }
.demo-ok   { color: #4ade80; margin-bottom: 0.22rem; }
.demo-ok::before { content: "✓  "; }
.demo-active { color: #4ade80; font-weight: 700; }
.wave-wrap  { margin: 0.8rem 0 0.4rem; display: flex; align-items: flex-end; gap: 3px; height: 36px; }
.wave-bar   { width: 5px; border-radius: 3px 3px 0 0; background: #22c55e; opacity: 0.85; }

/* ── Stats strip ── */
.stats-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 3rem;
}
.stat-item {
    background: #080808;
    padding: 1.3rem 1rem;
    text-align: center;
}
.stat-num  { font-size: 1.8rem; font-weight: 900; color: #22c55e; line-height: 1; }
.stat-lbl  { font-size: 0.78rem; color: rgba(255,255,255,0.55); margin-top: 0.3rem; }

/* ── Section label ── */
.sec-label {
    display: inline-flex; align-items: center; gap: 0.5rem;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #22c55e;
    margin-bottom: 0.6rem;
}
.sec-title { font-size: 1.7rem; font-weight: 800; color: #fff; margin-bottom: 0.5rem; }
.sec-sub   { font-size: 0.95rem; color: rgba(255,255,255,0.58); margin-bottom: 2rem; }

/* ── Feature cards ── */
.feat-card {
    background: #0d0d0d;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.6rem 1.3rem;
    height: 100%;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.feat-card:hover {
    border-color: rgba(34,197,94,0.30);
    box-shadow: 0 0 0 1px rgba(34,197,94,0.12);
}
.feat-icon { font-size: 2rem; margin-bottom: 0.7rem; }
.feat-card h4 { font-size: 1rem; font-weight: 700; color: #fff; margin: 0.4rem 0; }
.feat-card p  { font-size: 0.85rem; color: rgba(255,255,255,0.62); margin: 0; line-height: 1.6; }

/* ── Step cards ── */
.step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 2rem; height: 2rem; border-radius: 50%;
    background: rgba(34,197,94,0.15);
    border: 1px solid rgba(34,197,94,0.35);
    color: #22c55e; font-weight: 800; font-size: 0.9rem;
    margin-bottom: 0.7rem;
}

/* ── Genre badges ── */
.badge {
    display: inline-block;
    background: rgba(34,197,94,0.09);
    border: 1px solid rgba(34,197,94,0.22);
    border-radius: 20px;
    padding: 0.32rem 0.9rem;
    margin: 0.28rem;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.88);
    transition: background 0.18s, border-color 0.18s;
}
.badge:hover { background: rgba(34,197,94,0.18); border-color: rgba(34,197,94,0.45); }

/* ── Pricing cards ── */
.price-card {
    background: #0d0d0d;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 2rem 1.4rem;
    text-align: center;
    height: 100%;
    transition: border-color 0.2s;
}
.price-card:hover { border-color: rgba(34,197,94,0.25); }
.price-card.hot {
    background: linear-gradient(160deg, rgba(34,197,94,0.08) 0%, rgba(16,163,74,0.05) 100%);
    border: 1.5px solid rgba(34,197,94,0.45);
    box-shadow: 0 0 30px rgba(34,197,94,0.10);
}
.price-card h3   { color: rgba(255,255,255,0.95); font-size: 1.05rem; margin-bottom: 0.6rem; }
.price-amount    { font-size: 1.9rem; font-weight: 900; color: #22c55e; }
.price-period    { color: rgba(255,255,255,0.50); font-size: 0.82rem; margin-bottom: 1.2rem; }
.price-list      { text-align: left; padding-left: 1.1rem; color: rgba(255,255,255,0.82); font-size: 0.85rem; line-height: 2.1; }
.hot-tag {
    display: inline-block;
    background: rgba(34,197,94,0.18);
    border: 1px solid rgba(34,197,94,0.40);
    border-radius: 20px;
    padding: 0.18rem 0.7rem;
    font-size: 0.7rem;
    font-weight: 700;
    color: #4ade80;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── CTA banner ── */
.cta-banner {
    background: linear-gradient(135deg, rgba(34,197,94,0.08) 0%, rgba(16,163,74,0.04) 100%);
    border: 1px solid rgba(34,197,94,0.18);
    border-radius: 20px;
    padding: 3rem 2rem;
    text-align: center;
}
.cta-banner h2 { font-size: 1.9rem; font-weight: 800; color: #fff; margin-bottom: 0.7rem; }
.cta-banner p  { color: rgba(255,255,255,0.62); font-size: 1rem; margin-bottom: 2rem; }

/* ── Footer ── */
.footer { color: rgba(255,255,255,0.40); font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)

# ── Waveform helper ───────────────────────────────────────────────────────────
_heights = [14, 22, 30, 36, 28, 18, 34, 26, 16, 32, 24, 36, 20, 28, 36, 22, 30, 18, 34, 26]
_wave_bars = "".join(
    f'<div class="wave-bar" style="height:{h}px;opacity:{0.5 + h/80:.2f};"></div>'
    for h in _heights
)

# ── Hero ─────────────────────────────────────────────────────────────────────
hero_l, hero_r = st.columns([1, 1], gap="large")

with hero_l:
    st.markdown(f"""
    <div style="padding: 2.5rem 0 1rem;">
      <div class="hero-tag">🎵 AI Music Producer</div>
      <h1 class="hero-title">Sonicflowai —<br><span class="accent">AI tạo nhạc</span><br>chuyên nghiệp</h1>
      <p class="hero-sub">
        Tạo nhạc hoàn chỉnh từ ý tưởng chỉ trong vài phút.<br>
        Hỗ trợ <strong style="color:#4ade80;">10 thể loại nhạc</strong> —
        tự động viết lời, tạo beat, ảnh thumbnail và SEO YouTube.
      </p>
    </div>
    """, unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    bc1.page_link("views/app_music.py", label="🚀 Bắt đầu tạo nhạc", use_container_width=True)
    bc2.page_link("views/guide.py",     label="📋 Xem hướng dẫn",    use_container_width=True)

with hero_r:
    st.markdown(f"""
    <div style="padding: 2.5rem 0 1rem;">
      <div class="demo-win">
        <div class="demo-chrome">
          <span class="dot r"></span>
          <span class="dot y"></span>
          <span class="dot g"></span>
          <span class="label">AI Music Generator — sonicflowai.click</span>
        </div>
        <div class="demo-body">
          <div class="demo-kv"><span class="demo-key">genre</span>  <span style="color:rgba(255,255,255,0.30)">→</span>  <span class="demo-val">"Vinahouse Remix"</span></div>
          <div class="demo-kv"><span class="demo-key">model</span>  <span style="color:rgba(255,255,255,0.30)">→</span>  <span class="demo-val">suno-v4.5</span></div>
          <div class="demo-kv"><span class="demo-key">tempo</span>  <span style="color:rgba(255,255,255,0.30)">→</span>  <span class="demo-num">140</span> <span style="color:rgba(255,255,255,0.40)">BPM</span></div>
          <div class="demo-sep"></div>
          <div class="demo-ok">Lyrics &amp; structure generated</div>
          <div class="demo-ok">Style tags optimized</div>
          <div class="demo-ok">Thumbnail queued (16:9)</div>
          <div class="demo-ok">SEO title &amp; hashtags ready</div>
          <div class="demo-sep"></div>
          <div class="wave-wrap">{_wave_bars}</div>
          <div class="demo-active" style="margin-top:0.5rem;">● MP3 ready — 3:47 &nbsp;↓ Download</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Stats strip ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="stats-strip">
  <div class="stat-item"><div class="stat-num">10+</div><div class="stat-lbl">Thể loại nhạc</div></div>
  <div class="stat-item"><div class="stat-num">20</div><div class="stat-lbl">Bài tối đa / lần</div></div>
  <div class="stat-item"><div class="stat-num">5</div><div class="stat-lbl">Model Suno</div></div>
  <div class="stat-item"><div class="stat-num">3</div><div class="stat-lbl">Ngôn ngữ</div></div>
</div>
""", unsafe_allow_html=True)

# ── Features ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-label">✦ Tính năng</div>
<div class="sec-title">Tất cả trong một nền tảng</div>
<div class="sec-sub">Từ lời nhạc đến file MP3 — không cần kiến thức âm nhạc chuyên sâu.</div>
""", unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns(4, gap="medium")
for col, icon, title, desc in [
    (f1, "🤖", "AI Viết Lời & Cấu Trúc",
     "Claude AI tự động viết lời bài hát, cấu trúc âm nhạc và style tags chuyên nghiệp theo từng thể loại."),
    (f2, "🎶", "Tạo Nhạc Với Suno",
     "Kết nối Suno API — nhận file MP3 chất lượng cao, 2 phiên bản mỗi bài, tải về ngay lập tức."),
    (f3, "🖼️", "Ảnh & Video MV",
     "Tạo thumbnail 16:9 sắc nét cùng kịch bản MV chi tiết, sẵn sàng đăng YouTube ngay."),
    (f4, "📊", "SEO Tự Động",
     "Tiêu đề, mô tả, hashtag tối ưu cho thuật toán YouTube — không cần tốn thêm thời gian."),
]:
    with col:
        st.markdown(f"""
        <div class="feat-card">
          <div class="feat-icon">{icon}</div>
          <h4>{title}</h4>
          <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-label">✦ Quy trình</div>
<div class="sec-title">Chỉ 3 bước đơn giản</div>
<div class="sec-sub">Từ ý tưởng đến bài hát hoàn chỉnh trong vài phút.</div>
""", unsafe_allow_html=True)

h1, h2, h3 = st.columns(3, gap="large")
for col, num, title, desc in [
    (h1, "1", "Chọn thể loại & nhập chủ đề",
     "Chọn 1 trong 10 thể loại nhạc, nhập chủ đề hoặc để AI gợi ý chủ đề đang trending."),
    (h2, "2", "AI sản xuất toàn bộ nội dung",
     "Hệ thống tự động viết lời, tạo style tags, kịch bản MV và toàn bộ nội dung SEO."),
    (h3, "3", "Tải nhạc & đăng YouTube",
     "Nhấn 'Tạo nhạc Suno' — file MP3 sẵn sàng trong vài phút. Tải về và đăng lên ngay!"),
]:
    with col:
        st.markdown(f"<div class='step-num'>{num}</div>", unsafe_allow_html=True)
        st.markdown(f"**{title}**")
        st.caption(desc)

st.markdown("---")

# ── Genres ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-label">✦ Thể loại</div>
<div class="sec-title">10 Thể Loại Âm Nhạc</div>
""", unsafe_allow_html=True)

genres_html = "".join(f'<span class="badge">{g}</span>' for g in [
    "🎵 Thiếu Nhi", "💃 Nhạc Sàn EDM", "🔥 Vinahouse Remix", "🌀 Nonstop Mix",
    "🔊 Bass-Boosted", "🕶️ G-House", "🌀 Psytrance", "🤠 Brazilian Phonk",
    "⚙️ Techno", "💥 Hardstyle",
])
st.markdown(f'<div style="padding:0.8rem 0 1.6rem;">{genres_html}</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Pricing ───────────────────────────────────────────────────────────────────
st.markdown("""
<div id="pricing"></div>
<div class="sec-label">✦ Bảng giá</div>
<div class="sec-title">Thanh toán chuyển khoản nội địa</div>
<div class="sec-sub">Hỗ trợ tất cả ngân hàng Việt Nam qua cổng SePay — không cần thẻ quốc tế.</div>
""", unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4, gap="medium")
pricing = [
    ("☀️ Ngày",  "19.000 ₫",  "/ 24 giờ",
     ["Trải nghiệm toàn bộ tính năng", "Tất cả 10 thể loại nhạc", "Tối đa 20 bài mỗi lần", "Tạo ảnh thumbnail AI"], False),
    ("📅 Tuần",  "69.000 ₫",  "/ 7 ngày",
     ["Phù hợp dự án ngắn hạn", "Tất cả 10 thể loại nhạc", "Tối đa 20 bài mỗi lần", "Tạo video MV AI"], False),
    ("🗓️ Tháng", "199.000 ₫", "/ 30 ngày",
     ["Tất cả 10 thể loại nhạc", "Tối đa 20 bài mỗi lần", "Lưu lịch sử không giới hạn", "Ưu tiên hỗ trợ"], True),
    ("⭐ Năm",   "1.490.000 ₫","/ 365 ngày",
     ["Tiết kiệm hơn 37%", "Tất cả 10 thể loại nhạc", "Tối đa 20 bài mỗi lần", "Ưu tiên cập nhật tính năng"], False),
]
for col, (name, price, period, features, is_hot) in zip([p1, p2, p3, p4], pricing):
    with col:
        hot_class = "hot" if is_hot else ""
        hot_tag   = '<div class="hot-tag">⭐ Phổ biến nhất</div>' if is_hot else ""
        items = "".join(f"<li>{f}</li>" for f in features)
        st.markdown(f"""
        <div class="price-card {hot_class}">
          {hot_tag}
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

st.markdown("---")

# ── CTA banner ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cta-banner">
  <h2>🎵 Sẵn sàng tạo nhạc của bạn?</h2>
  <p>
    Đăng nhập bằng Google — miễn phí và không cần thẻ tín dụng.<br>
    Thanh toán qua chuyển khoản ngân hàng nội địa, kích hoạt ngay trong vài giây.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
ca2, cb2, cc2 = st.columns([3, 2, 3])
with cb2:
    st.page_link("views/app_music.py", label="🚀 Bắt đầu ngay", use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
ft = st.columns([3, 1, 1, 1, 1])
ft[0].markdown('<span class="footer">🎵 **Sonicflowai** © 2026 — AI Music Producer Automation</span>',
               unsafe_allow_html=True)
ft[1].page_link("views/about.py",  label="Giới thiệu")
ft[2].page_link("views/guide.py",  label="Hướng dẫn")
ft[3].page_link("views/policy.py", label="Chính sách")
ft[4].markdown('<a href="https://t.me/+Jm4a8vReOgA3N2E1" target="_blank" title="Nhóm hỗ trợ Telegram"><img src="/qr-telegram.jpg" width="72" style="border-radius:6px;display:block;"/><span style="font-size:0.7rem;color:#229ED9;">💬 Hỗ trợ Telegram</span></a>', unsafe_allow_html=True)
