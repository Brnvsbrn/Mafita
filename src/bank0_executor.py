import json
import re
from pathlib import Path

try:
    from .bank0_tools import (
        attach_evidence_to_ticket,
        check_kyc_status,
        check_reversal_status,
        check_transfer_status,
        create_dispute,
        create_support_ticket,
        escalate_to_human,
        get_account_restrictions,
        get_recent_transactions,
        get_support_ticket_by_transaction,
        get_transaction_by_reference,
        lookup_customer,
        mark_ticket_urgent,
        request_reversal,
    )
except ImportError:
    from bank0_tools import (
        attach_evidence_to_ticket,
        check_kyc_status,
        check_reversal_status,
        check_transfer_status,
        create_dispute,
        create_support_ticket,
        escalate_to_human,
        get_account_restrictions,
        get_recent_transactions,
        get_support_ticket_by_transaction,
        get_transaction_by_reference,
        lookup_customer,
        mark_ticket_urgent,
        request_reversal,
    )


MUTATING_TOOLS = {
    "attach_evidence_to_ticket",
    "create_dispute",
    "create_support_ticket",
    "escalate_to_human",
    "mark_ticket_urgent",
    "request_reversal",
}

SCHEMA_PATH = Path(__file__).resolve().parent / "bank0_issue_schemas.json"
ISSUE_SCHEMAS = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _yoruba_eta(text):
    value = str(text or "akoko die")
    replacements = {
        "1-3 hours or auto-reversal by midnight": "wakati 1 si 3, tabi auto-reversal ki midnight to de",
        "within 2 hours": "wakati 2",
        "check again in 30 minutes": "iseju 30",
        "same day": "oni gan-an",
    }
    return replacements.get(value, value)


