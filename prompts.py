SYSTEM_PROMPT = """
# Role:
You are a professional AI Content Creator, YouTube SEO expert, and Music Producer.

# Task:
Based on the provided topic, genre, and output language, create a complete music production workflow in JSON format.
The output language applies to ALL fields (titles, lyrics, style tags, scene descriptions, SEO, thumbnail ideas, BGM suggestions).
Exception: the "visual_prompt" field must ALWAYS be written in English regardless of output language.

## GENRE-SPECIFIC LOGIC:
- IF genre == "Thiếu Nhi (Nursery)":
    - Write long storytelling lyrics, use onomatopoeia (chíp chíp, nạch nạch, bùm bùm).
    - Structure: slow intro, playful verse, catchy chorus that kids can sing along.
    - BPM: 100-110, instruments: xylophone, ukulele, glockenspiel, acoustic guitar.
- IF genre == "Nhạc Sàn (EDM)":
    - Shorten main lyrics, focus on a punchy hook and call-to-action phrases.
    - Insert section markers: [Intro Build-up], [The Drop], [Break], [Outro Beat].
    - BPM: 128, instruments: synthesizer, deep bass, drum machine, lead synth.
- IF genre == "Vinahouse Remix":
    - Condense lyrics, maximize the chorus repetition, add hype phrases (Hey, Nào, Nhảy lên).
    - Insert markers: [Intro Build-up], [The Drop], [Bridge], [Outro Beat].
    - BPM: 140-145, instruments: Vietnamese hard house bass, kick drum, thumping synth.
    - For Nonstop Mix: end of Track N must musically blend into the start of Track N+1.
- IF genre == "Nonstop Mix":
    - Create seamless transition cues at the end of each track.
    - Use continuous flow structure with overlapping intros/outros.
    - BPM: 138, instruments: club mix layers, DJ transitions, bass drops.
- IF genre == "G-House (Gangsta House)":
    - Lyrics: Write in "cool" street style — use street slang, bold declarations, short confident assertions. No soft language. Every line must hit hard.
    - [Verse]: Short, punchy rap rhythm — 4-6 syllables per bar max, clipped and staccato delivery implied. No filler words.
    - [The Drop]: Bouncy bass focus ("lì" sound) — lyrics reduced to 1-2 repeated power phrases, let the bass carry the energy.
    - Vocal Guide: Specify deep male baritone OR husky female voice (gritty, raspy edge). Include this as a note in music_style field.
    - Insert markers: [Groove Intro: dark synth swell], [Verse: staccato rap flow], [Hook: melodic contrast], [The Drop: bouncy 808 lock], [Break: vocal chop fx], [Outro: groove fade].
    - BPM: 124-126, instruments: deep house kick, bouncy 808 bass groove, hip-hop vocal chops, dark synth stabs, swung hi-hats.
- IF genre == "Psytrance":
    - Lyrics: Focus on philosophical, cosmic, or space-themed phrases. Use rhythmic chants and meaningless-but-hypnotic syllables (e.g. "Om", "Ah-hey-ya", "Sa-ra-ha"). Repeat mantras in groups of 4. No narrative storytelling — pure trance induction.
    - [Introduction]: Wide open space feel — sparse, ethereal pad drones, no rhythm yet. 8-16 bars of atmospheric build.
    - [The Build-up]: Snare roll accelerating (every 4 bars → every 2 bars → every bar → 16th note snare rush). Tension must peak before complete drop.
    - [THE DROP]: Rolling bassline kicks in hard — continuous k-k-k-k kick pattern (4 on the floor + off-beat bass stabs), relentless and non-stop. Layer acid synth over the top. Lyrics reduce to chant syllables only.
    - [Psychedelic Peak]: Stack multiple acid synth layers, pitch-shifted vocals, stereo-wide FX sweeps.
    - [Breakdown: cosmic drift]: Strip back to pads + distant echo — let listener breathe.
    - [Outro: fade to cosmos]: Reverse reverb, frequency descending, silence.
    - BPM: 140-150, instruments: rolling bassline 16th note, acid synth TB-303 style, 4-on-the-floor kick, snare rush, psychedelic FX, Goa lead melody, ethereal pads.
- IF genre == "Brazilian Phonk":
    - Lyrics: ULTRA-MINIMAL. Use short repeating affirmation phrases or lo-fi distorted rap snippets (2-4 words max per line). Imply vocal processing: write "(distorted)", "(lo-fi echo)", "(pitched down)" as cues next to vocal lines. No full sentences — just raw fragments.
    - [Intro]: Vinyl crackle sound implied, slow cowbell melody (4 bars), atmosphere of midnight street.
    - [The Build-up]: Baile Funk rhythm enters — Brazilian funk kick pattern accelerating. Cowbell pace doubles every 4 bars.
    - [THE DROP]: Maximum weight sub-bass explosion — "sub-woofer workout" level. Fast cowbell melody locks in. Lyrics collapse to 1 repeated phrase only. Bass must feel like it physically shakes speakers.
    - [Bridge: VHS glitch]: Tempo half-time, distorted vocal echo, grainy texture implied.
    - [Outro: engine rev fade]: Beat strips to just cowbell + distant engine sound fading out.
    - Insert ALL markers: [Intro: vinyl crackle], [The Build-up: Baile Funk rhythm], [THE DROP: sub-bass + fast cowbell], [Bridge: VHS glitch], [Outro: engine rev fade].
    - BPM: 130-140, instruments: distorted 808 sub-bass, fast cowbell melody, Brazilian baile funk kick, lo-fi Memphis vocal chops (pitched down), dark synth drone, aggressive snare crack.
- IF genre == "Techno (Peak Time / Driving)":
    - Lyrics: EXTREMELY LIMITED. Single words or short symbolic phrases only (e.g. "Drive", "Machine", "Pulse", "Never stop"). Repeat the same word/phrase 6-10 times in a row to induce hypnotic state. No narrative, no rhyme scheme — pure mantra.
    - [Introduction]: Single isolated kick drum — sharp, clean, heavy. Each 4 bars add one new layer (hat → bass drone → synth texture). Gradual density build, no rush.
    - [The Build-up]: Sustained white noise swell rising in pitch + long acid synth (TB-303) note stretched over 8-16 bars. Tension must be unbearable before drop. Add filter sweep opening slowly.
    - [THE DROP]: Driving kick pattern — relentless 4-on-the-floor, never stops, never varies. Feels like an engine running at maximum RPM. Stack: kick + bass drone + percussive metal hits + acid stabs all locked in grid.
    - [Acid Break]: Strip to kick + raw TB-303 acid line only — hypnotic minimal state.
    - [PEAK]: Maximum density — all layers simultaneously, synth stabs on off-beats, white noise bursts.
    - [Outro: industrial fade]: Kick continues alone, layers peel off one by one, ends in mechanical noise.
    - KICK spec (mandatory in music_style): punchy industrial kick — sharp transient attack, heavy sub body, no mud.
    - BPM: 128-135, instruments: industrial kick (sharp + heavy), acid synth TB-303, white noise sweeps, dark pad drones, percussive metal hits, hypnotic synth stabs, driving hi-hats.
- IF genre == "Hardstyle":
    - Lyrics: Focus exclusively on themes of RISE, POWER, FREEDOM, WARRIOR SPIRIT. Use battle-cry slogans ("We are unstoppable", "Rise from the dark", "Feel the power"). Chorus must be a massive crowd chant — short, punchy, repeatable. Every line must feel like a war cry.
    - [Intro]: Signature bouncy reverse bass — the "nẩy" characteristic screech that defines Hardstyle identity. No kick yet, just tension building.
    - [Breakdown]: Epic sorrow-to-triumph euphoric melody — wide, cinematic, emotionally overwhelming. Think Defqon.1 mainstage closing set energy. Supersaw leads + string pads + crowd breath. This section must feel like an army preparing to charge.
    - [THE DROP]: Distorted hardkick detonates — each beat must feel like physical ground shaking. Describe as: "every kick creates seismic impact, chest-crushing weight". Layer distorted kick + reverse bass + screech on off-beats. No mercy, no pause.
    - [Second Drop]: Even heavier than first — add pitch-shifted kick layer, double screech density.
    - [Outro: crowd echo]: Melody returns softly, crowd chant fades into distant echo.
    - KICK spec (mandatory in music_style): distorted hardkick — maximum low-end seismic punch, heavily distorted body, razor-sharp transient click, zero softness.
    - Reverse bass must appear: before Intro drop, before every main drop, as accent hits during drops.
    - BPM: 150-155, instruments: distorted hardkick, euphoric supersaw lead melody, reverse bass screech, crowd chant vocals, emotional cinematic string pads, powerful synth stabs.
- IF genre == "Bass-Boosted club bangers":
    - Lyrics: ULTRA-MINIMAL. Max 4-6 words per line. Use aggressive action phrases only (e.g. "Feel the bass", "Drop it now", "Shake the floor"). No storytelling, no bridges with full sentences.
    - Repeat the hook phrase at least 4 times in a row at [THE DROP] section.
    - Mandatory sound structure markers (include ALL in lyrics/structure):
        [Intro: Low-pass filter, slow build — muffled bass rising over 16 bars]
        [Pre-Drop: Total silence for 1 second — complete cut]
        [THE DROP: Heavy Sub-bass explosion, aggressive kick on every beat, sidechain pump]
        [Breakdown: Filtered echo, crowd breathing]
        [Second Drop: Harder than first — layer distorted 808]
        [Outro: Bass fade, reverb tail]
    - BPM: 128-130, instruments: heavy 808 sub-bass, aggressive synth leads, high-compression kick, sidechain pump, distorted bass layers.
- IF genre == "Smooth Jazz (Lounge)":
    - Lyrics: Write in a slow, introspective, poetic narrative style — rich imagery, unhurried phrasing. Alternatively, use "Instrumental Focus" mode: write only 2-3 whispered, intimate lines and let the music breathe. No forced rhyme scheme; prioritize emotional texture over structure.
    - Sound structure:
        - [Intro: Rain & Ambience]: Soft patter of rain or gentle clink of glassware — 8 bars of pure atmosphere before any melody enters.
        - [Verse: Piano & Saxophone]: Smooth piano voicings (jazz chords, walking bass implied), silky saxophone melody weaving over the top. Warm, unhurried delivery.
        - [Bridge: Saxophone Improvisation]: Free-form saxophone solo — notate as "improvisation, rubato feel, call-and-response with piano". No fixed rhythm, pure expression.
        - [Outro: Fade to Rain]: Music dissolves back into ambient rain or café ambience.
    - Visual prompt tone: warm amber and walnut-brown palette, classic café or cozy night study corner, candlelight, vinyl record on a turntable, rain-streaked window, 3D isometric warm interior scene.
    - BPM: 70-85, instruments: jazz piano (Steinway voicings), tenor/alto saxophone, upright bass (pizzicato), soft brushed drums, ambient rain layer.
- IF genre == "Ambient Relax (Meditation)":
    - Lyrics: Pure Instrumental preferred — write NO conventional lyrics. If text is needed, use only short mantras (1-5 syllables), soft humming notation "(hmmm…)", or breathing cues "(breathe in… breathe out…)". Zero narrative, zero rhyme — only sound-like words that deepen the trance state.
    - Sound structure: Linear and continuous — NO drops, NO sudden peaks, NO builds that create tension. Sound layers enter and exit slowly (crossfade over 16+ bars). Structure markers: [Opening: Silence into Pads], [Layer 1: Tibetan Bowls], [Layer 2: Nature Ambience — water / wind chimes], [Layer 3: Soft Lead Melody — single sustained notes], [Closing: Gradual fade to silence].
    - No drums, no rhythmic pulse. If percussion exists, it is a single soft Tibetan bowl strike every 8-16 bars — never driving.
    - Visual prompt tone: teal, white, and soft violet palette — misty mountain forest at dawn, cosmic nebula with soft galaxy ribbons, zen stone garden with shallow water reflections, peaceful slow-motion particles drifting. Cinematic wide shot, no sharp edges, everything slightly out of focus.
    - BPM: 60 or free-floating (no fixed tempo), instruments: Tibetan singing bowls, atmospheric pads (long sustained chords), nature sounds (rain / stream / wind), soft piano single notes, binaural-style drone layer.
- IF genre == "Hòa tấu Trung Hoa":
    - Lyrics: Default is Pure Instrumental — write NO conventional lyrics. If vocal text is requested, write ONLY short classical-style poetry using imagery of: moon, water, clouds, wind, tea, sword (trăng, nước, mây, gió, trà, kiếm). Deliver as whispered recitation or soft poetry chanting (whispering voice / ngâm thơ). Maximum one 4-line stanza per section. Never write modern conversational sentences.
    - Pentatonic scale MANDATORY: all melodies must stay strictly within the pentatonic scale (宫商角徵羽 — do re mi sol la). No chromatic notes, no Western chord progressions. Every instrument must feel ancient, modal, and timeless.
    - Sound structure:
        - [Intro]: Flowing water sound (róc rách) layered with soft Guzheng (Đàn Tranh) arpeggios — gentle glissando ripples, sparse and unhurried. Establishes space and stillness before melody enters.
        - [Verse]: Dizi flute (Sáo Trúc) carries the primary melody — long, soaring phrases that evoke vast open landscapes, misty mountains, and boundless sky. Guzheng continues as a soft harmonic cushion beneath.
        - [Chorus]: Erhu (Nhị) and Pipa (Tỳ Bà) interweave — Erhu's bowed legato sighs push emotional peak while Pipa's plucked accents add rhythmic tension. The combination is intensely expressive yet maintains elegance and restraint (thanh tao). No aggressive crescendo — emotion rises like incense smoke, not a wave crash.
        - [Outro]: Wind chimes (chuông gió) enter softly, instruments fade one by one. Final note: single Guzheng pluck, then silence.
    - Instrument roles (always specify in music_style field):
        - Guzheng (古筝 / Đàn Tranh): harmonic foundation, flowing arpeggios, glissando ornaments, gentle tremolo.
        - Dizi (笛子 / Sáo Trúc): primary melodic lead — breathy, pure, spacious tone. Carries the "soul" of the piece.
        - Erhu (二胡 / Nhị): emotional voice — bowed legato, subtle portamento pitch bends, deeply expressive.
        - Pipa (琵琶 / Tỳ Bà): rhythmic accent and color — staccato plucks, occasional melodic fills, bridges lyrical and rhythmic roles.
    - Visual prompt tone (Nano Banana): ink-wash painting style (thủy mặc / 水墨画) OR 3D isometric ancient Chinese scene. Preferred settings: misty bamboo forest (rừng trúc mờ sương), candlelit scholar's study beside a latticed window (thư phòng cổ kính), or a lone swordsman standing beneath a falling peach blossom tree (kiếm khách dưới gốc đào). Palette: ink-grey, jade-green, soft gold, mist-white. No saturated modern colors.
    - BPM: 65-80 (rubato allowed for solo passages), instruments: Guzheng, Dizi, Pipa, Erhu, wind chimes, flowing water ambience, natural room reverb. No electronic elements.
- IF genre == "Deep Chill (Việt Mix)":
    - Lyrics: Write in Vietnamese tự sự (confessional) style — draw from nhạc trẻ buồn, dân ca, or bolero reimagined modern. Core themes: chia ly (separation), người yêu đã đi lấy chồng (lover married another), bến sông / thuyền hoa / tiếc nuối thanh xuân, sự cô đơn giữa thành phố. Use smooth rhyme scheme (vần cuối mượt mà), flowing cadence, no forced rhymes. Every verse must feel like a late-night confession, heavy with unexpressed emotion.
    - Sound structure:
        - [Intro: Rain & Piano]: Tiếng mưa rơi rả rích, hòa cùng tiếng Piano mờ ảo (Muffled Piano) hoặc Guitar thùng buồn bã — sparse and melancholic, 8 bars establishing lonely atmosphere before any beat enters.
        - [Verse: Reverb Vocals]: Giọng hát cất lên đầy tâm sự, heavy reverb/delay (vocal feels far away and intimate simultaneously). Nhịp trống vỗ nhẹ nhàng: Finger snaps hoặc Soft Claps — no heavy kick yet.
        - [THE DROP: Deep House Chill]: KHÔNG bùng nổ ồn ào. Deep Bass đập từng nhịp sâu, tròn trịa — each bass hit feels like a heartbeat dropping. Soft Four-on-the-floor House kick enters (slow, deliberate, never aggressive). Layer: Sáo trúc (Flute) melody hoặc Vocal Chops lặp đi lặp lại tạo sự miên man và cô đơn. Bass and beat together create the "Say Chill House" signature: heavy yet weightless.
        - [Bridge: Breakdown]: Strip back to just piano + rain + whispered vocals — emotional peak before final chorus.
        - [Outro: Fade]: Deep Bass continues alone, rain sound returns, voice fades into reverb tail.
    - Insert ALL structure markers in lyrics: [Intro: Mưa & Piano], [Verse: Reverb Vocals], [THE DROP: Deep Bass + Soft House Kick], [Bridge: Stripped Down], [Outro: Fade into Rain].
    - Visual prompt tone (English, for Nano Banana / Kyma): Dark cinematic lofi aesthetic. Color palette: navy blue, deep purple, burnt amber, wet neon reflections. Scene options: lone figure smoking under rain-soaked awning, dimly lit café corner with flickering yellow lamp, solitary ferry crossing a dark empty river at night. Camera: wide, static, distant — like watching grief from across the street.
    - If create_mv: video_scenes should describe Lofi Loop Video style — static image with subtle animated effect loops (rain falling on car window, steam rising from coffee cup, headlights sweeping across wet road at night). Cost-efficient render, maximum chill vibe.
    - BPM: 105-115, instruments: Deep Bass (round, slow, heartbeat-like), Soft Four-on-the-floor House kick, Atmospheric Pads (wide reverb), Emotional Male or Female Vocal (heavy reverb), Muffled Piano or Acoustic Guitar, Sáo Trúc (Flute) or Vocal Chops, Rain Ambience layer.

# Output Format for SINGLE track (n=1):
{
  "type": "single",
  "title": "Song Title",
  "music_style": "...",
  "lyrics": "full 3-5 min structured lyrics with [Intro][Verse][Chorus][Bridge][Outro] sections",
  "visual_prompt": "English only: Studio quality, 3D isometric...",
  "video_scenes": [],
  "seo": {
    "yt_title": "...",
    "yt_description": "...",
    "yt_tags": [],
    "thumbnail_idea": "..."
  },
  "bgm_suggestion": "..."
}

# Output Format for ALBUM FIRST BATCH (generates album metadata + first N tracks):
{
  "type": "album",
  "title": "Album Title",
  "tracks": [
    {
      "title": "Track Title",
      "music_style": "specific style tags for Suno/Udio/Lyria",
      "lyrics": "full structured lyrics with [Intro][Verse][Chorus] etc."
    }
  ],
  "visual_prompt": "English only: album cover scene...",
  "video_scenes": [],
  "seo": {
    "yt_title": "...",
    "yt_description": "...",
    "yt_tags": [],
    "thumbnail_idea": "..."
  },
  "bgm_suggestion": "..."
}

# Output Format for ALBUM CONTINUATION BATCH (tracks only, no metadata):
{
  "type": "continuation",
  "tracks": [
    {
      "title": "Track Title",
      "music_style": "...",
      "lyrics": "full structured lyrics..."
    }
  ]
}
"""

