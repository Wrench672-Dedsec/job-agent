from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


def _current_settings() -> dict[str, str]:
    return {
        "provider": os.getenv("LLM_PROVIDER", "mock").lower(),
        "model": os.getenv("LLM_MODEL", "llama3.1:8b"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }


def is_ollama_enabled() -> bool:
    return _current_settings()["provider"] in {"ollama", "meta-llama", "llama"}


def generate_text(prompt: str, fallback: str = "") -> str:
    settings = _current_settings()
    if not is_ollama_enabled():
        return fallback

    payload = json.dumps(
        {
            "model": settings["model"],
            "messages": [
                {"role": "system", "content": "You are a precise job-search assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
    ).encode("utf-8")

    req = request.Request(
        f"{settings['ollama_base_url']}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return fallback

    message = data.get("message", {})
    content = message.get("content", "")
    return content or fallback


def generate_json(prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    text = generate_text(
        prompt + "\nReturn valid JSON only. No markdown.",
        fallback=json.dumps(fallback, ensure_ascii=False),
    )
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return fallback
    if isinstance(parsed, dict):
        return parsed
    return fallback