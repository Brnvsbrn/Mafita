import re

try:
    from .yoruba_diacritics import tone_mark_yoruba
except ImportError:
    from yoruba_diacritics import tone_mark_yoruba


GREETING_PATTERNS = [
    re.compile(r"^\s*(hello|hi|hey|good\s*(morning|afternoon|evening)|how\s*far)[\s!.?]*$", re.IGNORECASE),
    re.compile(r"^\s*(bawo(\s+ni)?|e\s*ku(\s+(ile|irole|ojumo|aaro))?|eku(\s+(ile|irole|ojumo|aaro))?|pele(\s+o)?|sannu|nno)[\s!.?]*$", re.IGNORECASE),
    re.compile(r"^\s*(bawo|pele|e ku|eku|sannu|nno).*\b(?:need|nilo|iranlowo|assistance|help|ran mi lowo)\b", re.IGNORECASE),
]


def cached_response_for(query, history=None):
    clean = str(query or "").strip()
    lowered = clean.lower()
    
    has_assistant_msg = any(msg.get("role") == "assistant" for msg in history) if history else False
    is_first_msg = not has_assistant_msg
    is_greeting = any(pattern.search(clean) for pattern in GREETING_PATTERNS)
    
    if is_first_msg or is_greeting:
        # For the demo: force Yoruba greeting so the high-fidelity cached audio plays back successfully
        return _greeting_response("yo")
    return None


def cached_missing_details_response(query, plan_context):
    return None


def _greeting_response(language):
    if language == "yo":
        return {
            "cache_key": "greeting_yo",
            "language": "yo",
            "thinking_steps": [
                tone_mark_yoruba("Mo ri pe eyi je ikini."),
                tone_mark_yoruba("Ko si iwulo lati pe eto account fun eyi."),
            ],
            "reply": "Pẹlẹ o! Ẹ káàbọ, emi ni Mafita, alágbàṣe AI fún ìrànlọ́wọ́. Báwo ni mo ṣe lè ràn yín lọ́wọ́ lónìí?",
            "english_summary": "Cached Yoruba greeting response.",
        }
    return {
        "cache_key": "greeting_en",
        "language": "en",
        "thinking_steps": [
            "I recognized this as a greeting.",
            "No account or transaction lookup is needed.",
        ],
        "reply": "Hello, I'm Mafita, your AI support agent. How can I help you today?",
        "english_summary": "Cached English greeting response.",
    }


def _looks_yoruba(lowered):
    normalized = re.sub(r"[^\w\u0300-\u036f]+", " ", lowered, flags=re.UNICODE)
    tokens = set(normalized.split())
    token_terms = {
        "bawo",
        "kini",
        "owo",
        "iranlowo",
        "jowo",
        "nibo",
        "oruko",
        "ranse",
        "sugbon",
        "lemeji",
        "loni",
    }
    return any(term in tokens for term in token_terms) or "owo mi" in lowered
