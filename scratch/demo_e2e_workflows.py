import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bank0_executor import execute_validated_plan


INPUT_PATH = ROOT / "scratch" / "asr_planner_e2e_gemini35_validated.json"
OUT_PATH = ROOT / "scratch" / "e2e_workflow_examples.json"
EXAMPLE_IDS = ["S001", "S043", "S056", "S077", "S085"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    examples = []
    for row in data["rows"]:
        if row["id"] not in EXAMPLE_IDS:
            continue
        execution = execute_validated_plan(row["plan"], row.get("planner_query") or row.get("corrected_query", ""), dry_run=True)
        examples.append(
            {
                "id": row["id"],
                "reference_text": row["reference_text"],
                "raw_asr_output": row["raw_asr_output"],
                "corrected_query": row["corrected_query"],
                "gemini_raw_plan": row["raw_plan"],
                "validated_plan": row["plan"],
                "execution": execution,
            }
        )

    OUT_PATH.write_text(json.dumps(examples, indent=2, ensure_ascii=False), encoding="utf-8")
    for item in examples:
        print("\n" + "=" * 90)
        print(item["id"])
        print("Reference:", item["reference_text"])
        print("Raw ASR:", item["raw_asr_output"])
        print("Corrected:", item["corrected_query"])
        print("Gemini:", item["gemini_raw_plan"].get("issue_type"), item["gemini_raw_plan"].get("recommended_tools"))
        print("Validated:", item["validated_plan"].get("issue_type"), item["validated_plan"].get("recommended_tools"))
        print("Decision:", item["execution"]["decision"])
        print("Tools executed:", item["execution"]["tools_executed"])
        print("English:", item["execution"]["final_response"]["english"])
        print("Yoruba:", item["execution"]["final_response"]["yoruba"])
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
