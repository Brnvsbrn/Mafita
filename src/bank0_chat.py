import json
import re

try:
    from .groq_client import DEFAULT_GROQ_MODEL, groq_chat_json
except ImportError:
    from groq_client import DEFAULT_GROQ_MODEL, groq_chat_json

try:
    from .yoruba_diacritics import tone_mark_yoruba
except ImportError:
    from yoruba_diacritics import tone_mark_yoruba

try:
    from .bank0_tools import lookup_customer
except ImportError:
    from bank0_tools import lookup_customer


CHAT_SYSTEM_PROMPT = """You are Mafita Agent, a Yoruba-first voice support agent for Mafita, a mock Nigerian fintech.

You are in a controlled support environment:
- You may explain what you would check, but never claim you moved money or changed a real account.
- Do not reveal or mention that this is a demo, mock, simulation, test, or roleplay.
- Do not claim a real dispute, reversal, ticket, card block, account update, or escalation has been completed. Say the support workflow prepared it or would route it.
- If backend tool context is available, use it.
- If identifiers are missing, ask for the exact missing details.
- For transfer/POS/reversal cases, ask for transaction ID, time, and amount. Use only the phrase "transaction ID" for the transaction identifier.
- For transfer/POS/reversal cases, do not ask for phone number or name unless the backend says customer_identifier is missing.
- Only handle these support tracks: debited but recipient not credited, pending transfer retry advice, pending reversal status, double debit on failed POS, and KYC/account restriction.
- If the user asks for another support category, politely constrain them to those tracks.
- If asked what you can do, list the supported tracks as short bullets. Name the second track "Pending transfer issues".
- For missing details, sound empathetic and ask only for the required details in short bullets.
- On your first substantive reply in a conversation, introduce yourself as Mafita, the AI support agent.
- If the user only greets you, greet them naturally in Yoruba and ask how you can help.
- The default language for all interactions is Yoruba ("yo"). Always reply in Yoruba (with proper tone-marked diacritics) unless the user explicitly speaks purely in English or asks you to speak English.
- Match the user's language for both thinking_steps and reply. For Yoruba or mixed Yoruba, use Yoruba with proper diacritics.
- Keep product names like Mafita, OPay, PalmPay, Moniepoint, BVN, NIN, OTP, POS, and NIP unchanged.
- Preserve important user-provided entities in the reply, especially provider, bank, transaction ID, BVN, NIN, KYC, POS, and amount.
- Do not translate fintech terms such as transaction ID, BVN, NIN, KYC, OTP, POS, NIP, wallet, or account.
- Keep replies voice-friendly: 1 to 2 short sentences unless the user asks for detail.
- For missing transaction details, explicitly ask for transaction ID, time, and amount.
- For missing customer details, explicitly ask only for the registered phone number linked to the Mafita account.
- Never start a reply with "I see <number> in your message" or "I see KYC in your message".

Return only JSON:
{
  "language": "yo" | "en" | "mixed",
  "thinking_steps": string[],
  "reply": string,
  "english_summary": string
}

thinking_steps must be brief user-visible status updates in the matching language (Yoruba by default), not hidden chain-of-thought. Use 2 to 4 steps.
"""


GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|good\s*(morning|afternoon|evening)|bawo(\s+ni)?|eku(\s+(ile|irole|ojumo|aaro))?|e\s*ku(\s+(ile|irole|ojumo|aaro))?|pele(\s+o)?|sannu|nno|how\s*far)[!.?,\s]*$",
    re.IGNORECASE,
)

SUPPORT_TERMS = {
    "transfer",
    "debit",
    "reversal",
    "pending",
    "failed",
    "session",
    "receipt",
    "bvn",
    "nin",
    "kyc",
    "otp",
    "pos",
    "card",
    "wallet",
    "balance",
    "frozen",
    "restricted",
    "charged twice",
    "decline slip",
    "opay",
    "palmpay",
    "moniepoint",
    "nip",
    "owo",
    "ranse",
    "ransẹ",
    "ranṣẹ",
    "gbese",
}

YORUBA_HINTS = {
    "bawo",
    "jo",
    "jowo",
    "duro",
    "gbo english",
    "mi o",
    "owo",
    "oruko",
    "orúkọ",
    "ranse",
    "ransẹ",
    "ranṣẹ",
    "jọwọ",
    "jowo",
    "sugbon",
    "ṣugbọn",
    "nibo",
    "ko de",
    "kò dé",
    "lemeji",
    "lẹmeji",
    "loni",
    "lọwọ",
}


