import streamlit as st
import anthropic
from llm_router import generate_text, provider_label
from auth import (
    show_auth_ui, verify_and_load_user,
    activate_plan, save_music_history, get_music_history, sign_out,
    save_api_keys, load_api_keys,
    save_user_api_keys, load_user_api_keys,
    save_presets, load_presets,
    update_history_suno,
    save_video_prefs, load_video_prefs,
)
from views._nav import render as nav
from browser_notify import queue_notification, send_notification_direct

nav()

import requests
import json
import io
import os
import time
from datetime import date, datetime, timezone
from prompts import (
    SYSTEM_PROMPT,
    build_single_prompt,
    build_album_first_batch_prompt,
    build_album_continuation_prompt,
    build_video_script_prompt,
    build_keyword_prompt,
    build_topic_suggestion_prompt,
    build_mv_director_prompt,
)

# ---------------------------------------------------------------------------
# Auth gate — Google Sign-In + Firebase
# ---------------------------------------------------------------------------
import sys, importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sepay import PLANS_VND, TOPUP_VND, BYOK_PLAN, COIN_COSTS, create_payment_request, check_payment_status, fmt_vnd
from auth import deduct_coins as _deduct_coins

for _k, _v in {
    "user":             None,
    "mv_storyboards":   {},
    "sepay_payment":    None,   # dict: payment_code, amount_vnd, qr_url, plan, expires_at
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Chưa đăng nhập → trang yêu cầu đăng nhập
if not st.session_state.user:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem 1rem;">
        <div style="font-size:3.5rem;">🎵</div>
        <h2>Đăng nhập để tạo nhạc</h2>
        <p style="color:rgba(255,255,255,0.88); max-width:480px; margin:0 auto 2rem;">
            Các trang <b>Trang chủ</b>, <b>Giới thiệu</b>, <b>Hướng dẫn</b>
            và <b>Chính sách</b> xem tự do — không cần đăng nhập.<br><br>
            Để <b>tạo nhạc AI</b>, cần đăng nhập và chọn gói dịch vụ.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        show_auth_ui()
        st.divider()
        st.page_link("views/home.py", label="🏠 Về trang chủ",
                     use_container_width=True)
        st.page_link("views/home.py", label="💰 Xem bảng giá & gói dịch vụ",
                     use_container_width=True)
        st.page_link("views/guide.py", label="📋 Xem hướng dẫn sử dụng",
                     use_container_width=True)
    st.stop()

# Đã đăng nhập
_user = st.session_state.user
st.sidebar.markdown(
    f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>"
    f"<img src='{_user['photo']}' width='36' style='border-radius:50%'/>"
    f"<div><b>{_user['name']}</b><br/><small>{_user['email']}</small></div></div>",
    unsafe_allow_html=True,
)
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    sign_out()
    st.stop()

# Chưa thanh toán → trang chọn gói SePay
if not _user["is_paid"]:
    _PAY      = st.session_state.get("sepay_payment")
    _BYOK_PAY = st.session_state.get("sepay_byok_payment")

    # ── Auto-check cả 2 luồng thanh toán ─────────────────────────────────
    def _refresh_user_after_payment(clear_key: str):
        from supabase_db import load_user_with_subscription as _lwu
        _r = _lwu(_user["uid"])
        if _r.get("is_paid"):
            st.session_state.user = _r
            st.session_state.pop(clear_key, None)
            st.rerun()

    if _PAY and _PAY.get("payment_code"):
        if check_payment_status(_PAY["payment_code"]) == "completed":
            _refresh_user_after_payment("sepay_payment")

    if _BYOK_PAY and _BYOK_PAY.get("payment_code"):
        if check_payment_status(_BYOK_PAY["payment_code"]) == "completed":
            _refresh_user_after_payment("sepay_byok_payment")

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center; padding: 2rem 1rem 0.5rem;">
        <div style="font-size:3rem;">🎵</div>
        <h2>Chọn gói để bắt đầu tạo nhạc</h2>
        <p style="color:rgba(255,255,255,0.88); max-width:560px; margin:0 auto 0.5rem;">
            Xin chào <b>{_user['name']}</b>! Chọn mô hình phù hợp nhất với bạn.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 2 Tab: Gói Trọn Gói vs Gói Tự Túc ───────────────────────────────
    _tab_bundled, _tab_byok = st.tabs(["🪙 Gói Trọn Gói", "🔑 Gói Tự Túc (BYOK)"])

    # ════ TAB 1: BUNDLED ═════════════════════════════════════════════════
    with _tab_bundled:
        st.caption("Platform lo API — bạn chỉ nạp Xu và tạo. Không cần thẻ Visa, không cần biết kỹ thuật.")
        _plan_cols = st.columns(3)
        _default_plan = "Content Creator"
        _selected_plan = st.session_state.get("_sel_plan", _default_plan)
        if _selected_plan not in PLANS_VND and _selected_plan not in TOPUP_VND:
            _selected_plan = _default_plan

        _all_plans = {**PLANS_VND, **TOPUP_VND}
        for _ci, (_pname, _pinfo) in enumerate(PLANS_VND.items()):
            with _plan_cols[_ci]:
                _active = _selected_plan == _pname
                _border = f"2px solid {_pinfo['color']}" if _active else "1px solid rgba(255,255,255,0.1)"
                _bg     = f"{_pinfo['color']}22" if _active else "rgba(255,255,255,0.03)"
                _credits_txt = f"{_pinfo['credits']:,} Xu · {_pinfo['duration']}"
                st.markdown(f"""
                <div style="background:{_bg};border:{_border};border-radius:14px;padding:1rem 0.8rem;
                            text-align:center;min-height:160px;">
                    <div style="font-weight:700;font-size:1rem;color:{_pinfo['color']};">{_pname}</div>
                    <div style="font-size:1.3rem;font-weight:800;margin:0.3rem 0;">
                        {fmt_vnd(_pinfo['price_vnd'])}₫
                    </div>
                    <div style="font-size:0.78rem;color:{_pinfo['color']};font-weight:600;margin-bottom:0.25rem;">
                        🪙 {_credits_txt}
                    </div>
                    <div style="font-size:0.72rem;color:rgba(255,255,255,0.82);line-height:1.4;">
                        {_pinfo['desc']}
                    </div>
                    <div style="margin-top:0.5rem;background:{_pinfo['color']};color:#fff;
                                border-radius:9999px;font-size:0.68rem;padding:2px 8px;
                                display:inline-block;">{_pinfo['badge']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Chọn", key=f"sel_{_pname}", use_container_width=True,
                             type="primary" if _active else "secondary"):
                    st.session_state["_sel_plan"] = _pname
                    st.session_state.pop("sepay_payment", None)
                    st.rerun()

        # Top-up
        _has_active_sub = _user.get("has_active_sub", False)
        _topup_info   = TOPUP_VND["Nạp Thêm"]
        _topup_active = _selected_plan == "Nạp Thêm"
        _topup_bg     = f"{_topup_info['color']}22" if _topup_active else "rgba(255,255,255,0.02)"
        _topup_border = f"2px solid {_topup_info['color']}" if _topup_active else "1px dashed rgba(139,92,246,0.4)"
        st.markdown(f"""
        <div style="background:{_topup_bg};border:{_topup_border};border-radius:12px;
             padding:0.8rem 1.2rem;margin-top:0.75rem;display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
          <div style="font-size:1.4rem;">🔋</div>
          <div style="flex:1;min-width:180px;">
            <b style="color:{_topup_info['color']};">Nạp Thêm Xu</b>
            <span style="color:rgba(255,255,255,0.7);font-size:0.82rem;margin-left:8px;">
              {fmt_vnd(_topup_info['price_vnd'])}₫ → +{_topup_info['credits']:,} Xu vào gói đang dùng
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)
        _t1, _t2 = st.columns([4, 1])
        if _t2.button("Chọn Nạp", key="sel_topup", use_container_width=True,
                      type="primary" if _topup_active else "secondary"):
            st.session_state["_sel_plan"] = "Nạp Thêm"
            st.session_state.pop("sepay_payment", None)
            st.rerun()
        if _topup_active and not _has_active_sub:
            st.warning("⚠️ Nạp thêm chỉ hoạt động khi bạn đang có gói active.")

        _selected_plan = st.session_state.get("_sel_plan", _default_plan)
        if _selected_plan not in _all_plans:
            _selected_plan = _default_plan
        _pinfo = _all_plans[_selected_plan]
        st.divider()

        # QR section
        if _PAY and _PAY.get("plan") == _selected_plan:
            _status = check_payment_status(_PAY["payment_code"])
            if _status == "pending":
                _col_qr, _col_info = st.columns([1, 1.6])
                with _col_qr:
                    if _PAY.get("qr_url"):
                        st.image(_PAY["qr_url"], caption="Quét QR bằng app ngân hàng", width=220)
                with _col_info:
                    st.markdown(f"### Chuyển khoản — **{_selected_plan}**")
                    st.markdown(f"**Số tiền:** `{fmt_vnd(_PAY['amount_vnd'])} VNĐ`")
                    st.markdown(f"**Ngân hàng:** `{_PAY.get('account_name','')} — {_PAY.get('account_no','')}`")
                    st.markdown("**Nội dung CK (bắt buộc):**")
                    st.code(_PAY["payment_code"], language="text")
                    st.caption("⚠️ Nội dung chuyển khoản phải chứa đúng mã trên.")
                    _exp = _PAY.get("expires_at", "")
                    if _exp:
                        try:
                            _exp_dt = datetime.fromisoformat(_exp.replace("Z", "+00:00"))
                            _mins = max(0, int((_exp_dt - datetime.now(timezone.utc)).total_seconds() // 60))
                            st.caption(f"⏱️ Mã hết hạn sau: **{_mins} phút**")
                        except Exception:
                            pass
                    _cb1, _cb2 = st.columns(2)
                    if _cb1.button("✅ Tôi đã chuyển khoản", type="primary", use_container_width=True, key="ckbundled"):
                        _s = check_payment_status(_PAY["payment_code"])
                        if _s == "completed":
                            st.rerun()
                        elif _s == "pending":
                            st.warning("Chưa nhận được. Chờ 10–30 giây rồi thử lại.")
                        else:
                            st.error(f"Trạng thái: {_s}. Vui lòng tạo mã mới.")
                            st.session_state.pop("sepay_payment", None)
                    if _cb2.button("🔄 Tạo mã mới", use_container_width=True, key="renewbundled"):
                        st.session_state.pop("sepay_payment", None)
                        st.rerun()
            elif _status == "expired":
                st.warning("Mã đã hết hạn. Vui lòng tạo mã mới.")
                st.session_state.pop("sepay_payment", None)
                if st.button("🔄 Tạo mã mới", type="primary", key="newbundled2"):
                    st.rerun()
            elif _status == "failed":
                st.error("Giao dịch thất bại. Vui lòng liên hệ hỗ trợ.")
                st.session_state.pop("sepay_payment", None)
        else:
            st.markdown(f"**Gói đã chọn:** {_selected_plan} — `{fmt_vnd(_pinfo['price_vnd'])} VNĐ`")
            if st.button(f"📱 Tạo QR & Mã Thanh Toán — {_selected_plan}", type="primary", use_container_width=True):
                with st.spinner("Đang tạo mã chuyển khoản…"):
                    try:
                        _req = create_payment_request(_user["uid"], _selected_plan)
                        _req["plan"] = _selected_plan
                        st.session_state.sepay_payment = _req
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Lỗi tạo thanh toán: {_e}")

    # ════ TAB 2: BYOK ════════════════════════════════════════════════════
    with _tab_byok:
        _binfo = BYOK_PLAN["Gói Tự Túc"]
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.1);border:2px solid #6366f1;
             border-radius:16px;padding:1.5rem;margin-bottom:1rem;">
          <div style="font-size:1.6rem;font-weight:800;color:#818cf8;">🔑 {fmt_vnd(_binfo['price_vnd'])}₫ <span style="font-size:0.9rem;color:rgba(255,255,255,0.6);">/ {_binfo['duration']}</span></div>
          <div style="margin:0.5rem 0 0.75rem;font-size:1.05rem;color:rgba(255,255,255,0.9);">
            Gói Tự Túc — <b>Không Giới Hạn</b> với API Key cá nhân
          </div>
          <ul style="margin:0;padding-left:1.2rem;color:rgba(255,255,255,0.82);font-size:0.87rem;line-height:1.8;">
            {''.join(f'<li>{f}</li>' for f in _binfo['features'])}
          </ul>
          <div style="margin-top:0.75rem;background:#6366f1;color:#fff;border-radius:9999px;
               font-size:0.75rem;padding:3px 12px;display:inline-block;">{_binfo['badge']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 **Dành cho:** Pro MMO, Agency, developer — đã có tài khoản Anthropic / Suno / fal.ai riêng.")
        st.caption("Sau khi mua gói, vào **Cài đặt → API Keys** để nhập key của bạn. Hệ thống sẽ dùng key đó, không trừ Xu.")

        st.divider()
        if _BYOK_PAY and _BYOK_PAY.get("payment_code"):
            _bstatus = check_payment_status(_BYOK_PAY["payment_code"])
            if _bstatus == "pending":
                _bq, _bi = st.columns([1, 1.6])
                with _bq:
                    if _BYOK_PAY.get("qr_url"):
                        st.image(_BYOK_PAY["qr_url"], caption="Quét QR bằng app ngân hàng", width=220)
                with _bi:
                    st.markdown("### Chuyển khoản — **Gói Tự Túc**")
                    st.markdown(f"**Số tiền:** `{fmt_vnd(_BYOK_PAY['amount_vnd'])} VNĐ`")
                    st.markdown(f"**Ngân hàng:** `{_BYOK_PAY.get('account_name','')} — {_BYOK_PAY.get('account_no','')}`")
                    st.markdown("**Nội dung CK (bắt buộc):**")
                    st.code(_BYOK_PAY["payment_code"], language="text")
                    _bexp = _BYOK_PAY.get("expires_at", "")
                    if _bexp:
                        try:
                            _bexp_dt = datetime.fromisoformat(_bexp.replace("Z", "+00:00"))
                            _bmins = max(0, int((_bexp_dt - datetime.now(timezone.utc)).total_seconds() // 60))
                            st.caption(f"⏱️ Mã hết hạn sau: **{_bmins} phút**")
                        except Exception:
                            pass
                    _bb1, _bb2 = st.columns(2)
                    if _bb1.button("✅ Tôi đã chuyển khoản", type="primary", use_container_width=True, key="ckbyok"):
                        _s = check_payment_status(_BYOK_PAY["payment_code"])
                        if _s == "completed":
                            st.rerun()
                        elif _s == "pending":
                            st.warning("Chưa nhận được. Chờ 10–30 giây rồi thử lại.")
                        else:
                            st.error(f"Trạng thái: {_s}.")
                            st.session_state.pop("sepay_byok_payment", None)
                    if _bb2.button("🔄 Tạo mã mới", use_container_width=True, key="renewbyok"):
                        st.session_state.pop("sepay_byok_payment", None)
                        st.rerun()
            elif _bstatus == "expired":
                st.warning("Mã đã hết hạn. Vui lòng tạo mã mới.")
                st.session_state.pop("sepay_byok_payment", None)
                if st.button("🔄 Tạo mã mới", type="primary", key="newbyok2"):
                    st.rerun()
            elif _bstatus == "failed":
                st.error("Giao dịch thất bại. Vui lòng liên hệ hỗ trợ.")
                st.session_state.pop("sepay_byok_payment", None)
        else:
            if st.button(f"📱 Tạo QR — Gói Tự Túc ({fmt_vnd(_binfo['price_vnd'])}₫/tháng)",
                         type="primary", use_container_width=True, key="qrbyok"):
                with st.spinner("Đang tạo mã chuyển khoản…"):
                    try:
                        _breq = create_payment_request(_user["uid"], "Gói Tự Túc")
                        _breq["plan"] = "Gói Tự Túc"
                        st.session_state.sepay_byok_payment = _breq
                        st.rerun()
                    except Exception as _be:
                        st.error(f"Lỗi tạo thanh toán: {_be}")

    st.divider()
    st.page_link("views/home.py", label="🏠 Về trang chủ")
    st.stop()

_is_byok      = _user.get("is_byok", False)
_credits_left = _user.get("credits", 0)
if _is_byok:
    st.markdown(
        f'✅ Xin chào **{_user["name"]}** — Gói **{_user["plan"]}** · '
        f'<span style="color:#818cf8;font-weight:700;">🔑 Không giới hạn (BYOK)</span>',
        unsafe_allow_html=True,
    )
else:
    _coin_color = "#10b981" if _credits_left > 50 else ("#f59e0b" if _credits_left > 10 else "#ef4444")
    st.markdown(
        f'✅ Xin chào **{_user["name"]}** — Gói **{_user["plan"]}** · '
        f'<span style="color:{_coin_color};font-weight:700;">🪙 {_credits_left} Xu còn lại</span>'
        f'<span style="color:rgba(255,255,255,0.5);font-size:0.78rem;margin-left:8px;">'
        f'(Script=1Xu · Ảnh=1Xu · Nhạc=5Xu)</span>',
        unsafe_allow_html=True,
    )
    if _credits_left <= 10:
        st.warning(f"⚠️ Chỉ còn **{_credits_left} Xu** — vào **Tài khoản → Hỗ trợ** để nạp thêm.")

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
for _k, _v in {
    "suggested_topics": [],
    "topic_input": "",
    "pending_topic": None,
    "music_result": None,
    "music_meta": {},
    "images": {},
    "suno_tracks": {},
    "suno_audio": {},
    "suno_failed": {},        # track_key -> error message
    "suno_ext_keys": {},      # track_key -> [(ext_key, label), …]
    "video_scripts": {},      # track_key -> script text
    "keyword_result": None,   # trending keyword lookup result
    "kw_topic_results": [],   # topic suggestions from selected keywords
    "current_history_id": None,  # Firestore doc id for Suno URL updates
    "suno_credits": None,        # cached credit balance from sunoapi.org
    "fal_videos": {},            # scene_key -> video URL
    "grok_videos": {},           # scene_key -> video URL (Grok xAI)
    "grok_prefs": {},            # saved video preferences {duration, aspect, resolution}
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Load API keys — ưu tiên Firestore (user đã login), fallback cookie
def _apply_api_keys(keys: dict):
    if keys.get("anthropic"):
        st.session_state.anthropic_api_key = keys["anthropic"]
    if keys.get("suno"):
        st.session_state.suno_api_key = keys["suno"]
    if keys.get("fal"):
        st.session_state.fal_api_key = keys["fal"]
    if keys.get("xai"):
        st.session_state.xai_api_key = keys["xai"]

if "api_keys_loaded" not in st.session_state:
    _user = st.session_state.get("user")
    if _user:
        _saved = load_user_api_keys(_user["uid"])
        if not any(_saved.values()):          # Firestore trống → thử cookie
            _saved = load_api_keys()
    else:
        _saved = load_api_keys()
    _apply_api_keys(_saved)
    _vp = load_video_prefs()
    if _vp:
        st.session_state.grok_prefs = _vp
    st.session_state.api_keys_loaded = True

# Nếu user vừa login (session restore / OAuth) mà keys chưa load từ Firestore
_cur_user = st.session_state.get("user")
if _cur_user and not st.session_state.get("user_api_keys_loaded"):
    _apply_api_keys(load_user_api_keys(_cur_user["uid"]))
    _saved_prefs = load_video_prefs()
    if _saved_prefs:
        st.session_state.grok_prefs = _saved_prefs
    st.session_state.user_api_keys_loaded = True

# ---------------------------------------------------------------------------
# Batch size logic
# ---------------------------------------------------------------------------
BATCH_SIZE = 5
BATCH_THRESHOLD = 10

# ---------------------------------------------------------------------------
# Genre configuration
# ---------------------------------------------------------------------------
GENRE_CONFIG = {
    "Thiếu Nhi (Nursery)": {
        "bpm": "100-110 BPM",
        "style_tags": "Acoustic, Sweet, Playful, Educational",
        "visual_vibe": "Pastel colors, cute characters, bright daylight",
        "hashtags": "#nhacthieunhi #mamnon #phimhoathinh",
    },
    "Nhạc Sàn (EDM)": {
        "bpm": "128 BPM",
        "style_tags": "Big Room, Deep Bass, Synthesizer, Energetic",
        "visual_vibe": "Neon lights, stage smoke, cinematic concert lighting",
        "hashtags": "#edm #nhacsan #dance2026",
    },
    "Vinahouse Remix": {
        "bpm": "140-145 BPM",
        "style_tags": "Vietnamese Hard House, Thumping Bass, High Energy, Nẩy",
        "visual_vibe": "Vibrant contrast, laser beams, fast-paced transitions",
        "hashtags": "#vinahouse #remix2026 #nhacsanmanh",
    },
    "Nonstop Mix": {
        "bpm": "138 BPM",
        "style_tags": "Continuous flow, seamless transitions, club mix",
        "visual_vibe": "Abstract visuals, motion blur, kaleidoscope effects",
        "hashtags": "#nonstop #vietmix #lienkhucnhactre",
    },
    "Bass-Boosted club bangers": {
        "bpm": "128-130 BPM",
        "style_tags": "Heavy Bass, Sub-woofer focus, Club Bangers, Aggressive Synth, High Compression",
        "visual_vibe": "Extreme high-contrast dark club interior, massive subwoofer stacks glowing red, intense red and electric blue laser beams cutting through thick smoke, visible bass vibration waves in air, ultra-dramatic lighting",
        "hashtags": "#bassboosted #clubbangers #subwoofer #cực_mạnh #dance2026",
    },
    "G-House (Gangsta House)": {
        "bpm": "124-126 BPM",
        "style_tags": "G-House, Deep Bass, Hip-hop vocals, Gangsta aesthetic, Groovy, Dark Synth",
        "visual_vibe": "Urban Legends streetwear culture, dark cinematic tone, wet asphalt reflecting golden streetlights, neon yellow and white light accents, graffiti walls, low-angle shot of sneakers and luxury cars, moody atmospheric fog",
        "hashtags": "#ghouse #gangstahouse #deephouse #clubmusic #streetstyle #remix2026",
    },
    "Psytrance": {
        "bpm": "140-150 BPM",
        "style_tags": "Rolling Bassline, Psychedelic, Trippy, High Energy, Goa Trance, Acid Synth",
        "visual_vibe": "Sacred geometry sacred mandala, multidimensional polyhedra floating in cosmos, trippy reflective neon art with iridescent fluorescent colors, UV-reactive fractal patterns, deep space backdrop with glowing forest silhouette",
        "hashtags": "#psytrance #psychedelic #trancefamily #145bpm #trippyvisuals #goatrance",
    },
    "Brazilian Phonk": {
        "bpm": "130-140 BPM",
        "style_tags": "Distorted Bass, Brazilian Funk Beat, Cowbell Melody, Aggressive, Memphis Vocals, Dark Drift",
        "visual_vibe": "JDM car night city drift scene, mysterious anime character with dark hooded silhouette, Siren Head-style cryptid entity looming in background, deep purple and navy blue dominance with black shadows, neon purple headlights reflecting on wet asphalt, VHS scan-line grain overlay, ultra-cinematic low-angle",
        "hashtags": "#phonk #brazilianphonk #drift #cowbell #bassboosted #phonkmusic #phonkwalk",
    },
    "Techno (Peak Time / Driving)": {
        "bpm": "128-135 BPM",
        "style_tags": "Industrial Kick, Peak Time Techno, Driving Rhythm, Acid Synth, Dark Atmosphere, Hypnotic",
        "visual_vibe": "Cyberpunk brutalist architecture with raw concrete and exposed steel, cyclic mechanical gear movement in slow-motion, thin cold-white laser beams cutting through darkness, electric blue accent lighting on sharp geometric edges, underground rave tunnel perspective, monochromatic grey-black palette with single cyan highlight",
        "hashtags": "#techno #peaktime #drivingtechno #darktechno #industrial #underground",
    },
    "Hardstyle": {
        "bpm": "150-155 BPM",
        "style_tags": "Hardkick, Distorted Kick, Euphoric Melody, Screech, Reverse Bass, High Energy",
        "visual_vibe": "Defqon.1 festival mainstage style, massive outdoor stage with towering fire pillars and pyrotechnic explosions, armored futuristic warrior characters in battle stance, crowd of thousands with raised fists, epic orange and gold flame lighting against dark night sky, cinematic wide-angle aerial shot",
        "hashtags": "#hardstyle #euphorichardstyle #hardcore #gymmotivation #workoutmusic #defqon1",
    },
    # ── Chill / Mood ──────────────────────────────────────────────────────────
    "Lofi Hip-Hop": {
        "bpm": "70-90 BPM",
        "style_tags": "Lo-fi, Jazzy Chords, Vinyl Crackle, Mellow, Study Beats, Soft Drums",
        "visual_vibe": "Cozy anime bedroom at night, warm lamp glow on desk with books and coffee cup, rain on window, city skyline glowing softly outside, grain film texture overlay, muted warm brown and amber palette",
        "hashtags": "#lofi #studybeats #chilledcow #lofihiphop #studywithme #nhaclofi",
    },
    "Synthwave / Retrowave": {
        "bpm": "100-118 BPM",
        "style_tags": "Analog Synth, Retro 80s, Arpeggiated Lead, Gated Reverb Drums, Nostalgic, Dreamy",
        "visual_vibe": "80s retro synthwave aesthetic, neon pink and electric blue grid horizon stretching to infinity, chrome DeLorean silhouette, giant glowing sun setting behind mountain range, palm tree silhouettes, VHS distortion scanlines, ultra-cinematic widescreen",
        "hashtags": "#synthwave #retrowave #outrun #80svibes #neonlights #vaporwave",
    },
    "Chillout / Ambient": {
        "bpm": "60-80 BPM",
        "style_tags": "Atmospheric Pads, Slow Tempo, Ethereal, Calm, Meditative, Nature Sounds",
        "visual_vibe": "Aerial view of misty mountain valley at golden hour, wispy clouds drifting through ancient cedar forest, soft diffused light rays, ultra-serene minimal composition, muted green and gold palette, cinematic 2.39:1 aspect",
        "hashtags": "#chillout #ambient #relaxingmusic #nhacthugian #meditation #deeprelax",
    },
    "Future Bass": {
        "bpm": "140-160 BPM",
        "style_tags": "Emotional Drop, Supersaws, Chord Stabs, Pitched Vocals, Dreamy Build, Melodic Bass",
        "visual_vibe": "Dreamy pastel watercolor cosmos, floating island ecosystem with glowing crystal formations, luminous aurora ribbons in sky, anime-style protagonist gazing upward, soft pink purple blue gradient, magical realism illustration style",
        "hashtags": "#futurebass #emotionaldrop #flume #melodicbass #rave2026 #edmdrop",
    },
    # ── Drum & Bass / Breaks ──────────────────────────────────────────────────
    "Liquid Drum & Bass": {
        "bpm": "174 BPM",
        "style_tags": "Liquid DnB, Soulful Vocals, Rolling Breaks, Deep Sub Bass, Smooth, Jazz Influenced",
        "visual_vibe": "Smooth liquid metal surfaces forming organic flowing waves, deep ocean abyss with bioluminescent creatures, calming dark teal and chrome palette, seamless infinite loop visual, ultra-high-resolution fluid simulation render",
        "hashtags": "#liquiddnb #drumandbass #dnb #liquidfunk #deepdnb #bassmusic",
    },
    "Neurofunk / Dark DnB": {
        "bpm": "174-176 BPM",
        "style_tags": "Neurofunk, Reese Bass, Complex Breaks, Dark Industrial, Sci-fi, Mechanical Growl",
        "visual_vibe": "Dystopian cyberpunk megacity from insect eye-view, massive chrome machinery gears and pipes, acid rain corroding dark steel, flickering holographic warning signs, toxic green and rust orange on black, hyper-detailed mechanical horror aesthetic",
        "hashtags": "#neurofunk #darkdnb #drumandbass #dnb #scifi #bassweight",
    },
    # ── House Family ─────────────────────────────────────────────────────────
    "Melodic House & Techno": {
        "bpm": "120-125 BPM",
        "style_tags": "Melodic Techno, Emotional, Arpeggio Synth, Deep Groove, Organic Percussion, Tale of Us style",
        "visual_vibe": "Solitary figure standing at edge of vast salt flat at dusk, mirror reflection of moody purple-orange sky, minimalist vast empty landscape, single spotlight from above, cinematic melancholic tone, Terrence Malick visual poetry style",
        "hashtags": "#melodichouse #melodictechno #afterlife #taleofus #deephouse #underground",
    },
    "Afro House / Amapiano": {
        "bpm": "112-116 BPM",
        "style_tags": "Log Drum Bass, Afro Percussion, Piano Stabs, South African, Soulful Vocals, Groove",
        "visual_vibe": "Vibrant South African township sunset celebration, warm terracotta and gold earth tones, silhouette dancers against burning orange sky, traditional patterns blended with modern fashion, dust particles catching golden light, joyful communal energy",
        "hashtags": "#amapiano #afrohouse #piano #southafrica #logdrum #afrobeats",
    },
    "Progressive House": {
        "bpm": "126-128 BPM",
        "style_tags": "Long Build-up, Emotional Melody, Orchestral Stabs, Smooth Bassline, Epic Drop, Euphoric",
        "visual_vibe": "Sunrise over infinite ocean horizon from first-person perspective on luxury yacht deck, golden lens flare expanding across widescreen frame, wispy cirrus clouds turning gold-pink, calm deep blue water, epic scale solitary beauty",
        "hashtags": "#progressivehouse #proghouse #epicdrop #festival #mainstage #rave2026",
    },
    # ── Nhạc Việt ─────────────────────────────────────────────────────────────
    "Deep Chill (Việt Mix)": {
        "bpm": "105-115 BPM",
        "style_tags": "Deep Chill, Viet Mix Chill, Lofi House, Deep Bass, Emotional Male/Female Vocal, Atmospheric Pads, Soft Kick, Melancholy",
        "visual_vibe": "Lonely silhouette at a rainy window, neon lights reflecting on wet asphalt, late night cafe, moody sunset, cinematic lofi aesthetic — navy, deep purple, amber tones",
        "hashtags": "#deepchill #vietmix #nhacchill #lofihoanghon #nhacbuon #chillout #saychill #vietmixchill #nhacthattinh #deephouse",
    },
    "Nhạc Vàng / Bolero": {
        "bpm": "60-80 BPM",
        "style_tags": "Bolero, Guitar Điện, Kèn Saxophone, Câu từ sâu lắng, Nostalgic, Vietnamese Traditional",
        "visual_vibe": "Nostalgic 1970s Vietnamese street scene, warm sepia-tinted lantern light on old Saigon alleyway, áo dài woman silhouette by cyclo, antique photograph grain texture, warm amber and faded gold palette, bittersweet romantic atmosphere",
        "hashtags": "#nhacvang #bolero #nhactru #nhacviet #nhacbuon #amnhac",
    },
    "V-Pop / Nhạc Trẻ": {
        "bpm": "95-115 BPM",
        "style_tags": "Vietnamese Pop, Catchy Hook, Modern Production, Bright Melody, Youth Energy, Radio-ready",
        "visual_vibe": "Trendy young Vietnamese couple in modern Hanoi café district, soft pastel neon signage, lush tropical plants mixed with minimalist concrete architecture, golden hour light through glass facade, fresh vibrant color palette, Korean-influenced aesthetic",
        "hashtags": "#vpop #nhactre #nhacviet #pop2026 #vpopmusic #viet",
    },
    # ── Toàn cầu / Trending ──────────────────────────────────────────────────
    "K-Pop Style": {
        "bpm": "105-130 BPM",
        "style_tags": "K-Pop, Ultra-polished Production, Punchy Synth, Hook-driven, Dynamic Arrangement, Group Performance",
        "visual_vibe": "Ultra-modern K-Pop MV aesthetic, holographic stage with massive LED wall displaying geometric patterns, synchronized dancer formation on glass-floor stage, sharp fashion editorial lighting, bold primary colors on white backdrop, precision choreography energy",
        "hashtags": "#kpop #kpopcover #kmusic #idol #dance #pop2026",
    },
    "Trap / Dark Trap": {
        "bpm": "130-160 BPM",
        "style_tags": "808 Bass, Hi-hat Rolls, Trap Snare, Dark Atmosphere, Melodic Trap, Ominous Pad",
        "visual_vibe": "Midnight urban rooftop overlooking city skyline, lone hooded figure with back to camera, purple and black moody skyline, distant city lights blurred bokeh, dramatic god-rays through stormclouds, cinematic street noir aesthetic",
        "hashtags": "#trap #darktrap #808 #trapsoul #hiphop #trapmusic",
    },
    "Jersey Club / Ballroom": {
        "bpm": "130-160 BPM",
        "style_tags": "Jersey Club, Chopped Vocals, Rapid Hi-hat Pattern, Hard Kicks, Aggressive Sample, Dance Energy",
        "visual_vibe": "Underground ballroom voguing competition floor, dramatic runway lighting in hot pink and white, elaborate fashion-forward outfits, motion-blur dance energy, close-up of athletic footwork on reflective floor, raw high-energy documentary style",
        "hashtags": "#jerseyclub #ballroom #club #dancechallenge #voguing #clubmusic",
    },
    "Melodic Dubstep": {
        "bpm": "140 BPM",
        "style_tags": "Emotional Intro, Wubstep, Heavy Drop, Cinematic Build, Orchestra + Bass, Dubstep Wobble",
        "visual_vibe": "Anime battle scene at peak emotional moment, lone warrior standing in eye of massive energy storm, shockwave rings expanding outward, dramatic color contrast between ethereal light blue calm center and raging dark violet storm walls, ultra-cinematic widescreen",
        "hashtags": "#melodicdubstep #dubstep #bassdrop #emotional #edm #wub",
    },
    "Smooth Jazz (Lounge)": {
        "bpm": "70-85 BPM",
        "style_tags": "Smooth Jazz, Saxophone Lead, Piano Chords, Lounge Atmosphere, Slow Groovy, Soft Drums",
        "visual_vibe": "Classy vintage bar, rainy night through a window, warm dim lighting, 3D isometric cozy room",
        "hashtags": "#jazzmusic #smoothjazz #loungemusic #jazzcafe #rainynight #relaxingjazz",
    },
    "Ambient Relax (Meditation)": {
        "bpm": "60 BPM or Floating",
        "style_tags": "Ambient, Healing, Tibetan Bowls, Soft Pads, Deep Sleep, Nature Sounds, No Drums",
        "visual_vibe": "Cosmic nebula, misty morning forest, zen garden, peaceful floating particles, cinematic slow motion",
        "hashtags": "#relaxingmusic #meditationmusic #deepsleep #ambient #healingsounds #studybgm",
    },
    "Hòa tấu Trung Hoa": {
        "bpm": "65-80 BPM",
        "style_tags": "Chinese Traditional Instrumental, Guzheng Lead, Dizi Flute, Pipa, Erhu, Pentatonic Scale, Ancient Wuxia Melody, Cinematic Chill",
        "visual_vibe": "Ancient Chinese landscape painting, misty mountains and rivers, traditional tea house, bamboo forest, falling peach blossoms, ethereal lo-fi lighting",
        "hashtags": "#chinesemusic #traditionalinstruments #guzheng #dizi #guzhengchill #guzhengmeditation #nhaccotrong",
    },
}
GENRE_NAMES = list(GENRE_CONFIG.keys())

def compute_batches(num_tracks: int) -> list:
    if num_tracks < BATCH_THRESHOLD:
        return [(1, num_tracks)]
    batches, start = [], 1
    while start <= num_tracks:
        end = min(start + BATCH_SIZE - 1, num_tracks)
        batches.append((start, end))
        start = end + 1
    return batches

# ---------------------------------------------------------------------------
# fal.ai Nano Banana Pro — image generation
# ---------------------------------------------------------------------------
def generate_image(prompt: str, fal_key: str,
                   aspect_ratio: str = "16:9", resolution: str = "1K",
                   num_images: int = 1, output_format: str = "png") -> list:
    """Generate images via fal-ai/nano-banana-pro. Returns list[bytes]."""
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload  = {
        "prompt":        prompt,
        "aspect_ratio":  aspect_ratio,
        "resolution":    resolution,
        "output_format": output_format,
        "num_images":    num_images,
    }
    resp = requests.post(
        "https://fal.run/fal-ai/nano-banana-pro",
        json=payload, headers=headers, timeout=120,
    )
    resp.raise_for_status()
    results = []
    for img_obj in resp.json()["images"]:
        img_resp = requests.get(img_obj["url"], timeout=30)
        img_resp.raise_for_status()
        results.append(img_resp.content)
    return results

_IMG_ASPECT_OPTS  = ["16:9", "1:1", "9:16", "4:3", "3:4", "21:9"]
_IMG_RES_OPTS     = ["1K", "2K", "4K"]
_IMG_FORMAT_OPTS  = ["png", "jpeg", "webp"]
_IMG_MIME         = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}
_IMG_EXT          = {"png": "png",       "jpeg": "jpg",        "webp": "webp"}

def image_widget(prompt: str, img_key: str):
    st.code(prompt, language="text")
    fal_key = st.session_state.get("fal_api_key", "").strip()

    # ── Thông số render ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    aspect_ratio = c1.selectbox(
        "Aspect Ratio", _IMG_ASPECT_OPTS, index=0, key=f"img_ar_{img_key}"
    )
    resolution   = c2.selectbox(
        "Resolution",   _IMG_RES_OPTS,    index=0, key=f"img_res_{img_key}"
    )
    num_images   = c3.number_input(
        "Số ảnh", min_value=1, max_value=4, value=1, step=1, key=f"img_n_{img_key}"
    )
    out_fmt      = c4.selectbox(
        "Format", _IMG_FORMAT_OPTS, index=0, key=f"img_fmt_{img_key}"
    )

    # ── Nút tạo ảnh ──────────────────────────────────────────────────────────
    has_img     = img_key in st.session_state.images
    _img_user   = st.session_state.get("user", {})
    _img_byok   = _img_user.get("is_byok", False)
    _img_coins  = _img_user.get("credits", 0)
    _cd_img_key = f"_cd_img_{img_key}"
    _cd_img_rem = int(10 - (time.time() - st.session_state.get(_cd_img_key, 0)))
    _img_cost   = COIN_COSTS["image"]

    if _cd_img_rem > 0:
        st.button(f"⏳ Cooldown {_cd_img_rem}s…", disabled=True, key=f"btn_{img_key}", use_container_width=True)
    elif not _img_byok and _img_coins < _img_cost:
        st.button(f"🪙 Không đủ Xu (cần {_img_cost})", disabled=True, key=f"btn_{img_key}", use_container_width=True)
    else:
        btn_lbl = f"🔄 Tạo lại ảnh ({_img_cost} Xu)" if has_img else f"🎨 Tạo ảnh ({_img_cost} Xu)"
        if st.button(btn_lbl, key=f"btn_{img_key}", use_container_width=True):
            if not fal_key:
                st.warning("Nhập fal.ai API Key ở sidebar để tạo ảnh.")
            else:
                st.session_state[_cd_img_key] = time.time()
                effective_prompt = prompt
                if aspect_ratio == "1:1":
                    effective_prompt = (
                        prompt.rstrip(". ") +
                        ", no text, no typography, no letters, no words, no title, "
                        "no caption, no banner, no watermark, no labels, no overlay text, "
                        "pure visual image only"
                    )
                with st.spinner(f"Nano Banana Pro đang tạo {num_images} ảnh {aspect_ratio} {resolution}..."):
                    try:
                        st.session_state.images[img_key] = generate_image(
                            effective_prompt, fal_key,
                            aspect_ratio=aspect_ratio,
                            resolution=resolution,
                            num_images=int(num_images),
                            output_format=out_fmt,
                        )
                        send_notification_direct("🎨 Ảnh đã xong!", "Thumbnail của bạn đã tạo xong.")
                        # Trừ 1 Xu sau khi tạo ảnh thành công (chỉ với bundled)
                        _cu = st.session_state.get("user", {})
                        if _cu.get("uid") and not _cu.get("is_byok"):
                            _rem = _deduct_coins(_cu["uid"], _img_cost,
                                                 action="image", description="Tạo ảnh thumbnail")
                            st.session_state.user = {**_cu, "credits": _rem}
                    except Exception as e:
                        st.error(f"Lỗi tạo ảnh: {e}")

    # ── Hiển thị kết quả ─────────────────────────────────────────────────────
    if img_key in st.session_state.images:
        imgs = st.session_state.images[img_key]
        mime = _IMG_MIME.get(out_fmt, "image/png")
        ext  = _IMG_EXT.get(out_fmt, "png")
        if len(imgs) == 1:
            st.image(imgs[0], use_container_width=True)
            st.download_button(
                f"⬇️ Tải ảnh .{ext}", data=imgs[0],
                file_name=f"{img_key}.{ext}", mime=mime,
                key=f"dl_{img_key}_0",
            )
        else:
            # Lưới 2 cột cho 2-4 ảnh
            for row_start in range(0, len(imgs), 2):
                row_imgs = imgs[row_start:row_start + 2]
                cols = st.columns(len(row_imgs))
                for i, (col, img_bytes) in enumerate(zip(cols, row_imgs)):
                    idx = row_start + i
                    with col:
                        st.image(img_bytes, use_container_width=True)
                        st.download_button(
                            f"⬇️ Ảnh {idx + 1} .{ext}", data=img_bytes,
                            file_name=f"{img_key}_{idx + 1}.{ext}", mime=mime,
                            key=f"dl_{img_key}_{idx}",
                        )

# ---------------------------------------------------------------------------
# fal.ai Video generation
# ---------------------------------------------------------------------------
FAL_QUEUE_BASE = "https://queue.fal.run"
FAL_MODELS = {
    "Text-to-Video": "bytedance/seedance-2.0/text-to-video",
    "Image-to-Video": "bytedance/seedance-2.0/image-to-video",
    "Reference-to-Video": "bytedance/seedance-2.0/reference-to-video",
}
FAL_DURATIONS = ["auto"] + [str(i) for i in range(4, 16)]
FAL_ASPECTS   = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "auto"]
FAL_RESOLUTIONS = ["720p", "1080p", "480p"]

def call_fal_video(api_key: str, model_id: str, payload: dict, status_slot) -> str:
    """Submit to fal.ai queue, poll until COMPLETED, return video URL."""
    headers = {"Authorization": f"Key {api_key}", "Content-Type": "application/json"}
    resp = requests.post(f"{FAL_QUEUE_BASE}/{model_id}", json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    request_id = resp.json()["request_id"]
    status_url  = f"{FAL_QUEUE_BASE}/{model_id}/requests/{request_id}/status"
    result_url  = f"{FAL_QUEUE_BASE}/{model_id}/requests/{request_id}"
    for attempt in range(72):   # max ~6 min
        time.sleep(5)
        s = requests.get(status_url, headers=headers, timeout=15).json()
        st_code = s.get("status", "")
        q_pos   = s.get("queue_position")
        if q_pos:
            status_slot.info(f"⏳ Đang chờ xử lý… Vị trí hàng đợi: {q_pos}")
        elif st_code == "IN_PROGRESS":
            status_slot.info(f"🎬 Đang render video… ({attempt * 5}s)")
        if st_code == "COMPLETED":
            result = requests.get(result_url, headers=headers, timeout=15).json()
            return result["video"]["url"]
        if st_code in ("FAILED", "ERROR"):
            err = s.get("error") or {}
            raise ValueError(err.get("msg") or err.get("message") or "Video generation failed")
    raise TimeoutError("Video generation timed out (6 min)")


# ---------------------------------------------------------------------------
# Grok xAI Video generation (via Cloudflare AI Gateway or direct)
# ---------------------------------------------------------------------------
def _grok_base_url() -> str:
    """Trả về base URL xAI — qua CF Gateway nếu có cấu hình, không thì direct."""
    cf_account = st.secrets.get("CF_ACCOUNT_ID", "")
    cf_gateway = st.secrets.get("CF_GATEWAY_ID", "")
    if cf_account and cf_gateway:
        return f"https://gateway.ai.cloudflare.com/v1/{cf_account}/{cf_gateway}/grok"
    return "https://api.x.ai/v1"

GROK_DURATIONS  = [str(i) for i in range(3, 11)]   # 3–10 giây
GROK_ASPECTS    = ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3"]
GROK_RESOLUTIONS = ["720p", "480p"]

def call_grok_video(xai_key: str, prompt: str,
                    duration: int = 5,
                    aspect_ratio: str = "16:9",
                    resolution: str = "720p",
                    status_slot=None) -> str:
    """Submit Grok video job, poll until done, return video URL."""
    base = _grok_base_url()
    headers = {"Authorization": f"Bearer {xai_key}", "Content-Type": "application/json"}
    payload = {
        "model":        "grok-imagine-video-1.5-preview",
        "prompt":       prompt,
        "duration":     duration,
        "aspect_ratio": aspect_ratio,
        "resolution":   resolution,
    }
    resp = requests.post(f"{base}/videos/generations", json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    request_id = resp.json()["request_id"]

    poll_url = f"{base}/videos/{request_id}"
    for attempt in range(90):   # max ~15 min
        time.sleep(10)
        s = requests.get(poll_url, headers=headers, timeout=20).json()
        status = s.get("status", "")
        if status_slot:
            status_slot.info(f"🎬 Grok đang render… ({attempt * 10}s) [{status}]")
        if status == "done":
            return s["video"]["url"]
        if status in ("failed", "error"):
            raise ValueError(s.get("error", {}).get("message") or "Grok video generation failed")
    raise TimeoutError("Grok video generation timed out (15 min)")


def grok_video_widget(prompt: str, scene_key: str):
    """Per-scene Grok xAI video generation UI."""
    from llm_router import _secret
    xai_key = st.session_state.get("xai_api_key", "").strip() or _secret("XAI_API_KEY")
    if not xai_key:
        st.caption("🔑 Nhập xAI API Key trong tab **🔑 API Keys** để tạo video Grok.")
        return

    gkey = f"grok_{scene_key}"
    _cd_key = f"_cd_grok_{scene_key}"
    _cd_rem = int(15 - (time.time() - st.session_state.get(_cd_key, 0)))

    _prefs = st.session_state.get("grok_prefs", {})
    _def_dur = str(_prefs.get("duration", "5"))
    _def_asp = _prefs.get("aspect", "16:9")
    _def_res = _prefs.get("resolution", "720p")

    p1, p2, p3 = st.columns(3)
    duration   = int(p1.selectbox("Duration (s)", GROK_DURATIONS,
                     index=GROK_DURATIONS.index(_def_dur) if _def_dur in GROK_DURATIONS else 2,
                     key=f"grok_dur_{scene_key}"))
    aspect     = p2.selectbox("Aspect ratio", GROK_ASPECTS,
                     index=GROK_ASPECTS.index(_def_asp) if _def_asp in GROK_ASPECTS else 0,
                     key=f"grok_asp_{scene_key}")
    resolution = p3.selectbox("Resolution",   GROK_RESOLUTIONS,
                     index=GROK_RESOLUTIONS.index(_def_res) if _def_res in GROK_RESOLUTIONS else 0,
                     key=f"grok_res_{scene_key}")

    existing = st.session_state.grok_videos.get(scene_key)
    if existing:
        st.video(existing)
        st.download_button(
            "⬇️ Tải video Grok", existing,
            file_name=f"{scene_key}_grok.mp4", mime="video/mp4",
            key=f"grok_dl_{scene_key}",
        )

    _cost_usd = round(duration * 0.08, 2)
    btn_label = (f"🔄 Render lại (${_cost_usd})" if existing
                 else f"🎬 Tạo video Grok (${_cost_usd})")

    if _cd_rem > 0:
        st.button(f"⏳ Cooldown {_cd_rem}s…", disabled=True, key=f"grok_btn_{scene_key}")
    else:
        if st.button(btn_label, key=f"grok_btn_{scene_key}", use_container_width=True):
            st.session_state[_cd_key] = time.time()
            status_slot = st.empty()
            try:
                video_url = call_grok_video(
                    xai_key, prompt, duration, aspect, resolution, status_slot
                )
                st.session_state.grok_videos[scene_key] = video_url
                status_slot.empty()
                st.rerun()
            except Exception as _e:
                status_slot.empty()
                st.error(f"❌ Lỗi Grok video: {_e}")


def fal_video_widget(prompt: str, scene_key: str):
    """Per-scene fal.ai video generation UI."""
    fal_key = st.session_state.get("fal_api_key", "").strip()
    if not fal_key:
        st.caption("🔑 Nhập fal.ai API Key ở sidebar để tạo video.")
        return

    model_label = st.selectbox(
        "Model:", list(FAL_MODELS.keys()),
        key=f"fal_model_{scene_key}",
    )
    model_id = FAL_MODELS[model_label]

    image_url = ""
    if "Image" in model_label:
        image_url = st.text_input(
            "Image URL (JPG/PNG, max 30 MB):",
            key=f"fal_img_{scene_key}",
            placeholder="https://...",
        )

    p1, p2, p3, p4 = st.columns(4)
    duration   = p1.selectbox("Duration",    FAL_DURATIONS,    key=f"fal_dur_{scene_key}")
    aspect     = p2.selectbox("Aspect ratio", FAL_ASPECTS,     key=f"fal_asp_{scene_key}")
    resolution = p3.selectbox("Resolution",  FAL_RESOLUTIONS,  key=f"fal_res_{scene_key}")
    gen_audio  = p4.checkbox("Audio",  value=True,             key=f"fal_aud_{scene_key}")

    existing = st.session_state.fal_videos.get(scene_key)
    if existing:
        st.video(existing)
        st.download_button(
            "⬇️ Tải video", existing,
            file_name=f"{scene_key}.mp4", mime="video/mp4",
            key=f"fal_dl_{scene_key}",
        )

    btn_label = "🔄 Tạo lại Video" if existing else "🎬 Tạo Video"
    if st.button(btn_label, key=f"fal_gen_{scene_key}", use_container_width=True):
        payload = {
            "prompt":        prompt,
            "resolution":    resolution,
            "aspect_ratio":  aspect,
            "generate_audio": gen_audio,
        }
        if duration != "auto":
            payload["duration"] = int(duration)
        if image_url:
            payload["image_url"] = image_url
        status_slot = st.empty()
        try:
            with st.spinner("Đang gửi yêu cầu tới fal.ai…"):
                video_url = call_fal_video(fal_key, model_id, payload, status_slot)
            st.session_state.fal_videos[scene_key] = video_url
            status_slot.empty()
            queue_notification("🎬 Video đã xong!", "Video của bạn đã render xong.")
            st.rerun()
        except Exception as _fal_e:
            status_slot.empty()
            st.error(f"❌ Lỗi tạo video: {_fal_e}")


# Suno API integration
# ---------------------------------------------------------------------------
SUNO_BASE = "https://api.sunoapi.org/api/v1"
SUNO_FAIL_STATUS = {"CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "SENSITIVE_WORD_ERROR", "CALLBACK_EXCEPTION"}
MAX_SUNO_WORKERS = 15   # giới hạn thực tế qua test: 15 luồng song song

def suno_generate_task(api_key: str, title: str, style: str, lyrics: str, model: str) -> str:
    """Submit generation job, return taskId."""
    title_max = 80 if model in ("V4", "V4_5ALL") else 100
    safe_style = (style.strip() or "cheerful children's music, upbeat, catchy melody, fun")[:200]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "customMode": True,
        "instrumental": False,
        "model": model,
        "title": title[:title_max],
        "style": safe_style,
        "prompt": lyrics[:3000],   # Suno hard limit ~3000 chars
        "callBackUrl": "https://httpbin.org/post",
    }

    resp = requests.post(f"{SUNO_BASE}/generate", json=payload, headers=headers, timeout=30)

    if not resp.ok:
        try:
            err_body = resp.json()
            detail = f"code={err_body.get('code')} msg={err_body.get('msg')}"
        except Exception:
            detail = resp.text[:400]
        raise ValueError(f"Suno HTTP {resp.status_code}: {detail}")

    body = resp.json()
    if body.get("code") != 200:
        raise ValueError(f"Suno API lỗi {body.get('code')}: {body.get('msg', 'unknown')}")
    return body["data"]["taskId"]

def suno_extend_task(api_key: str, clip_id: str, continue_at: int,
                     title: str, style: str, lyrics: str, model: str) -> str:
    """
    Continuation (continue_at > 0) hoặc Remix (continue_at = 0).
    Dùng continueClipId để Suno giữ nguyên DNA âm thanh của bài gốc.
    """
    title_max  = 80 if model in ("V4", "V4_5ALL") else 100
    safe_style = (style.strip() or "")[:200]
    headers    = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload    = {
        "customMode":     True,
        "instrumental":   False,
        "model":          model,
        "continueClipId": clip_id,
        "continueAt":     continue_at,
        "title":          title[:title_max],
        "style":          safe_style,
        "prompt":         lyrics[:3000],
        "callBackUrl":    "https://httpbin.org/post",
    }
    resp = requests.post(f"{SUNO_BASE}/generate", json=payload, headers=headers, timeout=30)
    if not resp.ok:
        try:
            err_body = resp.json()
            detail = f"code={err_body.get('code')} msg={err_body.get('msg')}"
        except Exception:
            detail = resp.text[:400]
        raise ValueError(f"Suno HTTP {resp.status_code}: {detail}")
    body = resp.json()
    if body.get("code") != 200:
        raise ValueError(f"Suno API lỗi {body.get('code')}: {body.get('msg', 'unknown')}")
    return body["data"]["taskId"]


def suno_poll_task(api_key: str, task_id: str) -> dict:
    """Fetch task status once."""
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(
        f"{SUNO_BASE}/generate/record-info",
        params={"taskId": task_id},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]

def fmt_duration(secs) -> str:
    secs = int(secs or 0)
    return f"{secs // 60}:{secs % 60:02d}"

def _fetch_audio_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.content

# Ánh xạ status → (pct_start, pct_end) trên thanh tiến trình
_STAGE_RANGE = {
    "PENDING":       (0.03, 0.20),
    "TEXT_SUCCESS":  (0.20, 0.45),
    "FIRST_SUCCESS": (0.45, 0.82),
    "SUCCESS":       (1.00, 1.00),
}

def suno_poll_with_ui(api_key: str, task_id: str,
                      bar: "st.delta_generator.DeltaGenerator",
                      preview_slot: "st.delta_generator.DeltaGenerator") -> list:
    """
    Poll Suno mỗi 8s, cập nhật progress bar + preview streaming.
    Trả về list 2 track dict khi SUCCESS.
    """
    prev_status = None
    stage_step = 0
    preview_shown = False

    for attempt in range(45):
        data = suno_poll_task(api_key, task_id)
        status = data.get("status", "PENDING")
        elapsed = attempt * 8

        if status != prev_status:
            stage_step = 0
            prev_status = status
        else:
            stage_step += 1

        # Tính phần trăm
        if status == "SUCCESS":
            pct = 1.0
        else:
            lo, hi = _STAGE_RANGE.get(status, (0.03, 0.20))
            within = min(0.90, stage_step / 9)
            pct = lo + within * (hi - lo)

        bar.progress(pct, text=f"⏳ **{status}** — {elapsed}s — {int(pct * 100)}%")

        # Preview stream khi track đầu tiên sẵn sàng
        if not preview_shown and status in ("FIRST_SUCCESS", "SUCCESS"):
            suno_data = (data.get("response") or {}).get("sunoData", [])
            stream_tracks = [t for t in suno_data if t.get("streamAudioUrl")]
            if stream_tracks:
                preview_shown = True
                with preview_slot.container():
                    st.markdown("##### 🎵 Preview (stream — full track đang xử lý)")
                    cols = st.columns(len(stream_tracks[:2]))
                    for vi, t in enumerate(stream_tracks[:2]):
                        with cols[vi]:
                            st.caption(f"Version {'AB'[vi]}  ·  ⏱ {fmt_duration(t.get('duration'))}")
                            st.audio(t["streamAudioUrl"], format="audio/mpeg")

        if status == "SUCCESS":
            return data["response"]["sunoData"]
        if status in SUNO_FAIL_STATUS:
            err_msg = data.get("errorMessage") or data.get("msg") or status
            raise ValueError(f"Suno thất bại ({status}): {err_msg}")

        time.sleep(8)

    raise TimeoutError("Suno không hoàn thành sau 6 phút.")


def run_suno_generation(title: str, style: str, lyrics: str, track_key: str):
    suno_key = st.session_state.get("suno_api_key", "").strip()
    model    = st.session_state.get("suno_model", "V5_5")

    if not suno_key:
        st.warning("Nhập Suno API Key ở sidebar.")
        return
    if not lyrics:
        st.warning("Không có lyrics để gửi tới Suno.")
        return

    info_slot    = st.empty()
    bar_slot     = st.empty()
    preview_slot = st.empty()
    dl_slot      = st.empty()

    MAX_ATTEMPTS = 2
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            info_slot.info(f"📤 Gửi yêu cầu tới Suno: **{title[:60]}**"
                           + (f" (lần {attempt})" if attempt > 1 else ""))
            task_id = suno_generate_task(suno_key, title, style, lyrics, model)
            info_slot.info(f"🆔 Task: `{task_id}` — chờ Suno sinh nhạc (2–3 phút)…")

            bar = bar_slot.progress(0.0, text="⏳ Đang khởi động…")
            suno_list = suno_poll_with_ui(suno_key, task_id, bar, preview_slot)

            st.session_state.suno_tracks[track_key] = suno_list
            _persist_suno_to_history()
            bar_slot.progress(1.0, text="✅ 100% — Đang tải MP3 full track…")

            for vi, track in enumerate(suno_list):
                url = track.get("audioUrl", "")
                if url:
                    st.session_state.suno_audio[f"{track_key}_v{vi}"] = _fetch_audio_bytes(url)

            durations = " / ".join(fmt_duration(t.get("duration")) for t in suno_list)
            info_slot.success(f"✅ Hoàn thành: **{title}** — Duration: {durations}")
            bar_slot.empty()
            preview_slot.empty()
            dl_slot.empty()
            # Trừ 5 Xu sau khi render nhạc thành công (chỉ với bundled)
            _cu = st.session_state.get("user", {})
            if _cu.get("uid") and not _cu.get("is_byok"):
                _rem = _deduct_coins(_cu["uid"], COIN_COSTS["suno"],
                                     action="suno", description=f"Render nhạc: {title[:60]}")
                st.session_state.user = {**_cu, "credits": _rem}
            queue_notification("🎵 Nhạc đã xong!", f'"{title[:50]}" đã render xong.')
            st.rerun()
            return

        except Exception as e:
            bar_slot.empty()
            preview_slot.empty()
            if attempt < MAX_ATTEMPTS:
                info_slot.warning(f"⚠️ Lần {attempt} thất bại ({e}) — thử lại sau 5s…")
                time.sleep(5)
            else:
                info_slot.error(f"❌ {e}")


def run_suno_variation(clip_id: str, continue_at: int,
                       title: str, style: str, lyrics: str,
                       parent_key: str, label: str):
    """
    Tạo continuation hoặc remix từ clip_id đã có.
    Kết quả được lưu vào suno_tracks dưới key mới và thêm vào suno_ext_keys[parent_key].
    """
    suno_key = st.session_state.get("suno_api_key", "").strip()
    model    = st.session_state.get("suno_model", "V5_5")
    if not suno_key:
        st.warning("Nhập Suno API Key ở sidebar.")
        return

    ext_key      = f"{parent_key}_x{int(time.time())}"
    info_slot    = st.empty()
    bar_slot     = st.empty()
    preview_slot = st.empty()

    MAX_ATTEMPTS = 2
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            info_slot.info(f"📤 Gửi yêu cầu: **{title[:60]}**"
                           + (f" (lần {attempt})" if attempt > 1 else ""))
            task_id = suno_extend_task(suno_key, clip_id, continue_at,
                                       title, style, lyrics, model)
            info_slot.info(f"🆔 Task: `{task_id}` — chờ Suno (2–3 phút)…")
            bar      = bar_slot.progress(0.0, text="⏳ Đang khởi động…")
            suno_list = suno_poll_with_ui(suno_key, task_id, bar, preview_slot)

            st.session_state.suno_tracks[ext_key] = suno_list
            st.session_state.suno_ext_keys.setdefault(parent_key, []).append((ext_key, label))
            bar_slot.progress(1.0, text="✅ 100% — Đang tải MP3…")

            for vi, track in enumerate(suno_list):
                url = track.get("audioUrl", "")
                if url:
                    st.session_state.suno_audio[f"{ext_key}_v{vi}"] = _fetch_audio_bytes(url)

            durations = " / ".join(fmt_duration(t.get("duration")) for t in suno_list)
            info_slot.success(f"✅ Hoàn thành: **{title}** — {durations}")
            bar_slot.empty()
            preview_slot.empty()

            _cu = st.session_state.get("user", {})
            if _cu.get("uid") and not _cu.get("is_byok"):
                _vtype = "Tiếp tục" if continue_at > 0 else "Remix"
                _rem = _deduct_coins(_cu["uid"], COIN_COSTS["suno"],
                                     action="suno",
                                     description=f"{_vtype}: {title[:50]}")
                st.session_state.user = {**_cu, "credits": _rem}
            queue_notification("🎵 Nhạc đã xong!", f'"{title[:50]}" đã render xong.')
            st.rerun()
            return
        except Exception as e:
            bar_slot.empty()
            preview_slot.empty()
            if attempt < MAX_ATTEMPTS:
                info_slot.warning(f"⚠️ Lần {attempt} thất bại ({e}) — thử lại sau 5s…")
                time.sleep(5)
            else:
                info_slot.error(f"❌ {e}")


def generate_all_tracks(items: list, max_workers: int = 5):
    """
    items: list of (title, style, lyrics, track_key).
    Pha 1: Submit song song qua ThreadPoolExecutor (không update UI từ thread).
    Pha 2: Poll toàn bộ tasks từ main thread mỗi 8s — cập nhật progress + log an toàn.
    Pha 3: Download MP3 song song sau khi SUCCESS.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed

    suno_key = st.session_state.get("suno_api_key", "").strip()
    model    = st.session_state.get("suno_model", "V5_5")
    if not suno_key:
        st.warning("Nhập Suno API Key ở sidebar.")
        return

    n        = len(items)
    bar      = st.progress(0.0, text=f"📤 Đang submit {n} tracks lên Suno…")
    log_slot = st.empty()
    statuses = {tk: "queued" for _, _, _, tk in items}

    def _render_log():
        lines = "\n".join(
            f"{'✅' if 'done' in v else ('❌' if 'FAIL' in v else '⏳')} {tk}: {v}"
            for tk, v in sorted(statuses.items())
        )
        log_slot.code(lines)

    # ── Pha 1: Submit song song (chỉ trả dữ liệu, không gọi st.*) ──────────
    def _submit(item):
        title, style, lyrics, tk = item
        try:
            tid = suno_generate_task(suno_key, title, style, lyrics, model)
            return tk, tid, None
        except Exception as e:
            return tk, None, str(e)

    task_map   = {}   # tk -> task_id
    submit_ok  = 0
    _workers   = min(n, max_workers, MAX_SUNO_WORKERS)
    with ThreadPoolExecutor(max_workers=_workers) as ex:
        futs = {ex.submit(_submit, it): it for it in items}
        for f in _as_completed(futs):
            tk, tid, err = f.result()
            if tid:
                task_map[tk]  = tid
                statuses[tk]  = f"submitted {tid[:10]}"
                submit_ok    += 1
                st.session_state.suno_failed.pop(tk, None)
            else:
                statuses[tk] = f"FAIL submit: {err[:50]}"
                st.session_state.suno_failed[tk] = f"submit: {err}"
            bar.progress(submit_ok / n * 0.08, text=f"Submitted {submit_ok}/{n}…")
            _render_log()

    # ── Pha 2: Poll từ main thread mỗi 8s ──────────────────────────────────
    completed = set()   # tập tk đã xong (SUCCESS hoặc FAIL)
    suno_data_map = {}  # tk -> suno_list

    for attempt in range(45):
        pending = [tk for tk in task_map if tk not in completed]
        if not pending:
            break

        for tk in pending:
            try:
                data   = suno_poll_task(suno_key, task_map[tk])
                status = data.get("status", "PENDING")
                statuses[tk] = f"{status} {attempt*8}s"

                if status == "SUCCESS":
                    suno_list = data["response"]["sunoData"]
                    suno_data_map[tk] = suno_list
                    st.session_state.suno_tracks[tk] = suno_list
                    st.session_state.suno_failed.pop(tk, None)
                    dur = " / ".join(fmt_duration(t.get("duration")) for t in suno_list)
                    statuses[tk] = f"done ✅ {dur}"
                    completed.add(tk)
                elif status in SUNO_FAIL_STATUS:
                    err_msg = data.get("errorMessage") or data.get("msg") or status
                    statuses[tk] = f"FAIL {str(err_msg)[:50]}"
                    st.session_state.suno_failed[tk] = str(err_msg)
                    completed.add(tk)
            except Exception as e:
                statuses[tk] = f"poll error: {str(e)[:40]}"

        done_count = len(completed)
        bar.progress(0.08 + done_count / n * 0.82, text=f"⏳ Hoàn thành {done_count}/{n} tracks…")
        _render_log()

        if done_count >= len(task_map):
            break
        time.sleep(8)

    # ── Pha 3: Download MP3 song song ──────────────────────────────────────
    bar.progress(0.90, text="📥 Đang tải MP3 full track…")

    def _download(item):
        tk, suno_list = item
        results = {}
        for vi, t in enumerate(suno_list):
            url = t.get("audioUrl", "")
            if url:
                try:
                    results[f"{tk}_v{vi}"] = _fetch_audio_bytes(url)
                except Exception:
                    pass
        return results

    if suno_data_map:
        with ThreadPoolExecutor(max_workers=min(len(suno_data_map), max_workers, MAX_SUNO_WORKERS)) as ex:
            dl_results = list(ex.map(_download, suno_data_map.items()))
        # Ghi vào session_state từ main thread (thread-safe)
        for d in dl_results:
            st.session_state.suno_audio.update(d)

    bar.progress(1.0, text=f"✅ Xong {len(completed)}/{n} tracks!")
    _render_log()
    _persist_suno_to_history()
    queue_notification("🎵 Album đã xong!", f"{len(completed)}/{n} tracks đã render xong.")
    st.rerun()


_BASE_TRACK_KEY_SET = {"single_track"}

def _is_base_track_key(key: str) -> bool:
    """True nếu key là track gốc (single_track hoặc track_N), False nếu là ext/variation."""
    if key in _BASE_TRACK_KEY_SET:
        return True
    if key.startswith("track_") and key[6:].isdigit():
        return True
    return False


def _persist_suno_to_history():
    """Lưu audio URLs của các track gốc vào project history trên Supabase."""
    user    = st.session_state.get("user")
    hist_id = st.session_state.get("current_history_id")
    if not user or not hist_id or not st.session_state.suno_tracks:
        return
    slim = {
        tk: [
            {
                "audioUrl":       t.get("audioUrl", ""),
                "streamAudioUrl": t.get("streamAudioUrl", ""),
                "duration":       t.get("duration", 0),
                "id":             t.get("id", ""),
            }
            for t in tracks
        ]
        for tk, tracks in st.session_state.suno_tracks.items()
        if _is_base_track_key(tk)   # bỏ qua ext/variation keys
    }
    if not slim:
        return
    try:
        update_history_suno(user["uid"], hist_id, slim)
    except Exception:
        pass


def generate_video_script(title: str, style: str, lyrics: str, track_key: str):
    """Tạo script YouTube video bằng AI Router, lưu vào session_state."""
    api_key  = st.session_state.get("anthropic_api_key", "").strip()
    meta     = st.session_state.get("music_meta", {})
    topic    = meta.get("topic", title)
    genre    = meta.get("music_genre", "Thiếu Nhi (Nursery)")
    language = st.session_state.get("language_select", "Tiếng Việt")
    prompt   = build_video_script_prompt(title, topic, genre, style, lyrics, language)
    raw, _p  = generate_text(
        system_prompt="",
        user_prompt=prompt,
        max_tokens=1024,
        user_api_key=api_key,
        claude_model="claude-haiku-4-5-20251001",
    )
    st.session_state.video_scripts[track_key] = raw.strip()


def _parse_storyboard_prompts(storyboard_md: str) -> str:
    """
    Trích xuất cột 'Prompt AI (English)' + 'Camera Motion' từ bảng Markdown.
    Trả về chuỗi: mỗi scene là 1 đoạn, cách nhau 1 dòng trắng.
    """
    _SKIP = {"prompt", "english", "bắt buộc", "---", ":---", "cảnh", "scene"}
    prompts = []
    header_done = False

    for raw in storyboard_md.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]   # bỏ ô rỗng đầu/cuối

        if len(cells) < 5:
            continue

        # Dòng header hoặc separator
        low0 = cells[0].lower()
        if any(s in low0 for s in _SKIP) or set(cells[0].replace(":", "").replace("-", "").strip()) == set():
            header_done = True
            continue

        if not header_done:
            continue

        # Bỏ dòng separator :---
        if all(set(c.replace(":", "").replace("-", "").replace(" ", "")) <= {"", "-"} for c in cells):
            continue

        prompt = cells[4] if len(cells) > 4 else ""
        camera = cells[5] if len(cells) > 5 else ""

        # Bỏ ô placeholder
        if not prompt or prompt in {"...", "—", "-", "..."}:
            continue
        if any(s in prompt.lower() for s in _SKIP):
            continue

        # Ghép prompt + camera motion
        combined = prompt.rstrip(". ")
        if camera and camera not in {"...", "—", "-", "..."}:
            combined += f". {camera}"
        prompts.append(combined)

    return "\n\n".join(prompts)


def _gen_mv_storyboard(title: str, lyrics: str, track_key: str, tracks_data: list):
    """Tạo Storyboard MV bằng AI Router từ dữ liệu track Suno thực tế."""
    api_key = st.session_state.get("anthropic_api_key", "").strip()
    meta  = st.session_state.get("music_meta", {})
    topic = meta.get("topic", title)
    genre = meta.get("music_genre", "")

    # Lấy duration thực từ track dài nhất trong 2 version
    dur = max((float(t.get("duration") or 0) for t in tracks_data[:2]), default=180.0)
    scenes = max(4, round(dur / 8))

    prompt = build_mv_director_prompt(topic, genre, dur, lyrics)

    raw, _p = generate_text(
        system_prompt="",
        user_prompt=prompt,
        max_tokens=6000,
        user_api_key=api_key,
    )
    st.session_state.mv_storyboards[track_key] = raw.strip()


def music_widget(title: str, style: str, lyrics: str, track_key: str):
    """Per-track Suno UI: generate button → progress → preview → full player + download."""
    tracks   = st.session_state.suno_tracks.get(track_key)
    fail_msg = st.session_state.suno_failed.get(track_key)

    if fail_msg:
        st.error(f"❌ Thất bại: {fail_msg}")

    if tracks:
        ver_tabs = st.tabs(["🎵 Version A", "🎵 Version B"])
        for vi, (tab, t) in enumerate(zip(ver_tabs, tracks)):
            with tab:
                col_dur, col_info = st.columns([1, 2])
                col_dur.metric("⏱️ Duration", fmt_duration(t.get("duration")))
                col_info.caption(f"Model: {t.get('modelName', '')}  ·  ID: `{t.get('id', '')[:14]}…`")

                audio_url = t.get("audioUrl", "")
                if audio_url:
                    st.audio(audio_url, format="audio/mpeg")

                audio_bytes = st.session_state.suno_audio.get(f"{track_key}_v{vi}")
                if audio_bytes:
                    _dl_title = _clean_filename(t.get("title") or title)[:60]
                    st.download_button(
                        f"⬇️ Tải MP3 – Version {'AB'[vi]}",
                        data=audio_bytes,
                        file_name=f"{_dl_title} - Version {'AB'[vi]}.mp3",
                        mime="audio/mpeg",
                        key=f"dl_mp3_{track_key}_v{vi}",
                    )

    _suno_user   = st.session_state.get("user", {})
    _suno_byok   = _suno_user.get("is_byok", False)
    _suno_coins  = _suno_user.get("credits", 0)
    _cd_suno_key = f"_cd_suno_{track_key}"
    _cd_suno_rem = int(10 - (time.time() - st.session_state.get(_cd_suno_key, 0)))
    _suno_cost   = COIN_COSTS["suno"]

    _cost_suffix = "" if _suno_byok else f" ({_suno_cost} Xu)"
    if fail_msg:
        btn_label = f"🔄 Tạo lại{_cost_suffix}"
    elif tracks:
        btn_label = f"🔄 Tạo lại Suno{_cost_suffix}"
    else:
        btn_label = f"🎵 Tạo nhạc Suno{_cost_suffix}"

    if _cd_suno_rem > 0:
        st.button(f"⏳ Cooldown {_cd_suno_rem}s…", disabled=True, key=f"gen_suno_{track_key}")
    elif not _suno_byok and _suno_coins < _suno_cost:
        st.button(f"🪙 Không đủ Xu (cần {_suno_cost}, có {_suno_coins})", disabled=True, key=f"gen_suno_{track_key}")
    else:
        if st.button(btn_label, key=f"gen_suno_{track_key}"):
            st.session_state[_cd_suno_key] = time.time()
            st.session_state.suno_failed.pop(track_key, None)
            run_suno_generation(title, style, lyrics, track_key)

    # ── Video Script ───────────────────────────────────────────────────────
    script = st.session_state.video_scripts.get(track_key)
    with st.expander("📽️ Script Video", expanded=bool(script)):
        if script:
            st.code(script, language="markdown")
            sc1, sc2 = st.columns(2)
            if sc1.button("🔄 Tạo lại script", key=f"regen_script_{track_key}",
                          use_container_width=True):
                with st.spinner("Đang viết script…"):
                    try:
                        generate_video_script(title, style, lyrics, track_key)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi tạo script: {e}")
            if sc2.button("🗑️ Xóa script", key=f"del_script_{track_key}",
                          use_container_width=True):
                st.session_state.video_scripts.pop(track_key, None)
                st.rerun()
        else:
            if st.button("✍️ Tạo Script Video", key=f"gen_script_{track_key}",
                         use_container_width=True):
                with st.spinner("Claude đang viết script…"):
                    try:
                        generate_video_script(title, style, lyrics, track_key)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi tạo script: {e}")

    # ── MV Storyboard (AI Director) ────────────────────────────────────────
    # Chỉ enable khi đủ 2 version (A + B) với audioUrl thực tế
    _tracks_data = st.session_state.suno_tracks.get(track_key, [])
    _has_two     = (
        len(_tracks_data) >= 2
        and bool(_tracks_data[0].get("audioUrl"))
        and bool(_tracks_data[1].get("audioUrl"))
    )
    _mv_script = st.session_state.mv_storyboards.get(track_key)

    with st.expander("🎬 Kịch Bản MV (AI Storyboard)", expanded=bool(_mv_script)):
        if not _has_two:
            # Hiện trạng thái khoá — chưa đủ 2 track
            _done = sum(1 for t in _tracks_data if t.get("audioUrl"))
            st.info(
                f"🔒 Tính năng mở khóa khi có đủ **2 version nhạc (A & B)**.\n\n"
                f"Hiện tại: **{_done}/2** version hoàn thành."
            )
        elif _mv_script:
            st.markdown(_mv_script)

            # ── Copy All Prompts ──────────────────────────────────────────
            _all_prompts = _parse_storyboard_prompts(_mv_script)
            if _all_prompts:
                st.divider()
                st.caption(
                    "📋 **Tất cả AI Prompts** — mỗi scene 1 đoạn, "
                    "dán thẳng vào Veo 3 / Runway / Kling / Hailuo"
                )
                st.code(_all_prompts, language="text")

            mv1, mv2 = st.columns(2)
            if mv1.button("🔄 Tạo lại Storyboard", key=f"regen_mv_{track_key}",
                          use_container_width=True):
                with st.spinner("AI Director đang phân cảnh lại…"):
                    try:
                        _gen_mv_storyboard(title, lyrics, track_key, _tracks_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
            if mv2.button("🗑️ Xóa Storyboard", key=f"del_mv_{track_key}",
                          use_container_width=True):
                st.session_state.mv_storyboards.pop(track_key, None)
                st.rerun()
        else:
            # Hiện thông tin trước khi tạo
            _dur   = max((float(t.get("duration") or 0) for t in _tracks_data[:2]), default=0.0)
            _scenes = max(4, round(_dur / 8))
            st.markdown(
                f"🎵 **{fmt_duration(_dur)}** ({int(_dur)}s) &nbsp;→&nbsp; "
                f"**{_scenes} cảnh** (1 cảnh ≈ 8s)"
            )
            if st.button("🎬 Tạo Kịch Bản MV", key=f"gen_mv_{track_key}",
                         use_container_width=True, type="primary"):
                with st.spinner(f"AI Director đang phân cảnh {_scenes} cảnh… (30-60s)"):
                    try:
                        _gen_mv_storyboard(title, lyrics, track_key, _tracks_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi tạo storyboard: {e}")

    # ── Remix / Tiếp tục ──────────────────────────────────────────────────────
    if tracks:
        _is_byok     = st.session_state.get("user", {}).get("is_byok", False)
        _cost_sfx    = "" if _is_byok else f" ({COIN_COSTS['suno']} Xu)"
        _ver_opts    = [
            (vi, t.get("id", ""), float(t.get("duration") or 0),
             f"Version {'AB'[vi]} ({fmt_duration(t.get('duration'))})")
            for vi, t in enumerate(tracks[:2])
            if t.get("id")
        ]

        with st.expander("🔁 Remix / ▶️ Tiếp tục bài này", expanded=False):
            if not _ver_opts:
                st.warning("Không tìm thấy clip ID. Thử tạo lại bài nhạc.")
            else:
                _tab_ext, _tab_rmx = st.tabs(["▶️ Tiếp tục (Extend)", "🔁 Remix"])

                # ── Extend ────────────────────────────────────────────────────
                with _tab_ext:
                    st.caption("Kéo dài bài nhạc từ một mốc thời gian bất kỳ.")
                    _ext_ver_lbl = st.radio(
                        "Chọn phiên bản gốc:",
                        [v[3] for v in _ver_opts],
                        horizontal=True,
                        key=f"ext_ver_{track_key}",
                    )
                    _ext_vi, _ext_clip, _ext_dur, _ = next(
                        v for v in _ver_opts if v[3] == _ext_ver_lbl
                    )
                    _ext_max = max(10, int(_ext_dur))
                    _ext_default = min(int(_ext_dur * 0.75), _ext_max - 5) if _ext_dur > 10 else 0
                    _ext_at = st.slider(
                        "Tiếp tục từ giây thứ:",
                        min_value=0, max_value=_ext_max,
                        value=_ext_default, step=1,
                        key=f"ext_at_{track_key}",
                    )
                    st.caption(
                        f"⏱ Sẽ tạo từ **{fmt_duration(_ext_at)}** "
                        f"/ tổng **{fmt_duration(_ext_dur)}**"
                    )
                    _ext_title  = st.text_input(
                        "Tiêu đề phần tiếp:",
                        value=f"{title} (Part 2)",
                        key=f"ext_title_{track_key}",
                    )
                    _ext_style  = st.text_area(
                        "Style (giữ nguyên hoặc đổi):",
                        value=style, height=60,
                        key=f"ext_style_{track_key}",
                    )
                    _ext_lyrics = st.text_area(
                        "Lời tiếp theo (để trống = Suno tự sinh):",
                        value="", height=80,
                        placeholder="[Verse 2]\nLời tiếp theo…",
                        key=f"ext_lyrics_{track_key}",
                    )
                    _ext_coins = st.session_state.get("user", {}).get("credits", 0)
                    _ext_ok    = _is_byok or _ext_coins >= COIN_COSTS["suno"]
                    if not _ext_ok:
                        st.button(f"🪙 Không đủ Xu (cần {COIN_COSTS['suno']})",
                                  disabled=True, key=f"btn_ext_{track_key}")
                    elif st.button(f"▶️ Tạo phần tiếp{_cost_sfx}", type="primary",
                                   use_container_width=True, key=f"btn_ext_{track_key}"):
                        run_suno_variation(
                            clip_id=_ext_clip,
                            continue_at=_ext_at,
                            title=(_ext_title.strip() or f"{title} (Part 2)"),
                            style=(_ext_style.strip() or style),
                            lyrics=_ext_lyrics.strip(),
                            parent_key=track_key,
                            label=f"Tiếp tục từ {fmt_duration(_ext_at)} (Ver {'AB'[_ext_vi]})",
                        )

                # ── Remix ─────────────────────────────────────────────────────
                with _tab_rmx:
                    st.caption(
                        "Tái tạo bài nhạc với style / lời mới, "
                        "giữ nguyên DNA âm thanh của phiên bản gốc."
                    )
                    _rmx_ver_lbl = st.radio(
                        "Chọn phiên bản gốc:",
                        [v[3] for v in _ver_opts],
                        horizontal=True,
                        key=f"rmx_ver_{track_key}",
                    )
                    _rmx_vi, _rmx_clip, _rmx_dur, _ = next(
                        v for v in _ver_opts if v[3] == _rmx_ver_lbl
                    )
                    _rmx_title = st.text_input(
                        "Tiêu đề remix:",
                        value=f"{title} (Remix)",
                        key=f"rmx_title_{track_key}",
                    )
                    _rmx_style = st.text_area(
                        "Style mới:",
                        value=style, height=60,
                        key=f"rmx_style_{track_key}",
                    )
                    _rmx_lyrics = st.text_area(
                        "Lời mới (để trống = giữ lời gốc):",
                        value="", height=80,
                        placeholder="[Verse 1]\nLời mới…",
                        key=f"rmx_lyrics_{track_key}",
                    )
                    _rmx_coins = st.session_state.get("user", {}).get("credits", 0)
                    _rmx_ok    = _is_byok or _rmx_coins >= COIN_COSTS["suno"]
                    if not _rmx_ok:
                        st.button(f"🪙 Không đủ Xu (cần {COIN_COSTS['suno']})",
                                  disabled=True, key=f"btn_rmx_{track_key}")
                    elif st.button(f"🔁 Tạo Remix{_cost_sfx}", type="primary",
                                   use_container_width=True, key=f"btn_rmx_{track_key}"):
                        run_suno_variation(
                            clip_id=_rmx_clip,
                            continue_at=0,
                            title=(_rmx_title.strip() or f"{title} (Remix)"),
                            style=(_rmx_style.strip() or style),
                            lyrics=(_rmx_lyrics.strip() or lyrics),
                            parent_key=track_key,
                            label=f"Remix (Ver {'AB'[_rmx_vi]})",
                        )

        # ── Các biến thể đã tạo ───────────────────────────────────────────────
        _ext_list = st.session_state.suno_ext_keys.get(track_key, [])
        if _ext_list:
            st.markdown(f"**🎵 Biến thể đã tạo ({len(_ext_list)})**")
            for _ek, _elabel in _ext_list:
                _ext_tracks = st.session_state.suno_tracks.get(_ek, [])
                if not _ext_tracks:
                    continue
                with st.expander(f"🎵 {_elabel}", expanded=False):
                    _etabs = st.tabs(["Version A", "Version B"])
                    for _evi, (_etab, _et) in enumerate(zip(_etabs, _ext_tracks)):
                        with _etab:
                            _eurl = _et.get("audioUrl", "")
                            if _eurl:
                                st.audio(_eurl, format="audio/mpeg")
                            _ebytes = st.session_state.suno_audio.get(f"{_ek}_v{_evi}")
                            if _ebytes:
                                _edl_title = _clean_filename(_et.get("title") or _elabel)[:60]
                                st.download_button(
                                    f"⬇️ Tải MP3 – Version {'AB'[_evi]}",
                                    data=_ebytes,
                                    file_name=f"{_edl_title} - Version {'AB'[_evi]}.mp3",
                                    mime="audio/mpeg",
                                    key=f"dl_ext_{_ek}_v{_evi}",
                                )

# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------
def _clean_filename(title: str) -> str:
    """Làm sạch tên file MP3: bỏ Track_N prefix, underscore→space, bỏ _vX suffix."""
    import re
    s = title.strip()
    s = re.sub(r'^(?:Track[_ ]?\d+[_ :\-]+)+', '', s, flags=re.IGNORECASE)
    s = s.replace("_", " ")
    s = re.sub(r'\s*[_ ][vV]?[AB]\s*$', '', s)
    s = re.sub(r'\s{2,}', ' ', s)
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    return s.strip()

# JSON helpers
# ---------------------------------------------------------------------------
def _fix_control_chars(s: str) -> str:
    """Escape literal control characters inside JSON string values."""
    result = []
    in_string = False
    skip_next = False
    for ch in s:
        if skip_next:
            result.append(ch)
            skip_next = False
        elif ch == "\\" and in_string:
            result.append(ch)
            skip_next = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ch == "\n":
            result.append("\\n")
        elif in_string and ch == "\r":
            result.append("\\r")
        elif in_string and ch == "\t":
            result.append("\\t")
        elif in_string and ord(ch) < 0x20:
            result.append(f"\\u{ord(ch):04x}")
        else:
            result.append(ch)
    return "".join(result)


# ---------------------------------------------------------------------------
# Hot topic suggestions
# ---------------------------------------------------------------------------
def get_hot_topics(api_key: str, language: str) -> list:
    today = date.today().strftime("%B %d, %Y")
    raw, _p = generate_text(
        system_prompt="",
        user_prompt=(
            f"You are a YouTube content strategist for a children's music channel.\n"
            f"Today is {today}. Suggest 5 FRESH and DIFFERENT trending topic ideas for children's music videos.\n"
            f"Output language: {language}\n"
            f"Consider: current season, upcoming holidays, popular animals, vehicles, food, nature, fairy tales.\n"
            f"Each topic must be specific and creative, not generic.\n"
            f"Return ONLY a JSON array of 5 short topic strings (5-10 words each), no explanation.\n"
            f'Example: ["Little duck in the rainy day", "Fire truck saves the forest", ...]'
        ),
        max_tokens=512,
        user_api_key=api_key,
        claude_model="claude-haiku-4-5-20251001",
    )
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(_fix_control_chars(raw))

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
api_key = st.session_state.get("anthropic_api_key", "")

with st.sidebar:
    st.header("⚙️ Cấu hình quy trình")

    st.info("🔑 Cấu hình API Keys trong tab **🔑 API Keys** bên dưới.")
    st.divider()
    st.subheader("🎼 Phong cách âm nhạc")
    music_genre = st.radio("Chọn thể loại:", GENRE_NAMES, index=0, key="music_genre")
    _gcfg = GENRE_CONFIG[music_genre]
    st.caption(f"⚡ {_gcfg['bpm']}  |  {_gcfg['style_tags']}")

    st.divider()

    # Áp dụng gợi ý trước khi widget được khởi tạo
    if st.session_state.pending_topic is not None:
        st.session_state.topic_input = st.session_state.pending_topic
        st.session_state.pending_topic = None

    topic = st.text_input(
        "Chủ đề bài hát / album:",
        placeholder="Ví dụ: Chú vịt con lông vàng",
        key="topic_input",
    )

    suggest_btn = st.button("💡 Gợi ý 5 chủ đề hot", use_container_width=True)
    if suggest_btn:
        with st.spinner("Đang tìm chủ đề hot hôm nay..."):
            try:
                lang = st.session_state.get("language_select", "English")
                st.session_state.suggested_topics = get_hot_topics(api_key, lang)
            except Exception as e:
                st.error(f"Lỗi gợi ý: {e}")

    if st.session_state.suggested_topics:
        st.markdown("**Chọn để điền vào ô chủ đề:**")
        for idx, suggestion in enumerate(st.session_state.suggested_topics):
            if st.button(f"▶ {suggestion}", key=f"sug_{idx}", use_container_width=True):
                st.session_state.pending_topic = suggestion
                st.rerun()

    st.divider()

    num_tracks = st.number_input("Số lượng bài cần tạo:", min_value=1, max_value=20, value=10, key="num_tracks")
    language = st.selectbox(
        "Ngôn ngữ đầu ra:",
        ["English", "Tiếng Việt", "Japanese"],
        key="language_select",
    )

    batches = compute_batches(num_tracks)
    if len(batches) > 1:
        st.info(
            f"**Tự động chia {len(batches)} phần:**\n"
            + "\n".join(f"• Phần {i+1}: Tracks {s}–{e}" for i, (s, e) in enumerate(batches))
        )

    create_mv = False

    st.divider()
    # ── Presets ──────────────────────────────────────────────────────────────
    st.subheader("⭐ Presets")
    _presets = load_presets()
    _preset_names = [p["name"] for p in _presets]

    if _preset_names:
        _sel = st.selectbox("Preset đã lưu:", ["— Chọn —"] + _preset_names, key="preset_select")
        if _sel != "— Chọn —":
            _p = next((p for p in _presets if p["name"] == _sel), None)
            _pa, _pd = st.columns(2)
            if _pa.button("▶ Áp dụng", use_container_width=True, key="preset_apply"):
                st.session_state.music_genre       = _p.get("genre", GENRE_NAMES[0])
                st.session_state.language_select   = _p.get("language", "Tiếng Việt")
                st.session_state.num_tracks        = int(_p.get("num_tracks", 10))
                st.session_state.create_mv_check   = bool(_p.get("create_mv", False))
                st.session_state.suno_model        = _p.get("suno_model", "V5_5")
                st.rerun()
            if _pd.button("🗑️ Xóa", use_container_width=True, key="preset_delete"):
                save_presets([p for p in _presets if p["name"] != _sel])
                st.session_state.pop("preset_select", None)
                st.rerun()

    _pname = st.text_input("Tên preset:", placeholder="VD: Album EDM 10 bài VI", key="preset_name_input")
    if st.button("💾 Lưu cấu hình hiện tại", use_container_width=True, key="preset_save"):
        if not _pname.strip():
            st.warning("Nhập tên preset trước khi lưu.")
        else:
            _new = {
                "name":       _pname.strip(),
                "genre":      st.session_state.get("music_genre", GENRE_NAMES[0]),
                "num_tracks": int(st.session_state.get("num_tracks", 10)),
                "language":   st.session_state.get("language_select", "Tiếng Việt"),
                "create_mv":  bool(st.session_state.get("create_mv_check", False)),
                "suno_model": st.session_state.get("suno_model", "V5_5"),
            }
            _updated = [p for p in _presets if p["name"] != _new["name"]] + [_new]
            save_presets(_updated)
            st.success(f"Đã lưu preset **{_new['name']}**!")

    st.divider()
    if st.session_state.user:
        with st.expander("📁 Projects (72h)", expanded=False):
            try:
                history = get_music_history(st.session_state.user["uid"])
                if not history:
                    st.info("Chưa có project nào.")
                for _h in history:
                    _ts      = _h.get("created_at")
                    _ts_str  = _ts.strftime("%d/%m %H:%M") if _ts else ""
                    _n_suno  = len(_h.get("suno_results", {}))
                    _badge   = f" 🎵{_n_suno}" if _n_suno else ""
                    # Project name = Claude title (saved on generation) or fallback to topic
                    _pname   = _h.get("project_name") or _h.get("topic", "—")
                    _label   = f"📁 {_pname[:24]}{_badge}  ·  {_ts_str}"
                    with st.expander(_label, expanded=False):
                        st.caption(
                            f"**{_h.get('genre','')}** · {_h.get('num_tracks','')} bài"
                            + (f" · chủ đề: _{_h.get('topic','')}_" if _h.get("topic") else "")
                        )
                        _res   = _h.get("result", {})
                        _tlist = _res.get("tracks", [])
                        if _tlist:
                            for _t in _tlist[:6]:
                                if isinstance(_t, dict):
                                    st.caption(f"• {_t.get('title','')}")
                            if len(_tlist) > 6:
                                st.caption(f"  …+{len(_tlist)-6} bài")
                        elif _res.get("title"):
                            st.caption(f"🎵 Single: {_res['title']}")
                        if st.button("🔄 Khôi phục project", key=f"hr_{_h['id']}",
                                     use_container_width=True, type="primary"):
                            st.session_state.music_result = _res
                            st.session_state.music_meta   = {
                                "topic":        _h.get("topic", ""),
                                "num_tracks":   _h.get("num_tracks", 1),
                                "create_mv":    _h.get("create_mv", False),
                                "music_genre":  _h.get("genre", "Thiếu Nhi (Nursery)"),
                                "project_name": _pname,
                            }
                            _suno = _h.get("suno_results", {})
                            if _suno:
                                st.session_state.suno_tracks   = _suno
                                st.session_state.suno_audio    = {}
                                st.session_state.suno_failed   = {}
                                st.session_state.suno_ext_keys = {}
                            st.session_state.current_history_id = _h["id"]
                            st.rerun()
            except Exception:
                st.info("Không thể tải projects.")
    # ── Cost estimate ─────────────────────────────────────────────────────────
    _SONNET_IN  = 3.00  / 1_000_000   # $ per input token
    _SONNET_OUT = 15.00 / 1_000_000   # $ per output token
    _SYS_TOKENS = 4_000               # SYSTEM_PROMPT ≈ 4 000 tokens

    _est_batches  = compute_batches(num_tracks)
    _n_batches    = len(_est_batches)
    _est_in       = _SYS_TOKENS * _n_batches + 160 * _n_batches
    _est_out      = sum(700 + (e - s + 1) * 950 for s, e in _est_batches)
    _cost_in      = _est_in  * _SONNET_IN
    _cost_out     = _est_out * _SONNET_OUT
    _cost_total   = _cost_in + _cost_out
    _suno_clips   = num_tracks * 2
    _credits_left = st.session_state.suno_credits

    with st.expander("💰 Ước tính chi phí", expanded=True):
        st.markdown(
            f"**Claude Sonnet 4.6**\n"
            f"- Input : ~{_est_in:,} tokens → **${_cost_in:.3f}**\n"
            f"- Output: ~{_est_out:,} tokens → **${_cost_out:.3f}**\n"
            f"- Tổng  : **~${_cost_total:.3f}** / lần generate"
        )
        st.divider()
        _suno_line = (
            f"**Suno**: {num_tracks} track × 2 clips = **{_suno_clips} clips**\n"
            f"_(Kiểm tra số dư tại [sunoapi.org/dashboard](https://sunoapi.org/dashboard))_"
        )
        st.markdown(_suno_line)

    generate_btn = st.button("🚀 Bắt đầu sản xuất", use_container_width=True, type="primary")

# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------
def parse_json(raw: str) -> dict:
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    cleaned = _fix_control_chars(raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: json_repair xử lý quote không escape và lỗi cú pháp phổ biến
    try:
        from json_repair import repair_json
        repaired = repair_json(cleaned, return_objects=True)
        if isinstance(repaired, dict):
            return repaired
    except Exception:
        pass

    # Re-raise gốc để caller hiển thị lỗi
    return json.loads(cleaned)

# ---------------------------------------------------------------------------
# Claude API calls
# ---------------------------------------------------------------------------
def call_claude_single(api_key: str, topic: str, language: str, create_mv: bool,
                       genre: str = "Thiếu Nhi (Nursery)", bpm: str = "", style_tags: str = "",
                       byok_mode: bool = False) -> dict:
    raw, _p = generate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_single_prompt(topic, language, create_mv, genre, bpm, style_tags),
        max_tokens=16000,
        user_api_key=api_key,
        byok_mode=byok_mode,
    )
    return parse_json(raw)

def call_claude_album(api_key, topic, num_tracks, language, create_mv, status_ctx,
                      genre: str = "Thiếu Nhi (Nursery)", bpm: str = "", style_tags: str = "",
                      byok_mode: bool = False) -> dict:
    batches = compute_batches(num_tracks)
    all_results, album_title = [], None

    for i, (start, end) in enumerate(batches):
        status_ctx.write(f"⏳ Phần {i+1}/{len(batches)}: Tracks {start}–{end}…")
        prompt = (
            build_album_first_batch_prompt(topic, num_tracks, start, end, language, create_mv, genre, bpm, style_tags)
            if i == 0
            else build_album_continuation_prompt(topic, album_title, num_tracks, start, end, language, genre, bpm, style_tags)
        )
        raw, _provider = generate_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=16000,
            user_api_key=api_key,
            byok_mode=byok_mode,
        )
        batch_data = parse_json(raw)
        all_results.append(batch_data)
        if i == 0:
            album_title = batch_data.get("title", topic)
            status_ctx.write(f"✅ Phần 1 xong — Album: **{album_title}** _(via {provider_label(_provider)})_")
        else:
            status_ctx.write(f"✅ Phần {i+1} xong _(via {provider_label(_provider)})_")

    merged = all_results[0].copy()
    all_tracks = list(merged.get("tracks", []))
    for r in all_results[1:]:
        all_tracks.extend(r.get("tracks", []))
    merged["tracks"] = all_tracks
    return merged

# ---------------------------------------------------------------------------
# SEO copy block
# ---------------------------------------------------------------------------
def seo_copy_block(seo: dict, bgm: str = "", hashtags: str = ""):
    """Hiển thị toàn bộ thông tin SEO trong st.code() — có nút copy tích hợp."""
    tags_str = ", ".join(seo.get("yt_tags", []))
    block = (
        f"TITLE:\n{seo.get('yt_title', '')}\n\n"
        f"DESCRIPTION:\n{seo.get('yt_description', '')}\n\n"
        f"TAGS:\n{tags_str}\n\n"
        f"THUMBNAIL:\n{seo.get('thumbnail_idea', '')}"
    )
    if bgm:
        block += f"\n\nBGM:\n{bgm}"
    if hashtags:
        block += f"\n\nHASHTAGS:\n{hashtags}"
    st.markdown("**📋 Copy toàn bộ SEO:**")
    st.code(block, language="markdown")

# ---------------------------------------------------------------------------
# Render results
# ---------------------------------------------------------------------------
def render_results(data: dict, num_tracks: int, topic: str, create_mv: bool, music_genre: str = "Thiếu Nhi (Nursery)"):
    is_single = data.get("type") == "single" or num_tracks == 1
    gcfg = GENRE_CONFIG.get(music_genre, GENRE_CONFIG["Thiếu Nhi (Nursery)"])

    # Genre info banner
    st.info(f"🎼 **{music_genre}** — {gcfg['bpm']} | {gcfg['style_tags']}")

    col1, col2 = st.columns([1, 1], gap="large")

    # ── Cột trái: âm nhạc ──────────────────────────────────────────────────
    with col1:
        st.header("📋 Nội dung âm nhạc")

        if is_single:
            st.subheader(f"🎶 Single: {data.get('title', topic)}")
            style = data.get("music_style", "")
            lyrics = data.get("lyrics", "")
            if style:
                st.info(f"**Music Style / Tags:** {style}")
            if lyrics:
                with st.expander("📝 Lyrics (3-5 phút)", expanded=False):
                    st.write(lyrics)
            st.divider()
            music_widget(data.get("title", topic), style, lyrics, "single_track")

        else:
            st.subheader(f"💽 Album: {data.get('title', topic)}")
            tracks = data.get("tracks", [])
            if tracks:
                # ── Controls ──────────────────────────────────────────────
                ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2.5, 1, 1, 1.5])
                ctrl1.markdown(f"**{len(tracks)} tracks — Tích chọn rồi bấm Gửi:**")
                num_streams = int(ctrl4.number_input(
                    "Luồng song song:", min_value=1, max_value=15, value=5,
                    key="suno_streams",
                ))
                if ctrl2.button("☑ Tất cả", use_container_width=True, key="sel_all_btn"):
                    for _j in range(1, len(tracks) + 1):
                        st.session_state[f"chk_{_j}"] = True
                    st.rerun()
                if ctrl3.button("☐ Bỏ tất", use_container_width=True, key="sel_none_btn"):
                    for _j in range(1, len(tracks) + 1):
                        st.session_state[f"chk_{_j}"] = False
                    st.rerun()

                # ── Track list: checkbox column + expander column ──────────
                for i, t in enumerate(tracks, 1):
                    if isinstance(t, dict):
                        _tk_key = f"track_{i}"
                        _tk_failed = _tk_key in st.session_state.suno_failed
                        _tk_icon = "❌" if _tk_failed else "🎵"
                        chk_col, exp_col = st.columns([0.05, 0.95])
                        chk_col.checkbox("", key=f"chk_{i}", label_visibility="collapsed")
                        with exp_col:
                            with st.expander(f"{_tk_icon} Track {i}: {t.get('title', f'Track {i}')}", expanded=_tk_failed):
                                style = t.get("music_style", "")
                                lyrics = t.get("lyrics", "")
                                if style:
                                    st.info(f"**Style / Tags:** {style}")
                                if lyrics:
                                    with st.expander("📝 Lyrics", expanded=False):
                                        st.write(lyrics)
                                st.divider()
                                music_widget(t.get("title", f"Track {i}"), style, lyrics, _tk_key)
                    else:
                        st.markdown(f"{i}. {t}")

                # ── Failed tracks panel ────────────────────────────────────
                _failed_panel = [
                    (f"track_{i}", t)
                    for i, t in enumerate(tracks, 1)
                    if isinstance(t, dict) and f"track_{i}" in st.session_state.suno_failed
                ]
                if _failed_panel:
                    st.warning(f"⚠️ **{len(_failed_panel)} bài thất bại** — Thử lại từng bài:")
                    for _tk, _t in _failed_panel:
                        _err = st.session_state.suno_failed.get(_tk, "")
                        _fc1, _fc2 = st.columns([3, 1])
                        _fc1.caption(f"❌ **{_t.get('title', _tk)}** — {_err[:70]}")
                        if _fc2.button("🔄 Thử lại", key=f"retry_panel_{_tk}", use_container_width=True):
                            st.session_state.suno_failed.pop(_tk, None)
                            run_suno_generation(
                                _t.get("title", ""), _t.get("music_style", ""),
                                _t.get("lyrics", ""), _tk,
                            )

                # ── Send button ────────────────────────────────────────────
                selected_items = [
                    (t.get("title", f"Track {i}"), t.get("music_style", ""), t.get("lyrics", ""), f"track_{i}")
                    for i, t in enumerate(tracks, 1)
                    if isinstance(t, dict) and st.session_state.get(f"chk_{i}", False)
                ]
                n_sel = len(selected_items)
                btn_label = (
                    f"🚀 Gửi {n_sel} bài đã chọn • {num_streams} luồng"
                    if n_sel else "🚀 Chưa chọn bài nào"
                )
                if st.button(btn_label, key="gen_selected", type="primary",
                             use_container_width=True, disabled=(n_sel == 0)):
                    generate_all_tracks(selected_items, max_workers=num_streams)

    # ── Cột phải: hình ảnh & SEO ───────────────────────────────────────────
    with col2:
        st.header("🖼️ Hình ảnh & SEO")

        # Visual prompt — tự động tích hợp visual_vibe của genre
        visual_raw = data.get("visual_prompt", "")
        if visual_raw:
            st.subheader("Nano Banana 2 – Visual Prompt")
            visual_adjusted = (
                f"Studio quality, 3D isometric, {gcfg['visual_vibe']}, "
                f"centered on {topic}, {visual_raw}, 8k resolution."
            )
            image_widget(visual_adjusted, "visual_main")

        seo = data.get("seo", {})

        if create_mv:
            st.subheader("🎬 Kịch bản Video 2 (MV)")
            tabs = st.tabs(["Cấu trúc cảnh", "SEO & Metadata", "Thumbnail & BGM"])

            with tabs[0]:
                scenes = data.get("video_scenes", [])
                if scenes:
                    for i, scene in enumerate(scenes, 1):
                        with st.expander(f"🎬 Scene {i}", expanded=(i == 1)):
                            st.markdown(scene)
                            st.divider()
                            _vtab_fal, _vtab_grok = st.tabs(["🖼️ fal.ai (Seedance)", "🎬 Grok xAI Video"])
                            with _vtab_fal:
                                fal_video_widget(scene, f"scene_{i}")
                            with _vtab_grok:
                                grok_video_widget(scene, f"scene_{i}")
                else:
                    st.info("Không có dữ liệu cảnh.")
                if "Relax" in music_genre or music_genre == "Ambient Relax (Meditation)":
                    st.info(
                        "💡 **Gợi ý Video 2 – Ambient/Relax:** Sử dụng chuyển động lặp (seamless loop) "
                        "cực chậm để giữ người xem không bị mất tập trung. Ví dụ: tách trà bốc khói "
                        "nhẹ, lá cây khẽ lay trong gió, hoặc hạt bụi vàng lơ lửng dưới ánh nắng buổi sáng. "
                        "Tránh cắt cảnh đột ngột — dùng crossfade mờ dần (dissolve) giữa các shot. "
                        "Thời lượng lý tưởng: 1–3 giờ (loop video)."
                    )
                if music_genre == "Hòa tấu Trung Hoa":
                    st.info(
                        "💡 **Gợi ý Visual (Video 2) – Hòa tấu Trung Hoa:** Dùng slow-motion loop liền mạch "
                        "(seamless loop) mang phong cách thủy mặc cổ trang:\n"
                        "- 🌸 Cánh hoa đào khẽ rơi trên mặt nước tạo gợn sóng lăn tăn\n"
                        "- 🕯️ Làn khói trầm hương tỏa nhẹ từ lư hương trong thư phòng\n"
                        "- 💧 Giọt sương rơi xuống hồ tĩnh lặng — vòng sóng loang rồi tan\n\n"
                        "Tất cả shot dùng tông màu mực tàu, xanh ngọc, vàng nhạt. "
                        "Crossfade dissolve giữa các cảnh, không cắt cứng. "
                        "Thêm lớp hạt nhiễu film (grain) để tạo cảm giác cổ điển. "
                        "Thời lượng lý tưởng: 1–2 giờ (loop)."
                    )

            with tabs[1]:
                st.markdown(f"**YouTube Title:** {seo.get('yt_title', '')}")
                st.text_area(
                    "", value=seo.get("yt_description", ""),
                    height=150, label_visibility="collapsed", key="mv_desc",
                )
                tags = seo.get("yt_tags", [])
                if tags:
                    st.markdown("**Tags:** " + ", ".join(f"`{t}`" for t in tags))
                st.markdown(f"**Hashtags:** `{gcfg['hashtags']}`")
                st.divider()
                seo_copy_block(seo, data.get("bgm_suggestion", ""), gcfg["hashtags"])

            with tabs[2]:
                thumb_idea = seo.get("thumbnail_idea", "")
                if thumb_idea:
                    st.markdown("**Thumbnail Prompt (16:9):**")
                    image_widget(thumb_idea, "thumbnail")
                if music_genre == "Brazilian Phonk":
                    st.info(
                        "💡 **Gợi ý Thumbnail Phonk:** Dùng ảnh xe độ JDM hoặc nhân vật hoạt hình "
                        "dưới ánh đèn neon tím. Thêm hiệu ứng nhiễu hạt (noise/grain) và VHS scan-line "
                        "để tạo cảm giác bí ẩn, underground. Font chữ nên dùng kiểu grunge hoặc glitch."
                    )
                if music_genre == "Techno (Peak Time / Driving)":
                    st.info(
                        "💡 **SEO Strategy Techno:** Tập trung từ khóa **'Dark Techno'** và **'Driving Mix'** "
                        "để tiếp cận người nghe thích cảm giác lái xe đêm hoặc tập trung làm việc. "
                        "Title nên có: BPM + 'Peak Time' + năm (vd: *Dark Techno Driving Mix 130BPM 2026*). "
                        "Upload khung giờ 22:00–01:00 để bắt đúng đối tượng nghe nhạc đêm."
                    )
                if music_genre == "Hardstyle":
                    st.info(
                        "💡 **Gợi ý Thumbnail Hardstyle:** Dùng tông màu **cam lửa** là chủ đạo. "
                        "Hình ảnh nhân vật đang bùng nổ năng lượng hoặc biểu tượng loa sub bị nứt vỡ. "
                        "**SEO Strategy:** Nhắm từ khóa **'Gym Motivation'**, **'Workout Music'**, "
                        "'Euphoric Hardstyle Mix' — upload khung 05:00–07:00 sáng để bắt đúng "
                        "giờ tập gym buổi sáng của người dùng."
                    )
                if music_genre == "Smooth Jazz (Lounge)":
                    st.info(
                        "💡 **Gợi ý Thumbnail Jazz:** Dùng tông màu **vàng hổ phách và nâu gỗ** ấm áp. "
                        "Hình ảnh lý tưởng: góc cafe cổ điển với đèn vàng, ly rượu vang hoặc cà phê bốc khói, "
                        "cửa sổ mưa đêm thành phố. Tránh màu neon — giữ feel sang trọng, vintage.\n\n"
                        "**SEO Strategy:** Nhắm từ khóa **'Jazz Cafe Music'**, **'Smooth Jazz for Study'**, "
                        "'Relaxing Jazz Piano' — upload khung 19:00–22:00 để bắt đối tượng thư giãn buổi tối. "
                        "Title nên có: 'No Ads' hoặc '1 Hour' để tăng watch time."
                    )
                if music_genre == "Ambient Relax (Meditation)":
                    st.info(
                        "💡 **Gợi ý Thumbnail Ambient/Meditation:** Dùng palette **xanh ngọc, trắng và tím nhạt**. "
                        "Hình ảnh: dải ngân hà mềm mại, rừng núi mờ sương bình minh, hoặc mặt hồ phẳng lặng "
                        "phản chiếu bầu trời. Tuyệt đối không dùng chữ màu đỏ hay hiệu ứng bùng nổ.\n\n"
                        "**SEO Strategy:** Nhắm từ khóa **'Deep Sleep Music'**, **'Meditation Music'**, "
                        "'Study BGM', 'Healing Sounds' — upload bất kỳ giờ nào, lưu lượng tìm kiếm đều. "
                        "Title nên ghi rõ thời lượng (vd: *3 Hours Deep Sleep Music*) để YouTube "
                        "đề xuất vào danh sách phát tự động ban đêm."
                    )
                if music_genre == "Hòa tấu Trung Hoa":
                    st.info(
                        "💡 **Gợi ý Thumbnail Hòa tấu Trung Hoa:** Dùng phong cách **tranh thủy mặc** (水墨画) — "
                        "núi non mờ sương, đình cổ bên sông, hoa đào rụng trên mặt nước. "
                        "Palette: xanh ngọc bích, xám mực tàu, trắng sữa. Font chữ nên dùng kiểu thư pháp "
                        "Hán tự hoặc Việt ngữ mảnh thanh lịch.\n\n"
                        "**SEO Strategy:** Nhắm đồng thời hai thị trường: "
                        "**'Guzheng Music'**, **'Chinese Traditional Music'**, 'Wuxia OST', 'Asian Relax Music' (tiếng Anh) "
                        "và **'Nhạc Trung Hoa'**, 'Nhạc Cổ Trang', 'Đàn Tranh' (tiếng Việt). "
                        "Upload khung 20:00–23:00. Title nên có tên nhạc cụ nổi bật: "
                        "*Guzheng & Erhu – Ancient Chinese Music for Study/Relax 2026*."
                    )
                st.divider()
                st.markdown(f"**BGM Suggestion:** {data.get('bgm_suggestion', '')}")

        elif seo:
            with st.expander("📊 SEO & Metadata", expanded=False):
                st.markdown(f"**YouTube Title:** {seo.get('yt_title', '')}")
                st.text_area("Description", value=seo.get("yt_description", ""), height=120, key="seo_desc")
                tags = seo.get("yt_tags", [])
                if tags:
                    st.markdown("**Tags:** " + ", ".join(f"`{t}`" for t in tags))
                st.markdown(f"**Hashtags:** `{gcfg['hashtags']}`")
                thumb_idea = seo.get("thumbnail_idea", "")
                if thumb_idea:
                    st.markdown("**Thumbnail Prompt (16:9):**")
                    image_widget(thumb_idea, "thumbnail")
                st.markdown(f"**BGM:** {data.get('bgm_suggestion', '')}")
                st.divider()
                seo_copy_block(seo, data.get("bgm_suggestion", ""), gcfg["hashtags"])

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_music, tab_api = st.tabs(["🎵 Tạo nhạc", "🔑 API Keys"])

# ── API Keys tab ──────────────────────────────────────────────────────────────
with tab_api:
    st.markdown("""
    <style>
    .apicard {
        padding: 0.85rem 1rem; border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.09);
        background: #0d0d0d; margin-bottom: 0.4rem;
    }
    .apicard.sel {
        border-color: rgba(34,197,94,0.5);
        background: rgba(34,197,94,0.07);
    }
    .apicard-name { font-weight: 700; font-size: 0.95rem; color: #fff; }
    .apicard-ok   { font-size: 0.72rem; color: #22c55e; margin-top: 0.1rem; }
    .apicard-miss { font-size: 0.72rem; color: rgba(255,255,255,0.38); margin-top: 0.1rem; }
    .api-form-hdr {
        font-size: 1.3rem; font-weight: 800; color: #fff;
        display: flex; align-items: center; gap: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    _APIPROV = [
        {"id": "anthropic", "icon": "🤖", "name": "Anthropic Claude",
         "key": "anthropic_api_key", "ph": "sk-ant-api03-..."},
        {"id": "suno",      "icon": "🎵", "name": "Suno API",
         "key": "suno_api_key",       "ph": "Nhập Suno API key..."},
        {"id": "fal",       "icon": "🖼️",  "name": "fal.ai",
         "key": "fal_api_key",        "ph": "fal-..."},
        {"id": "xai",       "icon": "🎬", "name": "xAI (Grok Video)",
         "key": "xai_api_key",        "ph": "xai-..."},
    ]

    _api_left, _api_right = st.columns([1, 2.5], gap="large")

    # ── Left: provider cards ──────────────────────────────────────────────────
    with _api_left:
        st.markdown("**Chọn dịch vụ API**")
        for _ap in _APIPROV:
            _has   = bool(st.session_state.get(_ap["key"], "").strip())
            _issel = st.session_state.get("_api_sel", "anthropic") == _ap["id"]
            st.markdown(f"""
            <div class="apicard {'sel' if _issel else ''}">
                <div class="apicard-name">{_ap['icon']} &nbsp;{_ap['name']}</div>
                <div class="{'apicard-ok' if _has else 'apicard-miss'}">
                    {'● Đã cấu hình' if _has else '○ Chưa có key'}
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button("Chọn", key=f"selapi_{_ap['id']}", use_container_width=True,
                         type="primary" if _issel else "secondary"):
                st.session_state["_api_sel"] = _ap["id"]
                st.rerun()

    # ── Right: form ───────────────────────────────────────────────────────────
    _selid = st.session_state.get("_api_sel", "anthropic")
    _selap = next(p for p in _APIPROV if p["id"] == _selid)

    with _api_right:
        st.markdown(f'<div class="api-form-hdr">{_selap["icon"]} {_selap["name"].upper()}</div>',
                    unsafe_allow_html=True)
        st.markdown("---")

        _newkey = st.text_input(
            "API Key:",
            type="password",
            value=st.session_state.get(_selap["key"], ""),
            placeholder=_selap["ph"],
            key=f"apikey_{_selid}",
        )

        _newmodel = None

        if _selid == "anthropic":
            st.markdown("**Model đang hoạt động:**")
            st.markdown(
                "- **claude-sonnet-4-6** — Viết lyrics, album, storyboard MV\n"
                "- **claude-haiku-4-5-20251001** — Script video, gợi ý chủ đề, keywords\n"
            )
            st.caption("Hệ thống tự chọn model phù hợp cho từng tác vụ. Không cần cấu hình thêm.")

        elif _selid == "suno":
            st.markdown("**Model tạo nhạc:**")
            _sopts = ["V5_5", "V5", "V4_5PLUS", "V4_5", "V4"]
            _scur  = st.session_state.get("suno_model", "V5_5")
            _newmodel = st.radio(
                "suno_model:", _sopts,
                index=_sopts.index(_scur) if _scur in _sopts else 0,
                horizontal=True,
                key="suno_model_tab",
                label_visibility="collapsed",
            )
            st.caption("**V5_5 / V5**: thời lượng đến 8 phút  ·  **V4_5 / V4**: đến 4 phút")
            st.caption("[Xem credit tại sunoapi.org →](https://sunoapi.org/dashboard)")

        elif _selid == "fal":
            st.markdown("**Dùng cho:**")
            st.markdown(
                "- 🖼️ **Tạo ảnh thumbnail** — Nano Banana Pro (16:9, 1K/2K/4K)\n"
                "- 🎬 **Tạo video MV** — Seedance 2.0 (Text-to-Video / Image-to-Video)\n"
            )
            st.caption("[Lấy fal.ai API key →](https://fal.ai/dashboard)")
        else:
            st.markdown("**Dùng cho:**")
            st.markdown(
                "- 🎬 **Tạo video MV** — Grok Imagine Video 1.5 Preview\n"
                "- Text-to-Video, 3–10 giây, 720p, 7 aspect ratio\n"
                "- Giá: **$0.08/giây** (tự thanh toán xAI)\n"
            )
            st.caption("[Lấy xAI API key →](https://console.x.ai/)")
            if st.secrets.get("CF_ACCOUNT_ID") and st.secrets.get("CF_GATEWAY_ID"):
                st.success("✅ Cloudflare AI Gateway đã cấu hình — request đi qua Gateway.")

            st.divider()
            st.markdown("**🎛️ Cài đặt mặc định Grok Video**")
            _gp = st.session_state.get("grok_prefs", {})
            _gc1, _gc2, _gc3 = st.columns(3)
            _gp_dur = _gc1.selectbox(
                "Duration (giây)",
                GROK_DURATIONS,
                index=GROK_DURATIONS.index(str(_gp.get("duration", "5")))
                      if str(_gp.get("duration", "5")) in GROK_DURATIONS else 2,
                key="grok_pref_dur",
            )
            _gp_asp = _gc2.selectbox(
                "Aspect Ratio",
                GROK_ASPECTS,
                index=GROK_ASPECTS.index(_gp.get("aspect", "16:9"))
                      if _gp.get("aspect", "16:9") in GROK_ASPECTS else 0,
                key="grok_pref_asp",
            )
            _gp_res = _gc3.selectbox(
                "Chất lượng",
                GROK_RESOLUTIONS,
                index=GROK_RESOLUTIONS.index(_gp.get("resolution", "720p"))
                      if _gp.get("resolution", "720p") in GROK_RESOLUTIONS else 0,
                key="grok_pref_res",
            )
            _cost_preview = round(int(_gp_dur) * 0.08, 2)
            st.caption(f"💰 Giá ước tính: **${_cost_preview}** mỗi video")
            if st.button("💾 Lưu cài đặt video", key="save_grok_prefs", use_container_width=True):
                _new_prefs = {"duration": _gp_dur, "aspect": _gp_asp, "resolution": _gp_res}
                st.session_state.grok_prefs = _new_prefs
                save_video_prefs(_new_prefs)
                st.success("✅ Đã lưu cài đặt video (lưu trong trình duyệt 1 năm)!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"✅ Activate — {_selap['name']}", key=f"activate_{_selid}",
                     type="primary", use_container_width=True):
            st.session_state[_selap["key"]] = _newkey.strip()
            if _selid == "suno" and _newmodel:
                st.session_state["suno_model"] = _newmodel
            _au  = st.session_state.get("anthropic_api_key", "")
            _su  = st.session_state.get("suno_api_key", "")
            _fu  = st.session_state.get("fal_api_key", "")
            _xu  = st.session_state.get("xai_api_key", "")
            _usr = st.session_state.get("user")
            if _usr:
                try:
                    save_user_api_keys(_usr["uid"], _au, "", _su, _fu, _xu)
                    st.success(f"✅ **{_selap['name']}** đã kích hoạt và lưu vào tài khoản!")
                except Exception as _e:
                    st.warning(f"Đã lưu vào phiên. Lỗi lưu tài khoản: {_e}")
            else:
                save_api_keys(_au, "", _su, _fu, _xu)
                st.success(f"✅ **{_selap['name']}** đã kích hoạt!")

# ── Music tab placeholder ──────────────────────────────────────────────────────
with tab_music:
    if not st.session_state.get("music_result"):
        st.caption("Nhấn **🚀 Bắt đầu sản xuất** ở sidebar để tạo nhạc. Kết quả hiển thị bên dưới.")

# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------
if generate_btn:
    _gen_is_byok = _user.get("is_byok", False)
    if _gen_is_byok and not api_key:
        st.error("Gói Tự Túc (BYOK) yêu cầu Anthropic API Key của bạn. Vào **Cài đặt → API Keys** để nhập.")
    elif not topic:
        st.warning("Vui lòng nhập chủ đề bài hát / album.")
    else:
        batches = compute_batches(num_tracks)
        gcfg = GENRE_CONFIG[music_genre]
        g_bpm, g_tags = gcfg["bpm"], gcfg["style_tags"]
        try:
            if len(batches) == 1:
                with st.spinner("AI đang sản xuất…"):
                    if num_tracks == 1:
                        result = call_claude_single(api_key, topic, language, create_mv, music_genre, g_bpm, g_tags, byok_mode=_gen_is_byok)
                    else:
                        _prompt = build_album_first_batch_prompt(
                            topic, num_tracks, 1, num_tracks, language, create_mv, music_genre, g_bpm, g_tags
                        )
                        _raw, _p = generate_text(
                            system_prompt=SYSTEM_PROMPT,
                            user_prompt=_prompt,
                            max_tokens=16000,
                            user_api_key=api_key,
                            byok_mode=_gen_is_byok,
                        )
                        result = parse_json(_raw)
            else:
                with st.status(
                    f"Đang sản xuất {num_tracks} bài ({len(batches)} phần)…",
                    expanded=True,
                ) as status:
                    result = call_claude_album(api_key, topic, num_tracks, language, create_mv, status, music_genre, g_bpm, g_tags, byok_mode=_gen_is_byok)
                    status.update(
                        label=f"✅ Hoàn thành {num_tracks} bài — {len(batches)} phần",
                        state="complete",
                    )

            st.session_state.music_result = result
            st.session_state.music_meta = {
                "topic": topic, "num_tracks": num_tracks,
                "create_mv": create_mv, "music_genre": music_genre,
            }
            # Lưu lịch sử vào Firestore
            if st.session_state.user:
                try:
                    _hist_id = save_music_history(
                        st.session_state.user["uid"],
                        topic, music_genre, num_tracks, result, create_mv,
                    )
                    st.session_state.current_history_id = _hist_id
                except Exception:
                    pass
                # Trừ 1 Xu (script) sau khi tạo thành công (chỉ với bundled)
                try:
                    if not st.session_state.user.get("is_byok"):
                        _remaining = _deduct_coins(st.session_state.user["uid"], COIN_COSTS["script"],
                                                   action="script", description="Sinh kịch bản / lời nhạc")
                        st.session_state.user = {**st.session_state.user, "credits": _remaining}
                except Exception:
                    pass
            # Reset images & audio khi tạo plan mới
            st.session_state.images = {}
            st.session_state.suno_tracks   = {}
            st.session_state.suno_audio    = {}
            st.session_state.suno_failed   = {}
            st.session_state.suno_ext_keys = {}
            st.session_state.video_scripts = {}
            st.rerun()

        except json.JSONDecodeError as e:
            st.error(f"Lỗi phân tích JSON từ Claude: {e}")
        except anthropic.AuthenticationError:
            st.error("Anthropic API Key không hợp lệ.")
        except anthropic.APIError as e:
            st.error(f"Lỗi Anthropic API: {e}")
        except Exception as e:
            st.error(f"Lỗi không xác định: {e}")

# ---------------------------------------------------------------------------
# Trending Keywords tool (độc lập với music generation)
# ---------------------------------------------------------------------------
with st.expander("📈 Trending YouTube Keywords", expanded=False):
    kc1, kc2 = st.columns(2)
    kw_genre = kc1.selectbox("Thể loại:", GENRE_NAMES,
                              index=GENRE_NAMES.index(st.session_state.get("music_genre", GENRE_NAMES[0]))
                              if st.session_state.get("music_genre") in GENRE_NAMES else 0,
                              key="kw_genre")
    kw_lang  = kc2.selectbox("Thị trường:", ["Tiếng Việt", "English", "Japanese"],
                              index=["Tiếng Việt", "English", "Japanese"].index(
                                  st.session_state.get("language_select", "Tiếng Việt"))
                              if st.session_state.get("language_select") in ["Tiếng Việt", "English", "Japanese"] else 0,
                              key="kw_lang")
    kw_niche = st.text_input("Niche / chủ đề thêm (tùy chọn):",
                             placeholder="Ví dụ: nhạc thiếu nhi ru ngủ, nhạc gym 2026…",
                             key="kw_niche")

    if st.button("🔍 Tra cứu Trending Keywords", use_container_width=True, key="kw_search_btn"):
        _kw_api = st.session_state.get("anthropic_api_key", "").strip()
        with st.spinner("AI đang phân tích trending keywords…"):
            try:
                _kw_prompt = build_keyword_prompt(
                    kw_genre, kw_lang, kw_niche, date.today().strftime("%B %d, %Y")
                )
                _kw_raw, _kw_p = generate_text(
                    system_prompt="",
                    user_prompt=_kw_prompt,
                    max_tokens=1024,
                    user_api_key=_kw_api,
                    claude_model="claude-haiku-4-5-20251001",
                )
                _kw_raw = _kw_raw.strip()
                if not _kw_raw:
                    st.error("AI trả về phản hồi rỗng. Thử lại.")
                else:
                    st.session_state.keyword_result = parse_json(_kw_raw)
            except Exception as _kw_e:
                st.error(f"Lỗi tra cứu: {_kw_e}")

    kw = st.session_state.keyword_result
    if kw:
        kt1, kt2, kt3, kt4 = st.tabs(["🔥 Hot Keywords", "📌 Long-tail", "🏷️ Hashtags", "📝 Tiêu đề mẫu"])

        with kt1:
            hot = kw.get("hot_keywords", [])
            st.caption("Tích chọn từ khóa muốn dùng rồi nhấn **Gợi ý chủ đề**:")
            cols = st.columns(3)
            for idx, kw_item in enumerate(hot):
                cols[idx % 3].checkbox(kw_item, key=f"kw_chk_{idx}")

            tips = kw.get("tips", [])
            if tips:
                st.divider()
                st.markdown("**💡 SEO Tips:**")
                for tip in tips:
                    st.markdown(f"- {tip}")

            st.divider()
            _selected_kws = [
                kw.get("hot_keywords", [])[i]
                for i in range(len(kw.get("hot_keywords", [])))
                if st.session_state.get(f"kw_chk_{i}", False)
            ]
            _topic_api = st.session_state.get("anthropic_api_key", "").strip()
            _suggest_disabled = not _selected_kws
            _suggest_label = (
                f"💡 Gợi ý 5 chủ đề hot từ {len(_selected_kws)} từ khóa đã chọn"
                if _selected_kws else "💡 Gợi ý 5 chủ đề hot (chọn ít nhất 1 từ khóa)"
            )
            if st.button(_suggest_label, key="kw_suggest_btn",
                         use_container_width=True, disabled=_suggest_disabled):
                with st.spinner("AI đang phân tích chủ đề tiềm năng…"):
                    try:
                        _tp_prompt = build_topic_suggestion_prompt(
                            _selected_kws, kw_genre, kw_lang
                        )
                        _tp_raw, _tp_p = generate_text(
                            system_prompt="",
                            user_prompt=_tp_prompt,
                            max_tokens=1024,
                            user_api_key=_topic_api,
                            claude_model="claude-haiku-4-5-20251001",
                        )
                        _tp_raw = _tp_raw.strip()
                        _topics = parse_json(_tp_raw)
                        _topics.sort(key=lambda x: x.get("score", 0), reverse=True)
                        st.session_state.kw_topic_results = _topics
                    except Exception as _tp_e:
                        st.error(f"Lỗi gợi ý chủ đề: {_tp_e}")

            # Hiển thị kết quả chủ đề
            if st.session_state.kw_topic_results:
                st.markdown("#### 🎯 Chủ đề tiềm năng (cao → thấp)")
                for _tidx, _tp in enumerate(st.session_state.kw_topic_results):
                    _score = _tp.get("score", 0)
                    _bar   = "🟩" * _score + "⬜" * (10 - _score)
                    _tc1, _tc2 = st.columns([0.85, 0.15])
                    _tc1.markdown(f"**{_tp.get('topic','')}**  \n_{_tp.get('reason','')}_")
                    _tc2.markdown(f"**{_score}/10**  \n{_bar}")
                    # Nút điền thẳng vào ô chủ đề
                    if st.button(f"➕ Dùng chủ đề này", key=f"use_topic_{_tidx}",
                                 use_container_width=True):
                        st.session_state.pending_topic = _tp.get("topic", "")
                        st.rerun()
                    st.divider()

        with kt2:
            for phrase in kw.get("long_tail", []):
                st.markdown(f"- `{phrase}`")

        with kt3:
            tags = kw.get("hashtags", [])
            st.markdown(" ".join(f"`{t}`" for t in tags))
            if tags:
                st.code(" ".join(tags), language="text")

        with kt4:
            for tpl in kw.get("title_templates", []):
                st.markdown(f"- {tpl}")

        if st.button("🗑️ Xóa kết quả", key="kw_clear_btn"):
            st.session_state.keyword_result = None
            st.session_state.kw_topic_results = []
            st.rerun()


if st.session_state.music_result:
    result = st.session_state.music_result
    meta = st.session_state.music_meta
    _proj_label = meta.get("project_name") or result.get("title") or meta["topic"]
    _topic_suffix = f"  ·  chủ đề: _{meta['topic']}_" if _proj_label != meta["topic"] else ""
    st.success(f"✅ Project: **{_proj_label}**{_topic_suffix}")
    render_results(result, meta["num_tracks"], meta["topic"], meta["create_mv"], meta.get("music_genre", "Thiếu Nhi (Nursery)"))

    st.divider()
    st.download_button(
        label="⬇️ Tải xuống JSON đầy đủ",
        data=json.dumps(result, ensure_ascii=False, indent=2),
        file_name=f"{meta['topic'][:30].replace(' ', '_')}_production.json",
        mime="application/json",
        key="dl_json",
    )