def _extract_reference(text):
    match = re.search(
        r"\b(?:[A-Z]{2,3}\d{4}[A-Z]{1,2}|(?:B0|MF)[\s-]*TX[\s-]*\d{4,}|TX[\s-]*\d{4,})\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    value = re.sub(r"\s+", "-", match.group(0).upper())
    return f"MF-{value}" if value.startswith("TX-") else value


def _extract_customer_hint(text):
    lowered = text.lower()
    for name in ["femi", "sade", "segun", "funmi"]:
        if name in lowered:
            return name
    match = re.search(r"(?:\+234\d{10}|0\d{10})\b", text)
    return match.group(0) if match else None


def _clarification_message(missing_identifiers, issue_type):
    schema = ISSUE_SCHEMAS.get(issue_type)
    if schema:
        return {
            "english": schema["clarification_en"],
            "yoruba": schema["clarification_yo"],
        }
    missing = set(missing_identifiers)
    if {"transaction_id", "transaction_time", "amount"} & missing:
        return {
            "english": "Please provide the transaction ID, time, and amount so I can continue.",
            "yoruba": "Jowo fi transaction ID, akoko, ati iye owo ranse ki n le tesiwaju.",
        }
    if "customer_identifier" in missing:
        return {
            "english": "Please provide the registered phone number on the account.",
            "yoruba": "Jowo fi nomba foonu account ranse.",
        }
    return {
        "english": f"I need one more detail before I can safely handle this {issue_type.replace('_', ' ')} case.",
        "yoruba": "Mo nilo alaye kan si ki n to le sise lori oro yii lailewu.",
    }


def _dry_result(tool_name, **kwargs):
    return {"status": "dry_run", "tool": tool_name, "would_call_with": kwargs}


def execute_validated_plan(plan, query, dry_run=True):
    decision = plan.get("validation", {}).get("decision", "ask_clarification")
    issue_type = plan.get("issue_type", "needs_more_info")
    missing = plan.get("needed_identifiers", [])
    tools = plan.get("recommended_tools", [])
    reference = _extract_reference(query)
    customer_hint = _extract_customer_hint(query)
    context = {
        "customer": None,
        "transactions": [],
        "transaction": None,
        "transaction_status": None,
        "ticket": None,
    }
    tool_results = []

    if reference and not customer_hint:
        tx = get_transaction_by_reference(reference)
        if tx:
            customer_hint = tx["customer_id"]

    for tool in tools:
        if dry_run and tool in MUTATING_TOOLS:
            result = _dry_mutating_result(tool, issue_type, context)
            tool_results.append({"tool": tool, "result": result})
            continue

        if tool == "lookup_customer":
            result = lookup_customer(customer_hint) if customer_hint else None
            context["customer"] = result
        elif tool == "get_recent_transactions":
            result = get_recent_transactions(context["customer"]["customer_id"]) if context["customer"] else []
            context["transactions"] = result
        elif tool == "get_transaction_by_reference":
            result = get_transaction_by_reference(reference) if reference else None
            context["transaction"] = result
            if result and not context["customer"]:
                context["customer"] = lookup_customer(result["customer_id"])
        elif tool == "check_transfer_status":
            result = check_transfer_status(context["transaction"]["transaction_id"]) if context["transaction"] else None
            context["transaction_status"] = result
        elif tool == "check_reversal_status":
            tx = context["transaction"]
            result = check_reversal_status(tx["transaction_id"]) if tx else None
        elif tool == "get_support_ticket_by_transaction":
            tx = context["transaction"]
            result = get_support_ticket_by_transaction(tx["transaction_id"]) if tx else None
            context["ticket"] = result
        elif tool == "check_kyc_status":
            result = check_kyc_status(context["customer"]["customer_id"]) if context["customer"] else None
        elif tool == "get_account_restrictions":
            result = get_account_restrictions(context["customer"]["customer_id"]) if context["customer"] else []
        elif tool == "create_support_ticket":
            result = _create_ticket(issue_type, context)
        elif tool == "create_dispute":
            tx = context["transaction"]
            result = create_dispute(tx["transaction_id"], issue_type) if tx else None
        elif tool == "request_reversal":
            tx = context["transaction"]
            result = request_reversal(tx["transaction_id"], issue_type) if tx else None
        elif tool == "attach_evidence_to_ticket":
            result = attach_evidence_to_ticket(context["ticket"]["ticket_id"], ["evidence uploaded in chat"]) if context["ticket"] else None
            context["ticket"] = result.get("ticket") if isinstance(result, dict) else context["ticket"]
        elif tool == "mark_ticket_urgent":
            result = mark_ticket_urgent(context["ticket"]["ticket_id"], issue_type) if context["ticket"] else None
            context["ticket"] = result.get("ticket") if isinstance(result, dict) else context["ticket"]
        elif tool == "escalate_to_human":
            channel = "#kyc-review" if issue_type == "kyc_restriction" else "#disputes"
            result = escalate_to_human(
                context["customer"]["customer_id"] if context["customer"] else None,
                issue_type,
                context["ticket"]["ticket_id"] if context["ticket"] else None,
                channel,
            )
        else:
            result = {"status": "skipped", "reason": "unknown_tool"}

        tool_results.append({"tool": tool, "result": result})

    if decision == "ask_clarification":
        return {
            "decision": decision,
            "tools_executed": [item["tool"] for item in tool_results],
            "tool_results": tool_results,
            "final_response": _clarification_message(missing, issue_type),
        }

    return {
        "decision": decision,
        "tools_executed": [item["tool"] for item in tool_results],
        "tool_results": tool_results,
        "final_response": _final_response(decision, issue_type, tool_results),
    }


def _dry_mutating_result(tool, issue_type, context):
    if tool == "create_support_ticket" and context["customer"]:
        context["ticket"] = {
            "ticket_id": f"DRY-{issue_type.upper()}",
            "customer_id": context["customer"]["customer_id"],
            "transaction_id": context["transaction"]["transaction_id"] if context["transaction"] else None,
        }
    return _dry_result(
        tool,
        customer_id=context["customer"]["customer_id"] if context["customer"] else None,
        transaction_id=context["transaction"]["transaction_id"] if context["transaction"] else None,
        ticket_id=context["ticket"]["ticket_id"] if context["ticket"] else None,
        reason=issue_type,
    )


def _create_ticket(issue_type, context):
    if not context["customer"]:
        return None
    result = create_support_ticket(
        context["customer"]["customer_id"],
        issue_type,
        "high" if issue_type in {"double_debit_pos", "kyc_restriction"} else "normal",
        issue_type,
        context["transaction"]["transaction_id"] if context["transaction"] else None,
    )
    context["ticket"] = result.get("ticket") if isinstance(result, dict) else None
    return result


def _final_response(decision, issue_type, tool_results):
    tx = None
    reversal = None
    restrictions = []
    for item in tool_results:
        result = item.get("result")
        if item.get("tool") == "get_transaction_by_reference" and isinstance(result, dict):
            tx = result
        elif item.get("tool") == "check_reversal_status" and isinstance(result, dict):
            reversal = result
        elif item.get("tool") == "get_account_restrictions" and isinstance(result, list):
            restrictions = result

    if decision == "escalate":
        if issue_type == "kyc_restriction":
            reason = restrictions[0].get("reason") if restrictions else "account restriction review"
            return {
                "english": f"I found the account restriction. It needs compliance review because of {reason}; I prepared the case for the KYC review team.",
                "yoruba": "Mo rí restriction lórí account rẹ. Ó nílò compliance review, mo sì ti pèsè case yìí fún KYC review team wa láti yẹ̀ ẹ́ wò.",
            }
        channel = "#kyc-review" if issue_type == "kyc_restriction" else "#disputes"
        return {
            "english": f"I can see this needs human review. I prepared an urgent ticket with the details and routed it to {channel}.",
            "yoruba": "Ọ̀rọ̀ yìí nílò human review. Mo ti pèsè urgent ticket pẹ̀lú gbogbo àlàyé rẹ, mo sì ti gbé e lọ sí team tí ó yẹ.",
        }
    if issue_type == "failed_transfer" and tx:
        return {
            "english": f"I found the transfer. The debit is posted, but the recipient credit is still pending at settlement; expected resolution is {tx.get('expected_resolution', 'soon')}. Please do not retry it.",
            "yoruba": f"Mo rí transfer náà. Debit ti jáde lórí account rẹ, ṣùgbọ́n credit recipient ṣì wà ní settlement lọ́wọ́; ó yẹ kí ó parí láàrin {_yoruba_eta(tx.get('expected_resolution'))}. Jọ̀wọ́, má ṣe tún transfer náà ṣe mọ́.",
        }
    if issue_type == "pending_transfer" and tx:
        return {
            "english": f"I found the transfer. It is still pending, not failed. Do not send it again; wait {tx.get('expected_resolution', 'a little longer')} before checking back.",
            "yoruba": f"Mo rí transaction náà. Ó ṣì wà ní pending lọ́wọ́, kò tíì fail; jọ̀wọ́ dúró fún {_yoruba_eta(tx.get('expected_resolution'))} kí o tó yẹ̀ ẹ́ wò padà. Jọ̀wọ́, má ṣe tún owó náà rán mọ́.",
        }
    if issue_type == "pending_reversal":
        eta = reversal.get("eta") if reversal else "3-5 working days"
        return {
            "english": f"I found the reversal record. It is still in process with the partner bank, with an expected timeline of {eta}.",
            "yoruba": "Mo rí reversal record náà. Ó ṣì wà ní ìṣe pẹ̀lú partner bank, kò tíì di stuck.",
        }
    return {
        "english": f"I checked the Mafita records for this {issue_type.replace('_', ' ')} case.",
        "yoruba": "Mo ti ṣàyẹ̀wò àwọn record Mafita fún ọ̀rọ̀ yìí.",
    }
