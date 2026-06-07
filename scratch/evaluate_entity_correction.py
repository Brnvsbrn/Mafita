import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from entity_correction import correct_entities

SCRATCH = ROOT / "scratch"
METADATA_PATH = SCRATCH / "dispute_metadata.json"
NATLAS_PATH = SCRATCH / "natlas_full_results.json"
OUT_PATH = SCRATCH / "entity_correction_eval.json"
LEXICON_PATH = ROOT / "src" / "entity_lexicon.json"

PREVIOUS_SEED_RESULT = {
    "raw_avg_entity_preservation": 0.5375,
    "corrected_avg_entity_preservation": 0.9875,
    "absolute_lift": 0.45,
    "avg_correction_latency_ms": 5.4883
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


def load_expanded_entities():
    lexicon = json.load(LEXICON_PATH.open(encoding="utf-8"))
    excluded_types = {"support_term", "payment_term", "account_term", "status", "security_term", "fraud_term", "transfer_issue", "transfer_term", "legal_term"}
    entities = []
    for entity in lexicon["entities"]:
        if entity["type"] in excluded_types:
            continue
        entities.append(normalize(entity["canonical"]))
    return sorted(set(entities), key=len, reverse=True)


def normalize(text):
    text = unicodedata.normalize("NFKD", text).lower()
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^\w\s+#-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def expected_entities(sample):
    text = normalize(f"{sample['text']} {sample['translation']} {sample['category']}")
    return sorted({entity for entity in BRAND_ENTITIES if entity in text})


def expected_expanded_entities(sample, expanded_entities):
    text = normalize(f"{sample['text']} {sample['translation']} {sample['category']}")
    return sorted({entity for entity in expanded_entities if entity in text})


def entity_score(expected, output):
    normalized = normalize(output)
    found = [entity for entity in expected if entity in normalized]
    missing = [entity for entity in expected if entity not in normalized]
    score = len(found) / len(expected) if expected else 1.0
    return score, found, missing


def main():
    metadata = {row["id"]: row for row in json.load(METADATA_PATH.open(encoding="utf-8"))}
    natlas = json.load(NATLAS_PATH.open(encoding="utf-8"))
    expanded_entities = load_expanded_entities()
    rows = []

    for row in natlas:
        sample = metadata[row["id"]]
        expected = expected_entities(sample)
        expanded_expected = expected_expanded_entities(sample, expanded_entities)
        raw_score, raw_found, raw_missing = entity_score(expected, row["output"])
        expanded_raw_score, expanded_raw_found, expanded_raw_missing = entity_score(expanded_expected, row["output"])
        corrected = correct_entities(row["output"])
        corrected_score, corrected_found, corrected_missing = entity_score(
            expected,
            corrected["corrected_transcript"],
        )
        expanded_corrected_score, expanded_corrected_found, expanded_corrected_missing = entity_score(
            expanded_expected,
            corrected["corrected_transcript"],
        )
        rows.append(
            {
                "id": row["id"],
                "category": sample["category"],
                "expected_entities": expected,
                "expanded_expected_entities": expanded_expected,
                "raw_output": row["output"],
                "corrected_output": corrected["corrected_transcript"],
                "raw_entity_preservation": raw_score,
                "corrected_entity_preservation": corrected_score,
                "expanded_raw_entity_preservation": expanded_raw_score,
                "expanded_corrected_entity_preservation": expanded_corrected_score,
                "raw_missing": raw_missing,
                "corrected_missing": corrected_missing,
                "expanded_raw_missing": expanded_raw_missing,
                "expanded_corrected_missing": expanded_corrected_missing,
                "corrections": corrected["corrections"],
                "needs_confirmation": corrected["needs_confirmation"],
                "correction_latency_ms": corrected["latency_ms"],
            }
        )

    raw_avg = sum(row["raw_entity_preservation"] for row in rows) / len(rows)
    corrected_avg = sum(row["corrected_entity_preservation"] for row in rows) / len(rows)
    expanded_raw_values = [
        row["expanded_raw_entity_preservation"]
        for row in rows
        if row["expanded_expected_entities"]
    ]
    expanded_corrected_values = [
        row["expanded_corrected_entity_preservation"]
        for row in rows
        if row["expanded_expected_entities"]
    ]
    latency_avg = sum(row["correction_latency_ms"] for row in rows) / len(rows)
    summary = {
        "samples": len(rows),
        "previous_seed_lexicon_result": PREVIOUS_SEED_RESULT,
        "current_robust_lexicon_result": {
            "metric_note": "Critical benchmark entity metric is kept comparable with previous result.",
            "raw_avg_entity_preservation": round(raw_avg, 4),
            "corrected_avg_entity_preservation": round(corrected_avg, 4),
            "absolute_lift": round(corrected_avg - raw_avg, 4),
            "avg_correction_latency_ms": round(latency_avg, 4)
        },
        "expanded_domain_entity_result": {
            "metric_note": "Broader domain metric uses expanded lexicon entities that appear in the existing 20-sample metadata.",
            "raw_avg_entity_preservation": round(sum(expanded_raw_values) / len(expanded_raw_values), 4) if expanded_raw_values else None,
            "corrected_avg_entity_preservation": round(sum(expanded_corrected_values) / len(expanded_corrected_values), 4) if expanded_corrected_values else None,
            "absolute_lift": round((sum(expanded_corrected_values) / len(expanded_corrected_values)) - (sum(expanded_raw_values) / len(expanded_raw_values)), 4) if expanded_raw_values else None
        },
        "raw_avg_entity_preservation": round(raw_avg, 4),
        "corrected_avg_entity_preservation": round(corrected_avg, 4),
        "absolute_lift": round(corrected_avg - raw_avg, 4),
        "avg_correction_latency_ms": round(latency_avg, 4),
    }

    OUT_PATH.write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
