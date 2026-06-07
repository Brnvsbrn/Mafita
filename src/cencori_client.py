import os

import httpx
from cencori import Cencori


DEFAULT_CENCORI_MODEL = os.getenv("CENCORI_MODEL", "gemini-2.5-flash")
OPENAI_COMPAT_BASE_URL = "https://api.cencori.com/v1"


class MissingCencoriKey(RuntimeError):
    pass


def get_cencori_client():
    api_key = os.getenv("CENCORI_API_KEY")
    if not api_key:
        raise MissingCencoriKey("CENCORI_API_KEY is not set.")
    return Cencori(api_key=api_key)


def cencori_chat(messages, model=None, temperature=0.2, max_tokens=600, user_id=None):
    client = get_cencori_client()
    return client.ai.chat(
        model=model or DEFAULT_CENCORI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        user_id=user_id,
    )


def cencori_chat_stream(messages, model=None, temperature=0.2, max_tokens=600, user_id=None):
    client = get_cencori_client()
    return client.ai.chat_stream(
        model=model or DEFAULT_CENCORI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        user_id=user_id,
    )


def cencori_openai_chat(messages, model=None, temperature=0.2, max_tokens=600):
    api_key = os.getenv("CENCORI_API_KEY")
    if not api_key:
        raise MissingCencoriKey("CENCORI_API_KEY is not set.")
    response = httpx.post(
        f"{OPENAI_COMPAT_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or DEFAULT_CENCORI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