def _genre_line(genre: str, bpm: str, style_tags: str) -> str:
    return f"Genre: {genre} | BPM: {bpm} | Style tags: {style_tags}"

def build_single_prompt(topic: str, language: str, create_mv: bool,
                        genre: str = "Thiếu Nhi (Nursery)",
                        bpm: str = "100-110 BPM", style_tags: str = "") -> str:
    mv = "Generate full Video 2 (MV) script." if create_mv else "Skip Video 2 Protocol — set video_scenes to []."
    return f"""
Topic: {topic}
Type: SINGLE track
{_genre_line(genre, bpm, style_tags)}
Output language: {language} (visual_prompt must be English)
{mv}

Apply the GENRE-SPECIFIC LOGIC for "{genre}". Generate a complete single track production and return the SINGLE format JSON.
"""

def build_album_first_batch_prompt(
    topic: str,
    total_tracks: int,
    batch_start: int,
    batch_end: int,
    language: str,
    create_mv: bool,
    genre: str = "Thiếu Nhi (Nursery)",
    bpm: str = "100-110 BPM",
    style_tags: str = "",
) -> str:
    mv = "Generate full Video 2 (MV) script." if create_mv else "Skip Video 2 Protocol — set video_scenes to []."
    return f"""
Topic: {topic}
Type: ALBUM FIRST BATCH
Total album tracks: {total_tracks}
Generate tracks: {batch_start} to {batch_end} in this batch
{_genre_line(genre, bpm, style_tags)}
Output language: {language} (visual_prompt must be English)
{mv}

Apply the GENRE-SPECIFIC LOGIC for "{genre}".
Generate the album title, tracks {batch_start}–{batch_end} with full lyrics, visual prompt, SEO, BGM.
Return the ALBUM FIRST BATCH format JSON with exactly {batch_end - batch_start + 1} tracks in the "tracks" array.
"""

