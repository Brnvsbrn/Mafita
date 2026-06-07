"""
Evaluate Gemini audio understanding on the existing Yoruba fintech benchmark.

This keeps the current app architecture unchanged. It only checks whether LLM
audio input can produce useful Yoruba transcripts and English meaning
translations from the same audio fixtures used by the ASR eval.

Example:
    python scratch/run_llm_audio_eval.py --models gemini-3.1-flash-lite gemini-3.5-flash --batch-size 5 --limit 20
"""

from __future__ import annotations

import argparse
import base64
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
sys.path.insert(0, str(ROOT / "src"))

from run_asr_eval import (  # noqa: E402
    char_error_rate,
    entity_preservation,
    expected_entities,
    load_dataset,
    token_f1,
    word_error_rate,
)

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

TARGETS = {
    "yoruba": {
        "prompt": (
            "You will receive multiple Yoruba customer-support audio clips. "
            "For each clip, transcribe exactly what the speaker said in Yoruba. "
            "Preserve fintech entities exactly when possible, including OPay, PalmPay, Moniepoint, Access Bank, BVN, NIN, KYC, USSD, ATM, Session ID. "
            "Do not explain. Return one line per clip using this exact format: "
            "Q01: transcription"
        ),
    },
    "english": {
        "prompt": (
            "You will receive multiple Yoruba customer-support audio clips. "
            "For each clip, translate the meaning into concise English. "
            "Preserve fintech entities exactly when possible, including OPay, PalmPay, Moniepoint, Access Bank, BVN, NIN, KYC, USSD, ATM, Session ID. "
            "Do not explain. Return one line per clip using this exact format: "
            "Q01: translation"
        ),
    },
}


def api_key() -> str:
    key = os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_GEMINI_KEY or GEMINI_API_KEY is not set.")
    return key


def audio_part(sample: dict) -> dict:
    audio_path = Path(sample["audio_path"])
    data = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    mime_type = "audio/wav" if audio_path.suffix.lower() == ".wav" else "audio/mpeg"
    return {"inlineData": {"mimeType": mime_type, "data": data}}


def batch_parts(samples: list[dict], target: str) -> list[dict]:
    parts = [
        {
            "text": (
                TARGETS[target]["prompt"]
                + "\n\nClip ids in order: "
                + ", ".join(sample["id"] for sample in samples)
            )
        }
    ]
    for sample in samples:
        parts.append({"text": f"Audio clip id: {sample['id']}"})
        parts.append(audio_part(sample))
    return parts


