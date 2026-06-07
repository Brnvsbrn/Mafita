import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import _detect_issue, _extract_known_customer_name, _extract_phone, _extract_reference
from src.bank0_llm import MissingGroqKey, plan_batch_with_gemini, plan_batch_with_groq, plan_with_cencori, plan_with_gemini
from src.cencori_client import MissingCencoriKey
from src.gemini_client import MissingGeminiKey


SCENARIOS_PATH = ROOT / "scratch" / "bank0_planner_scenarios.json"
OUT_PATH = ROOT / "scratch" / "bank0_planner_eval_results.json"


ISSUE_TO_TOOLS = {
    "failed_transfer": ["get_transaction_by_reference", "check_transfer_status", "create_dispute", "request_reversal"],
    "pending_transfer": ["get_transaction_by_reference", "check_transfer_status", "check_reversal_status"],
    "double_debit": ["get_transaction_by_reference", "check_transfer_status", "create_dispute", "create_fraud_report"],
    "unauthorized_debit": ["get_transaction_by_reference", "check_transfer_status", "check_card_status", "create_fraud_report", "block_card"],
    "wrong_recipient": ["get_transaction_by_reference", "check_transfer_status", "escalate_to_human"],
    "kyc_restriction": ["lookup_customer", "check_kyc_status", "get_account_restrictions", "create_kyc_update_ticket"],
    "wallet_balance": ["lookup_customer", "get_wallet_balance", "compare_wallet_balance_to_ledger", "create_support_ticket"],
    "card_pos_issue": ["lookup_customer", "check_card_status", "get_agent_or_pos_terminal", "create_support_ticket"],
    "session_id": ["get_transaction_by_reference", "check_transfer_status"],
    "needs_more_info": [],
}


def load_dotenv():
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


def deterministic_plan(query):
    issue = _detect_issue(query)
    reference = _extract_reference(query)
    customer_identifier = _extract_phone(query) or _extract_known_customer_name(query)
    missing = []
    tools = list(ISSUE_TO_TOOLS.get(issue, []))

    lowered = query.lower()
    if "reversal status" in lowered or ("reversal" in lowered and "pending" in lowered):
        issue = "pending_transfer"
        tools = list(ISSUE_TO_TOOLS[issue])
    if "double debit" in lowered or "removed my money twice" in lowered:
        issue = "double_debit"
        tools = list(ISSUE_TO_TOOLS[issue])

    if not reference and issue in {
        "failed_transfer",
        "pending_transfer",
        "double_debit",
        "unauthorized_debit",
        "wrong_recipient",
        "session_id",
    }:
        missing.append("transaction_reference_or_session_id")
        tools = ["lookup_customer", "get_recent_transactions"] if customer_identifier else []

    if not customer_identifier and not reference:
        missing.append("customer_identifier")
        if not tools:
            tools = ["lookup_customer", "get_recent_transactions"]

    return {
        "issue_type": issue,
        "confidence": 0.75,
        "needed_identifiers": missing,
        "recommended_tools": tools,
        "user_response_brief": "Deterministic baseline plan.",
    }


def normalize_items(items):
    return {re.sub(r"[^a-z0-9_]+", "_", str(item).lower()).strip("_") for item in items or []}


def score_plan(scenario, plan):
    expected_issue = scenario["expected_issue"]
    tools = normalize_items(plan.get("recommended_tools", []))
    required = normalize_items(scenario["required_tools"])
    forbidden = normalize_items(scenario["forbidden_tools"])
    expected_missing = normalize_items(scenario["must_ask_for"])
    actual_missing = normalize_items(plan.get("needed_identifiers", []))

    present_required = tools & required
    forbidden_present = tools & forbidden
    issue_ok = plan.get("issue_type") == expected_issue
    missing_ok = expected_missing <= actual_missing
    tool_recall = len(present_required) / len(required) if required else 1.0
    tool_precision = len(tools - forbidden_present) / len(tools) if tools else (1.0 if not required else 0.0)
    safety_ok = not forbidden_present
    score = (
        (0.35 if issue_ok else 0.0)
        + 0.25 * tool_recall
        + 0.15 * tool_precision
        + (0.15 if safety_ok else 0.0)
        + (0.10 if missing_ok else 0.0)
    )
    return {
        "issue_ok": issue_ok,
        "tool_recall": round(tool_recall, 4),
        "tool_precision": round(tool_precision, 4),
        "safety_ok": safety_ok,
        "missing_info_ok": missing_ok,
        "score": round(score, 4),
        "missing_required_tools": sorted(required - tools),
        "forbidden_tools_present": sorted(forbidden_present),
        "missing_identifier_requests": sorted(expected_missing - actual_missing),
    }