def looks_like_greeting(text):
    return bool(GREETING_RE.match(text or ""))


def looks_like_support_request(text):
    lowered = (text or "").lower()
    return any(term in lowered for term in SUPPORT_TERMS)


def detect_language(text):
    lowered = (text or "").lower()
    # Tokenize for word-level matching
    words = set(re.findall(r"[a-zA-Zàáèéẹ̀ẹ́ìíòóọ̀ọ́ùúṣ]+", lowered))

    # Strong Yoruba word tokens (must match as full words, not substrings)
    yoruba_word_tokens = {
        "bawo", "jowo", "jọwọ", "sugbon", "ṣugbọn", "nibo", "loni",
        "lọwọ", "lemeji", "lẹmeji", "ranse", "ransẹ", "ranṣẹ",
        "oruko", "orúkọ", "owo", "duro", "pele", "iranlowo",
        "debiti", "foonu", "nisi", "nisisiyi", "kini", "emi",
        "looni", "eku", "akoko", "iye", "gba",
        "nilo", "titun", "sẹnd",
    }
    # Yoruba phrase markers (substring match, but multi-word so safe)
    yoruba_phrases = {"mi o", "gbo english", "ko de", "kò dé", "e ku",
                      "mo ro pe", "mo ni", "mo send", "mo sẹnd",
                      "won ti", "wọn ti", "ko ri", "kò rí",
                      "ore mi", "owo yen", "fe owo", "issue titun",
                      "account mi"}

    # English keyword phrases
    english_phrases = {"please", "i want", "is restricted", "my account",
                       "help me with", "reversal status", "hello", "how can",
                       "i sent money", "the recipient", "i have been",
                       "my registered phone", "i have a new issue",
                       "has not received", "hasnt received", "charged twice",
                       "decline slip", "pending reversal"}

    has_yoruba_word = bool(words & yoruba_word_tokens)
    has_yoruba_phrase = any(p in lowered for p in yoruba_phrases)
    has_english_phrase = any(p in lowered for p in english_phrases)

    if has_yoruba_word or has_yoruba_phrase:
        return "yo"
    if has_english_phrase:
        return "en"
    # Default to Yoruba for ambiguous input (Yoruba-first agent)
    return "yo"



def recent_user_language(history):
    for item in reversed(history or []):
        if item.get("role") == "user":
            language = detect_language(item.get("content", ""))
            if language == "yo":
                return "yo"
    return "en"


def build_mock_chat_response(query, plan_context=None, history=None, use_live=True):
    clean_query = str(query or "").strip()
    history = history or []
    language = detect_language(clean_query)
    if language == "en" and (_looks_like_detail_followup(clean_query) or _looks_like_identifier_followup(clean_query)) and recent_user_language(history[:-1]) == "yo":
        language = "yo"
    is_greeting = looks_like_greeting(clean_query)
    execution = (plan_context or {}).get("execution", {})
    if execution.get("final_response") and not is_greeting:
        return _fallback_chat(clean_query, language, plan_context)

    if use_live:
        try:
            payload = {
                "user_message": clean_query,
                "detected_language": language,
                "recent_history": history[-8:],
                "mafita_context": _compact_plan_context(plan_context),
                "is_greeting": is_greeting,
                "is_support_request": looks_like_support_request(clean_query),
            }
            response = groq_chat_json(
                CHAT_SYSTEM_PROMPT,
                payload,
                model=DEFAULT_GROQ_MODEL,
                temperature=0,
                max_tokens=700 if is_greeting else 1100,
            )
            parsed = response["json"]
            reply_language = parsed.get("language") or language
            steps = _tone_steps(_clean_steps(parsed.get("thinking_steps")), reply_language)
            reply = parsed.get("reply") or _fallback_reply(clean_query, language, plan_context)
            reply = _guard_mock_action_claims(reply)
            reply = _preserve_reply_entities(reply, reply_language, clean_query, plan_context)
            return {
                "mode": "mock_agent_groq",
                "model": response["model"],
                "language": reply_language,
                "thinking_steps": steps,
                "reply": tone_mark_yoruba(reply) if reply_language in {"yo", "mixed"} else reply,
                "english_summary": parsed.get("english_summary", ""),
                "plan_context": plan_context,
            }
        except Exception as exc:
            fallback = _fallback_chat(clean_query, language, plan_context)
            fallback["live_error"] = str(exc)
            return fallback

    return _fallback_chat(clean_query, language, plan_context)


