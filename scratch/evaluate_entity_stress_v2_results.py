import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from entity_correction import correct_entities

SCRATCH = ROOT / "scratch"
METADATA_PATH = SCRATCH / "entity_stress_v2_metadata.json"
RESULTS_PATH = SCRATCH / "entity_stress_v2_natlas_full_results.json"
OUT_PATH = SCRATCH / "entity_stress_v2_correction_eval.json"


def normalize(text):
    text = unicodedata.normalize("NFKD", text).lower()
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^\w\s+#-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def score_entities(expected, output):
    normalized = normalize(output)
    expected_normalized = [normalize(entity) for entity in expected]
    found = [
        original
        for original, normalized_entity in zip(expected, expected_normalized)
        if normalized_entity in normalized
    ]
    missing = [
        original
        for original, normalized_entity in zip(expected, expected_normalized)
        if normalized_entity not in normalized
    ]
    score = len(found) / len(expected) if expected else 1.0
    return score, found, missing


def main():
    metadata = {row["id"]: row for row in json.load(METADATA_PATH.open(encoding="utf-8"))}
    results = json.load(RESULTS_PATH.open(encoding="utf-8"))
    rows = []

    for row in results:
        sample = metadata[row["id"]]
        expected = sample["expected_entities"]
        raw_score, raw_found, raw_missing = score_entities(expected, row["output"])
        corrected = correct_entities(row["output"])
        corrected_score, corrected_found, corrected_missing = score_entities(
            expected,
            corrected["corrected_transcript"],
        )
        rows.append(
            {
                "id": row["id"],
                "category": sample["category"],
                "expected_entities": expected,
                "raw_output": row["output"],
                "corrected_output": corrected["corrected_transcript"],
                "raw_entity_preservation": raw_score,
                "corrected_entity_preservation": corrected_score,
                "raw_missing": raw_missing,
                "corrected_missing": corrected_missing,
                "corrections": corrected["corrections"],
                "correction_latency_ms": corrected["latency_ms"],
            }
        )

    raw_avg = sum(row["raw_entity_preservation"] for row in rows) / len(rows)
    corrected_avg = sum(row["corrected_entity_preservation"] for row in rows) / len(rows)
    latency_avg = sum(row["correction_latency_ms"] for row in rows) / len(rows)
    summary = {
        "samples": len(rows),
        "previous_original_benchmark": {
            "samples": 20,
            "raw_entity_preservation": 0.5375,
            "corrected_entity_preservation": 0.9875,
            "absolute_lift": 0.45
        },
        "previous_expanded_benchmark": {
            "samples": 40,
            "raw_entity_preservation": 0.2908,
            "corrected_entity_preservation": 0.8504,
            "absolute_lift": 0.5596
        },
        "entity_stress_v2": {
            "raw_entity_preservation": round(raw_avg, 4),
            "corrected_entity_preservation": round(corrected_avg, 4),
            "absolute_lift": round(corrected_avg - raw_avg, 4),
            "avg_correction_latency_ms": round(latency_avg, 4)
        }
    }
    OUT_PATH.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
