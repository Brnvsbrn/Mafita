import json
import os
import re
import time

try:
    import httpx

    from .cencori_client import cencori_chat, cencori_chat_stream, cencori_openai_chat
    from .entity_correction import correct_entities
    from .gemini_client import gemini_generate
    from .groq_client import (
        DEFAULT_GROQ_MODEL,
        GROQ_BASE_URL,
        MissingGroqKey,
        groq_chat_json,
        groq_key,
    )
except ImportError:
    import httpx

    from cencori_client import cencori_chat, cencori_chat_stream, cencori_openai_chat
    from entity_correction import correct_entities
    from gemini_client import gemini_generate
    from groq_client import DEFAULT_GROQ_MODEL, GROQ_BASE_URL, MissingGroqKey, groq_chat_json, groq_key


PLANNER_SYSTEM_PROMPT = """You are the LLM planner for Mafita, a mock Nigerian fintech support system.
You do not execute tools yourself. You inspect the corrected transcript and policy context, then return a JSON plan.

Supported demo issue_type values:
- failed_transfer
- pending_transfer
- pending_reversal
- double_debit_pos
- kyc_restriction
- needs_more_info

Only classify into these five support tracks. If the user is outside these tracks, choose needs_more_info.
Use only "transaction ID" in user-facing language for the transaction identifier.

Available recommended_tools values:
- lookup_customer
- get_recent_transactions
- get_transaction_by_reference
- check_transfer_status
- create_dispute
- request_reversal
- check_reversal_status
- get_support_ticket_by_transaction
- check_kyc_status
- create_kyc_update_ticket
- get_account_restrictions
- create_support_ticket
- attach_evidence_to_ticket
- mark_ticket_urgent
- escalate_to_human

Never put issue_type labels inside recommended_tools. For example, "failed_transfer" is not a tool.

Return only compact JSON with these fields:
{
  "issue_type": string,
  "confidence": number,
  "needed_identifiers": string[],
  "recommended_tools": string[],
  "user_response_brief": string
}

Do not invent transaction records. If identifiers are missing, choose needs_more_info.
For transaction cases, ask for all three details when missing: transaction ID, time, and amount.
For escalation cases, collect the issue details and evidence before handing off.
"""

def build_planner_messages(query):
    return [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": build_planner_payload(query)},
    ]


_MAFITA_POLICY_CONTEXT = """# Failed Transfer
Use when money left the customer's wallet/account but the recipient did not receive it.
Required: transaction ID, time, amount. Look up transaction, check status and ledger debit.
If failed and debit posted, create dispute and request reversal. Failed NIP transfers usually reverse within 24-48 business hours.

# Pending Transfer
Use when a transaction is still pending or timeout is mentioned.
Required: transaction ID, time, amount. Check if a reversal already exists.
Check if the transaction is inside the 24-48 hour NIP settlement window.
If already processing, give the reversal ETA. If outside the window, create a dispute.

# Pending Reversal
Use when a customer is asking about the status of an existing reversal.
Required: transaction ID, time, amount. Look up the reversal record and any support ticket.
Give the current reversal status and ETA.

# Double Debit POS
Use when a customer reports duplicate debit from a POS or failed withdrawal that was debited.
Required: transaction ID, time, amount. Pull recent transactions, compare timestamps.
If duplicate confirmed, create dispute, attach evidence, mark urgent, escalate to #disputes.

# KYC Restriction
Use when account is blocked, restricted, BVN mismatch, NIN missing, or KYC upgrade needed.
Required: registered phone number. Check KYC tier, BVN status, NIN status, and restrictions.
If NIN missing, create KYC update ticket. BVN/NIN fixes usually take 24-48 hours.

# Escalation Rules
Escalate to human when: BVN/NIN/identity conflicts, transaction outside reversal window,
or customer reports fraud/scam/account takeover. Always ask for confirmation before guessing entities.
"""


def build_planner_payload(query):
    correction = correct_entities(query)
    corrected = correction["corrected_transcript"]
    user_payload = {
        "raw_query": query,
        "corrected_transcript": corrected,
        "entity_corrections": correction["corrections"],
        "policy_context": _MAFITA_POLICY_CONTEXT,
    }
    return json.dumps(user_payload, ensure_ascii=False)


def plan_with_cencori(query, model=None):
    messages = build_planner_messages(query)
    try:
        response = cencori_chat(messages, model=model, temperature=0.1, max_tokens=500)
        content = response.content.strip()
    except (KeyError, AttributeError, TypeError):
        content = cencori_openai_chat(messages, model=model, temperature=0.1, max_tokens=500).strip()
    try:
        return _parse_plan_json(content)
    except json.JSONDecodeError:
        return {
            "issue_type": "needs_more_info",
            "confidence": 0.0,
            "needed_identifiers": ["parseable_json_plan"],
            "recommended_tools": [],
            "user_response_brief": content,
        }


