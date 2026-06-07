import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from functools import lru_cache

BASE_DIR = os.path.dirname(__file__)
LEXICON_PATH = os.path.join(BASE_DIR, "entity_lexicon.json")


@dataclass
class Correction:
    raw: str
    canonical: str
    entity_type: str
    confidence: float
    action: str
    reason: str


@lru_cache(maxsize=4)
def _load_lexicon(path=LEXICON_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=4)
def _alias_records(path=LEXICON_PATH):
    records = []
    lexicon = _load_lexicon(path)
    for entity in lexicon["entities"]:
        for alias in entity["aliases"]:
            alias_norm = normalize(alias)
            if not alias_norm:
                continue
            pattern = re.compile(rf"(?<!\w){re.escape(alias_norm)}(?!\w)", re.IGNORECASE)
            records.append((alias_norm, pattern, entity))
    return tuple(sorted(records, key=lambda item: len(item[0]), reverse=True))


def strip_diacritics(text):
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def normalize(text):
    text = strip_diacritics(text).lower()
    text = re.sub(r"[^\w\s+#-]", " ", text, flags=re.UNICODE)
    text = text.replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def _context_present(text, context_terms):
    normalized = normalize(text)
    return any(normalize(term) in normalized for term in context_terms)


def _replace_phrase(text, phrase, replacement):
    pattern = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", re.IGNORECASE)
    return pattern.sub(replacement, text)


def _find_high_risk(text, lexicon):
    normalized = normalize(text)
    findings = []
    for spec in lexicon.get("high_risk_patterns", []):
        for match in re.finditer(spec["pattern"], normalized, flags=re.IGNORECASE):
            findings.append(
                Correction(
                    raw=match.group(0),
                    canonical=match.group(0),
                    entity_type=spec["name"],
                    confidence=1.0,
                    action="confirm",
                    reason="high_risk_identifier",
                )
            )
    return findings


def _best_fuzzy_match(token, entities):
    best = None
    for entity in entities:
        if entity.get("context_required"):
            continue
        for alias in entity["aliases"]:
            alias_norm = normalize(alias)
            if len(alias_norm) < 4:
                continue
            score = SequenceMatcher(None, token, alias_norm).ratio()
            if score >= 0.88 and (best is None or score > best[0]):
                best = (score, entity, alias_norm)
    return best


def correct_entities(text, lexicon_path=LEXICON_PATH, fuzzy=False):
    start = time.perf_counter()
    lexicon = _load_lexicon(lexicon_path)
    entities = lexicon["entities"]
    normalized_text = normalize(text)
    corrected = normalized_text
    corrections = []

    context_required = {}
    for entity in entities:
        if entity.get("context_required") and not _context_present(text, entity.get("context_terms", [])):
            context_required[entity["canonical"]] = False
        elif entity.get("context_required"):
            context_required[entity["canonical"]] = True

    for alias, pattern, entity in _alias_records(lexicon_path):
        if context_required.get(entity["canonical"]) is False:
            continue
        if not pattern.search(corrected):
            continue
        canonical = entity["canonical"]
        corrected = pattern.sub(canonical, corrected)
        corrections.append(
            Correction(
                raw=alias,
                canonical=canonical,
                entity_type=entity["type"],
                confidence=0.98,
                action="auto_correct" if entity.get("risk") != "medium" else "flag",
                reason="known_alias",
            )
        )

    if fuzzy:
        tokens = corrected.split()
        for index, token in enumerate(tokens):
            if any(char.isdigit() for char in token):
                continue
            if token.lower() != token:
                continue
            match = _best_fuzzy_match(token, entities)
            if not match:
                continue
            score, entity, _alias = match
            tokens[index] = entity["canonical"]
            corrections.append(
                Correction(
                    raw=token,
                    canonical=entity["canonical"],
                    entity_type=entity["type"],
                    confidence=round(score, 3),
                    action="auto_correct",
                    reason="fuzzy_alias",
                )
            )
        corrected = " ".join(tokens)

    high_risk = _find_high_risk(text, lexicon)
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "raw_transcript": text,
        "corrected_transcript": corrected,
        "corrections": [asdict(item) for item in corrections],
        "high_risk_items": [asdict(item) for item in high_risk],
        "needs_confirmation": bool(high_risk),
        "latency_ms": latency_ms,
    }


if __name__ == "__main__":
    examples = [
        "mo gbe owo lati pampe si access bank sugbon o kuna",
        "nibo ni mo ti le ri recession id fun gbigbe owo to kuna",
        "bawo ni mo se le so bvn ati ni mi po mo ope",
    ]
    for example in examples:
        print(json.dumps(correct_entities(example), indent=2, ensure_ascii=False))
