"""
Kaggle/Colab harness for the YPIT Yoruba fintech ASR benchmark.

Primary comparison:
- N-ATLaS ASR: localized Yoruba speech recognition.
- Whisper Large-v3: global multilingual baseline.

The benchmark keeps two references per sample:
- Yoruba source text: used for ASR WER/CER.
- English meaning: used for the final native-audio-to-English task.

Run on Kaggle/Colab:
    pip install -q transformers accelerate datasets soundfile jiwer
    python run_asr_eval.py --audio-dir dispute_audio_fixed --metadata dispute_metadata.json

If you only have the zip:
    unzip yoruba_fintech_benchmark.zip
    python run_asr_eval.py --audio-dir dispute_audio --metadata dispute_metadata.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import unicodedata
from pathlib import Path

try:
    from jiwer import cer, wer
except ImportError:
    cer = None
    wer = None


MODEL_SPECS = {
    "natlas_yoruba_asr": {
        "model": "NCAIR1/Yoruba-ASR",
        "task": "automatic-speech-recognition",
        "generate_kwargs": {},
        "target": "yoruba",
    },
    "whisper_large_v3_yoruba_asr": {
        "model": "openai/whisper-large-v3",
        "task": "automatic-speech-recognition",
        "generate_kwargs": {"language": "yoruba", "task": "transcribe"},
        "target": "yoruba",
    },
    "whisper_large_v3_english_translate": {
        "model": "openai/whisper-large-v3",
        "task": "automatic-speech-recognition",
        "generate_kwargs": {"language": "yoruba", "task": "translate"},
        "target": "english",
    },
}

BRAND_ENTITIES = [
    "opay",
    "palmpay",
    "moniepoint",
    "access bank",
    "bvn",
    "nin",
    "kyc",
    "ussd",
    "atm",
    "session id",
]


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s+#-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def levenshtein(a: list[str], b: list[str]) -> int:
    previous = list(range(len(b) + 1))
    for i, token_a in enumerate(a, start=1):
        current = [i]
        for j, token_b in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (token_a != token_b)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]


def fallback_error_rate(reference: str, hypothesis: str, char_level: bool = False) -> float:
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)
    ref_units = list(ref) if char_level else ref.split()
    hyp_units = list(hyp) if char_level else hyp.split()
    if not ref_units:
        return 0.0 if not hyp_units else 1.0
    return levenshtein(ref_units, hyp_units) / len(ref_units)


def word_error_rate(reference: str, hypothesis: str) -> float:
    if wer:
        return float(wer(normalize_text(reference), normalize_text(hypothesis)))
    return fallback_error_rate(reference, hypothesis)


def char_error_rate(reference: str, hypothesis: str) -> float:
    if cer:
        return float(cer(normalize_text(reference), normalize_text(hypothesis)))
    return fallback_error_rate(reference, hypothesis, char_level=True)


def token_f1(reference: str, hypothesis: str) -> float:
    ref_tokens = normalize_text(reference).split()
    hyp_tokens = normalize_text(hypothesis).split()
    if not ref_tokens and not hyp_tokens:
        return 1.0
    if not ref_tokens or not hyp_tokens:
        return 0.0

    ref_counts = {}
    for token in ref_tokens:
        ref_counts[token] = ref_counts.get(token, 0) + 1

    overlap = 0
    for token in hyp_tokens:
        if ref_counts.get(token, 0):
            overlap += 1
            ref_counts[token] -= 1

    precision = overlap / len(hyp_tokens)
    recall = overlap / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def expected_entities(sample: dict) -> list[str]:
    combined = f"{sample['text']} {sample['translation']} {sample['category']}"
    normalized = normalize_text(strip_diacritics(combined))
    entities = [entity for entity in BRAND_ENTITIES if entity in normalized]
    entities.extend(re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", normalized))
    return sorted(set(entities))


def entity_preservation(expected: list[str], hypothesis: str) -> dict:
    hyp = normalize_text(strip_diacritics(hypothesis))
    found = [entity for entity in expected if entity in hyp]
    missing = [entity for entity in expected if entity not in hyp]
    score = len(found) / len(expected) if expected else 1.0
    return {"score": score, "found": found, "missing": missing}


def load_dataset(metadata_path: Path, audio_dir: Path) -> list[dict]:
    with metadata_path.open("r", encoding="utf-8") as f:
        records = json.load(f)

    samples = []
    for record in records:
        audio_path = audio_dir / record["audio_filename"]
        if not audio_path.exists():
            raise FileNotFoundError(f"Missing audio for {record['id']}: {audio_path}")
        samples.append({**record, "audio_path": str(audio_path)})
    return samples


def build_pipelines(model_names: list[str], device: int, torch_dtype):
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

    loaded = {}
    for model_name in model_names:
        spec = MODEL_SPECS[model_name]
        print(f"Loading {model_name}: {spec['model']}")
        if "whisper" in model_name:
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                spec["model"],
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            model.to("cuda:0" if device == 0 else "cpu")
            processor = AutoProcessor.from_pretrained(spec["model"])
            loaded[model_name] = {
                "kind": "whisper_direct",
                "model": model,
                "processor": processor,
                "device": "cuda:0" if device == 0 else "cpu",
                "dtype": torch_dtype,
            }
            continue

        loaded[model_name] = pipeline(
            spec["task"],
            model=spec["model"],
            device=device,
            torch_dtype=torch_dtype,
        )
        if "whisper" in model_name and hasattr(loaded[model_name], "generation_config"):
            loaded[model_name].generation_config.return_timestamps = False
            loaded[model_name].model.generation_config.return_timestamps = False
    return loaded


def run_model(model_name: str, pipe, audio_path: str) -> tuple[str, float]:
    import librosa

    generate_kwargs = MODEL_SPECS[model_name]["generate_kwargs"]
    start = time.perf_counter()
    if isinstance(pipe, dict) and pipe.get("kind") == "whisper_direct":
        audio, _ = librosa.load(audio_path, sr=16000, mono=True)
        processor = pipe["processor"]
        model = pipe["model"]
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
        input_features = inputs.input_features.to(pipe["device"], dtype=pipe["dtype"])

        task = generate_kwargs.get("task", "transcribe")
        forced_decoder_ids = processor.get_decoder_prompt_ids(language="yoruba", task=task)
        generated_ids = model.generate(
            input_features,
            forced_decoder_ids=forced_decoder_ids,
            max_new_tokens=128,
        )
        transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return transcription, time.perf_counter() - start

    call_kwargs = {"generate_kwargs": generate_kwargs}
    if "whisper" in model_name:
        call_kwargs["return_timestamps"] = False
    result = pipe(audio_path, **call_kwargs)
    latency = time.perf_counter() - start
    return result.get("text", "").strip(), latency


def evaluate_sample(sample: dict, model_name: str, transcription: str, latency: float) -> dict:
    target = MODEL_SPECS[model_name]["target"]
    reference = sample["translation"] if target == "english" else sample["text"]
    entities = expected_entities(sample)
    entity_result = entity_preservation(entities, transcription)

    result = {
        "id": sample["id"],
        "audio_filename": sample["audio_filename"],
        "voice": sample["voice"],
        "category": sample["category"],
        "model": model_name,
        "target": target,
        "reference": reference,
        "transcription": transcription,
        "latency_seconds": round(latency, 3),
        "entity_preservation": round(entity_result["score"], 4),
        "entities_expected": entities,
        "entities_found": entity_result["found"],
        "entities_missing": entity_result["missing"],
    }

    if target == "yoruba":
        result["wer"] = round(word_error_rate(reference, transcription), 4)
        result["cer"] = round(char_error_rate(reference, transcription), 4)
        result["english_token_f1"] = None
    else:
        result["wer"] = None
        result["cer"] = None
        result["english_token_f1"] = round(token_f1(reference, transcription), 4)

    return result


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for model in sorted({row["model"] for row in rows}):
        model_rows = [row for row in rows if row["model"] == model]
        numeric_keys = ["wer", "cer", "english_token_f1", "entity_preservation", "latency_seconds"]
        summary[model] = {"samples": len(model_rows)}
        for key in numeric_keys:
            values = [row[key] for row in model_rows if row.get(key) is not None]
            if values:
                summary[model][f"avg_{key}"] = round(sum(values) / len(values), 4)
    return summary


def write_csv(rows: list[dict], path: Path):
    fieldnames = [
        "id",
        "audio_filename",
        "voice",
        "category",
        "model",
        "target",
        "latency_seconds",
        "wer",
        "cer",
        "english_token_f1",
        "entity_preservation",
        "entities_missing",
        "reference",
        "transcription",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate N-ATLaS vs Whisper on YPIT Yoruba fintech audio.")
    parser.add_argument("--metadata", default="dispute_metadata.json", type=Path)
    parser.add_argument("--audio-dir", default="dispute_audio_fixed", type=Path)
    parser.add_argument("--out-json", default="asr_evaluation_report.json", type=Path)
    parser.add_argument("--out-csv", default="asr_evaluation_report.csv", type=Path)
    parser.add_argument(
        "--models",
        nargs="+",
        default=[
            "natlas_yoruba_asr",
            "whisper_large_v3_yoruba_asr",
            "whisper_large_v3_english_translate",
        ],
        choices=sorted(MODEL_SPECS),
    )
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    import torch

    samples = load_dataset(args.metadata, args.audio_dir)
    if args.limit:
        samples = samples[: args.limit]

    device = 0 if torch.cuda.is_available() else -1
    torch_dtype = torch.float16 if device == 0 else torch.float32
    print(f"Device: {'cuda:0' if device == 0 else 'cpu'}")
    pipes = build_pipelines(args.models, device, torch_dtype)

    rows = []
    for sample in samples:
        print(f"\nSample {sample['id']}: {sample['audio_filename']}")
        for model_name, pipe in pipes.items():
            print(f"  Running {model_name}...")
            transcription, latency = run_model(model_name, pipe, sample["audio_path"])
            rows.append(evaluate_sample(sample, model_name, transcription, latency))
            print(f"    {latency:.2f}s | {transcription[:120]}")

    report = {"summary": summarize(rows), "results": rows}
    with args.out_json.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    write_csv(rows, args.out_csv)

    print("\nSummary")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    print(f"\nSaved {args.out_json} and {args.out_csv}")


if __name__ == "__main__":
    main()
