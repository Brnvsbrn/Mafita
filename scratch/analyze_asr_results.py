import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "dispute_metadata.json"
WHISPER_PATH = ROOT / "whisper_full_results.json"
NATLAS_PATH = ROOT / "natlas_full_results.json"
OUT_JSON = ROOT / "asr_comparison_summary.json"
OUT_CSV = ROOT / "asr_comparison_rows.csv"

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


def normalize(text):
    text = unicodedata.normalize("NFKD", text).lower()
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^\w\s+#-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def levenshtein(a, b):
    previous = list(range(len(b) + 1))
    for i, item_a in enumerate(a, start=1):
        current = [i]
        for j, item_b in enumerate(b, start=1):
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (item_a != item_b),
                )
            )
        previous = current
    return previous[-1]


def wer(reference, output):
    ref = normalize(reference).split()
    hyp = normalize(output).split()
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)


def cer(reference, output):
    ref = list(normalize(reference))
    hyp = list(normalize(output))
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)


def token_f1(reference, output):
    ref_tokens = set(normalize(reference).split())
    hyp_tokens = set(normalize(output).split())
    if not ref_tokens and not hyp_tokens:
        return 1.0
    if not ref_tokens or not hyp_tokens:
        return 0.0
    overlap = len(ref_tokens & hyp_tokens)
    precision = overlap / len(hyp_tokens)
    recall = overlap / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def expected_entities(sample):
    text = normalize(f"{sample['text']} {sample['translation']} {sample['category']}")
    entities = {entity for entity in BRAND_ENTITIES if entity in text}
    entities.update(re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", text))
    return sorted(entities)


def entity_score(expected, output):
    out = normalize(output)
    found = [entity for entity in expected if entity in out]
    missing = [entity for entity in expected if entity not in out]
    score = len(found) / len(expected) if expected else 1.0
    return score, found, missing


def load_rows():
    metadata = {row["id"]: row for row in json.load(METADATA_PATH.open(encoding="utf-8"))}
    whisper = json.load(WHISPER_PATH.open(encoding="utf-8"))
    natlas = json.load(NATLAS_PATH.open(encoding="utf-8"))

    rows = []
    for row in whisper:
        sample = metadata[row["id"]]
        task = row["task"]
        reference = sample["translation"] if task == "translate" else sample["text"]
        expected = expected_entities(sample)
        e_score, found, missing = entity_score(expected, row["output"])
        rows.append(
            {
                "id": row["id"],
                "category": sample["category"],
                "model": f"whisper_{task}",
                "target": "english" if task == "translate" else "yoruba",
                "reference": reference,
                "output": row["output"],
                "latency_seconds": row["latency_seconds"],
                "wer": wer(reference, row["output"]) if task == "transcribe" else None,
                "cer": cer(reference, row["output"]) if task == "transcribe" else None,
                "english_token_f1": token_f1(reference, row["output"]) if task == "translate" else None,
                "entity_preservation": e_score,
                "entities_expected": expected,
                "entities_found": found,
                "entities_missing": missing,
            }
        )

    for row in natlas:
        sample = metadata[row["id"]]
        expected = expected_entities(sample)
        e_score, found, missing = entity_score(expected, row["output"])
        rows.append(
            {
                "id": row["id"],
                "category": sample["category"],
                "model": "natlas_transcribe",
                "target": "yoruba",
                "reference": sample["text"],
                "output": row["output"],
                "latency_seconds": row["latency_seconds"],
                "wer": wer(sample["text"], row["output"]),
                "cer": cer(sample["text"], row["output"]),
                "english_token_f1": None,
                "entity_preservation": e_score,
                "entities_expected": expected,
                "entities_found": found,
                "entities_missing": missing,
            }
        )

    return rows


def summarize(rows):
    summary = {}
    for model in sorted({row["model"] for row in rows}):
        model_rows = [row for row in rows if row["model"] == model]
        summary[model] = {"samples": len(model_rows)}
        for key in ["latency_seconds", "wer", "cer", "english_token_f1", "entity_preservation"]:
            values = [row[key] for row in model_rows if row[key] is not None]
            if values:
                summary[model][f"avg_{key}"] = round(sum(values) / len(values), 4)
    return summary


def write_csv(rows):
    fields = [
        "id",
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
        "output",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = row.copy()
            out["entities_missing"] = "; ".join(out["entities_missing"])
            writer.writerow({field: out.get(field) for field in fields})


def main():
    rows = load_rows()
    summary = summarize(rows)
    OUT_JSON.write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_csv(rows)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
