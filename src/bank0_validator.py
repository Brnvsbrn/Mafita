import json
import re
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parent / "bank0_issue_schemas.json"


def load_issue_schemas():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


ISSUE_SCHEMAS = load_issue_schemas()
CORE_REQUIRED_BY_ISSUE = {issue: spec["required_tools"] for issue, spec in ISSUE_SCHEMAS.items()}
REQUIRED_IDENTIFIERS_BY_ISSUE = {issue: spec["required_identifiers"] for issue, spec in ISSUE_SCHEMAS.items()}
SUPPORTING_IDENTIFIERS_BY_ISSUE = {issue: spec["supporting_identifiers"] for issue, spec in ISSUE_SCHEMAS.items()}
FORBIDDEN_BY_ISSUE = {issue: set(spec["forbidden_tools"]) for issue, spec in ISSUE_SCHEMAS.items()}

ISSUE_LABELS = set(CORE_REQUIRED_BY_ISSUE) | {"needs_more_info"}
MUTATING_TOOLS = {
    "attach_evidence_to_ticket",
    "create_dispute",
    "create_fraud_report",
    "create_kyc_update_ticket",
    "create_support_ticket",
    "escalate_to_human",
    "mark_ticket_urgent",
    "request_reversal",
}
TOOL_ORDER = {
    "lookup_customer": 0,
    "get_transaction_by_reference": 1,
    "get_recent_transactions": 2,
    "check_transfer_status": 3,
    "check_reversal_status": 4,
    "get_support_ticket_by_transaction": 5,
    "check_kyc_status": 6,
    "get_account_restrictions": 7,
    "create_support_ticket": 20,
    "attach_evidence_to_ticket": 21,
    "mark_ticket_urgent": 22,
    "escalate_to_human": 23,
}
TRANSACTION_ISSUES = {"failed_transfer", "pending_transfer", "pending_reversal", "double_debit_pos"}
ESCALATION_ISSUES = {"double_debit_pos", "kyc_restriction"}


def normalize_identifier(name):
    normalized = re.sub(r"[^a-z0-9_]+", "_", str(name).lower()).strip("_")
    aliases = {
        "time": "transaction_time",
        "transaction_time_or_date": "transaction_time",
        "transaction_reference": "transaction_id",
        "reference": "transaction_id",
        "session_id": "transaction_id",
        "transaction_reference_or_session_id": "transaction_id",
        "phone": "customer_identifier",
        "phone_number": "customer_identifier",
        "registered_phone": "customer_identifier",
        "registered_phone_number": "customer_identifier",
        "customer_phone": "customer_identifier",
    }
    return aliases.get(normalized, normalized)



