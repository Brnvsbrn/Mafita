import os

import httpx


DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class MissingGeminiKey(RuntimeError):
    pass


def _api_key():
    key = os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise MissingGeminiKey("GOOGLE_GEMINI_KEY or GEMINI_API_KEY is not set.")
    return key


def gemini_generate(system_prompt, user_text, model=None, temperature=0.1, max_output_tokens=1200, thinking_budget=32):
    generation_config = {
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
    }
    if thinking_budget is not None:
        generation_config["thinkingConfig"] = {"thinkingBudget": thinking_budget}

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_text}],
            }
        ],
        "generationConfig": generation_config,
    }
    response = httpx.post(
        f"{GEMINI_BASE_URL}/models/{model or DEFAULT_GEMINI_MODEL}:generateContent",
        params={"key": _api_key()},
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    parts = data["candidates"][0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    return {
        "text": text,
        "raw": data,
    }