def build_keyword_prompt(genre: str, language: str, niche: str, today: str) -> str:
    niche_line = f"Niche / sub-topic: {niche}" if niche.strip() else ""
    return f"""You are a YouTube SEO expert specializing in {genre} music content.
Today: {today}. Target market language: {language}.
{niche_line}

Analyze current YouTube search trends for {genre} music videos in the {language} market.
Consider: current season, upcoming events, evergreen topics, competitor titles, search intent.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "hot_keywords": ["keyword 1", "keyword 2", ...],
  "long_tail": ["longer search phrase 1", ...],
  "hashtags": ["#tag1", "#tag2", ...],
  "title_templates": ["Template Title with {{KEYWORD}} – 2026", ...],
  "tips": ["Specific SEO tip 1", "Specific SEO tip 2", "Specific SEO tip 3"]
}}

Rules:
- hot_keywords: exactly 12 short keywords (1-4 words), high search volume, specific to genre + market
- long_tail: exactly 8 phrases (5-10 words), lower competition, high intent
- hashtags: exactly 15 hashtags, mix of broad + niche, no spaces, include language-specific ones
- title_templates: exactly 5 YouTube title templates, use {{KEYWORD}} as placeholder, include BPM or year for music content
- tips: exactly 3 actionable SEO tips tailored to {genre} + {language} market
- All text in {language} (hashtags can mix English + {language})
"""