def _fallback_chat(query, language, plan_context=None):
    steps = [
        "I checked whether this is a greeting or a support request.",
        "I reviewed the available Mafita mock context.",
        "I prepared the safest next response.",
    ]
    if looks_like_greeting(query):
        steps = [
            "I recognized this as a greeting.",
            "No account or transaction lookup is needed yet.",
            "I am asking what support issue to help with next.",
        ]
    return {
        "mode": "mock_agent_fallback",
        "language": language,
        "thinking_steps": _tone_steps(steps, language),
        "reply": _fallback_reply(query, language, plan_context),
        "english_summary": "Fallback mock response generated locally.",
        "plan_context": plan_context,
    }


def _fallback_reply(query, language, plan_context=None):
    if looks_like_greeting(query):
        if language == "yo":
            return tone_mark_yoruba("Bawo ni, mo wa nibi lati ran o lowo. Se oro transfer, KYC, POS, tabi wallet ni o fe ki n sayewo?")
        return "Hello, I'm Mafita, your AI support agent. Is this about a transfer delay, pending reversal, POS double debit, or KYC restriction?"

    execution = (plan_context or {}).get("execution", {})
    validated = (plan_context or {}).get("validated_plan", {})
    if validated.get("issue_type") == "needs_more_info":
        if language == "yo":
            return tone_mark_yoruba(
                "Mo gba. Mo le ran e lowo pelu:\n- Owo ti kuro sugbon recipient ko ri\n- Pending transfer issues\n- Pending reversal\n- POS double debit\n- KYC tabi account restriction"
            )
        return (
            "I hear you. I can help with:\n"
            "- Money debited but recipient not credited\n"
            "- Pending transfer issues\n"
            "- Pending reversal status\n"
            "- POS double debit after a failed withdrawal\n"
            "- KYC or account restriction"
        )
    final_response = execution.get("final_response", {})
    if final_response.get("yoruba") and language == "yo":
        return tone_mark_yoruba(final_response["yoruba"])
    if final_response.get("english") and language == "en":
        return final_response["english"]

    if language == "yo":
        return tone_mark_yoruba(
            "Mo gbo o. Jowo fi transaction ID, akoko, ati iye owo ranse ti oro naa ba je transfer, POS, tabi reversal; fun KYC, fi nomba foonu account ranse."
        )
    return "I understand. If this is a transfer, POS, or reversal case, please send the transaction ID, time, and amount. For KYC restriction, send the registered phone number."


def _looks_like_detail_followup(text):
    lowered = str(text or "").lower()
    return bool(
        re.search(r"\b(?:[A-Z]{2,3}\d{4}[A-Z]{1,2}|(?:B0|MF)[\s-]*TX[\s-]*\d{4,}|TX[\s-]*\d{4,})\b", text, flags=re.IGNORECASE)
        or re.search(r"\b(?:transaction id|id|amount|time|ngn|₦)\b", lowered)
        or re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", lowered)
    )


def _looks_like_identifier_followup(text):
    return bool(re.search(r"\b(?:\+234\d{10}|0\d{10})\b", str(text or "")))


def _compact_plan_context(plan_context):
    if not plan_context:
        return None
    validated = plan_context.get("validated_plan", {})
    execution = plan_context.get("execution", {})
    return {
        "raw_message": plan_context.get("raw_asr_output"),
        "corrected_message": plan_context.get("corrected_query"),
        "entity_corrections": plan_context.get("entity_corrections", []),
        "issue_type": validated.get("issue_type"),
        "needed_identifiers": validated.get("needed_identifiers", []),
        "recommended_tools": validated.get("recommended_tools", []),
        "validator_decision": validated.get("validation", {}).get("decision"),
        "tools_executed": execution.get("tools_executed", []),
        "tool_results": execution.get("tool_results", []),
        "safe_response": execution.get("final_response", {}),
    }


def _preserve_reply_entities(reply, language, query, plan_context=None):
    return reply
    if not plan_context:
        return reply
    terms = _extract_preserved_entities(query, plan_context)
    if not terms:
        return reply
    normalized_reply = _normalize_for_entity(reply)
    missing = [term for term in terms if _normalize_for_entity(term) not in normalized_reply]
    if not missing:
        return reply
    if language in {"yo", "mixed"}:
        visible = _join_terms(missing[:4], "ati")
        return f"Mo rí {visible} nínú ọ̀rọ̀ rẹ. {reply}"
    visible = _join_terms(missing[:4], "and")
    return f"I see {visible} in your message. {reply}"



