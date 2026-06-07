from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bank0_chat import CHAT_SYSTEM_PROMPT  # noqa: E402

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

SCRATCH = ROOT / "scratch"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

DEFAULT_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]

CASES = [
    {
        "id": "yo_greeting",
        "message": "Báwo ni",
        "expected_language": "yo",
        "required_terms": ["Mafita"],
        "should_ask_missing": False,
    },
    {
        "id": "yo_failed_transfer_missing_ref",
        "message": "Jọwọ, mo ran owó sí Access Bank lori OPay, owó ti kuro sugbon recipient kò rí i.",
        "expected_language": "yo",
        "required_terms": ["OPay", "Access Bank"],
        "should_ask_missing": True,
    },
    {
        "id": "yo_pending_with_session",
        "message": "Transfer mi lori Moniepoint ṣi wa pending. Session ID ni B0-TX-2001.",
        "expected_language": "yo",
        "required_terms": ["Moniepoint", "Session ID", "B0-TX-2001"],
        "should_ask_missing": False,
    },
    {
        "id": "yo_kyc_restriction",
        "message": "Account PalmPay mi ti di restricted nitori BVN ati NIN KYC.",
        "expected_language": "yo",
        "required_terms": ["PalmPay", "BVN", "NIN", "KYC"],
        "should_ask_missing": False,
    },
    {
        "id": "yo_double_debit_missing",
        "message": "Wọn yọ owó lẹ́ẹ̀mejì lori card mi, mi ò mọ transaction reference.",
        "expected_language": "yo",
        "required_terms": ["transaction reference"],
        "should_ask_missing": True,
    },
    {
        "id": "mixed_wrong_recipient",
        "message": "Mo mistakenly send money to wrong recipient on OPay, please help me.",
        "expected_language": "yo",
        "required_terms": ["OPay"],
        "should_ask_missing": True,
    },
    {
        "id": "en_failed_transfer",
        "message": "My transfer to Access Bank failed on OPay and I was debited.",
        "expected_language": "en",
        "required_terms": ["OPay", "Access Bank"],
        "should_ask_missing": True,
    },
    {
        "id": "yo_fraud",
        "message": "Jọwọ ẹ ran mi lọwọ, scammer gba gbogbo owó mi lori OPay.",
        "expected_language": "yo",
        "required_terms": ["OPay"],
        "should_ask_missing": True,
    },
]


def api_key() -> str:
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY or GROQ_KEY is not set.")
    return key


def strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text or "")
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def normalize(text: str) -> str:
    text = strip_diacritics(text).lower()
    text = re.sub(r"[^\w\s.-]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def parse_json(text: str) -> dict:
    clean = str(text or "").strip()
    if clean.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, flags=re.DOTALL | re.IGNORECASE)
        if match:
            clean = match.group(1)
    if not clean.startswith("{"):
        start = clean.find("{")
        end = clean.rfind("}")
        if start >= 0 and end > start:
            clean = clean[start : end + 1]
    return json.loads(clean)


