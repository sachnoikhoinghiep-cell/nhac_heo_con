import streamlit as st


def render():
    st.markdown("""
    <script>
    (function() {
        var metas = {
            'description': 'Sonicflowai — Nền tảng tạo nhạc AI tự động cho YouTube. Viết lời, tạo beat, kịch bản MV và SEO chỉ trong vài phút. Hỗ trợ 10 thể loại nhạc.',
            'keywords': 'tạo nhạc AI, AI music producer, nhạc YouTube tự động, Suno AI, Claude AI music, sonicflowai, nhạc tự động, tạo bài hát AI',
            'author': 'Sonicflowai',
            'robots': 'index, follow',
        };
        Object.entries(metas).forEach(([name, content]) => {
            if (!document.querySelector('meta[name="' + name + '"]')) {
                var m = document.createElement('meta');
                m.name = name; m.content = content;
                document.head.appendChild(m);
            }
        });
        var og = {
            'og:title': 'Sonicflowai — AI Music Producer tự động',
            'og:description': 'Tạo nhạc AI chuyên nghiệp cho YouTube. Lời nhạc, beat, MV script và SEO — tự động hoàn toàn.',
            'og:url': 'https://sonicflowai.click',
            'og:type': 'website',
            'og:image': 'https://sonicflowai.click/_static/og-image.jpg',
            'twitter:card': 'summary_large_image',
            'twitter:title': 'Sonicflowai — AI Music Producer',
            'twitter:description': 'Tạo nhạc AI tự động cho YouTube. Hỗ trợ 10 thể loại, xuất bản nhanh.',
        };
        Object.entries(og).forEach(([prop, content]) => {
            if (!document.querySelector('meta[property="' + prop + '"], meta[name="' + prop + '"]')) {
                var m = document.createElement('meta');
                m.setAttribute(prop.startsWith('og:') ? 'property' : 'name', prop);
                m.content = content;
                document.head.appendChild(m);
            }
        });
    })();
    </script>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ── Global background ── */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background-color: #080808 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0d0d0d !important;
        border-right: 1px solid rgba(255,255,255,0.07) !important;
    }
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }

    /* ── Typography defaults ── */
    .stMarkdown p { color: rgba(255,255,255,0.82); line-height: 1.7; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
    hr { border-color: rgba(255,255,255,0.08) !important; margin: 1.8rem 0 !important; }

    /* ── Streamlit metrics ── */
    [data-testid="stMetricValue"]  { color: #22c55e !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"]  { color: rgba(255,255,255,0.60) !important; font-size: 0.78rem !important; }

    /* ── Buttons (Streamlit native) ── */
    .stButton > button {
        background: #22c55e !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 9px !important;
        padding: 0.5rem 1.4rem !important;
        transition: background 0.18s, transform 0.14s !important;
    }
    .stButton > button:hover {
        background: #16a34a !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(34,197,94,0.35) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ── Page links ── */
    [data-testid="stPageLink"] a {
        color: rgba(240,240,240,0.80) !important;
        text-decoration: none !important;
        font-weight: 500;
        padding: 0.28rem 0.65rem;
        border-radius: 7px;
        font-size: 0.9rem;
        transition: color 0.18s, background 0.18s;
    }
    [data-testid="stPageLink"] a:hover {
        color: #22c55e !important;
        background: rgba(34,197,94,0.10);
    }

    /* ── Caption / small text ── */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: rgba(255,255,255,0.55) !important;
    }

    /* ── Inputs ── */
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label,
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label { color: rgba(255,255,255,0.80) !important; }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: #111 !important;
        color: #fff !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #22c55e !important;
        box-shadow: 0 0 0 2px rgba(34,197,94,0.20) !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: #0f0f0f !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] summary { color: rgba(255,255,255,0.90) !important; }
    [data-testid="stExpander"] p       { color: rgba(255,255,255,0.75) !important; }

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div > div { background: #22c55e !important; }

    /* ── Tabs ── */
    button[data-baseweb="tab"]            { color: rgba(255,255,255,0.55) !important; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #22c55e !important;
        border-bottom: 2px solid #22c55e !important;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"] { border-radius: 10px !important; }

    /* ── Hide default Streamlit header ── */
    header[data-testid="stHeader"] { display: none; }

    /* ── Logo ── */
    .snf-logo {
        font-size: 1.22rem;
        font-weight: 900;
        color: #22c55e !important;
        letter-spacing: -0.3px;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

    user     = st.session_state.get("user")
    is_admin = st.session_state.get("is_admin", False)

    if is_admin:
        c0, c1, c2, c3, c4, c5, c6, c7 = st.columns([2.2, 1, 1, 1, 1, 1, 1.2, 1.6])
    else:
        c0, c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1, 1, 1, 1, 1, 1.6])
        c7 = None

    c0.markdown('<span class="snf-logo">🎵 Sonicflowai</span>', unsafe_allow_html=True)
    c1.page_link("views/home.py",      label="Trang chủ")
    c2.page_link("views/app_music.py", label="Ứng dụng")
    c3.page_link("views/about.py",     label="Giới thiệu")
    c4.page_link("views/guide.py",     label="Hướng dẫn")
    c5.page_link("views/policy.py",    label="Chính sách")

    if user:
        if is_admin and c7 is not None:
            c6.page_link("views/admin.py", label="⚙️ Admin")
            name = (user.get("name") or "User")[:14]
            with c7:
                if st.button(f"👤 {name}", use_container_width=True, key="nav_user_btn"):
                    st.switch_page("views/user_dashboard.py")
        else:
            name = (user.get("name") or "User")[:14]
            with c6:
                if st.button(f"👤 {name}", use_container_width=True, key="nav_user_btn"):
                    st.switch_page("views/user_dashboard.py")
    else:
        c6.page_link("views/app_music.py", label="🟢 Đăng nhập")

    st.divider()

    # Floating buttons
    st.markdown("""
    <script>
    (function() {
        if (document.getElementById('nhc-scroll-top')) return;
        var btn = document.createElement('button');
        btn.id = 'nhc-scroll-top';
        btn.title = 'Về đầu trang';
        btn.innerHTML = '&#8679;';
        btn.style.cssText = [
            'position:fixed', 'bottom:2rem', 'right:2rem',
            'width:44px', 'height:44px',
            'background:rgba(34,197,94,0.85)',
            'color:#000', 'border:none', 'border-radius:50%',
            'font-size:1.5rem', 'line-height:1',
            'cursor:pointer', 'display:none',
            'align-items:center', 'justify-content:center',
            'z-index:99999',
            'box-shadow:0 4px 14px rgba(34,197,94,0.40)',
            'transition:opacity .25s,transform .2s,background .2s',
            'opacity:0'
        ].join(';');
        btn.onmouseenter = function(){ this.style.background='rgba(34,197,94,1)'; this.style.transform='scale(1.12)'; };
        btn.onmouseleave = function(){ this.style.background='rgba(34,197,94,0.85)'; this.style.transform='scale(1)'; };
        btn.onclick = function(){
            window.scrollTo({top:0,behavior:'smooth'});
            var m = document.querySelector('.main');
            if (m) m.scrollTo({top:0,behavior:'smooth'});
        };
        document.body.appendChild(btn);

        function onScroll() {
            var top = window.scrollY || (document.querySelector('.main')||{}).scrollTop || 0;
            if (top > 280) {
                btn.style.display = 'flex';
                setTimeout(function(){ btn.style.opacity='1'; }, 10);
            } else {
                btn.style.opacity = '0';
                setTimeout(function(){ btn.style.display='none'; }, 260);
            }
        }
        window.addEventListener('scroll', onScroll, {passive:true});
        var m = document.querySelector('.main');
        if (m) m.addEventListener('scroll', onScroll, {passive:true});
    })();
    </script>

    <!-- Telegram floating button + QR popup -->
    <script>
    (function() {
        if (document.getElementById('tg-support-btn')) return;

        var card = document.createElement('div');
        card.id = 'tg-qr-card';
        card.innerHTML = '<div style="font-size:0.8rem;font-weight:600;color:#229ED9;margin-bottom:6px;">💬 Nhóm hỗ trợ Telegram</div>'
                       + '<img src="/qr-telegram.jpg" width="150" height="150" style="border-radius:8px;display:block;"/>'
                       + '<div style="font-size:0.72rem;color:#aaa;margin-top:5px;text-align:center;">Quét QR hoặc nhấn nút để tham gia</div>';
        card.style.cssText = 'position:fixed;bottom:6.5rem;right:5rem;background:#111;border:1px solid rgba(34,158,217,0.4);border-radius:12px;padding:12px;z-index:99998;pointer-events:none;opacity:0;transform:translateY(6px);transition:opacity .2s,transform .2s;box-shadow:0 8px 24px rgba(0,0,0,0.6);';
        document.body.appendChild(card);

        var btn = document.createElement('a');
        btn.id = 'tg-support-btn';
        btn.href = 'https://t.me/+Jm4a8vReOgA3N2E1';
        btn.target = '_blank';
        btn.title = 'Nhóm hỗ trợ Telegram';
        btn.innerHTML = '<svg viewBox="0 0 24 24" fill="white" width="22" height="22"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L7.26 13.56l-2.956-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.884.999z"/></svg>';
        btn.style.cssText = [
            'position:fixed','bottom:5.5rem','right:2rem',
            'width:44px','height:44px',
            'background:linear-gradient(135deg,#229ED9,#1a7fc4)',
            'border:none','border-radius:50%',
            'display:flex','align-items:center','justify-content:center',
            'z-index:99999',
            'box-shadow:0 4px 14px rgba(34,158,217,0.5)',
            'cursor:pointer','text-decoration:none',
            'transition:transform .2s,box-shadow .2s',
        ].join(';');
        btn.onmouseenter = function(){
            this.style.transform='scale(1.12)';
            this.style.boxShadow='0 6px 20px rgba(34,158,217,0.7)';
            card.style.opacity='1'; card.style.transform='translateY(0)';
        };
        btn.onmouseleave = function(){
            this.style.transform='scale(1)';
            this.style.boxShadow='0 4px 14px rgba(34,158,217,0.5)';
            card.style.opacity='0'; card.style.transform='translateY(6px)';
        };
        document.body.appendChild(btn);
    })();
    </script>
    """, unsafe_allow_html=True)
