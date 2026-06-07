import re
from dataclasses import dataclass

try:
    from .bank0_rag import retrieve_policy
    from .bank0_tools import (
        block_card,
        check_card_status,
        check_kyc_status,
        check_reversal_status,
        check_transfer_status,
        compare_wallet_balance_to_ledger,
        create_dispute,
        create_fraud_report,
        create_kyc_update_ticket,
        create_support_ticket,
        escalate_to_human,
        get_account_restrictions,
        get_agent_or_pos_terminal,
        get_recent_transactions,
        get_transaction_by_reference,
        get_wallet_balance,
        lookup_customer,
        request_reversal,
    )
    from .entity_correction import correct_entities
except ImportError:
    from bank0_rag import retrieve_policy
    from bank0_tools import (
        block_card,
        check_card_status,
        check_kyc_status,
        check_reversal_status,
        check_transfer_status,
        compare_wallet_balance_to_ledger,
        create_dispute,
        create_fraud_report,
        create_kyc_update_ticket,
        create_support_ticket,
        escalate_to_human,
        get_account_restrictions,
        get_agent_or_pos_terminal,
        get_recent_transactions,
        get_transaction_by_reference,
        get_wallet_balance,
        lookup_customer,
        request_reversal,
    )
    from entity_correction import correct_entities


ISSUE_HINTS = {
    "failed_transfer": {
        "failed", "fail", "kuna", "ko de", "deducted", "debited", "debit", "recipient did not receive",
        "recipient ko ri", "reversal", "refund", "transfer", "pending"
    },
    "pending_transfer": {"pending", "timeout", "time out", "thyme out", "settlement", "processing"},
    "double_debit": {"double debit", "duplicate", "charged twice", "debit twice", "meji", "lemeji"},
    "unauthorized_debit": {"unauthorized", "unauthorised", "scam", "fraud", "i did not", "mi o se", "card compromise"},
    "wrong_recipient": {"wrong recipient", "wrong account", "wrong bank", "mistake", "asise", "court order"},
    "kyc_restriction": {"kyc", "bvn", "nin", "restricted", "blocked", "limit", "daily limit", "account restricted"},
    "wallet_balance": {"wallet balance", "balance", "ledger", "money disappeared", "owo mi sonu"},
    "card_pos_issue": {"card", "virtual card", "pos", "atm", "terminal", "verve", "visa", "mastercard"},
    "reversal_status": {"reversal status", "where is my reversal", "delayed reversal", "reversed"},
    "session_id": {"session id", "receipt", "transaction reference", "reference"},
}

ISSUE_PRIORITY = [
    "unauthorized_debit",
    "double_debit",
    "wrong_recipient",
    "kyc_restriction",
    "wallet_balance",
    "card_pos_issue",
    "reversal_status",
    "session_id",
    "pending_transfer",
    "failed_transfer",
]


@dataclass(frozen=True)
class AgentResponse:
    provider: str | None
    intent: str
    english: str
    yoruba: str
    tool_result: dict | None
    policy_matches: list


def _normalize_phone(phone):
    if not phone:
        return None
    if phone.startswith("0") and len(phone) == 11:
        return "+234" + phone[1:]
    return phone


def _extract_phone(text):
    match = re.search(r"(\+234\d{10}|0\d{10})\b", text)
    return _normalize_phone(match.group(1)) if match else None


