import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import handle_query


SCENARIOS = [
    (
        "failed_transfer",
        "Femi says OPay transfer B0-TX-1001 to Access Bank failed, money was debited but recipient ko ri",
        "transaction_review_needed",
    ),
    (
        "pending_transfer",
        "Sade wants reversal status for B0-TX-2001, the Moniepoint transfer is pending",
        "pending_transfer",
    ),
    (
        "kyc_restriction",
        "Segun account is restricted because BVN and NIN KYC issue",
        "kyc_ticket_created",
    ),
    (
        "wallet_balance",
        "Sade wallet balance does not match ledger",
        "wallet_reconciliation",
    ),
    (
        "double_debit",
        "Funmi saw double debit on card transaction B0-TX-4002",
        "fraud_escalated",
    ),
    (
        "unauthorized_debit",
        "Funmi says unauthorized debit on card transaction B0-TX-4001, she did not authorize it",
        "fraud_escalated",
    ),
    (
        "successful_trace",
        "Femi needs Session ID for transaction B0-TX-1002 because recipient bank asked for it",
        "successful_transfer_trace",
    ),
]


def main():
    failures = []
    for name, query, expected_intent in SCENARIOS:
        response = handle_query(query, auto_create_dispute=False)
        ok = response.intent == expected_intent
        print(f"{name}: {response.intent} {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append((name, expected_intent, response.intent, response.english))

    if failures:
        print("\nFailures:")
        for name, expected, actual, english in failures:
            print(f"- {name}: expected {expected}, got {actual}")
            print(f"  {english}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
