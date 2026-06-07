import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent / "bank0_mock.json"


def _load():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _save(data):
    DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _find(items, **criteria):
    for item in items:
        if all(item.get(key) == value for key, value in criteria.items()):
            return item
    return None


def _normalize_lookup(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _phone_variants(value):
    compact = _normalize_lookup(value)
    variants = {compact}
    if compact.startswith("234") and len(compact) == 13:
        variants.add("0" + compact[3:])
    if compact.startswith("0") and len(compact) == 11:
        variants.add("234" + compact[1:])
    return variants


def lookup_customer(phone_or_name):
    data = _load()
    needle = str(phone_or_name or "").strip().lower()
    compact = _normalize_lookup(needle)
    for customer in data["customers"]:
        lookup_values = {
            customer["phone"].lower(),
            customer["name"].lower(),
            customer["customer_id"].lower(),
            _normalize_lookup(customer["phone"]),
            _normalize_lookup(customer["name"]),
            _normalize_lookup(customer["customer_id"]),
            *_phone_variants(customer["phone"]),
        }
        if needle in lookup_values or compact in lookup_values or bool(_phone_variants(needle) & lookup_values):
            return deepcopy(customer)
        if needle and needle in customer["name"].lower():
            return deepcopy(customer)
    tx = get_transaction_by_reference(phone_or_name)
    if tx:
        customer = _find(data["customers"], customer_id=tx["customer_id"])
        return deepcopy(customer) if customer else None
    return None


def get_recent_transactions(customer_id, limit=5):
    data = _load()
    rows = [tx for tx in data["transactions"] if tx["customer_id"] == customer_id]
    rows.sort(key=lambda row: row["created_at"], reverse=True)
    return deepcopy(rows[:limit])


def get_transaction_by_reference(reference_or_session_id):
    data = _load()
    needle = str(reference_or_session_id or "").strip().lower()
    compact = _normalize_lookup(needle)
    for tx in data["transactions"]:
        aliases = tx.get("aliases", [])
        lookup_values = {
            tx["reference"].lower(),
            tx["transaction_id"].lower(),
            _normalize_lookup(tx["reference"]),
            _normalize_lookup(tx["transaction_id"]),
            *[str(alias).lower() for alias in aliases],
            *[_normalize_lookup(alias) for alias in aliases],
        }
        if tx.get("session_id"):
            lookup_values.add(tx["session_id"].lower())
            lookup_values.add(_normalize_lookup(tx["session_id"]))
        if needle in lookup_values or compact in lookup_values:
            return deepcopy(tx)
    return None


def check_transfer_status(transaction_id):
    data = _load()
    tx = _find(data["transactions"], transaction_id=transaction_id)
    if not tx:
        return {"status": "not_found", "transaction_id": transaction_id}
    ledger = [entry for entry in data["ledger_entries"] if entry["transaction_id"] == transaction_id]
    reversal = _find(data["reversals"], transaction_id=transaction_id)
    return {
        "status": "found",
        "transaction": deepcopy(tx),
        "ledger_entries": deepcopy(ledger),
        "reversal": deepcopy(reversal),
    }


def request_reversal(transaction_id, reason):
    data = _load()
    tx = _find(data["transactions"], transaction_id=transaction_id)
    if not tx:
        return {"status": "error", "message": "Transaction not found."}
    existing = _find(data["reversals"], transaction_id=transaction_id)
    if existing:
        return {"status": "exists", "reversal": deepcopy(existing)}
    reversal = {
        "reversal_id": f"REV-{len(data['reversals']) + 1:04d}",
        "transaction_id": transaction_id,
        "status": "processing",
        "eta": "24-48 business hours",
        "reason": reason,
        "created_at": _now(),
    }
    data["reversals"].append(reversal)
    tx["reversal_status"] = "pending"
    _save(data)
    return {"status": "created", "reversal": deepcopy(reversal)}


def check_reversal_status(transaction_id):
    data = _load()
    reversal = _find(data["reversals"], transaction_id=transaction_id)
    return deepcopy(reversal) if reversal else None


def get_support_ticket_by_transaction(transaction_id):
    data = _load()
    for ticket in data["support_tickets"]:
        if ticket.get("transaction_id") == transaction_id:
            return deepcopy(ticket)
    return None


def create_dispute(transaction_id, reason, priority="normal"):
    data = _load()
    tx = _find(data["transactions"], transaction_id=transaction_id)
    if not tx:
        return {"status": "error", "message": "Transaction not found."}
    existing = _find(data["disputes"], transaction_id=transaction_id)
    if existing:
        return {"status": "exists", "dispute": deepcopy(existing)}
    dispute = {
        "dispute_id": f"DSP-{len(data['disputes']) + 1:04d}",
        "transaction_id": transaction_id,
        "customer_id": tx["customer_id"],
        "reason": reason,
        "priority": priority,
        "status": "open",
        "created_at": _now(),
    }
    data["disputes"].append(dispute)
    _save(data)
    return {"status": "created", "dispute": deepcopy(dispute)}


def check_kyc_status(customer_id):
    data = _load()
    customer = _find(data["customers"], customer_id=customer_id)
    restrictions = [row for row in data["account_restrictions"] if row["customer_id"] == customer_id]
    if not customer:
        return {"status": "not_found"}
    return {
        "status": "found",
        "customer_id": customer_id,
        "kyc_tier": customer["kyc_tier"],
        "bvn_status": customer["bvn_status"],
        "nin_status": customer["nin_status"],
        "risk_flags": customer["risk_flags"],
        "restrictions": deepcopy(restrictions),
    }


def create_kyc_update_ticket(customer_id, reason):
    return create_support_ticket(customer_id, "kyc_update", "normal", reason)


def get_wallet_balance(customer_id):
    data = _load()
    wallet = _find(data["wallets"], customer_id=customer_id)
    return deepcopy(wallet) if wallet else None


def compare_wallet_balance_to_ledger(customer_id):
    data = _load()
    wallet = _find(data["wallets"], customer_id=customer_id)
    entries = [entry for entry in data["ledger_entries"] if entry["customer_id"] == customer_id]
    if not wallet:
        return {"status": "not_found"}
    delta = wallet["ledger_balance"] - wallet["available_balance"]
    return {
        "status": "found",
        "wallet": deepcopy(wallet),
        "ledger_entries": deepcopy(entries),
        "balance_delta": delta,
        "needs_review": delta != 0,
    }


def get_account_restrictions(customer_id):
    data = _load()
    return deepcopy([row for row in data["account_restrictions"] if row["customer_id"] == customer_id])


def check_card_status(customer_id, card_id=None):
    data = _load()
    cards = [card for card in data["cards"] if card["customer_id"] == customer_id]
    if card_id:
        cards = [card for card in cards if card["card_id"] == card_id]
    return deepcopy(cards)


def block_card(customer_id, card_id, reason):
    data = _load()
    card = _find(data["cards"], customer_id=customer_id, card_id=card_id)
    if not card:
        return {"status": "error", "message": "Card not found."}
    card["status"] = "blocked"
    card["block_reason"] = reason
    card["blocked_at"] = _now()
    _save(data)
    return {"status": "blocked", "card": deepcopy(card)}


def create_fraud_report(customer_id, transaction_id, details):
    return create_support_ticket(customer_id, "fraud_report", "high", f"{transaction_id}: {details}")


def get_agent_or_pos_terminal(agent_id_or_terminal_id):
    data = _load()
    needle = agent_id_or_terminal_id.strip().lower()
    for terminal in data["pos_terminals"]:
        if needle in {terminal["terminal_id"].lower(), terminal["agent_id"].lower()}:
            return deepcopy(terminal)
    return None


def create_support_ticket(customer_id, category, priority, summary, transaction_id=None):
    data = _load()
    ticket = {
        "ticket_id": f"TCK-{len(data['support_tickets']) + 1:04d}",
        "customer_id": customer_id,
        "transaction_id": transaction_id,
        "category": category,
        "priority": priority,
        "summary": summary,
        "status": "open",
        "evidence": [],
        "slack_escalation": None,
        "created_at": _now(),
    }
    data["support_tickets"].append(ticket)
    _save(data)
    return {"status": "created", "ticket": deepcopy(ticket)}


def update_support_ticket(ticket_id, status, note):
    data = _load()
    ticket = _find(data["support_tickets"], ticket_id=ticket_id)
    if not ticket:
        return {"status": "error", "message": "Ticket not found."}
    ticket["status"] = status
    ticket.setdefault("notes", []).append({"note": note, "created_at": _now()})
    _save(data)
    return {"status": "updated", "ticket": deepcopy(ticket)}


def attach_evidence_to_ticket(ticket_id, evidence_items):
    data = _load()
    ticket = _find(data["support_tickets"], ticket_id=ticket_id)
    if not ticket:
        return {"status": "error", "message": "Ticket not found."}
    normalized = []
    for item in evidence_items if isinstance(evidence_items, list) else [evidence_items]:
        normalized.append({"description": str(item), "attached_at": _now()})
    ticket.setdefault("evidence", []).extend(normalized)
    _save(data)
    return {"status": "attached", "ticket": deepcopy(ticket)}


def mark_ticket_urgent(ticket_id, reason):
    data = _load()
    ticket = _find(data["support_tickets"], ticket_id=ticket_id)
    if not ticket:
        return {"status": "error", "message": "Ticket not found."}
    ticket["priority"] = "urgent"
    ticket.setdefault("notes", []).append({"note": f"Urgent: {reason}", "created_at": _now()})
    _save(data)
    return {"status": "updated", "ticket": deepcopy(ticket)}


def escalate_to_human(customer_id=None, reason=None, ticket_id=None, channel=None):
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except Exception:
        pass

    data = _load()
    ticket = _find(data["support_tickets"], ticket_id=ticket_id) if ticket_id else None
    if not ticket:
        created = create_support_ticket(customer_id, "human_escalation", "high", reason)
        ticket = created["ticket"]
        ticket_id = ticket["ticket_id"]
        data = _load()
        ticket = _find(data["support_tickets"], ticket_id=ticket_id)
    channel = channel or ("#kyc-review" if ticket.get("category") == "kyc_restriction" else "#disputes")
    customer = _find(data["customers"], customer_id=ticket.get("customer_id"))
    payload = {
        "channel": channel,
        "ticket_id": ticket["ticket_id"],
        "customer_id": ticket.get("customer_id"),
        "customer_phone": customer.get("phone") if customer else None,
        "category": ticket.get("category"),
        "priority": ticket.get("priority"),
        "summary": ticket.get("summary"),
        "transaction_id": ticket.get("transaction_id"),
        "evidence_count": len(ticket.get("evidence", [])),
    }

    # Slack Integration check
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    token = os.environ.get("SLACK_BOT_TOKEN")
    
    # Format blocks for Slack message
    category_label = str(ticket.get("category", "")).replace("_", " ").title()
    priority_emoji = "🔴" if ticket.get("priority") in {"high", "urgent"} else "🟡"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{priority_emoji} New Mafita Agent Escalation",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Ticket ID:* `{ticket['ticket_id']}`"},
                {"type": "mrkdwn", "text": f"*Category:* `{category_label}`"},
                {"type": "mrkdwn", "text": f"*Priority:* `{str(ticket.get('priority')).upper()}`"},
                {"type": "mrkdwn", "text": f"*Customer ID:* `{ticket.get('customer_id')}`"}
            ]
        }
    ]
    
    if customer:
        blocks[1]["fields"].append({"type": "mrkdwn", "text": f"*Phone:* `{customer.get('phone')}`"})
        
    if ticket.get("transaction_id"):
        blocks[1]["fields"].append({"type": "mrkdwn", "text": f"*Transaction ID:* `{ticket.get('transaction_id')}`"})
        
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Summary of Issue:*\n>{ticket.get('summary', 'No summary provided')}"
        }
    })
    
    evidence = ticket.get("evidence", [])
    if evidence:
        evidence_text = "\n".join(f"• {item.get('description')}" for item in evidence)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Attached Evidence:*\n{evidence_text}"
            }
        })
        
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Escalated automatically at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })

    sent = False
    if webhook_url:
        try:
            import httpx
            resp = httpx.post(webhook_url, json={"text": f"New Escalation: {ticket['ticket_id']}", "blocks": blocks}, timeout=10)
            resp.raise_for_status()
            sent = True
        except Exception as e:
            print(f"Error posting Slack webhook: {e}")
            
    elif token:
        try:
            import httpx
            slack_channel = os.environ.get("SLACK_CHANNEL") or channel
            resp = httpx.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "channel": slack_channel,
                    "text": f"New Escalation: {ticket['ticket_id']}",
                    "blocks": blocks
                },
                timeout=10
            )
            resp.raise_for_status()
            if resp.json().get("ok"):
                sent = True
            else:
                print(f"Slack API error: {resp.json().get('error')}")
        except Exception as e:
            print(f"Error calling Slack API: {e}")

    if sent:
        ticket["slack_escalation"] = {
            "status": "slack_sent",
            "sent_at": _now(),
            "payload": payload,
        }
        _save(data)
        return {"status": "slack_sent", "slack_payload": deepcopy(payload), "ticket": deepcopy(ticket)}

    ticket["slack_escalation"] = {
        "status": "mock_sent",
        "sent_at": _now(),
        "payload": payload,
    }
    _save(data)
    return {"status": "mock_sent", "slack_payload": deepcopy(payload), "ticket": deepcopy(ticket)}