def call_gemini_batch(
    model: str,
    samples: list[dict],
    target: str,
    retries: int = 2,
    retry_sleep: float = 20,
) -> tuple[dict[str, str], float, str]:
    payload = {
        "contents": [{"role": "user", "parts": batch_parts(samples, target)}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": max(512, 160 * len(samples)),
        },
    }
    start = time.perf_counter()
    response = None
    for attempt in range(retries + 1):
        response = httpx.post(
            f"{GEMINI_BASE_URL}/models/{model}:generateContent",
            params={"key": api_key()},
            json=payload,
            timeout=180,
        )
        if response.status_code != 429 or attempt >= retries:
            break
        sleep_for = retry_sleep * (attempt + 1)
        safe_print(f"Rate limited on {model}; sleeping {sleep_for:.0f}s before retry {attempt + 1}/{retries}.")
        time.sleep(sleep_for)
    latency = time.perf_counter() - start
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(redact_secret(str(exc))) from exc
    data = response.json()
    parts = data["candidates"][0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    try:
        parsed = parse_output(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse model output: {exc}. Raw: {text[:1000]}") from exc
    outputs = {str(row.get("id", "")).strip(): str(row.get("text", "")).strip() for row in parsed.get("results", [])}
    return outputs, latency, text


def parse_output(text: str) -> dict:
    clean = str(text or "").strip()
    line_rows = parse_lines(clean)
    if line_rows:
        return {"results": line_rows}
    if clean.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, flags=re.DOTALL | re.IGNORECASE)
        if match:
            clean = match.group(1)
    if not clean.startswith("{"):
        start = clean.find("{")
        end = clean.rfind("}")
        if start >= 0 and end > start:
            clean = clean[start : end + 1]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        rows = parse_lines(clean)
        if rows:
            return {"results": rows}
        raise


def parse_lines(text: str) -> list[dict]:
    rows = []
    for line in str(text or "").splitlines():
        match = re.match(r'\s*[-*]?\s*"?([A-Za-z]\d{2})"?\s*[:=-]\s*"?(.*?)"?\s*,?\s*$', line)
        if match:
            value = match.group(2).strip().strip('"')
            if value:
                rows.append({"id": match.group(1), "text": value})
    return rows


def redact_secret(text: str) -> str:
    key = os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEY") or ""
    redacted = str(text)
    if key:
        redacted = redacted.replace(key, "[REDACTED]")
    return re.sub(r"key=[^&\s']+", "key=[REDACTED]", redacted)


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(str(text).encode("ascii", "backslashreplace").decode("ascii"))


def evaluate_sample(sample: dict, model: str, target: str, output: str, batch_latency: float, batch_size: int) -> dict:
    reference = sample["translation"] if target == "english" else sample["text"]
    entities = expected_entities(sample)
    entity_result = entity_preservation(entities, output)
    row = {
        "id": sample["id"],
        "audio_filename": sample["audio_filename"],
        "voice": sample["voice"],
        "category": sample["category"],
        "model": model,
        "target": target,
        "reference": reference,
        "output": output,
        "batch_latency_seconds": round(batch_latency, 3),
        "amortized_latency_seconds": round(batch_latency / max(batch_size, 1), 3),
        "entity_preservation": round(entity_result["score"], 4),
        "entities_expected": entities,
        "entities_found": entity_result["found"],
        "entities_missing": entity_result["missing"],
    }
    if target == "yoruba":
        row["wer"] = round(word_error_rate(reference, output), 4)
        row["cer"] = round(char_error_rate(reference, output), 4)
        row["english_token_f1"] = None
    else:
        row["wer"] = None
        row["cer"] = None
        row["english_token_f1"] = round(token_f1(reference, output), 4)
    return row


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for model in sorted({row["model"] for row in rows}):
        for target in sorted({row["target"] for row in rows if row["model"] == model}):
            key = f"{model}:{target}"
            group = [row for row in rows if row["model"] == model and row["target"] == target]
            summary[key] = {"samples": len(group)}
            for metric in ["wer", "cer", "english_token_f1", "entity_preservation", "amortized_latency_seconds"]:
                values = [row[metric] for row in group if row.get(metric) is not None]
                if values:
                    summary[key][f"avg_{metric}"] = round(sum(values) / len(values), 4)
    return summary


def write_csv(rows: list[dict], path: Path):
    fieldnames = [
        "id",
        "audio_filename",
        "voice",
        "category",
        "model",
        "target",
        "batch_latency_seconds",
        "amortized_latency_seconds",
        "wer",
        "cer",
        "english_token_f1",
        "entity_preservation",
        "entities_missing",
        "reference",
        "output",
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
    parser = argparse.ArgumentParser(description="Batch-evaluate Gemini audio transcription on Yoruba fintech clips.")
    parser.add_argument("--metadata", default=SCRATCH / "dispute_metadata.json", type=Path)
    parser.add_argument("--audio-dir", default=SCRATCH / "dispute_audio_fixed", type=Path)
    parser.add_argument("--out-json", default=SCRATCH / "llm_audio_eval_report.json", type=Path)
    parser.add_argument("--out-csv", default=SCRATCH / "llm_audio_eval_rows.csv", type=Path)
    parser.add_argument("--models", nargs="+", default=["gemini-3.1-flash-lite", "gemini-3.5-flash"])
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-sleep", type=float, default=20)
    parser.add_argument("--sleep-between-batches", type=float, default=0)
    return parser.parse_args()


def main():
    args = parse_args()
    samples = load_dataset(args.metadata, args.audio_dir)
    if args.limit:
        samples = samples[: args.limit]

    rows = []
    failures = []
    for model in args.models:
        for target in ["yoruba", "english"]:
            for batch in chunks(samples, args.batch_size):
                ids = ", ".join(sample["id"] for sample in batch)
                safe_print(f"Running {model} {target} batch: {ids}")
                try:
                    outputs, latency, raw_text = call_gemini_batch(
                        model,
                        batch,
                        target,
                        retries=args.retries,
                        retry_sleep=args.retry_sleep,
                    )
                except Exception as exc:
                    error = redact_secret(str(exc))
                    failures.append({"model": model, "target": target, "ids": ids, "error": error})
                    safe_print(f"Failed {model} {target} {ids}: {error}")
                    continue
                for sample in batch:
                    output = outputs.get(sample["id"], "")
                    rows.append(evaluate_sample(sample, model, target, output, latency, len(batch)))
                missing = [sample["id"] for sample in batch if sample["id"] not in outputs]
                if missing:
                    failures.append({"model": model, "target": target, "ids": ids, "error": f"missing outputs: {missing}", "raw": raw_text})
                if args.sleep_between_batches:
                    time.sleep(args.sleep_between_batches)

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
