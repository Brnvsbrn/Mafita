"""Diagnose what Turn 3 reply text looks like and whether resolution detection works."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from web_demo.server import chat_response, SESSION_STATES, build_support_context
from src.yoruba_diacritics import strip_diacritics

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SESSION_STATES.clear()
history = []

queries = [
    "hello",
    "i sent money but the recipient hasnt received it and i have been debited",
    "ID: OPY7834KL time: 1:47pm amount: 15,000",
]

for i, q in enumerate(queries, 1):
    history.append({"role": "user", "content": q})
    r = chat_response(q, use_live=True, history=history, voice="femi", session_id=None)
    reply = r.get("reply", "")
    history.append({"role": "assistant", "content": reply})
    if i == 3:
        print(f"=== TURN {i} REPLY ===")
        print(reply)
        print(f"\n=== STRIPPED ===")
        stripped = strip_diacritics(reply).lower()
        print(stripped)
        
        # Check keywords
        keywords = [
            "debit is posted", "debit ti", "debit posted",
            "recipient credit", "credit pending", "settlement",
            "do not retry", "ma tun", "ma ṣe tún",
            "auto-reversal", "auto reversal",
            "resolution is", "expected resolution",
            "escalat", "slack", "human review", "nilo human",
            "dispute", "reversal record", "reversal path",
            "mo ri transaction", "i found transaction", "i see transaction",
            "mo ri transfer", "i found the transfer", "i found the reversal",
            "mo ti sayewo", "i checked the mafita", "ticket",
            "support team", "review team",
        ]
        print(f"\n=== KEYWORD MATCHES ===")
        matches = []
        for kw in keywords:
            if kw in stripped:
                matches.append(kw)
                print(f"  MATCH: '{kw}'")
        print(f"Total matches: {len(matches)}")

        # Now test the post-resolution query
        print(f"\n=== TESTING POST-RESOLUTION QUERY ===")
        history.append({"role": "user", "content": "08010000001"})
        ctx = build_support_context("08010000001", history, session_id=None)
        print(f"after_resolution: {ctx.get('after_resolution')}")
        r2 = chat_response("08010000001", use_live=True, history=history, voice="femi", session_id=None)
        print(f"plan_context is None: {r2.get('plan_context') is None}")
        print(f"reply: {r2.get('reply', '')[:100]}")