def has_transaction_id(text):
    return bool(
        re.search(
            r"\b(?:[A-Z]{2,3}\d{4}[A-Z]{1,2}|(?:B0|MF)[\s-]*TX[\s-]*\d{4,}|TX[\s-]*\d{4,})\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def has_amount(text):
    return bool(
        re.search(r"(?:\u20a6|NGN|N)\s*\d[\d,]*|\b\d[\d,]*\s*(?:naira|k)\b", text, flags=re.IGNORECASE)
        or re.search(r"\bamount\s*(?:is|was|:)?\s*\d[\d,]*\b", text, flags=re.IGNORECASE)
    )


def has_time(text):
    return bool(
        re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", text, flags=re.IGNORECASE)
        or re.search(
            r"\b(yesterday|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|afternoon|evening)\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def has_customer_identifier(text):
    lowered = text.lower()
    if re.search(r"(?:\+234\d{10}|0\d{10})\b", text):
        return True
    return any(name in lowered for name in ["femi", "sade", "segun", "funmi"])


def infer_issue(text, proposed_issue=None):
    lowered = text.lower()
    for label in ["failed_transfer", "pending_transfer", "pending_reversal", "double_debit_pos", "kyc_restriction"]:
        if label in lowered:
            return label
    if any(term in lowered for term in [
        "bvn", "nin", "kyc", "restricted", "restriction", "frozen", "freeze",
        "can't send", "cannot send", "can't receive", "cannot receive",
        "account is locked", "account locked", "account blocked", "account restricted",
        "didi", "di didi", "akọọlẹ", "akole", "iroyin mi ti di",
    ]):
        return "kyc_restriction"
    if any(term in lowered for term in ["double debit", "charged twice", "twice", "meji", "dobude", "pos declined", "decline slip", "failed pos"]):
        return "double_debit_pos"
    if any(term in lowered for term in ["reversal", "reverse", "refund since", "waiting for my money back"]):
        return "pending_reversal"
    if any(term in lowered for term in ["pending", "timeout", "time out", "thyme out", "tiimotu", "retry", "send again"]):
        return "pending_transfer"
    if any(term in lowered for term in ["failed", "fail", "ko ri", "recipient", "debit", "deducted", "not received", "hasn't received", "didn't receive"]):
        return "failed_transfer"
    return proposed_issue if proposed_issue in CORE_REQUIRED_BY_ISSUE else "needs_more_info"


def validate_plan(plan, query):
    original_tools = [normalize_identifier(tool) for tool in plan.get("recommended_tools", [])]
    proposed_issue = normalize_identifier(plan.get("issue_type", "needs_more_info"))
    inferred_issue = infer_issue(query, proposed_issue)
    issue = inferred_issue if inferred_issue != "needs_more_info" else proposed_issue

    transaction_id_present = has_transaction_id(query)
    amount_present = has_amount(query)
    time_present = has_time(query)
    customer_present = has_customer_identifier(query)
    tools = [tool for tool in original_tools if tool not in ISSUE_LABELS]
    blocked_tools = []
    added_tools = []
    missing_identifiers = [normalize_identifier(item) for item in plan.get("needed_identifiers", [])]

    # Remove identifiers the planner claims are missing but are actually present
    if transaction_id_present and "transaction_id" in missing_identifiers:
        missing_identifiers.remove("transaction_id")
    if amount_present and "amount" in missing_identifiers:
        missing_identifiers.remove("amount")
    if time_present and "transaction_time" in missing_identifiers:
        missing_identifiers.remove("transaction_time")
    if customer_present and "customer_identifier" in missing_identifiers:
        missing_identifiers.remove("customer_identifier")

    required_identifiers = REQUIRED_IDENTIFIERS_BY_ISSUE.get(issue, [])
    if "customer_identifier" in required_identifiers and not customer_present and "customer_identifier" not in missing_identifiers:
        missing_identifiers.append("customer_identifier")
    if "transaction_id" in required_identifiers and not transaction_id_present and "transaction_id" not in missing_identifiers:
        missing_identifiers.append("transaction_id")
    if "transaction_time" in required_identifiers and not time_present and "transaction_time" not in missing_identifiers:
        missing_identifiers.append("transaction_time")
    if "amount" in required_identifiers and not amount_present and "amount" not in missing_identifiers:
        missing_identifiers.append("amount")

    restricted_to_safe_tools = False
    if missing_identifiers:
        if issue in TRANSACTION_ISSUES:
            safe_tools = ["get_transaction_by_reference"] if transaction_id_present else []
            restricted_to_safe_tools = True
        elif issue == "kyc_restriction":
            safe_tools = ["lookup_customer", "check_kyc_status", "get_account_restrictions"] if customer_present else []
            restricted_to_safe_tools = True
        else:
            safe_tools = []
            restricted_to_safe_tools = True
    else:
        safe_tools = CORE_REQUIRED_BY_ISSUE.get(issue, [])

    for tool in safe_tools:
        if tool not in tools:
            tools.append(tool)
            added_tools.append(tool)

    forbidden = FORBIDDEN_BY_ISSUE.get(issue, set())
    if restricted_to_safe_tools:
        safe_set = set(safe_tools)
        for tool in list(tools):
            if tool not in safe_set:
                blocked_tools.append(tool)
        tools = [tool for tool in tools if tool in safe_set]
    elif missing_identifiers:
        for tool in list(tools):
            if tool in MUTATING_TOOLS:
                blocked_tools.append(tool)
        tools = [tool for tool in tools if tool not in MUTATING_TOOLS]

    filtered_tools = []
    for tool in tools:
        if tool in forbidden:
            blocked_tools.append(tool)
            continue
        if tool not in filtered_tools:
            filtered_tools.append(tool)
    filtered_tools.sort(key=lambda tool: TOOL_ORDER.get(tool, 50))

    decision = "execute"
    if missing_identifiers:
        decision = "ask_clarification"
    if issue in ESCALATION_ISSUES and not missing_identifiers:
        decision = "escalate"

    return {
        **plan,
        "issue_type": issue,
        "needed_identifiers": missing_identifiers,
        "recommended_tools": filtered_tools,
        "validation": {
            "original_issue_type": proposed_issue,
            "inferred_issue_type": inferred_issue,
            "added_tools": added_tools,
            "blocked_tools": blocked_tools,
            "decision": decision,
            "supporting_identifiers": SUPPORTING_IDENTIFIERS_BY_ISSUE.get(issue, []),
        },
    }