def stream_cencori_plan(query, model=None):
    return cencori_chat_stream(build_planner_messages(query), model=model, temperature=0.1, max_tokens=500)


def plan_with_gemini(query, model=None, thinking_budget=32):
    response = gemini_generate(
        PLANNER_SYSTEM_PROMPT,
        build_planner_payload(query),
        model=model,
        temperature=0.1,
        max_output_tokens=1200,
        thinking_budget=thinking_budget,
    )
    content = response["text"].strip()
    try:
        plan = _parse_plan_json(content)
    except json.JSONDecodeError:
        plan = {
            "issue_type": "needs_more_info",
            "confidence": 0.0,
            "needed_identifiers": ["parseable_json_plan"],
            "recommended_tools": [],
            "user_response_brief": content,
        }
    plan["_usage"] = response["raw"].get("usageMetadata", {})
    return plan


def plan_with_groq(query, model=None):
    response = groq_chat_json(
        PLANNER_SYSTEM_PROMPT,
        build_planner_payload(query),
        model=model or DEFAULT_GROQ_MODEL,
        temperature=0,
        max_tokens=1400,
    )
    plan = response["json"]
    plan["_usage"] = response.get("usage", {})
    plan["_model"] = response["model"]
    return plan


def plan_batch_with_gemini(queries, model=None, thinking_budget=32):
    payload = {
        "cases": [
            {
                "id": item["id"],
                "query": item["query"],
                "planner_payload": build_planner_payload(item["query"]),
            }
            for item in queries
        ]
    }
    system_prompt = PLANNER_SYSTEM_PROMPT + """

You will receive multiple cases.
Return only a JSON array.
Each item must include:
{
  "id": string,
  "issue_type": string,
  "confidence": number,
  "needed_identifiers": string[],
  "recommended_tools": string[],
  "user_response_brief": string
}
"""
    response = gemini_generate(
        system_prompt,
        json.dumps(payload, ensure_ascii=False),
        model=model,
        temperature=0.1,
        max_output_tokens=6000,
        thinking_budget=thinking_budget,
    )
    content = response["text"].strip()
    try:
        plans = _parse_json_array(content)
    except json.JSONDecodeError:
        plans = [
            {
                "id": item["id"],
                "issue_type": "needs_more_info",
                "confidence": 0.0,
                "needed_identifiers": ["parseable_json_batch_plan"],
                "recommended_tools": [],
                "user_response_brief": content,
            }
            for item in queries
        ]
    usage = response["raw"].get("usageMetadata", {})
    for plan in plans:
        plan["_usage"] = usage
    return plans


def plan_batch_with_groq(queries, model=None):
    model = model or "llama-3.3-70b-versatile"
    payload = {
        "cases": [
            {
                "id": item["id"],
                "query": item["query"],
                "planner_payload": build_planner_payload(item["query"]),
            }
            for item in queries
        ]
    }
    system_prompt = PLANNER_SYSTEM_PROMPT + """

You will receive multiple cases.
Return only a JSON object with a "plans" array.
Each item must include:
{
  "id": string,
  "issue_type": string,
  "confidence": number,
  "needed_identifiers": string[],
  "recommended_tools": string[],
  "user_response_brief": string
}
"""
    request = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_completion_tokens": max(1200, 500 * len(queries)),
        "response_format": {"type": "json_object"},
    }
    start = time.perf_counter()
    response = httpx.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {groq_key()}", "Content-Type": "application/json"},
        json=request,
        timeout=120,
    )
    response.raise_for_status()
    latency = time.perf_counter() - start
    raw = response.json()
    content = raw["choices"][0]["message"].get("content", "").strip()
    try:
        parsed = _parse_plan_json(content)
        plans = parsed.get("plans") or parsed.get("results") or []
    except json.JSONDecodeError:
        plans = [
            {
                "id": item["id"],
                "issue_type": "needs_more_info",
                "confidence": 0.0,
                "needed_identifiers": ["parseable_json_batch_plan"],
                "recommended_tools": [],
                "user_response_brief": content,
            }
            for item in queries
        ]
    usage = raw.get("usage", {})
    for plan in plans:
        plan["_usage"] = usage
        plan["_latency_seconds"] = round(latency, 3)
        plan["_amortized_latency_seconds"] = round(latency / max(len(queries), 1), 3)
    return plans



def _parse_plan_json(content):
    text = content.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def _parse_json_array(content):
    text = content.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
    if not text.startswith("["):
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)
