import re
from dataclasses import dataclass
from pathlib import Path


POLICY_DIR = Path(__file__).resolve().parent / "bank0_policies"


@dataclass(frozen=True)
class PolicyMatch:
    issue: str
    score: int
    title: str
    content: str
    path: str


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _read_policy(path):
    content = path.read_text(encoding="utf-8")
    title = path.stem.replace("_", " ").title()
    for line in content.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return title, content


def retrieve_policy(query, issue_type=None, limit=3):
    query_tokens = _tokens(query)
    matches = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        title, content = _read_policy(path)
        search_text = f"{path.stem.replace('_', ' ')} {title} {content}"
        score = len(query_tokens & _tokens(search_text))
        if issue_type and issue_type in path.stem:
            score += 8
        for word in path.stem.split("_"):
            if word in query.lower():
                score += 3
        if score:
            matches.append(
                PolicyMatch(
                    issue=path.stem,
                    score=score,
                    title=title,
                    content=content,
                    path=str(path),
                )
            )
    return sorted(matches, key=lambda item: item.score, reverse=True)[:limit]