def _extract_reference(text):
    patterns = [
        r"\bB0-TX-\d{4,}\b",
        r"\bB0\s+TX\s+\d{4,}\b",
        r"\bTX-\d{4,}\b",
        r"\bTX\s+\d{4,}\b",
        r"\b999\d{10,}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = re.sub(r"\s+", "-", match.group(0).upper())
            if value.startswith("TX-"):
                return "B0-" + value
            return value
    return None


def _detect_issue(text):
    lowered = text.lower()
    scores = {}
    for issue, hints in ISSUE_HINTS.items():
        score = 0
        for hint in hints:
            if hint in lowered:
                score += 3 if " " in hint else 1
        scores[issue] = score
    best_issue, best_score = max(
        scores.items(),
        key=lambda item: (item[1], -ISSUE_PRIORITY.index(item[0])),
    )
    return best_issue if best_score else "failed_transfer"


def _extract_known_customer_name(text):
    lowered = text.lower()
    for name in ["femi", "sade", "segun", "funmi"]:
        if name in lowered:
            return name
    return None


def _customer_from_query(text):
    phone = _extract_phone(text)
    if phone:
        return lookup_customer(phone)
    name = _extract_known_customer_name(text)
    return lookup_customer(name) if name else None


def _policy_brief(policy_matches):
    if not policy_matches:
        return ""
    top = policy_matches[0]
    return f"Policy used: {top.title}."


def _yoruba(intent, **kwargs):
    reference = kwargs.get("reference")
    ticket_id = kwargs.get("ticket_id")
    eta = kwargs.get("eta", "wakati 24 si 48")
    if intent == "failed_transfer_reversal_requested":
        return f"A ti ṣii dispute fun transaction {reference}. Reversal wa ni processing; ETA ni {eta}."
    if intent == "successful_transfer_trace":
        return f"Transaction {reference} successful. Lo Session ID yii fun banki olugba lati trace owo naa."
    if intent == "pending_transfer":
        return f"Transaction {reference} ṣi wa ni pending. Jọwọ duro titi di {eta}; a ti ṣayẹwo reversal status."
    if intent == "kyc_ticket_created":
        return f"A ti ṣẹda ticket KYC {ticket_id}. Fi BVN/NIN tabi ID to yẹ ranṣẹ fun atunṣe."
    if intent == "wallet_reconciliation":
        return f"Balance wallet ko ba ledger mu. A ti ṣẹda ticket {ticket_id} fun reconciliation."
    if intent == "fraud_escalated":
        return f"A ti gbe ọrọ yii lọ si fraud team. Ticket rẹ ni {ticket_id}. Ma ṣe lo card naa titi support yoo fi dahun."
    if intent == "needs_more_info":
        return "Jọwọ fi nọmba foonu account, transaction reference, tabi Session ID ranṣẹ ki n le ṣayẹwo."
    return "Mo ti ṣayẹwo ọrọ naa, mo si ti gbe igbesẹ to yẹ ninu eto Mafita."


def _format_tx(tx):
    return (
        f"{tx['reference']} ({tx['status']}): NGN {tx['amount']:,.0f}, "
        f"{tx['provider']} -> {tx.get('recipient_bank') or tx.get('recipient_name')}"
    )


def _route_by_transaction(issue, tx, policy_matches, auto_create_dispute):
    status = check_transfer_status(tx["transaction_id"])
    reversal = status.get("reversal")

    if issue in {"unauthorized_debit", "double_debit"}:
        dispute = create_dispute(tx["transaction_id"], issue, priority="high") if auto_create_dispute else None
        ticket = create_fraud_report(tx["customer_id"], tx["transaction_id"], issue) if auto_create_dispute else None
        cards = check_card_status(tx["customer_id"])
        card_action = None
        if cards and auto_create_dispute:
            card_action = block_card(tx["customer_id"], cards[0]["card_id"], issue)
        english = (
            f"I found {_format_tx(tx)}. Because this looks like {issue.replace('_', ' ')}, "
            f"{'I created a high-priority fraud/support record. ' if ticket else 'a high-priority fraud/support record should be created. '}"
        )
        if ticket:
            english += f"Ticket: {ticket['ticket']['ticket_id']}."
        if card_action:
            english += f" Card {card_action['card']['card_id']} has been blocked pending review."
        ticket_id = ticket["ticket"]["ticket_id"] if ticket else "pending"
        return AgentResponse(
            tx.get("provider"),
            "fraud_escalated",
            english + " " + _policy_brief(policy_matches),
            _yoruba("fraud_escalated", ticket_id=ticket_id),
            {"status": status, "dispute": dispute, "ticket": ticket, "card_action": card_action},
            policy_matches,
        )

    if tx["status"] == "successful":
        english = (
            f"I found {_format_tx(tx)}. It is marked successful. "
            f"Session ID: {tx['session_id']}. The receiving bank should trace the transfer with that Session ID."
        )
        if issue == "wrong_recipient":
            ticket = escalate_to_human(tx["customer_id"], "Wrong-recipient transfer requires compliance review.")
            english += f" I also escalated it because wrong-recipient reversals need compliance handling. Ticket: {ticket['ticket']['ticket_id']}."
            tool_result = {"status": status, "ticket": ticket}
        else:
            tool_result = {"status": status}
        return AgentResponse(
            tx.get("provider"),
            "successful_transfer_trace",
            english + " " + _policy_brief(policy_matches),
            _yoruba("successful_transfer_trace", reference=tx["reference"]),
            tool_result,
            policy_matches,
        )

    if tx["status"] == "pending":
        english = f"I found {_format_tx(tx)}. It is still pending."
        if reversal:
            english += f" Reversal {reversal['reversal_id']} is {reversal['status']} with ETA {reversal['eta']}."
        else:
            new_reversal = request_reversal(tx["transaction_id"], issue) if auto_create_dispute else None
            reversal = new_reversal.get("reversal") if new_reversal else None
            english += f" I requested reversal {reversal['reversal_id']}." if reversal else " A reversal can be requested."
        return AgentResponse(
            tx.get("provider"),
            "pending_transfer",
            english + " " + _policy_brief(policy_matches),
            _yoruba("pending_transfer", reference=tx["reference"], eta=(reversal or {}).get("eta", "wakati 24 si 48")),
            {"status": status, "reversal": reversal},
            policy_matches,
        )

    if tx["status"] in {"failed", "duplicate"}:
        dispute = create_dispute(tx["transaction_id"], issue, priority="high" if tx["status"] == "duplicate" else "normal") if auto_create_dispute else None
        reversal_result = request_reversal(tx["transaction_id"], issue) if auto_create_dispute else None
        reversal = reversal_result.get("reversal") if reversal_result else check_reversal_status(tx["transaction_id"])
        english = (
            f"I found {_format_tx(tx)}. Debit posted: {tx['debit_posted']}; recipient credited: {tx['recipient_credited']}. "
        )
        if dispute:
            english += f"Dispute {dispute['dispute']['dispute_id']} is open. "
        if reversal:
            english += f"Reversal {reversal['reversal_id']} is {reversal['status']} with ETA {reversal['eta']}."
        intent = "failed_transfer_reversal_requested" if auto_create_dispute else "transaction_review_needed"
        yoruba_intent = "failed_transfer_reversal_requested" if auto_create_dispute else "default"
        return AgentResponse(
            tx.get("provider"),
            intent,
            english + " " + _policy_brief(policy_matches),
            _yoruba(yoruba_intent, reference=tx["reference"], eta=(reversal or {}).get("eta", "24-48 business hours")),
            {"status": status, "dispute": dispute, "reversal": reversal},
            policy_matches,
        )

    return AgentResponse(
        tx.get("provider"),
        "transaction_review_needed",
        f"I found {_format_tx(tx)}, but its status needs manual review. " + _policy_brief(policy_matches),
        _yoruba("transaction_review_needed"),
        {"status": status},
        policy_matches,
    )


def handle_query(text, auto_create_dispute=True):
    correction = correct_entities(text)
    corrected_text = correction["corrected_transcript"]
    search_text = f"{text} {corrected_text}"
    issue = _detect_issue(search_text)
    policy_matches = retrieve_policy(search_text, issue_type=issue, limit=3)
    reference = _extract_reference(text) or _extract_reference(corrected_text)
    customer = _customer_from_query(search_text)

    if reference:
        tx = get_transaction_by_reference(reference)
        if tx:
            return _route_by_transaction(issue, tx, policy_matches, auto_create_dispute)
        english = f"I could not find transaction/reference {reference}. Please confirm the reference or provide the account phone number."
        return AgentResponse(None, "needs_more_info", english, _yoruba("needs_more_info"), {"entity_correction": correction}, policy_matches)

    if customer and issue == "kyc_restriction":
        kyc = check_kyc_status(customer["customer_id"])
        ticket = None
        if auto_create_dispute:
            ticket = create_kyc_update_ticket(customer["customer_id"], "KYC restriction or identity mismatch.")
        english = (
            f"{customer['name']} is on KYC tier {kyc['kyc_tier']}. BVN: {kyc['bvn_status']}; NIN: {kyc['nin_status']}. "
            f"Restrictions: {', '.join(item['reason'] for item in kyc['restrictions']) or 'none'}."
        )
        if ticket:
            english += f" KYC ticket {ticket['ticket']['ticket_id']} created."
        return AgentResponse(
            "Mafita",
            "kyc_ticket_created",
            english + " " + _policy_brief(policy_matches),
            _yoruba("kyc_ticket_created", ticket_id=(ticket or {"ticket": {"ticket_id": "pending"}})["ticket"]["ticket_id"]),
            {"kyc": kyc, "ticket": ticket},
            policy_matches,
        )

    if customer and issue == "wallet_balance":
        balance = get_wallet_balance(customer["customer_id"])
        reconciliation = compare_wallet_balance_to_ledger(customer["customer_id"])
        ticket = None
        if reconciliation["needs_review"] and auto_create_dispute:
            ticket = create_support_ticket(customer["customer_id"], "wallet_reconciliation", "normal", "Wallet balance does not match ledger balance.")
        english = (
            f"Wallet balance for {customer['name']}: available NGN {balance['available_balance']:,.0f}; "
            f"ledger NGN {balance['ledger_balance']:,.0f}; delta NGN {reconciliation['balance_delta']:,.0f}."
        )
        if ticket:
            english += f" Reconciliation ticket {ticket['ticket']['ticket_id']} created."
        return AgentResponse(
            "Mafita",
            "wallet_reconciliation",
            english + " " + _policy_brief(policy_matches),
            _yoruba("wallet_reconciliation", ticket_id=(ticket or {"ticket": {"ticket_id": "pending"}})["ticket"]["ticket_id"]),
            {"wallet": balance, "reconciliation": reconciliation, "ticket": ticket},
            policy_matches,
        )

    if customer and issue == "card_pos_issue":
        cards = check_card_status(customer["customer_id"])
        terminal_match = re.search(r"\b(?:POS-\d+|AGT-\d+)\b", corrected_text, flags=re.IGNORECASE)
        terminal = get_agent_or_pos_terminal(terminal_match.group(0)) if terminal_match else None
        ticket = create_support_ticket(customer["customer_id"], "card_pos_issue", "normal", corrected_text) if auto_create_dispute else None
        english = f"I found {len(cards)} card(s) for {customer['name']}."
        if terminal:
            english += f" POS terminal {terminal['terminal_id']} is {terminal['status']} with settlement {terminal['last_settlement_status']}."
        if ticket:
            english += f" Ticket {ticket['ticket']['ticket_id']} created."
        return AgentResponse("Mafita", "card_pos_issue", english + " " + _policy_brief(policy_matches), _yoruba("default"), {"cards": cards, "terminal": terminal, "ticket": ticket}, policy_matches)

    if customer:
        transactions = get_recent_transactions(customer["customer_id"])
        restrictions = get_account_restrictions(customer["customer_id"])
        english = (
            f"I found {customer['name']}. Recent transactions:\n"
            + "\n".join(f"- {_format_tx(tx)}" for tx in transactions[:3])
        )
        if restrictions:
            english += "\nRestrictions:\n" + "\n".join(f"- {item['reason']}: {item['resolution']}" for item in restrictions)
        return AgentResponse("Mafita", "customer_context_found", english + "\n" + _policy_brief(policy_matches), _yoruba("needs_more_info"), {"customer": customer, "transactions": transactions, "restrictions": restrictions}, policy_matches)

    english = "I need the Mafita account phone number, customer name, transaction reference, or Session ID to continue."
    return AgentResponse(None, "needs_more_info", english, _yoruba("needs_more_info"), {"entity_correction": correction}, policy_matches)
