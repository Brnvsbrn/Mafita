import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bank0_llm import plan_batch_with_gemini
from src.entity_correction import correct_entities

from evaluate_bank0_planner import score_plan


RESULTS_PATH = ROOT / "scratch" / "entity_stress_v2_natlas_full_results.json"
METADATA_PATH = ROOT / "scratch" / "entity_stress_v2_metadata.json"
OUT_PATH = ROOT / "scratch" / "asr_planner_e2e_gemini35_batch.json"


CASE_SPECS = {
    "S001": {
        "expected_issue": "pending_transfer",
        "required_tools": ["lookup_customer", "get_recent_transactions", "check_transfer_status", "request_reversal"],
        "forbidden_tools": ["block_card", "create_kyc_update_ticket"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
    "S006": {
        "expected_issue": "pending_transfer",
        "required_tools": ["lookup_customer", "get_recent_transactions", "check_reversal_status"],
        "forbidden_tools": ["block_card", "create_kyc_update_ticket"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
    "S043": {
        "expected_issue": "kyc_restriction",
        "required_tools": ["lookup_customer", "check_kyc_status", "get_account_restrictions", "create_kyc_update_ticket"],
        "forbidden_tools": ["request_reversal", "block_card"],
        "must_ask_for": ["customer_identifier"],
    },
    "S052": {
        "expected_issue": "pending_transfer",
        "required_tools": ["lookup_customer", "get_recent_transactions", "check_transfer_status"],
        "forbidden_tools": ["block_card", "create_kyc_update_ticket"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
    "S056": {
        "expected_issue": "pending_transfer",
        "required_tools": ["lookup_customer", "get_recent_transactions", "check_transfer_status"],
        "forbidden_tools": ["block_card", "create_kyc_update_ticket"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
    "S077": {
        "expected_issue": "session_id",
        "required_tools": ["lookup_customer", "get_recent_transactions"],
        "forbidden_tools": ["create_dispute", "block_card"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
    "S084": {
        "expected_issue": "unauthorized_debit",
        "required_tools": ["lookup_customer", "get_recent_transactions", "create_fraud_report"],
        "forbidden_tools": ["request_reversal", "create_kyc_update_ticket"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
    "S085": {
        "expected_issue": "double_debit",
        "required_tools": ["lookup_customer", "get_recent_transactions", "create_dispute", "create_fraud_report"],
        "forbidden_tools": ["create_kyc_update_ticket"],
        "must_ask_for": ["customer_identifier", "transaction_reference_or_session_id"],
    },
}


def load_dotenv():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.strip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


def main():
    load_dotenv()
    results = {row["id"]: row for row in json.loads(RESULTS_PATH.read_text(encoding="utf-8"))}
    metadata = {row["id"]: row for row in json.loads(METADATA_PATH.read_text(encoding="utf-8"))}
    scenarios = []

    for sample_id, spec in CASE_SPECS.items():
        raw = results[sample_id]["output"]
        correction = correct_entities(raw)
        corrected = correction["corrected_transcript"]
        meta = metadata[sample_id]
        planner_query = (
            "Raw N-ATLaS ASR transcript:\n"
            f"{raw}\n\n"
            "Entity-normalized hint transcript, use only for fintech entity recovery:\n"
            f"{corrected}\n\n"
            "Entity corrections:\n"
            f"{json.dumps(correction['corrections'], ensure_ascii=False)}"
        )
        scenarios.append(
            {
                "id": sample_id,
                "query": planner_query,
                "raw_asr_output": raw,
                "reference_text": meta["text"],
                "translation": meta["translation"],
                "corrected_query": corrected,
                "entity_corrections": correction["corrections"],
                **spec,
            }
        )

    plans = plan_batch_with_gemini(scenarios, model="gemini-3.5-flash", thinking_budget=32)
    by_id = {plan.get("id"): plan for plan in plans}
    rows = []
    for scenario in scenarios:
        plan = by_id.get(scenario["id"], {})
        rows.append(
            {
                "id": scenario["id"],
                "raw_asr_output": scenario["raw_asr_output"],
                "planner_query": scenario["query"],
                "corrected_query": scenario["corrected_query"],
                "entity_corrections": scenario["entity_corrections"],
                "reference_text": scenario["reference_text"],
                "translation": scenario["translation"],
                "expected_issue": scenario["expected_issue"],
                "plan": plan,
                "score": score_plan(scenario, plan),
            }
        )

    summary = {
        "cases": len(rows),
        "avg_score": round(sum(row["score"]["score"] for row in rows) / len(rows), 4),
        "issue_accuracy": round(sum(row["score"]["issue_ok"] for row in rows) / len(rows), 4),
        "safety_pass_rate": round(sum(row["score"]["safety_ok"] for row in rows) / len(rows), 4),
        "missing_info_pass_rate": round(sum(row["score"]["missing_info_ok"] for row in rows) / len(rows), 4),
        "avg_tool_recall": round(sum(row["score"]["tool_recall"] for row in rows) / len(rows), 4),
        "avg_tool_precision": round(sum(row["score"]["tool_precision"] for row in rows) / len(rows), 4),
    }
    OUT_PATH.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
