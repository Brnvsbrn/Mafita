"""
Evaluate Groq chat models on Yoruba fintech text understanding.

This does not test speech-to-text. It tests whether each model understands
Yoruba customer-support queries well enough to translate meaning, preserve
entities, and classify the support issue.

Example:
    python scratch/run_groq_text_eval.py --batch-size 5 --limit 5
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "scratch"
sys.path.insert(0, str(SCRATCH))

from run_asr_eval import entity_preservation, expected_entities, load_dataset, token_f1  # noqa: E402

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass


GROQ_BASE_URL = "https://api.groq.com/openai/v1"

DEFAULT_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "groq/compound-mini",
    "groq/compound",
    "allam-2-7b",
]


def api_key() -> str:
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY or GROQ_KEY is not set.")
    return key


def redact_secret(text: str) -> str:
    key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY") or ""
    redacted = str(text)
    if key:
        redacted = redacted.replace(key, "[REDACTED]")
    return re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", redacted)


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(str(text).encode("ascii", "backslashreplace").decode("ascii"))


def build_prompt(samples: list[dict]) -> str:
    allowed_categories = sorted({sample["category"] for sample in samples})
    lines = [
        "You are evaluating Yoruba fintech customer-support understanding.",
        "For each query:",
        "1. Translate the meaning into concise English.",
        "2. Classify it using one of the allowed categories.",
        "3. Preserve fintech entities such as OPay, PalmPay, Moniepoint, Access Bank, BVN, NIN, KYC, USSD, ATM, Session ID.",
        "Return only JSON, no markdown.",
        "",
        "Schema:",
        '{"results":[{"id":"Q01","english":"...","category":"...","entities":["..."]}]}',
        "",
        "Allowed categories for this batch:",
        ", ".join(allowed_categories),
        "",
        "Queries:",
    ]
    for sample in samples:
        lines.append(f'{sample["id"]}: {sample["text"]}')
    return "\n".join(lines)


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


def call_groq(model: str, samples: list[dict], retries: int, retry_sleep: float) -> tuple[dict[str, dict], float, dict, str]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise evaluator. Output valid JSON only.",
            },
            {"role": "user", "content": build_prompt(samples)},
        ],
        "temperature": 0,
        "max_completion_tokens": max(700, 180 * len(samples)),
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"}
    response = None
    start = time.perf_counter()
    with httpx.Client(timeout=120) as client:
        for attempt in range(retries + 1):
            response = client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
            if response.status_code != 429 or attempt >= retries:
                break
            sleep_for = retry_sleep * (attempt + 1)
            safe_print(f"Rate limited on {model}; sleeping {sleep_for:.0f}s before retry {attempt + 1}/{retries}.")
            time.sleep(sleep_for)
    latency = time.perf_counter() - start
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(redact_secret(str(exc)) + f" Body: {redact_secret(response.text[:1000])}") from exc
    data = response.json()
    text = data["choices"][0]["message"].get("content", "")
    parsed = parse_json(text)
    outputs = {str(row.get("id", "")).strip(): row for row in parsed.get("results", [])}
    return outputs, latency, data.get("usage", {}), text


def evaluate_sample(sample: dict, model: str, output: dict, latency: float, batch_size: int, usage: dict) -> dict:
    english = str(output.get("english", "")).strip()
    category = str(output.get("category", "")).strip()
    output_entities = output.get("entities", [])
    entity_text = " ".join([english, category, " ".join(str(item) for item in output_entities)])
    entities = expected_entities(sample)
    entity_result = entity_preservation(entities, entity_text)
    return {
        "id": sample["id"],
        "model": model,
        "reference_english": sample["translation"],
        "output_english": english,
        "reference_category": sample["category"],
        "output_category": category,
        "category_exact": category == sample["category"],
        "english_token_f1": round(token_f1(sample["translation"], english), 4),
        "entity_preservation": round(entity_result["score"], 4),
        "entities_expected": entities,
        "entities_missing": entity_result["missing"],
        "batch_latency_seconds": round(latency, 3),
        "amortized_latency_seconds": round(latency / max(batch_size, 1), 3),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for model in sorted({row["model"] for row in rows}):
        group = [row for row in rows if row["model"] == model]
        summary[model] = {
            "samples": len(group),
            "avg_english_token_f1": round(sum(row["english_token_f1"] for row in group) / len(group), 4),
            "avg_entity_preservation": round(sum(row["entity_preservation"] for row in group) / len(group), 4),
            "category_accuracy": round(sum(1 for row in group if row["category_exact"]) / len(group), 4),
            "avg_amortized_latency_seconds": round(sum(row["amortized_latency_seconds"] for row in group) / len(group), 4),
            "avg_batch_latency_seconds": round(sum(row["batch_latency_seconds"] for row in group) / len(group), 4),
        }
    return dict(sorted(summary.items(), key=lambda item: (-item[1]["avg_entity_preservation"], -item[1]["category_accuracy"], item[1]["avg_amortized_latency_seconds"])))


def write_csv(rows: list[dict], path: Path):
    fieldnames = [
        "id",
        "model",
        "batch_latency_seconds",
        "amortized_latency_seconds",
        "english_token_f1",
        "entity_preservation",
        "category_exact",
        "reference_category",
        "output_category",
        "entities_missing",
        "reference_english",
        "output_english",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def chunks(items: list[dict], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def parse_args():
    parser = argparse.ArgumentParser(description="Batch-evaluate Groq chat models on Yoruba fintech text.")
    parser.add_argument("--metadata", default=SCRATCH / "dispute_metadata.json", type=Path)
    parser.add_argument("--audio-dir", default=SCRATCH / "dispute_audio_fixed", type=Path)
    parser.add_argument("--out-json", default=SCRATCH / "groq_text_eval_report.json", type=Path)
    parser.add_argument("--out-csv", default=SCRATCH / "groq_text_eval_rows.csv", type=Path)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-sleep", type=float, default=20)
    parser.add_argument("--sleep-between-models", type=float, default=0)
    return parser.parse_args()


def main():
    args = parse_args()
    samples = load_dataset(args.metadata, args.audio_dir)
    if args.limit:
        samples = samples[: args.limit]

    rows = []
    failures = []
    for model in args.models:
        for batch in chunks(samples, args.batch_size):
            ids = ", ".join(sample["id"] for sample in batch)
            safe_print(f"Running {model} batch: {ids}")
            try:
                outputs, latency, usage, raw_text = call_groq(model, batch, args.retries, args.retry_sleep)
            except Exception as exc:
                error = redact_secret(str(exc))
                failures.append({"model": model, "ids": ids, "error": error})
                safe_print(f"Failed {model} {ids}: {error}")
                continue
            for sample in batch:
                rows.append(evaluate_sample(sample, model, outputs.get(sample["id"], {}), latency, len(batch), usage))
            missing = [sample["id"] for sample in batch if sample["id"] not in outputs]
            if missing:
                failures.append({"model": model, "ids": ids, "error": f"missing outputs: {missing}", "raw": raw_text})
            if args.sleep_between_models:
                time.sleep(args.sleep_between_models)

    report = {"summary": summarize(rows), "failures": failures, "rows": rows}
    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(rows, args.out_csv)
    safe_print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if failures:
        safe_print(f"Failures: {len(failures)}")
    safe_print(f"Wrote {args.out_json}")
    safe_print(f"Wrote {args.out_csv}")


if __name__ == "__main__":
    main()