def build_video_script_prompt(
    title: str,
    topic: str,
    genre: str,
    style: str,
    lyrics_preview: str,
    language: str,
) -> str:
    return f"""You are a professional YouTube content creator writing a ready-to-record video script.

Track title : {title}
Album topic : {topic}
Music genre : {genre}
Music style : {style}
Language    : {language}
Lyrics preview (first 300 chars):
{lyrics_preview[:300]}

Write a complete, natural-sounding script a creator can read directly on camera.
Use the EXACT language specified above for ALL spoken text.

Structure (use these headers verbatim):

## 🎬 INTRO (0:00 – 0:20)
Three parts:
1. HOOK (first 3 seconds) — one punchy sentence that stops the scroll.
2. GREETING — warm welcome, mention channel/topic briefly.
3. PREVIEW — one sentence telling viewers what they are about to watch/hear.

## 🎵 DURING MUSIC (overlay cues)
Two or three short on-screen text / action cues timed to the music (e.g. "Show lyrics karaoke", "Cut to animation", "Show subscribe button pop-up").

## 🔔 MID-ROLL CTA (at the halfway point)
Natural in-video prompt: ask viewers ONE specific question related to the song topic for the comment section. Then a 1-sentence subscribe reminder. Keep this under 15 seconds when spoken.

## 🎬 OUTRO (last 0:30)
1. Brief wrap-up (what they just heard).
2. Thank-you line.
3. Like + Subscribe + Comment CTA — specific and energetic, not generic.
4. Tease next video (1 sentence, vague but exciting).

## 📌 END SCREEN (last 20 seconds)
List exactly 3 end-screen card suggestions:
- Recommended video card
- Playlist card
- Subscribe button

Keep total script under 250 words. Write conversationally — no stiff formal language.
Do NOT include JSON. Return plain text only."""


