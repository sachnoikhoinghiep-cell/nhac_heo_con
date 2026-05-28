import streamlit as st


def render():
    # SEO meta tags — inject vào <head> qua JS
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
    [data-testid="stPageLink"] a {
        color: rgba(250,250,250,0.85) !important;
        text-decoration: none !important;
        font-weight: 500;
        padding: 0.35rem 0.75rem;
        border-radius: 8px;
        transition: background 0.2s;
    }
    [data-testid="stPageLink"] a:hover {
        color: #fff !important;
        background: rgba(255,255,255,0.12);
    }
    header[data-testid="stHeader"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    user     = st.session_state.get("user")
    is_admin = st.session_state.get("is_admin", False)

    if is_admin:
        c0, c1, c2, c3, c4, c5, c6, c7 = st.columns([2.2, 1, 1, 1, 1, 1, 1.2, 1.6])
    else:
        c0, c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1, 1, 1, 1, 1, 1.6])
        c7 = None

    c0.markdown("#### 🎵 **Sonicflowai**")
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
        c6.page_link("views/app_music.py", label="🔵 Đăng nhập")

    st.divider()

    # Nút scroll-to-top — tạo qua JS để tồn tại qua mỗi lần Streamlit re-render
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
            'background:rgba(99,102,241,0.82)',
            'color:#fff', 'border:none', 'border-radius:50%',
            'font-size:1.5rem', 'line-height:1',
            'cursor:pointer', 'display:none',
            'align-items:center', 'justify-content:center',
            'z-index:99999',
            'box-shadow:0 4px 14px rgba(0,0,0,0.45)',
            'transition:opacity .25s,transform .2s,background .2s',
            'opacity:0'
        ].join(';');
        btn.onmouseenter = function(){ this.style.background='rgba(99,102,241,1)'; this.style.transform='scale(1.12)'; };
        btn.onmouseleave = function(){ this.style.background='rgba(99,102,241,0.82)'; this.style.transform='scale(1)'; };
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
    """, unsafe_allow_html=True)
