import json
import os
import re
from dataclasses import dataclass

BASE_DIR = os.path.dirname(__file__)
RULES_PATH = os.path.join(BASE_DIR, "fintech_rules.json")


@dataclass(frozen=True)
class PolicyMatch:
    provider: str
    issue: str
    score: int
    policy: dict


def _load_rules():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def flatten_policies():
    """Returns every policy entry as provider/issue/policy records."""
    rules = _load_rules()
    records = []
    for provider, issues in rules.items():
        for issue, policy in issues.items():
            records.append(
                {
                    "provider": provider,
                    "issue": issue,
                    "policy": policy,
                    "search_text": " ".join(
                        [
                            provider,
                            issue.replace("_", " "),
                            policy.get("problem", ""),
                            " ".join(policy.get("steps", [])),
                            policy.get("resolution_timeline", ""),
                        ]
                    ),
                }
            )
    return records


def search_policies(query, provider=None, limit=3):
    """Small lexical retriever for the demo before ChromaDB is introduced."""
    query_tokens = _tokens(query)
    matches = []

    for record in flatten_policies():
        if provider and record["provider"] != provider:
            continue

        record_tokens = _tokens(record["search_text"])
        score = len(query_tokens & record_tokens)

        if record["provider"] in query.lower():
            score += 4
        for word in record["issue"].split("_"):
            if word in query.lower():
                score += 2

        if score > 0:
            matches.append(
                PolicyMatch(
                    provider=record["provider"],
                    issue=record["issue"],
                    score=score,
                    policy=record["policy"],
                )
            )

    return sorted(matches, key=lambda item: item.score, reverse=True)[:limit]