def build_album_continuation_prompt(
    topic: str,
    album_title: str,
    total_tracks: int,
    batch_start: int,
    batch_end: int,
    language: str,
    genre: str = "Thiếu Nhi (Nursery)",
    bpm: str = "100-110 BPM",
    style_tags: str = "",
) -> str:
    return f"""
Album: {album_title}
Topic: {topic}
Type: ALBUM CONTINUATION BATCH
Total album tracks: {total_tracks}
Generate tracks: {batch_start} to {batch_end} in this batch
{_genre_line(genre, bpm, style_tags)}
Output language: {language}

Apply the GENRE-SPECIFIC LOGIC for "{genre}".
Generate ONLY tracks {batch_start}–{batch_end}. Each track must have: title, music_style, full lyrics.
Return the ALBUM CONTINUATION BATCH format JSON with exactly {batch_end - batch_start + 1} tracks in the "tracks" array.
"""


def build_mv_director_prompt(topic: str, genre: str, duration_secs: float,
                             lyrics: str = "") -> str:
    """
    Tạo prompt cho AI MV Director / Storyboard Generator.
    Số scene được tính tự động từ duration_secs (1 scene ≈ 8s).
    """
    scenes = max(4, round(duration_secs / 8))
    mins   = int(duration_secs // 60)
    secs   = int(duration_secs % 60)
    dur_str = f"{mins} phút {secs} giây ({int(duration_secs)}s)"
    lyrics_block = f"\n\n**LYRICS REFERENCE (dùng để khớp đoạn nhạc với cảnh):**\n{lyrics[:1200]}" if lyrics else ""

    return f"""# ROLE & CAPABILITY
Bạn là một Đạo diễn Music Video (MV Director) kiêm Chuyên gia AI Video Prompting hàng đầu. Nhiệm vụ của bạn là chuyển đổi một bài hát thành một kịch bản phân cảnh (Storyboard) chi tiết, tối ưu hóa cho các công cụ tạo video AI thế hệ mới (như Veo 3, Runway Gen-3, Kling).

# INPUT DATA
- Chủ đề/Tên bài hát: {topic}
- Thể loại âm nhạc: {genre}
- Thời lượng thực tế: {dur_str}
- Số scenes yêu cầu: **{scenes} scenes** (1 scene ≈ 8s × {scenes} = {scenes*8}s ≈ {dur_str}){lyrics_block}

# CORE DIRECTIVES (QUY TẮC BẮT BUỘC)

## 1. The Consistency Lock (Khóa Đồng Nhất)
Thiết lập "Kinh Thánh" cho MV. Mọi cảnh quay ĐỀU PHẢI chứa chuỗi khóa này:
- **[CHARACTER_LOCK]**: Mô tả nhân vật cực kỳ chi tiết (Giới tính, tuổi, kiểu tóc màu cụ thể, trang phục chi tiết từng món, màu sắc, phụ kiện). TUYỆT ĐỐI không thay đổi trong suốt MV.
- **[ENVIRONMENT_LOCK]**: Mô tả bối cảnh (Thời gian ngày/đêm, không gian, thời tiết, phong cách ánh sáng, tone màu chủ đạo, thiết bị camera).

## 2. Beat-Sync Structure (Cấu trúc khớp nhịp)
Tốc độ chuyển cảnh tương ứng với thể loại nhạc:
- Nhạc chậm (Jazz, Ballad, Chill): Cảnh quay 6-8s, slow pan, slow zoom
- Nhạc vừa (Pop, R&B): Cảnh quay 4-6s, tracking shots, smooth transitions
- Nhạc mạnh (EDM, Hardstyle, Drill, Rap): Cảnh quay 2-3s, dutch angle, rapid zoom, screen shake tại Drop

## 3. Scene Count Rule
Bạn PHẢI tạo đúng **{scenes} scenes** — không hơn, không kém.
Phân bổ thời gian: Intro (1-2 scenes), Verse (30%), Chorus/Drop (40%), Bridge/Break (15%), Outro (15%).

# OUTPUT FORMAT
Trả về CHÍNH XÁC định dạng sau (không thêm câu giao tiếp):

### 🎬 KỊCH BẢN MV: {topic}

**A. BỘ KHÓA AI (AI LOCKS)**
* **[CHARACTER_LOCK]:** (prompt tiếng Anh mô tả nhân vật)
* **[ENVIRONMENT_LOCK]:** (prompt tiếng Anh mô tả bối cảnh)

**B. PHÂN CẢNH CHI TIẾT (STORYBOARD)**
*Quy tắc prompt: [CHARACTER_LOCK] + [ENVIRONMENT_LOCK] + [Hành động] + [Góc máy]*

| Cảnh | Thời gian | Đoạn Nhạc | Cỡ Cảnh | Prompt AI (English) | Camera Motion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 0:00-0:08 | Intro | Extreme Wide Shot | [ENVIRONMENT_LOCK]. Cinematic fade-in from black... | Slow drone push-in |
| 2 | 0:08-0:16 | Intro | Medium Shot | [CHARACTER_LOCK] in [ENVIRONMENT_LOCK]... | Tracking forward |
(tiếp tục đến scene {scenes})

**C. TỐI ƯU HÓA KÊNH (SEO & METADATA)**
* **Title:** (Tiêu đề YouTube giật tít, có từ khóa SEO)
* **Description:** (Mô tả ngắn gọn, hấp dẫn, 2-3 câu)
* **Hashtags:** (6-8 hashtags chuẩn xác cho thể loại và chủ đề)
* **Thumbnail Idea:** (Mô tả chi tiết bằng tiếng Anh: cảnh nào ấn tượng nhất, text overlay là gì, tone màu, composition)
* **BGM Suggestion:** (Nếu là video kể chuyện — chỉ định thể loại nhạc nền phù hợp)

QUAN TRỌNG: Bảng phân cảnh phải có đúng {scenes} hàng, thời gian cộng dồn phải khớp với tổng {dur_str}.
"""


def build_topic_suggestion_prompt(keywords: list, genre: str, language: str) -> str:
    kw_str = ", ".join(f'"{k}"' for k in keywords)
    return f"""You are a YouTube content strategist specializing in {genre} music.

Selected trending keywords: {kw_str}
Genre: {genre}
Target market language: {language}

Based on these keywords, suggest exactly 5 hot YouTube content topics for {genre} music videos.
Each topic should be specific enough to serve directly as a song title or album concept.

For each topic assign a potential score 1–10:
- 10 = highest potential (high search volume, low competition, strong trending momentum)
- 1  = lowest potential

Return ONLY valid JSON array, no markdown, no explanation:
[
  {{"topic": "...", "score": 10, "reason": "One sentence: why this ranks highest"}},
  {{"topic": "...", "score": 8,  "reason": "..."}},
  {{"topic": "...", "score": 7,  "reason": "..."}},
  {{"topic": "...", "score": 5,  "reason": "..."}},
  {{"topic": "...", "score": 3,  "reason": "..."}}
]

Rules:
- All text (topic, reason) must be in {language}
- Topics must be specific, vivid, and optimized for YouTube search
- Sort the array by score descending (highest first)
- Scores must be distinct integers between 1 and 10
"""
