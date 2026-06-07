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

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


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


def call_audio(model: str, audio_path: Path, task: str) -> tuple[str, float]:
    endpoint = "translations" if task == "translate" else "transcriptions"
    data = {"model": model, "response_format": "json"}
    if task == "transcribe":
        data["language"] = "yo"
    headers = {"Authorization": f"Bearer {api_key()}"}
    start = time.perf_counter()
    with audio_path.open("rb") as f:
        response = httpx.post(
            f"{GROQ_BASE_URL}/audio/{endpoint}",
            headers=headers,
            data=data,
            files={"file": (audio_path.name, f, "audio/wav")},
            timeout=120,
        )
    latency = time.perf_counter() - start
    response.raise_for_status()
    return response.json().get("text", "").strip(), latency


def evaluate_sample(sample: dict, model: str, task: str, output: str, latency: float) -> dict:
    target = "english" if task == "translate" else "yoruba"
    reference = sample["translation"] if target == "english" else sample["text"]
    entity_result = entity_preservation(expected_entities(sample), output)
    row = {
        "id": sample["id"],
        "model": model,
        "task": task,
        "target": target,
        "latency_seconds": round(latency, 3),
        "reference": reference,
        "output": output,
        "entity_preservation": round(entity_result["score"], 4),
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
        for task in sorted({row["task"] for row in rows if row["model"] == model}):
            group = [row for row in rows if row["model"] == model and row["task"] == task]
            item = {"samples": len(group)}
            for key in ["latency_seconds", "wer", "cer", "english_token_f1", "entity_preservation"]:
                vals = [row[key] for row in group if row.get(key) is not None]
                if vals:
                    item[f"avg_{key}"] = round(sum(vals) / len(vals), 4)
            summary[f"{model}:{task}"] = item
    return summary


def write_csv(rows: list[dict], path: Path):
    fields = ["id", "model", "task", "target", "latency_seconds", "wer", "cer", "english_token_f1", "entity_preservation", "entities_missing", "reference", "output"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", default=SCRATCH / "dispute_metadata.json", type=Path)
    parser.add_argument("--audio-dir", default=SCRATCH / "dispute_audio_fixed", type=Path)
    parser.add_argument("--models", nargs="+", default=["whisper-large-v3", "whisper-large-v3-turbo"])
    parser.add_argument("--tasks", nargs="+", default=["transcribe", "translate"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--out-json", default=SCRATCH / "groq_whisper_eval_report.json", type=Path)
    parser.add_argument("--out-csv", default=SCRATCH / "groq_whisper_eval_rows.csv", type=Path)
    args = parser.parse_args()

    samples = load_dataset(args.metadata, args.audio_dir)[: args.limit]
    rows = []
    failures = []
    for model in args.models:
        for task in args.tasks:
            for sample in samples:
                try:
                    output, latency = call_audio(model, Path(sample["audio_path"]), task)
                    rows.append(evaluate_sample(sample, model, task, output, latency))
                    print(f"{model} {task} {sample['id']} {latency:.2f}s")
                except Exception as exc:
                    error = redact_secret(f"{type(exc).__name__}: {exc}")
                    failures.append({"model": model, "task": task, "id": sample["id"], "error": error})
                    print(f"FAILED {model} {task} {sample['id']}: {error}")
    report = {"summary": summarize(rows), "failures": failures, "rows": rows}
    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(rows, args.out_csv)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if failures:
        print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
