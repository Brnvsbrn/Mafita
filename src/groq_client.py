import json
import os
import re

import httpx


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = os.getenv("GROQ_DEFAULT_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODELS = [
    item.strip()
    for item in os.getenv("GROQ_FALLBACK_MODELS", "llama-3.3-70b-versatile,openai/gpt-oss-20b").split(",")
    if item.strip()
]


class MissingGroqKey(RuntimeError):
    pass


def groq_key():
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
    if not key:
        raise MissingGroqKey("GROQ_API_KEY or GROQ_KEY is not set.")
    return key


def redact_groq_secret(text):
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY") or ""
    redacted = str(text)
    if key:
        redacted = redacted.replace(key, "[REDACTED]")
    return re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", redacted)


def groq_chat_json(system_prompt, user_payload, model=None, temperature=0, max_tokens=1200, fallback_models=None):
    models = [model or DEFAULT_GROQ_MODEL]
    for fallback in fallback_models if fallback_models is not None else GROQ_FALLBACK_MODELS:
        if fallback not in models:
            models.append(fallback)

    errors = []
    for candidate in models:
        try:
            return _call_groq_json(candidate, system_prompt, user_payload, temperature, max_tokens)
        except Exception as exc:
            errors.append(f"{candidate}: {redact_groq_secret(type(exc).__name__ + ': ' + str(exc))}")
    raise RuntimeError("Groq fallback chain failed: " + " | ".join(errors))


def _call_groq_json(model, system_prompt, user_payload, temperature, max_tokens):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_payload if isinstance(user_payload, str) else json.dumps(user_payload, ensure_ascii=False),
            },
        ],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    response = httpx.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {groq_key()}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"].get("content", "")
    return {
        "model": model,
        "text": content,
        "json": _parse_json_object(content),
        "raw": data,
        "usage": data.get("usage", {}),
    }


def _parse_json_object(content):
    text = str(content or "").strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)