def call_model(model: str, cases: list[dict], retries: int = 1, retry_sleep: float = 20) -> tuple[dict[str, dict], float, str, dict]:
    user_payload = {
        "instruction": (
            "For each case, respond as Mafita Agent using the app contract. "
            "Return a JSON object with a responses array. Each response must include "
            "id, language, thinking_steps, reply, and english_summary."
        ),
        "cases": [{"id": case["id"], "user_message": case["message"]} for case in cases],
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_completion_tokens": max(1200, 420 * len(cases)),
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"}
    start = time.perf_counter()
    response = None
    with httpx.Client(timeout=120) as client:
        for attempt in range(retries + 1):
            response = client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
            if response.status_code != 429 or attempt >= retries:
                break
            time.sleep(retry_sleep * (attempt + 1))
    latency = time.perf_counter() - start
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"].get("content", "")
    parsed = parse_json(content)
    responses = parsed.get("responses") or parsed.get("results") or []
    return {str(item.get("id", "")).strip(): item for item in responses}, latency, content, data.get("usage", {})


def has_yoruba_signal(text: str) -> bool:
    lowered = normalize(text)
    words = set(lowered.split())
    yoruba_terms = {
        "jowo",
        "owo",
        "ran",
        "iranlowo",
        "lọwọ",
        "lowo",
        "oruko",
        "nomba",
        "tesiwaju",
        "sayewo",
        "le",
        "ki",
        "fun",
        "re",
        "mi",
        "yii",
        "naa",
    }
    return bool(words & yoruba_terms) or any(char in text for char in "áàéèẹ́ẹ̀íìóòọ́ọ̀úùṣṢ")


def english_leak_score(text: str) -> float:
    allowed = {
        "mafita",
        "opay",
        "palmpay",
        "moniepoint",
        "access",
        "bank",
        "bvn",
        "nin",
        "kyc",
        "otp",
        "pos",
        "nip",
        "session",
        "id",
        "transaction",
        "reference",
        "card",
        "account",
    }
    common_english = {
        "please",
        "provide",
        "send",
        "need",
        "help",
        "transfer",
        "failed",
        "pending",
        "recipient",
        "money",
        "continue",
        "check",
        "details",
        "safely",
        "support",
        "issue",
    }
    tokens = normalize(text).split()
    if not tokens:
        return 1.0
    leaks = [token for token in tokens if token in common_english and token not in allowed]
    return len(leaks) / len(tokens)


def preserves_terms(reply: str, terms: list[str]) -> tuple[float, list[str]]:
    norm_reply = normalize(reply)
    missing = [term for term in terms if normalize(term) not in norm_reply]
    score = 1 - (len(missing) / len(terms)) if terms else 1.0
    return round(score, 4), missing


def asks_missing(reply: str) -> bool:
    norm = normalize(reply)
    signals = [
        "transaction reference",
        "session id",
        "nomba",
        "nom ba",
        "oruko",
        "phone",
        "name",
        "fi",
        "ranse",
        "send",
        "provide",
    ]
    return any(signal in norm for signal in signals)


def score_case(case: dict, model: str, response: dict, latency: float, batch_size: int, usage: dict) -> dict:
    reply = str(response.get("reply", "")).strip()
    language = str(response.get("language", "")).strip()
    term_score, missing_terms = preserves_terms(reply, case["required_terms"])
    expected_language = case["expected_language"]
    language_ok = language == expected_language or (expected_language == "yo" and language == "mixed")
    if expected_language == "yo":
        language_ok = language_ok and has_yoruba_signal(reply)
    missing_ok = asks_missing(reply) if case["should_ask_missing"] else True
    word_count = len(reply.split())
    voice_ok = 5 <= word_count <= 70
    english_leak = english_leak_score(reply) if expected_language == "yo" else 0.0
    score = (
        (0.25 if language_ok else 0.0)
        + 0.25 * term_score
        + (0.20 if missing_ok else 0.0)
        + (0.20 if voice_ok else 0.0)
        + 0.10 * max(0.0, 1.0 - min(english_leak * 4, 1.0))
    )
    return {
        "id": case["id"],
        "model": model,
        "message": case["message"],
        "expected_language": expected_language,
        "language": language,
        "language_ok": language_ok,
        "required_terms": case["required_terms"],
        "entity_preservation": term_score,
        "missing_terms": missing_terms,
        "should_ask_missing": case["should_ask_missing"],
        "missing_details_ok": missing_ok,
        "voice_friendly": voice_ok,
        "word_count": word_count,
        "english_leak_score": round(english_leak, 4),
        "score": round(score, 4),
        "batch_latency_seconds": round(latency, 3),
        "amortized_latency_seconds": round(latency / max(batch_size, 1), 3),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "reply": reply,
        "thinking_steps": response.get("thinking_steps"),
        "english_summary": response.get("english_summary"),
    }


def chunks(items: list[dict], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for model in sorted({row["model"] for row in rows}):
        group = [row for row in rows if row["model"] == model]
        summary[model] = {
            "cases": len(group),
            "avg_score": round(sum(row["score"] for row in group) / len(group), 4),
            "language_pass_rate": round(sum(row["language_ok"] for row in group) / len(group), 4),
            "avg_entity_preservation": round(sum(row["entity_preservation"] for row in group) / len(group), 4),
            "missing_details_pass_rate": round(sum(row["missing_details_ok"] for row in group) / len(group), 4),
            "voice_friendly_rate": round(sum(row["voice_friendly"] for row in group) / len(group), 4),
            "avg_english_leak_score": round(sum(row["english_leak_score"] for row in group) / len(group), 4),
            "avg_batch_latency_seconds": round(sum(row["batch_latency_seconds"] for row in group) / len(group), 4),
            "avg_amortized_latency_seconds": round(sum(row["amortized_latency_seconds"] for row in group) / len(group), 4),
        }
    return dict(sorted(summary.items(), key=lambda item: (-item[1]["avg_score"], item[1]["avg_batch_latency_seconds"])))


def write_csv(rows: list[dict], path: Path):
    fields = [
        "id",
        "model",
        "score",
        "batch_latency_seconds",
        "amortized_latency_seconds",
        "language_ok",
        "language",
        "entity_preservation",
        "missing_terms",
        "missing_details_ok",
        "voice_friendly",
        "word_count",
        "english_leak_score",
        "message",
        "reply",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main():
    parser = argparse.ArgumentParser(description="Evaluate Groq models for Yoruba customer-support response generation.")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=len(CASES))
    parser.add_argument("--out-json", default=SCRATCH / "groq_yoruba_response_eval_report.json", type=Path)
    parser.add_argument("--out-csv", default=SCRATCH / "groq_yoruba_response_eval_rows.csv", type=Path)
    args = parser.parse_args()

    cases = CASES[: args.limit]
    rows = []
    failures = []
    for model in args.models:
        for batch in chunks(cases, args.batch_size):
            ids = ", ".join(case["id"] for case in batch)
            print(f"Running {model}: {ids}")
            try:
                outputs, latency, raw, usage = call_model(model, batch)
            except Exception as exc:
                failures.append({"model": model, "ids": ids, "error": str(exc)})
                print(f"FAILED {model} {ids}: {exc}")
                continue
            for case in batch:
                rows.append(score_case(case, model, outputs.get(case["id"], {}), latency, len(batch), usage))
            missing = [case["id"] for case in batch if case["id"] not in outputs]
            if missing:
                failures.append({"model": model, "ids": ids, "error": f"missing outputs: {missing}", "raw": raw})

    report = {"system_prompt": CHAT_SYSTEM_PROMPT, "summary": summarize(rows), "failures": failures, "rows": rows}
    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(rows, args.out_csv)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if failures:
        print(f"Failures: {len(failures)}")
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_csv}")


if __name__ == "__main__":
    main()