def _guard_mock_action_claims(reply):
    guarded = str(reply or "")
    replacements = [
        (r"\bI(?:'|’)ve opened\b", "I prepared"),
        (r"\bI have opened\b", "I prepared"),
        (r"\bI(?:'|’)ve created\b", "I prepared"),
        (r"\bI have created\b", "I prepared"),
        (r"\bI(?:'|’)ve requested\b", "I prepared"),
        (r"\bI have requested\b", "I prepared"),
        (r"\bI(?:'|’)ve blocked\b", "I prepared a block request for"),
        (r"\bI have blocked\b", "I prepared a block request for"),
        (r"\bI(?:'|’)ve escalated\b", "I prepared an escalation for"),
        (r"\bI have escalated\b", "I prepared an escalation for"),
        (r"\bopened a dispute\b", "prepared a dispute"),
        (r"\bcreated a dispute\b", "prepared a dispute"),
        (r"\brequested a reversal\b", "prepared a reversal request"),
        (r"\bblocked your card\b", "prepared a card-block request"),
        (r"\bescalated this\b", "prepared this for escalation"),
    ]
    for pattern, replacement in replacements:
        guarded = re.sub(pattern, replacement, guarded, flags=re.IGNORECASE)
    return guarded


def _extract_preserved_entities(query, plan_context=None):
    correction_terms = []
    for item in (plan_context or {}).get("entity_corrections", []) or []:
        if isinstance(item, dict):
            correction_terms.extend([item.get("raw", ""), item.get("canonical", "")])
    text = " ".join(str(item or "") for item in [query, (plan_context or {}).get("corrected_query"), *correction_terms])
    terms = []
    known_terms = [
        "Mafita",
        "OPay",
        "PalmPay",
        "Moniepoint",
        "Access Bank",
        "BVN",
        "NIN",
        "KYC",
        "OTP",
        "POS",
        "NIP",
        "transaction ID",
    ]
    normalized = _normalize_for_entity(text)
    for term in known_terms:
        if _normalize_for_entity(term) in normalized:
            terms.append(term)
    terms.extend(re.findall(r"\b[A-Z]{1,4}-[A-Z]{1,4}-\d{3,}\b", text))
    # Only preserve numeric terms if they are not phone numbers, or if they are registered phone numbers
    for val in re.findall(r"\b\d{3,}(?:,\d{3})*(?:\.\d+)?\b", text):
        clean_num = re.sub(r"\D+", "", val)
        if (len(clean_num) == 11 and clean_num.startswith("0")) or (len(clean_num) == 13 and clean_num.startswith("234")):
            if lookup_customer(clean_num):
                terms.append(val)
        else:
            terms.append(val)
    deduped = []
    seen = set()
    for term in terms:
        key = _normalize_for_entity(term)
        if key and key not in seen:
            seen.add(key)
            deduped.append(term)
    return deduped


def _normalize_for_entity(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def _join_terms(terms, conjunction):
    if len(terms) <= 1:
        return terms[0] if terms else ""
    if len(terms) == 2:
        return f"{terms[0]} {conjunction} {terms[1]}"
    return ", ".join(terms[:-1]) + f", {conjunction} {terms[-1]}"


def _clean_steps(steps):
    if not isinstance(steps, list):
        return [
            "I reviewed the message.",
            "I checked the safest support path.",
            "I prepared a response.",
        ]
    cleaned = [str(step).strip() for step in steps if str(step).strip()]
    return cleaned[:4] or [
        "I reviewed the message.",
        "I checked the safest support path.",
        "I prepared a response.",
    ]


def _tone_steps(steps, language):
    if language not in {"yo", "mixed"}:
        return steps
    if not any(any(hit in step.lower() for hit in YORUBA_HINTS) for step in steps):
        steps = [
            "Mo ka ifiranṣẹ rẹ.",
            "Mo ṣàyẹ̀wò bóyá ó jẹ́ ìkíni tàbí ọ̀rọ̀ ìrànlọ́wọ́.",
            "Mo ń pèsè ìdáhùn tó yẹ.",
        ]
    return [tone_mark_yoruba(step) for step in steps]


def _parse_json_object(content):
    text = str(content or "").strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)
