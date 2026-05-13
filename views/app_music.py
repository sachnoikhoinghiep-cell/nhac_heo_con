import streamlit as st
import anthropic
from auth import (
    show_auth_ui, verify_and_load_user,
    activate_plan, save_music_history, get_music_history, sign_out,
    save_api_keys, load_api_keys,
)
import requests
import json
import io
import os
import time
from datetime import date
from prompts import (
    SYSTEM_PROMPT,
    build_single_prompt,
    build_album_first_batch_prompt,
    build_album_continuation_prompt,
)

# ---------------------------------------------------------------------------
# Auth gate — Google Sign-In + Firebase
# ---------------------------------------------------------------------------
PLANS = {
    "Ngày":  {"price": "0.99",  "desc": "Sử dụng trong 24h",      "plan_id": "P-48U172572M537580PNICAPDY"},
    "Tuần":  {"price": "4.99",  "desc": "Tiết kiệm 30%",           "plan_id": "P-12862804M08177324NICAPSI"},
    "Tháng": {"price": "14.99", "desc": "Phổ biến nhất",           "plan_id": "P-5AV04190G6017082ENICAOVA"},
    "Năm":   {"price": "99.99", "desc": "Gói chuyên nghiệp (VIP)", "plan_id": "P-055284903H354632FNICAN7I"},
}
PLAN_ID_TO_NAME = {v["plan_id"]: k for k, v in PLANS.items()}

def _paypal_client_id() -> str:
    try:    return st.secrets["PAYPAL_CLIENT_ID"]
    except Exception: return os.environ.get("PAYPAL_CLIENT_ID", "")

def _paypal_secret() -> str:
    try:    return st.secrets["PAYPAL_SECRET"]
    except Exception: return os.environ.get("PAYPAL_SECRET", "")

def _app_url() -> str:
    try:    return st.secrets["REDIRECT_URI"].rstrip("/")
    except Exception: return os.environ.get("REDIRECT_URI", "http://localhost:8501")

