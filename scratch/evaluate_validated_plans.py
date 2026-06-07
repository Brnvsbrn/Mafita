import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bank0_validator import validate_plan
from evaluate_bank0_planner import score_plan


def summarize(rows):
    return {
        "cases": len(rows),
        "avg_score": round(sum(row["score"]["score"] for row in rows) / len(rows), 4),
        "issue_accuracy": round(sum(row["score"]["issue_ok"] for row in rows) / len(rows), 4),
        "safety_pass_rate": round(sum(row["score"]["safety_ok"] for row in rows) / len(rows), 4),
        "missing_info_pass_rate": round(sum(row["score"]["missing_info_ok"] for row in rows) / len(rows), 4),
        "avg_tool_recall": round(sum(row["score"]["tool_recall"] for row in rows) / len(rows), 4),
        "avg_tool_precision": round(sum(row["score"]["tool_precision"] for row in rows) / len(rows), 4),
    }


def scenario_from_row(row):
    return {
        "expected_issue": row["expected_issue"],
        "required_tools": row["score"]["missing_required_tools"] + [
            tool for tool in row["plan"].get("recommended_tools", [])
            if tool not in row["score"]["forbidden_tools_present"]
        ],
        "forbidden_tools": row["score"]["forbidden_tools_present"],
        "must_ask_for": row["score"]["missing_identifier_requests"] + row["plan"].get("needed_identifiers", []),
    }


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python scratch/evaluate_validated_plans.py INPUT_JSON OUTPUT_JSON")
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    data = json.loads(in_path.read_text(encoding="utf-8"))
    rows = []

    for row in data["rows"]:
        query = row.get("corrected_query") or row.get("query") or ""
        scenario = scenario_from_row(row)
        validated = validate_plan(row["plan"], query)
        rows.append(
            {
                **row,
                "raw_plan": row["plan"],
                "plan": validated,
                "score": score_plan(scenario, validated),
            }
        )

    result = {
        "input": str(in_path),
        "raw_summary": data.get("summary"),
        "validated_summary": summarize(rows),
        "rows": rows,
    }
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"raw": result["raw_summary"], "validated": result["validated_summary"]}, indent=2, ensure_ascii=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
