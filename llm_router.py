"""
llm_router.py — Bộ định tuyến AI đa nhà cung cấp.

Thứ tự ưu tiên:
  1. API key của user (Anthropic) nếu được cung cấp
  2. CLAUDE_API_KEY     — platform Claude Sonnet 4.6
  3. OPENAI_API_KEY     — GPT-4o-mini   (rẻ, thông minh, fallback tốt)
  4. GEMINI_API_KEY     — Gemini 1.5 Flash (nhanh, miễn phí quota cao)

Thêm vào .streamlit/secrets.toml:
  CLAUDE_API_KEY  = "sk-ant-..."
  OPENAI_API_KEY  = "sk-proj-..."
  GEMINI_API_KEY  = "AIzaSy..."

Sử dụng:
  from llm_router import generate_text
  raw, provider = generate_text(system_prompt, user_prompt, max_tokens=16000)
"""

import os
import logging

logger = logging.getLogger(__name__)

_PROVIDER_LABELS = {
    "claude_user":     "Claude (key của bạn)",
    "claude_platform": "Claude (platform)",
    "openai":          "GPT-4o-mini",
    "gemini":          "Gemini Flash",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _secret(key: str) -> str:
    try:
        import streamlit as st
        return st.secrets.get(key, "") or os.environ.get(key, "")
    except Exception:
        return os.environ.get(key, "")


def _strip_md_fence(text: str) -> str:
    """Xóa wrapper ```markdown / ```json / ``` mà OpenAI & Gemini thỉnh thoảng thêm vào."""
    text = text.strip()
    for prefix in ("```markdown", "```json", "```"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return text.removesuffix("```").strip()


# ---------------------------------------------------------------------------
# Provider helpers
# ---------------------------------------------------------------------------

def _call_claude(api_key: str, system_prompt: str, user_prompt: str,
                 max_tokens: int, model: str = "claude-sonnet-4-6") -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    kwargs: dict = {
        "model":      model,
        "max_tokens": max_tokens,
        "messages":   [{"role": "user", "content": user_prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    msg = client.messages.create(**kwargs)
    return msg.content[0].text


def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    from openai import OpenAI
    key = _secret("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY chưa cấu hình trong secrets.toml")
    client = OpenAI(api_key=key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=min(max_tokens, 16384),
        temperature=0.7,
    )
    return _strip_md_fence(resp.choices[0].message.content)


def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    import google.generativeai as genai
    key = _secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY chưa cấu hình trong secrets.toml")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt or None,
    )
    gen_cfg = genai.types.GenerationConfig(max_output_tokens=min(max_tokens, 8192))
    resp = model.generate_content(user_prompt, generation_config=gen_cfg)
    return _strip_md_fence(resp.text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_text(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 16000,
    user_api_key: str = "",
    claude_model: str = "claude-sonnet-4-6",
    byok_mode: bool = False,
) -> tuple[str, str]:
    """
    Gọi AI với chuỗi fallback tự động.

    Args:
        system_prompt:  System / instruction prompt.
        user_prompt:    Nội dung yêu cầu của user.
        max_tokens:     Số token tối đa cho phần output.
        user_api_key:   Anthropic API key của user (ưu tiên cao nhất, tùy chọn).
        claude_model:   Model Claude cần dùng (default claude-sonnet-4-6).
        byok_mode:      True = chỉ dùng user_api_key, không fallback sang platform keys.
                        Dùng cho gói Tự Túc (BYOK).

    Returns:
        (text, provider_id)
        provider_id ∈ {"claude_user", "claude_platform", "openai", "gemini"}

    Raises:
        RuntimeError — khi tất cả providers đều thất bại.
    """
    errors: list[str] = []

    # ── 0. API key của user (ưu tiên tuyệt đối) ──────────────────────────────
    if user_api_key:
        try:
            return (
                _call_claude(user_api_key, system_prompt, user_prompt, max_tokens, claude_model),
                "claude_user",
            )
        except Exception as e:
            errors.append(f"Claude (user key): {e}")
            logger.warning("Claude user key failed: %s", e)
            if byok_mode:
                raise RuntimeError(
                    f"Gói Tự Túc (BYOK): API Key của bạn gặp lỗi.\n{e}\n"
                    "Kiểm tra lại key tại Cài đặt → API Keys."
                )
    elif byok_mode:
        raise RuntimeError(
            "Gói Tự Túc (BYOK): Chưa nhập Anthropic API Key.\n"
            "Vui lòng vào Cài đặt → API Keys để nhập key của bạn."
        )

    # ── 1. Platform Claude ────────────────────────────────────────────────────
    platform_claude = _secret("CLAUDE_API_KEY")
    if platform_claude:
        try:
            return (
                _call_claude(platform_claude, system_prompt, user_prompt, max_tokens, claude_model),
                "claude_platform",
            )
        except Exception as e:
            errors.append(f"Claude (platform): {e}")
            logger.warning("Claude platform failed: %s", e)

    # ── 2. OpenAI GPT-4o-mini ─────────────────────────────────────────────────
    try:
        return _call_openai(system_prompt, user_prompt, max_tokens), "openai"
    except Exception as e:
        errors.append(f"OpenAI: {e}")
        logger.warning("OpenAI failed: %s", e)

    # ── 3. Gemini 1.5 Flash ───────────────────────────────────────────────────
    try:
        return _call_gemini(system_prompt, user_prompt, max_tokens), "gemini"
    except Exception as e:
        errors.append(f"Gemini: {e}")
        logger.warning("Gemini failed: %s", e)

    raise RuntimeError(
        "Tất cả AI providers đều không khả dụng:\n"
        + "\n".join(f"  · {err}" for err in errors)
    )


def provider_label(provider_id: str) -> str:
    """Trả về tên hiển thị của provider."""
    return _PROVIDER_LABELS.get(provider_id, provider_id)