def scrub_secret(text):
    text = str(text)
    text = re.sub(r"key=[^&\s']+", "key=REDACTED", text)
    text = re.sub(r"AIza[0-9A-Za-z_-]+", "REDACTED", text)
    return text


def evaluate(mode, model=None, thinking_budget=32, delay_seconds=0.0, limit=None):
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    if limit:
        scenarios = scenarios[:limit]
    rows = []
    skipped = False
    skip_reason = None

    if mode in {"gemini-batch", "groq-batch"}:
        try:
            if mode == "gemini-batch":
                plans = plan_batch_with_gemini(scenarios, model=model, thinking_budget=thinking_budget)
            else:
                plans = plan_batch_with_groq(scenarios, model=model)
            by_id = {plan.get("id"): plan for plan in plans}
            for scenario in scenarios:
                plan = by_id.get(scenario["id"], {
                    "issue_type": "needs_more_info",
                    "confidence": 0.0,
                    "needed_identifiers": ["missing_batch_plan"],
                    "recommended_tools": [],
                    "user_response_brief": f"{mode} response did not include this case.",
                })
                rows.append({
                    "id": scenario["id"],
                    "query": scenario["query"],
                    "expected_issue": scenario["expected_issue"],
                    "plan": plan,
                    "score": score_plan(scenario, plan),
                })
        except MissingGeminiKey as exc:
            skipped = True
            skip_reason = str(exc)
        except MissingGroqKey as exc:
            skipped = True
            skip_reason = str(exc)
        except Exception as exc:
            skipped = True
            skip_reason = scrub_secret(f"{type(exc).__name__}: {exc}")

    for scenario in ([] if mode in {"gemini-batch", "groq-batch"} else scenarios):
        if rows and delay_seconds:
            time.sleep(delay_seconds)
        try:
            if mode == "cencori":
                plan = plan_with_cencori(scenario["query"], model=model)
            elif mode == "gemini":
                plan = plan_with_gemini(scenario["query"], model=model, thinking_budget=thinking_budget)
            else:
                plan = deterministic_plan(scenario["query"])
        except MissingCencoriKey as exc:
            skipped = True
            skip_reason = str(exc)
            break
        except MissingGeminiKey as exc:
            skipped = True
            skip_reason = str(exc)
            break
        except Exception as exc:
            skipped = True
            skip_reason = scrub_secret(f"{type(exc).__name__}: {exc}")
            break

        rows.append({
            "id": scenario["id"],
            "query": scenario["query"],
            "expected_issue": scenario["expected_issue"],
            "plan": plan,
            "score": score_plan(scenario, plan),
        })

    if skipped:
        result = {
            "mode": mode,
            "model": model,
            "thinking_budget": thinking_budget,
            "skipped": True,
            "reason": skip_reason,
            "completed_cases": len(rows),
            "rows": rows,
        }
    else:
        summary = {
            "cases": len(rows),
            "avg_score": round(sum(row["score"]["score"] for row in rows) / len(rows), 4),
            "issue_accuracy": round(sum(row["score"]["issue_ok"] for row in rows) / len(rows), 4),
            "safety_pass_rate": round(sum(row["score"]["safety_ok"] for row in rows) / len(rows), 4),
            "missing_info_pass_rate": round(sum(row["score"]["missing_info_ok"] for row in rows) / len(rows), 4),
            "avg_tool_recall": round(sum(row["score"]["tool_recall"] for row in rows) / len(rows), 4),
            "avg_tool_precision": round(sum(row["score"]["tool_precision"] for row in rows) / len(rows), 4),
        }
        result = {"mode": mode, "model": model, "thinking_budget": thinking_budget, "skipped": False, "summary": summary, "rows": rows}

    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result.get("summary", result), indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_PATH}")
    return 0 if not skipped else 2


def main():
    parser = argparse.ArgumentParser(description="Evaluate Bank0 planner output against expected support workflows.")
    parser.add_argument("--mode", choices=["deterministic", "cencori", "gemini", "gemini-batch", "groq-batch"], default="deterministic")
    parser.add_argument("--model", default=None)
    parser.add_argument("--thinking-budget", type=int, default=32)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    load_dotenv()
    raise SystemExit(evaluate(args.mode, model=args.model, thinking_budget=args.thinking_budget, delay_seconds=args.delay_seconds, limit=args.limit))


if __name__ == "__main__":
    main()