for _k, _v in {
    "user": None,
    "paypal_approval_url": None,
    "paypal_selected_plan": None,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Chưa đăng nhập → trang yêu cầu đăng nhập
if not st.session_state.user:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem 1rem;">
        <div style="font-size:3.5rem;">🎵</div>
        <h2>Đăng nhập để tạo nhạc</h2>
        <p style="color:rgba(255,255,255,0.55); max-width:480px; margin:0 auto 2rem;">
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

# Chưa thanh toán → trang chọn gói
if not _user["is_paid"]:
    st.markdown(f"""
    <div style="text-align:center; padding: 2rem 1rem 1rem;">
        <div style="font-size:3rem;">🎟️</div>
        <h2>Chọn gói để bắt đầu tạo nhạc</h2>
        <p style="color:rgba(255,255,255,0.55);">
            Xin chào <b>{_user['name']}</b>! Bạn đã đăng nhập thành công.<br>
            Chọn gói dịch vụ phù hợp để mở khoá toàn bộ tính năng AI Music Producer.
        </p>
    </div>
    """, unsafe_allow_html=True)

    selected_plan = st.selectbox("Chọn gói dịch vụ:", list(PLANS.keys()), key="selected_plan_key")
    plan_info     = PLANS[selected_plan]
    st.markdown(f"**Giá:** ${plan_info['price']} USD — {plan_info['desc']}")
    st.divider()

    if st.session_state.paypal_selected_plan != selected_plan:
        st.session_state.paypal_approval_url  = None
        st.session_state.paypal_selected_plan = selected_plan

    if st.session_state.paypal_approval_url:
        st.info(f"Đã tạo đơn đăng ký — Gói **{selected_plan}** — ${plan_info['price']} USD/kỳ")
        st.link_button(
            "💳 Tiếp tục đăng ký trên PayPal",
            st.session_state.paypal_approval_url,
            type="primary",
            use_container_width=True,
        )
        if st.button("🔄 Tạo lại đơn mới", use_container_width=True):
            st.session_state.paypal_approval_url = None
            st.rerun()
    else:
        if st.button("💳 Đăng ký qua PayPal", type="primary", use_container_width=True):
            with st.spinner("Đang tạo đơn đăng ký PayPal…"):
                try:
                    from paypal import create_subscription as _pp_create_sub
                    _app_u = _app_url()
                    _, _approval = _pp_create_sub(
                        _paypal_client_id(), _paypal_secret(),
                        plan_info["plan_id"],
                        _app_u, _app_u,
                    )
                    st.session_state.paypal_approval_url  = _approval
                    st.session_state.paypal_selected_plan = selected_plan
                    st.rerun()
                except Exception as _e:
                    st.error(f"Lỗi tạo đơn đăng ký PayPal: {_e}")

    st.warning("Vui lòng hoàn tất thanh toán để sử dụng tính năng tạo nhạc AI.")
    st.stop()

st.success(f"✅ Xin chào **{_user['name']}** — Gói **{_user['plan']}** đang hoạt động")

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
for _k, _v in {
    "suggested_topics": [],
    "topic_input": "",
    "pending_topic": None,
    "google_key_idx": 0,
    "music_result": None,
    "music_meta": {},
    "images": {},
    "suno_tracks": {},
    "suno_audio": {},
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Load API keys từ cookie (chỉ lần đầu)
if "api_keys_loaded" not in st.session_state:
    _saved = load_api_keys()
    if _saved.get("anthropic"):
        st.session_state.anthropic_api_key = _saved["anthropic"]
    if _saved.get("google"):
        st.session_state.google_api_keys_raw = _saved["google"]
    if _saved.get("suno"):
        st.session_state.suno_api_key = _saved["suno"]
    st.session_state.api_keys_loaded = True

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
# Google API key rotation (Nano Banana 2)
# ---------------------------------------------------------------------------
def get_google_keys() -> list:
    raw = st.session_state.get("google_api_keys_raw", "")
    return [k.strip() for k in raw.splitlines() if k.strip()]

def next_google_key() -> str:
    keys = get_google_keys()
    if not keys:
        raise ValueError("Chưa nhập Google API Key.")
    idx = st.session_state.google_key_idx % len(keys)
    st.session_state.google_key_idx = idx + 1
    return keys[idx]

def generate_image(prompt: str) -> bytes:
    from google import genai
    keys = get_google_keys()
    if not keys:
        raise ValueError("Chưa nhập Google API Key.")

    full_prompt = (
        f"{prompt}. "
        "16:9 widescreen landscape format, YouTube-ready. "
        "Vibrant colors, cinematic lighting, 8K resolution."
    )

    # Thử lần lượt tất cả key cho đến khi 1 key thành công
    last_error = None
    start_idx = st.session_state.google_key_idx % len(keys)

    for offset in range(len(keys)):
        idx = (start_idx + offset) % len(keys)
        api_key = keys[idx]
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[full_prompt],
            )
            for part in response.parts:
                if part.inline_data is not None:
                    # Cập nhật idx để lần sau bắt đầu từ key tiếp theo
                    st.session_state.google_key_idx = idx + 1
                    return part.inline_data.data
            raise ValueError("Model không trả về ảnh.")

        except Exception as e:
            err_str = str(e)
            # Chỉ xoay vòng sang key khác nếu là lỗi quota/rate limit
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                last_error = f"Key #{idx + 1} hết quota: {err_str[:120]}"
                continue  # thử key tiếp theo
            # Lỗi khác (400, 401...) → báo ngay, không thử tiếp
            raise

    raise ValueError(
        f"Tất cả {len(keys)} Google API key đều hết quota.\n"
        f"Lỗi cuối: {last_error}"
    )

def image_widget(prompt: str, img_key: str):
    st.code(prompt, language="text")
    has_img = img_key in st.session_state.images
    if st.button("🔄 Tạo lại ảnh" if has_img else "🎨 Tạo ảnh (16:9)", key=f"btn_{img_key}"):
        if not get_google_keys():
            st.warning("Nhập ít nhất 1 Google API Key ở sidebar.")
        else:
            with st.spinner("Nano Banana 2 đang tạo ảnh 16:9..."):
                try:
                    st.session_state.images[img_key] = generate_image(prompt)
                except Exception as e:
                    st.error(f"Lỗi tạo ảnh: {e}")
    if img_key in st.session_state.images:
        st.image(st.session_state.images[img_key], use_container_width=True)
        st.download_button(
            "⬇️ Tải ảnh PNG",
            data=st.session_state.images[img_key],
            file_name=f"{img_key}.png",
            mime="image/png",
            key=f"dl_{img_key}",
        )

# ---------------------------------------------------------------------------
# Suno API integration
# ---------------------------------------------------------------------------
SUNO_BASE = "https://api.sunoapi.org/api/v1"
SUNO_FAIL_STATUS = {"CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "SENSITIVE_WORD_ERROR", "CALLBACK_EXCEPTION"}
MAX_SUNO_WORKERS = 15   # giới hạn thực tế qua test: 15 luồng song song

def suno_generate_task(api_key: str, title: str, style: str, lyrics: str, model: str) -> str:
    """Submit generation job, return taskId."""
    # V4 / V4_5ALL max title 80 chars; others 100 chars
    title_max = 80 if model in ("V4", "V4_5ALL") else 100
    # style fallback nếu Claude trả về rỗng
    safe_style = (style.strip() or "cheerful children's music, upbeat, catchy melody, fun")[:1000]

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
        "prompt": lyrics[:5000],
        "callBackUrl": "https://httpbin.org/post",  # bắt buộc; dùng polling nên không cần webhook thật
    }

    resp = requests.post(f"{SUNO_BASE}/generate", json=payload, headers=headers, timeout=30)

    # Hiển thị lỗi chi tiết thay vì raise_for_status mù
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
            raise ValueError(f"Suno thất bại ({status}): {data.get('errorMessage', status)}")

        time.sleep(8)

    raise TimeoutError("Suno không hoàn thành sau 6 phút.")


def run_suno_generation(title: str, style: str, lyrics: str, track_key: str):
    suno_key = st.session_state.get("suno_api_key", "").strip()
    model    = st.session_state.get("suno_model", "V4_5")

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

    try:
        info_slot.info(f"📤 Gửi yêu cầu tới Suno: **{title[:60]}**")
        task_id = suno_generate_task(suno_key, title, style, lyrics, model)
        info_slot.info(f"🆔 Task: `{task_id}` — chờ Suno sinh nhạc (2–3 phút)…")

        # Hiển thị thanh tiến trình + preview streaming
        bar = bar_slot.progress(0.0, text="⏳ Đang khởi động…")
        suno_list = suno_poll_with_ui(suno_key, task_id, bar, preview_slot)

        # Hoàn thành — lưu metadata
        st.session_state.suno_tracks[track_key] = suno_list
        bar_slot.progress(1.0, text="✅ 100% — Đang tải MP3 full track…")

        # Tải MP3 full cho cả 2 version
        for vi, track in enumerate(suno_list):
            url = track.get("audioUrl", "")
            if url:
                st.session_state.suno_audio[f"{track_key}_v{vi}"] = _fetch_audio_bytes(url)

        durations = " / ".join(fmt_duration(t.get("duration")) for t in suno_list)
        info_slot.success(f"✅ Hoàn thành: **{title}** — Duration: {durations}")
        bar_slot.empty()
        preview_slot.empty()
        dl_slot.empty()
        st.rerun()

    except Exception as e:
        bar_slot.empty()
        preview_slot.empty()
        info_slot.error(f"❌ {e}")


def generate_all_tracks(tracks: list):
    """
    Pha 1: Submit tất cả tasks song song qua ThreadPoolExecutor (không update UI từ thread).
    Pha 2: Poll toàn bộ tasks từ main thread mỗi 8s — cập nhật progress + log an toàn.
    Pha 3: Download MP3 song song sau khi SUCCESS.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed

    suno_key = st.session_state.get("suno_api_key", "").strip()
    model    = st.session_state.get("suno_model", "V4_5")
    if not suno_key:
        st.warning("Nhập Suno API Key ở sidebar.")
        return

    n     = len(tracks)
    items = [(t.get("title", f"Track {i+1}"), t.get("music_style",""), t.get("lyrics",""), f"track_{i+1}")
             for i, t in enumerate(tracks)]

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
    with ThreadPoolExecutor(max_workers=min(n, MAX_SUNO_WORKERS)) as ex:
        futs = {ex.submit(_submit, it): it for it in items}
        for f in _as_completed(futs):
            tk, tid, err = f.result()
            if tid:
                task_map[tk]  = tid
                statuses[tk]  = f"submitted {tid[:10]}"
                submit_ok    += 1
            else:
                statuses[tk] = f"FAIL submit: {err[:50]}"
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
                    dur = " / ".join(fmt_duration(t.get("duration")) for t in suno_list)
                    statuses[tk] = f"done ✅ {dur}"
                    completed.add(tk)
                elif status in SUNO_FAIL_STATUS:
                    statuses[tk] = f"FAIL {data.get('errorMessage', status)[:50]}"
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
        with ThreadPoolExecutor(max_workers=min(len(suno_data_map), MAX_SUNO_WORKERS)) as ex:
            dl_results = list(ex.map(_download, suno_data_map.items()))
        # Ghi vào session_state từ main thread (thread-safe)
        for d in dl_results:
            st.session_state.suno_audio.update(d)

    bar.progress(1.0, text=f"✅ Xong {len(completed)}/{n} tracks!")
    _render_log()
    st.rerun()


def music_widget(title: str, style: str, lyrics: str, track_key: str):
    """Per-track Suno UI: generate button → progress → preview → full player + download."""
    tracks = st.session_state.suno_tracks.get(track_key)

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
                    safe = title[:40].replace(" ", "_").replace("/", "-")
                    st.download_button(
                        f"⬇️ Tải MP3 – Version {'AB'[vi]}",
                        data=audio_bytes,
                        file_name=f"{safe}_v{'AB'[vi]}.mp3",
                        mime="audio/mpeg",
                        key=f"dl_mp3_{track_key}_v{vi}",
                    )

    btn_label = "🔄 Tạo lại Suno" if tracks else "🎵 Tạo nhạc Suno"
    if st.button(btn_label, key=f"gen_suno_{track_key}"):
        run_suno_generation(title, style, lyrics, track_key)

# ---------------------------------------------------------------------------
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
    client = anthropic.Anthropic(api_key=api_key)
    today = date.today().strftime("%B %d, %Y")
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"You are a YouTube content strategist for a children's music channel.\n"
                f"Today is {today}. Suggest 5 FRESH and DIFFERENT trending topic ideas for children's music videos.\n"
                f"Output language: {language}\n"
                f"Consider: current season, upcoming holidays, popular animals, vehicles, food, nature, fairy tales.\n"
                f"Each topic must be specific and creative, not generic.\n"
                f"Return ONLY a JSON array of 5 short topic strings (5-10 words each), no explanation.\n"
                f'Example: ["Little duck in the rainy day", "Fire truck saves the forest", ...]'
            ),
        }],
    )
    raw = message.content[0].text.strip()
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

    st.text_input(
        "Anthropic API Key:",
        type="password",
        key="anthropic_api_key",
        placeholder="sk-ant-...",
    )

    st.subheader("🖼️ Google API Keys – Nano Banana 2")
    st.text_area(
        "Nhập mỗi key một dòng (xoay vòng credit):",
        key="google_api_keys_raw",
        height=90,
        placeholder="AIzaSy...\nAIzaSy...",
    )
    _gkeys = get_google_keys()
    if _gkeys:
        _active = (st.session_state.google_key_idx % len(_gkeys)) + 1
        st.caption(f"✅ {len(_gkeys)} key | Key #{_active} tiếp theo")

    st.subheader("🎵 Suno Music Generation")
    st.text_input(
        "Suno API Key:",
        type="password",
        key="suno_api_key",
        placeholder="Suno API key...",
    )
    st.selectbox(
        "Suno Model:",
        ["V4_5", "V4_5PLUS", "V5", "V4", "V5_5"],
        key="suno_model",
        help="V4_5/V5: up to 8 phút | V4: up to 4 phút",
    )

    if st.button("💾 Lưu API Keys", use_container_width=True):
        save_api_keys(
            st.session_state.get("anthropic_api_key", ""),
            st.session_state.get("google_api_keys_raw", ""),
            st.session_state.get("suno_api_key", ""),
        )
        st.success("Đã lưu! Lần sau vào app sẽ tự điền.")

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
        if not api_key:
            st.warning("Nhập Anthropic API Key để dùng tính năng gợi ý.")
        else:
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

    num_tracks = st.number_input("Số lượng bài cần tạo:", min_value=1, max_value=20, value=10)
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

    st.subheader("🎨 Tùy chọn Visual")
    create_mv = st.checkbox("Tạo kịch bản MV (Video 2)")

    st.divider()
    if st.session_state.user:
        with st.expander("🕘 Lịch sử tạo nhạc (20 gần nhất)", expanded=False):
            try:
                history = get_music_history(st.session_state.user["uid"])
                if history:
                    for h in history:
                        ts = h.get("created_at")
                        ts_str = ts.strftime("%d/%m %H:%M") if ts else ""
                        st.caption(f"🎵 {h.get('topic','')} — {h.get('genre','')} — {h.get('num_tracks','')} bài  `{ts_str}`")
                else:
                    st.info("Chưa có lịch sử tạo nhạc.")
            except Exception:
                st.info("Không thể tải lịch sử.")
    st.divider()
    generate_btn = st.button("🚀 Bắt đầu sản xuất", use_container_width=True, type="primary")

# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------
def parse_json(raw: str) -> dict:
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(_fix_control_chars(raw))

# ---------------------------------------------------------------------------
# Claude API calls
# ---------------------------------------------------------------------------
def call_claude_single(api_key: str, topic: str, language: str, create_mv: bool,
                       genre: str = "Thiếu Nhi (Nursery)", bpm: str = "", style_tags: str = "") -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_single_prompt(topic, language, create_mv, genre, bpm, style_tags)}],
    )
    return parse_json(msg.content[0].text)

def call_claude_album(api_key, topic, num_tracks, language, create_mv, status_ctx,
                      genre: str = "Thiếu Nhi (Nursery)", bpm: str = "", style_tags: str = "") -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    batches = compute_batches(num_tracks)
    all_results, album_title = [], None

    for i, (start, end) in enumerate(batches):
        status_ctx.write(f"⏳ Phần {i+1}/{len(batches)}: Tracks {start}–{end}…")
        prompt = (
            build_album_first_batch_prompt(topic, num_tracks, start, end, language, create_mv, genre, bpm, style_tags)
            if i == 0
            else build_album_continuation_prompt(topic, album_title, num_tracks, start, end, language, genre, bpm, style_tags)
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        batch_data = parse_json(msg.content[0].text)
        all_results.append(batch_data)
        if i == 0:
            album_title = batch_data.get("title", topic)
            status_ctx.write(f"✅ Phần 1 xong — Album: **{album_title}**")
        else:
            status_ctx.write(f"✅ Phần {i+1} xong")

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
                col_hdr, col_all = st.columns([2, 1])
                col_hdr.markdown(f"**{len(tracks)} tracks — Click để xem lyrics & tạo nhạc:**")
                if col_all.button("🚀 Tạo tất cả nhạc", key="gen_all", type="primary", use_container_width=True):
                    generate_all_tracks([t for t in tracks if isinstance(t, dict)])
                for i, t in enumerate(tracks, 1):
                    if isinstance(t, dict):
                        label = f"🎵 Track {i}: {t.get('title', f'Track {i}')}"
                        with st.expander(label, expanded=False):
                            style = t.get("music_style", "")
                            lyrics = t.get("lyrics", "")
                            if style:
                                st.info(f"**Style / Tags:** {style}")
                            if lyrics:
                                with st.expander("📝 Lyrics", expanded=False):
                                    st.write(lyrics)
                            st.divider()
                            music_widget(t.get("title", f"Track {i}"), style, lyrics, f"track_{i}")
                    else:
                        st.markdown(f"{i}. {t}")

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
                        st.markdown(f"**Scene {i}:** {scene}")
                else:
                    st.info("Không có dữ liệu cảnh.")

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
# Main logic
# ---------------------------------------------------------------------------
if generate_btn:
    if not api_key:
        st.error("Vui lòng nhập Anthropic API Key ở sidebar.")
    elif not topic:
        st.warning("Vui lòng nhập chủ đề bài hát / album.")
    else:
        batches = compute_batches(num_tracks)
        gcfg = GENRE_CONFIG[music_genre]
        g_bpm, g_tags = gcfg["bpm"], gcfg["style_tags"]
        try:
            if len(batches) == 1:
                with st.spinner("Claude đang sản xuất…"):
                    if num_tracks == 1:
                        result = call_claude_single(api_key, topic, language, create_mv, music_genre, g_bpm, g_tags)
                    else:
                        client = anthropic.Anthropic(api_key=api_key)
                        prompt = build_album_first_batch_prompt(
                            topic, num_tracks, 1, num_tracks, language, create_mv, music_genre, g_bpm, g_tags
                        )
                        msg = client.messages.create(
                            model="claude-sonnet-4-6", max_tokens=8192,
                            system=SYSTEM_PROMPT,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        result = parse_json(msg.content[0].text)
            else:
                with st.status(
                    f"Đang sản xuất {num_tracks} bài ({len(batches)} phần)…",
                    expanded=True,
                ) as status:
                    result = call_claude_album(api_key, topic, num_tracks, language, create_mv, status, music_genre, g_bpm, g_tags)
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
                    save_music_history(
                        st.session_state.user["uid"],
                        topic, music_genre, num_tracks, result,
                    )
                except Exception:
                    pass
            # Reset images & audio khi tạo plan mới
            st.session_state.images = {}
            st.session_state.suno_tracks = {}
            st.session_state.suno_audio = {}

        except json.JSONDecodeError as e:
            st.error(f"Lỗi phân tích JSON từ Claude: {e}")
        except anthropic.AuthenticationError:
            st.error("Anthropic API Key không hợp lệ.")
        except anthropic.APIError as e:
            st.error(f"Lỗi Anthropic API: {e}")

if st.session_state.music_result:
    result = st.session_state.music_result
    meta = st.session_state.music_meta
    st.success(f"✅ Đã hoàn thành kế hoạch sản xuất cho: **{meta['topic']}**")
    render_results(result, meta["num_tracks"], meta["topic"], meta["create_mv"], meta.get("music_genre", "Thiếu Nhi (Nursery)"))

    st.divider()
    st.download_button(
        label="⬇️ Tải xuống JSON đầy đủ",
        data=json.dumps(result, ensure_ascii=False, indent=2),
        file_name=f"{meta['topic'][:30].replace(' ', '_')}_production.json",
        mime="application/json",
        key="dl_json",
    )
