"""Unified AI client supporting 13+ providers for text generation."""

import json
import httpx
from config.settings import settings


# ── OpenAI-compatible provider registry ──
# Each entry: (base_url, api_key_attr, default_model)
OPENAI_COMPATIBLE = {
    "groq": (
        "https://api.groq.com/openai/v1",
        "groq_api_key",
        "llama-3.3-70b-versatile",
    ),
    "cerebras": (
        "https://api.cerebras.ai/v1",
        "cerebras_api_key",
        "llama3.1-8b",
    ),
    "sambanova": (
        "https://api.sambanova.ai/v1",
        "sambanova_api_key",
        "Meta-Llama-3.3-70B-Instruct",
    ),
    "mistral": (
        "https://api.mistral.ai/v1",
        "mistral_api_key",
        "mistral-small-latest",
    ),
    "openrouter": (
        "https://openrouter.ai/api/v1",
        "openrouter_api_key",
        "meta-llama/llama-3.3-70b-instruct:free",
    ),
    "github": (
        "https://models.inference.ai.azure.com",
        "github_token",
        "Meta-Llama-3.1-8B-Instruct",
    ),
    "siliconcloud": (
        "https://api.siliconflow.cn/v1",
        "siliconcloud_api_key",
        "Qwen/Qwen2.5-72B-Instruct",
    ),
    "novita": (
        "https://api.novita.ai/v3/openai",
        "novita_api_key",
        "meta-llama/llama-3.3-70b-instruct",
    ),
    "cloudflare": (
        "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        "cloudflare_api_key",
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    ),
    "openai": (
        "https://api.openai.com/v1",
        "openai_api_key",
        "gpt-4o-mini",
    ),
    "together": (
        "https://api.together.xyz/v1",
        "together_api_key",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    ),
}


def ai_chat(prompt: str, max_tokens: int = 4096, json_mode: bool = False) -> str:
    """Send a prompt to the configured AI provider and return the response text."""
    provider = settings.ai_provider

    if provider == "ollama":
        return _ollama_chat(prompt, max_tokens, json_mode)
    elif provider == "gemini":
        return _gemini_chat(prompt, max_tokens)
    elif provider == "anthropic":
        return _anthropic_chat(prompt, max_tokens)
    elif provider in OPENAI_COMPATIBLE:
        return _openai_compatible_chat(provider, prompt, max_tokens, json_mode)
    else:
        raise ValueError(
            f"Unknown AI provider: {provider}. "
            f"Available: ollama, gemini, anthropic, "
            f"{', '.join(OPENAI_COMPATIBLE.keys())}"
        )


def _openai_compatible_chat(provider: str, prompt: str,
                             max_tokens: int, json_mode: bool) -> str:
    """Generic handler for all OpenAI-compatible APIs."""
    base_url, key_attr, default_model = OPENAI_COMPATIBLE[provider]

    api_key = getattr(settings, key_attr, "")
    if not api_key:
        raise ValueError(f"{provider} requires {key_attr} to be set")

    # Cloudflare needs account_id in the URL
    if "{account_id}" in base_url:
        base_url = base_url.format(account_id=settings.cloudflare_account_id)

    # Use default model for this provider unless AI_MODEL is explicitly set
    # and looks like it belongs to this provider (not a leftover from another)
    configured_model = settings.ai_model
    if configured_model in ("llama3.2", "") or provider != settings.ai_provider:
        model = default_model
    else:
        model = configured_model

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # OpenRouter wants extra headers
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/ai-video-pipeline"
        headers["X-Title"] = "AI Video Pipeline"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = httpx.post(
        f"{base_url}/chat/completions",
        json=payload, headers=headers, timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _ollama_chat(prompt: str, max_tokens: int, json_mode: bool) -> str:
    """Call Ollama local API — completely free, no key needed."""
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7,
        },
    }
    if json_mode:
        payload["format"] = "json"

    resp = httpx.post(url, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["response"]


def _gemini_chat(prompt: str, max_tokens: int) -> str:
    """Call Google Gemini API — free tier available."""
    api_key = settings.google_api_key or settings.gemini_api_key
    if not api_key:
        raise ValueError("Gemini requires google_api_key or gemini_api_key")

    model = settings.ai_model if settings.ai_model != "llama3.2" else "gemini-2.0-flash"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7,
        },
    }
    resp = httpx.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _anthropic_chat(prompt: str, max_tokens: int) -> str:
    """Call Anthropic Claude API — paid."""
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    model = settings.ai_model if settings.ai_model != "llama3.2" else "claude-sonnet-4-20250514"
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def parse_json_response(raw: str) -> dict:
    """Parse JSON from AI response, handling markdown code blocks."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw)


def list_providers() -> dict[str, bool]:
    """Return all providers and whether they have a key configured."""
    result = {
        "ollama": bool(settings.ollama_base_url),
        "gemini": bool(settings.google_api_key or getattr(settings, "gemini_api_key", "")),
        "anthropic": bool(settings.anthropic_api_key),
    }
    for name, (_, key_attr, _) in OPENAI_COMPATIBLE.items():
        result[name] = bool(getattr(settings, key_attr, ""))
    return result
