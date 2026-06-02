from __future__ import annotations

import json
import logging
import os
import re
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a precise investment research career advisor specialising in "
    "buy-side and sell-side equity research roles in Hong Kong and Shanghai. "
    "Always reply in the same language as the user prompt unless instructed otherwise."
)


def _settings() -> dict[str, str]:
    return {
        "provider": os.getenv("LLM_PROVIDER", "mock").lower(),
        "model": os.getenv("LLM_MODEL", "llama3.1:8b"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    }


def _strip_json_fence(text: str) -> str:
    """Remove markdown code fences so json.loads() can parse the result."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# ── OpenRouter / OpenAI (openai-compatible) ──────────────────────────────────

def _call_openai_compatible(
    prompt: str,
    base_url: str,
    api_key: str,
    model: str,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode("utf-8")

    req = request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


# ── Ollama ────────────────────────────────────────────────────────────────────

def _call_ollama(prompt: str, base_url: str, model: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
    ).encode("utf-8")

    req = request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_text(prompt: str, fallback: str = "") -> str:
    s = _settings()
    provider = s["provider"]
    try:
        if provider == "openrouter":
            return _call_openai_compatible(
                prompt,
                base_url="https://openrouter.ai/api/v1",
                api_key=s["openrouter_api_key"],
                model=s["model"],
            )
        if provider == "openai":
            return _call_openai_compatible(
                prompt,
                base_url="https://api.openai.com/v1",
                api_key=s["openai_api_key"],
                model=s["model"],
            )
        if provider in {"ollama", "meta-llama", "llama"}:
            return _call_ollama(prompt, s["ollama_base_url"], s["model"])
        # provider == "mock" or anything else
        logger.debug("LLM provider is '%s'; returning fallback.", provider)
        return fallback
    except (error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        logger.warning("generate_text failed (%s): %s", type(exc).__name__, exc)
        return fallback


def generate_json(prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    raw = generate_text(
        prompt + "\nReturn valid JSON only. No markdown code fences.",
        fallback=json.dumps(fallback, ensure_ascii=False),
    )
    try:
        return json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError:
        logger.warning("generate_json: could not parse LLM output as JSON.")
        return fallback
