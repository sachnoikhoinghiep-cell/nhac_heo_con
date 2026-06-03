"""
browser_notify.py — Web Notifications API helper for Sonicflowai.

Usage:
  1. Call init_notifications() once per render (in _nav.py render()).
  2. Call queue_notification(title, body) BEFORE st.rerun() after generation.
  3. Call send_notification_direct(title, body) when there is no st.rerun()
     (e.g. after image generation).
"""
import json
import streamlit as st

_SETUP_SCRIPT = """
<script>
(function() {
    if (window._snfNotifInit) return;
    window._snfNotifInit = true;

    window.snfNotify = function(title, body) {
        if (!('Notification' in window) || Notification.permission !== 'granted') return;
        new Notification(title, { body: body, icon: '/favicon.ico', tag: 'sonicflowai' });
    };

    if (!('Notification' in window)) return;
    if (Notification.permission !== 'default') return;
    if (sessionStorage.getItem('snf-notif-dismissed')) return;
    if (document.getElementById('snf-notif-bar')) return;

    var bar = document.createElement('div');
    bar.id = 'snf-notif-bar';
    bar.style.cssText = [
        'position:fixed','bottom:9rem','right:2rem',
        'background:#1a1a1a',
        'border:1px solid rgba(34,197,94,0.4)',
        'border-radius:12px','padding:12px 14px',
        'z-index:99999','max-width:270px',
        'box-shadow:0 8px 24px rgba(0,0,0,0.7)',
        'font-family:sans-serif','display:flex',
        'align-items:center','gap:10px',
        'animation:snfIn .3s ease',
    ].join(';');
    bar.innerHTML =
        '<span style="font-size:1.3rem">🔔</span>'
        + '<div style="flex:1;font-size:0.8rem;color:rgba(255,255,255,0.9)">'
        + '<b>Nhận thông báo?</b><br>'
        + '<span style="color:rgba(255,255,255,0.55);font-size:0.74rem">'
        + 'Báo khi nhạc / video xong</span></div>'
        + '<button id="snf-n-ok" style="background:#22c55e;color:#000;border:none;'
        + 'border-radius:7px;padding:5px 10px;cursor:pointer;font-weight:700;'
        + 'font-size:0.78rem;white-space:nowrap">Bật</button>'
        + '<button id="snf-n-x" style="background:transparent;'
        + 'color:rgba(255,255,255,0.4);border:none;cursor:pointer;'
        + 'font-size:1.1rem;line-height:1;padding:0 2px">✕</button>';
    document.body.appendChild(bar);

    document.getElementById('snf-n-ok').onclick = function() {
        Notification.requestPermission().then(function(p) {
            bar.remove();
            if (p === 'granted') {
                window.snfNotify('Sonicflowai 🎵', '✅ Thông báo đã được bật!');
            }
        });
    };
    document.getElementById('snf-n-x').onclick = function() {
        bar.remove();
        sessionStorage.setItem('snf-notif-dismissed', '1');
    };
})();
</script>
<style>
@keyframes snfIn {
    from { opacity:0; transform:translateY(10px); }
    to   { opacity:1; transform:translateY(0); }
}
</style>
"""


def init_notifications():
    """
    Inject notification setup into the page and fire any queued notification.
    Call once per render inside _nav.py render().
    """
    pending = st.session_state.pop("_snf_notif", None)
    if pending:
        t = json.dumps(pending.get("title", "Sonicflowai"))
        b = json.dumps(pending.get("body", ""))
        st.markdown(f"""
<script>
(function() {{
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    new Notification({t}, {{ body: {b}, icon: '/favicon.ico', tag: 'sonicflowai' }});
}})();
</script>""", unsafe_allow_html=True)

    st.markdown(_SETUP_SCRIPT, unsafe_allow_html=True)


def queue_notification(title: str, body: str):
    """
    Queue a notification to fire on the next page render.
    Call this immediately BEFORE st.rerun() after a generation completes.
    """
    st.session_state["_snf_notif"] = {"title": title, "body": body}


def send_notification_direct(title: str, body: str):
    """
    Fire a notification immediately (no rerun needed).
    Use for generation flows that don't call st.rerun() at the end.
    """
    t = json.dumps(title)
    b = json.dumps(body)
    st.markdown(f"""
<script>
(function() {{
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    new Notification({t}, {{ body: {b}, icon: '/favicon.ico', tag: 'sonicflowai' }});
}})();
</script>""", unsafe_allow_html=True)
