import argparse
import hashlib
import json
import mimetypes
import os
import re
import wave
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
EXAMPLES_PATH = ROOT / "scratch" / "e2e_workflow_examples.json"
AUDIO_DIR = ROOT / "scratch" / "entity_stress_v2_audio"

sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

from src.bank0_chat import build_mock_chat_response, looks_like_support_request, detect_language, recent_user_language

from src.bank0_executor import execute_validated_plan
from src.bank0_tools import get_transaction_by_reference
from src.bank0_validator import validate_plan, infer_issue
from src.entity_correction import correct_entities
from src.response_cache import cached_missing_details_response, cached_response_for
from src.yoruba_diacritics import tone_mark_yoruba, strip_diacritics

try:
    from src.bank0_llm import plan_with_groq
except Exception:
    plan_with_groq = None


AUDIO_BY_ID = {
    "S001": "S001_femi_provider_bank_status_support.wav",
    "S043": "S043_segun_identity_security.wav",
    "S056": "S056_funmi_critical_variant_moniepoint.wav",
    "S077": "S077_femi_critical_variant_session_id.wav",
    "S085": "S085_femi_critical_variant_debit.wav",
}

TTS_DIR = ROOT / "scratch" / "tts_cache"
TTS_VOICES = {"femi", "segun", "sade", "funmi"}


SESSION_STATES = {}

def get_session_state(session_id):
    if not session_id:
        return {"resolved": False, "resolved_index": -1}
    return SESSION_STATES.setdefault(session_id, {"resolved": False, "resolved_index": -1})

def set_session_resolved(session_id, resolved, resolved_index=-1, plan_context=None):
    if session_id:
        state = SESSION_STATES.setdefault(session_id, {})
        state["resolved"] = resolved
        state["resolved_index"] = resolved_index
        if plan_context is not None:
            state["last_plan_context"] = plan_context


def set_session_case(session_id, issue_type=None, pending_identifiers=None, plan_context=None):
    if not session_id:
        return
    state = SESSION_STATES.setdefault(session_id, {})
    if issue_type and issue_type != "needs_more_info":
        state["active_issue"] = issue_type
    if pending_identifiers is not None:
        state["pending_identifiers"] = list(pending_identifiers)
    if plan_context is not None:
        state["last_plan_context"] = plan_context


def load_examples():
    examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    for item in examples:
        audio_name = AUDIO_BY_ID.get(item["id"])
        if audio_name and (AUDIO_DIR / audio_name).exists():
            item["audio_url"] = f"/audio/{audio_name}"
    return examples


def heuristic_plan(query):
    corrected = correct_entities(query)
    plan = {
        "issue_type": "needs_more_info",
        "confidence": 0.45,
        "needed_identifiers": [],
        "recommended_tools": [],
        "user_response_brief": "Local heuristic planner used because live Gemini was not requested or unavailable.",
    }
    validated = validate_plan(plan, corrected["corrected_transcript"])
    dry_run = os.environ.get("DEMO_DRY_RUN", "false").lower() == "true"
    execution = execute_validated_plan(validated, corrected["corrected_transcript"], dry_run=dry_run)
    return {
        "mode": "local_heuristic",
        "raw_asr_output": query,
        "corrected_query": corrected["corrected_transcript"],
        "entity_corrections": corrected["corrections"],
        "gemini_raw_plan": plan,
        "validated_plan": validated,
        "execution": execution,
    }


def extract_transaction_id(text):
    # Strip all whitespace and hyphens
    norm = re.sub(r"[\s-]+", "", str(text or "")).upper()
    m = re.search(r"([A-Z]{2,3}\d{4}[A-Z]{1,2}|(?:B0|MF)TX\d{4,}|TX\d{4,})", norm)
    if m:
        return m.group(1)
    # Fallback to original search just in case
    m_orig = re.search(r"\b([A-Z]{2,3}\d{4}[A-Z]{1,2}|(?:B0|MF)[\s-]*TX[\s-]*\d{4,}|TX[\s-]*\d{4,})\b", text, flags=re.IGNORECASE)
    return m_orig.group(1).upper() if m_orig else None



def extract_amount(text):
    m = re.search(r"((?:\u20a6|NGN|N)\s*\d[\d,]*|\b\d[\d,]*\s*(?:naira|k)\b)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\bamount\s*(?:is|was|:)?\s*(\d[\d,]*)\b", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    # Standalone number matching, but restrict to avoid years and times
    for val in re.findall(r"\b(\d{3,6})\b", text):
        val_int = int(val)
        # Exclude years 2000-2030
        if 2000 <= val_int <= 2030:
            continue
        # Exclude 24-hour times (1000-2400) or hours/minutes (0100-0959)
        if len(val) == 4 and 100 <= val_int <= 2400:
            continue
        # Exclude phone prefixes or short standalone numbers under 5 digits unless they escape the filters
        if len(val) >= 5 or (len(val) == 4 and val_int > 2400):
            return val
    return None


def extract_time(text):
    m = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(
        r"\b(yesterday|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|afternoon|evening)\b",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(0)
    return None


def extract_customer_identifier(text):
    # Strip spaces and keep only numbers and plus sign
    digits = re.sub(r"[^\d+]", "", str(text or ""))
    m = re.search(r"(\+?234\d{10}|0\d{10})", digits)
    if m:
        return m.group(1)
    
    lowered = text.lower()
    for name in ["femi", "sade", "segun", "funmi"]:
        if name in lowered:
            return name.capitalize()
    return None



def is_standalone_transaction_id(text):
    clean = str(text or "").strip()
    return bool(clean and extract_transaction_id(clean) == clean)


def is_standalone_customer_identifier(text):
    clean = str(text or "").strip()
    return bool(clean and extract_customer_identifier(clean) == clean)


def issue_from_transaction(tx):
    if not tx:
        return None
    tx_type = str(tx.get("type", "")).lower()
    status = str(tx.get("status", "")).lower()
    if tx_type == "pos_withdrawal" or "pos" in status:
        return "double_debit_pos"
    if "pending" in status and status != "settlement_pending":
        return "pending_transfer"
    if tx.get("recipient_credited") is False and tx.get("debit_posted"):
        return "failed_transfer"
    return "failed_transfer"


def wants_yoruba_explanation(text):
    normalized = strip_diacritics(str(text or "").lower())
    patterns = [
        "mi o gbo english",
        "mi o understand english",
        "i do not understand english",
        "i dont understand english",
        "so ni yoruba",
        "soro yoruba",
        "yoruba please",
        "explain in yoruba",
    ]
    return any(pattern in normalized for pattern in patterns)


def is_explicit_new_case_request(text):
    normalized = strip_diacritics(str(text or "").lower())
    new_case_terms = [
        "new issue",
        "another issue",
        "different issue",
        "new problem",
        "account is restricted",
        "account restricted",
        "my account is frozen",
        "kyc",
        "bvn",
        "nin",
        "double debit",
        "charged twice",
        "pos declined",
        "pending reversal",
        # Yoruba terms and general keywords
        "issue titun",
        "issue tuntun",
        "oro titun",
        "oro tuntun",
        "tuntun",
        "titun",
        "restricted",
        "didi",
        "lemeji",
        "emeji",
        "failing",
        "pos",
    ]
    return any(term in normalized for term in new_case_terms)


def is_post_resolution_followup(text):
    normalized = strip_diacritics(str(text or "").lower())
    if not normalized.strip():
        return False
    if is_explicit_new_case_request(text) or is_standalone_customer_identifier(text):
        return False
    followup_terms = [
        "urgent",
        "now",
        "nisisiyi",
        "nisi",
        "kia kia",
        "expecting",
        "needs it",
        "need it",
        "what can i do",
        "anything i can do",
        "kini mo le se",
        "ki ni mo le se",
        "mo le se bayi",
        "meantime",
        "in the meantime",
        "meanwhile",
        "why",
        "sure",
        "are you sure",
        "can you speed",
        "speed it up",
        "ore mi",
        "owo yen",
        "fe owo",
        "duro",
    ]
    return any(term in normalized for term in followup_terms)


def _last_transaction_from_history(history):
    for msg in reversed(history or []):
        tx_id = extract_transaction_id(str(msg.get("content", "")))
        if tx_id:
            tx = get_transaction_by_reference(tx_id)
            if tx:
                return tx
    return None


def _local_response(reply, language="en", plan_context=None):
    if language in {"yo", "mixed"}:
        reply = tone_mark_yoruba(reply)
    return {
        "mode": "local_response",
        "language": language,
        "thinking_steps": [],
        "reply": reply,
        "english_summary": reply if language == "en" else "Local Yoruba response.",
        "plan_context": plan_context,
    }


def _yoruba_eta(text):
    value = str(text or "akoko die")
    replacements = {
        "1-3 hours or auto-reversal by midnight": "laarin wakati 1 si 3, tabi auto-reversal laarin idaji oru",
        "within 2 hours": "laarin wakati 2",
        "check again in 30 minutes": "laarin iseju 30",
        "same day": "loni gan-an",
    }
    return replacements.get(value, value)



def _standalone_identifier_response(query, history=None):
    if is_standalone_customer_identifier(query):
        language = detect_language(query)
        if language == "en" and recent_user_language(history) == "yo":
            language = "yo"
        if language == "yo":
            return _local_response(
                "Mo gba nomba foonu naa. Jowo so iru oro ti o fe ki n sayewo: transfer, POS double debit, reversal, tabi KYC restriction.",
                "yo",
            )
        return _local_response(
            "I have the phone number. What issue should I check: transfer, POS double debit, reversal, or KYC restriction?",
            "en",
        )
    if is_standalone_transaction_id(query):
        return None
    return None



def _yoruba_explanation_response(history):
    tx = _last_transaction_from_history(history)
    if tx:
        return _local_response(
            f"Ma binu. Transfer naa ti debit jade, sugbon recipient ko ti ri owo naa. O wa ni settlement, o si ye ki o pari laarin {_yoruba_eta(tx.get('expected_resolution'))}. Jowo ma tun transfer naa se.",
            "yo",
        )
    return _local_response(
        "Ma binu. Emi yoo dahun ni Yoruba bayii. Jowo so oro naa die sii ki n le ran e lowo.",
        "yo",
    )


def _latest_tx_from_plan_context(plan_context):
    for item in ((plan_context or {}).get("execution") or {}).get("tool_results", []):
        if item.get("tool") == "get_transaction_by_reference" and isinstance(item.get("result"), dict):
            return item["result"]
    return None


def _post_resolution_followup_response(query, history, plan_context=None):
    language = detect_language(query)
    if language == "en":
        for item in reversed(history or []):
            if item.get("role") == "user" and detect_language(item.get("content", "")) == "yo":
                language = "yo"
                break

    issue_type = ((plan_context or {}).get("validated_plan") or {}).get("issue_type")
    tx = _latest_tx_from_plan_context(plan_context) or _last_transaction_from_history(history)
    eta = tx.get("expected_resolution") if tx else None
    tx_ref = tx.get("reference") if tx else None

    if issue_type in {"failed_transfer", "pending_transfer", "pending_reversal"} or tx:
        if language == "yo":
            eta_part = f" O yẹ kí ó parí {_yoruba_eta(eta)}." if eta else ""
            return _local_response(
                f"Mo mọ̀ pé ọ̀rọ̀ yìí kánjú. Jọ̀wọ́, má ṣe tún transfer náà ṣe; a ń ṣiṣẹ́ lórí rẹ̀ lọ́wọ́ bayìí.{eta_part} Ti ko ba tètè yanjú, reversal yóò bẹ̀rẹ̀ fúnra rẹ̀ tàbí kí support team wa tẹ̀lé e.",
                "yo",
            )
        eta_part = f" Expected resolution is {eta}." if eta else ""
        return _local_response(
            f"I understand it is urgent. Please do not retry the transfer; the money sent is still in settlement/processing.{eta_part} If it does not complete, the reversal path will continue automatically.",
            "en",
        )

    if issue_type == "double_debit_pos":
        if language == "yo":
            return _local_response(
                "Mo mọ̀ pé ọ̀rọ̀ yìí kánjú. Jọ̀wọ́, tọ́jú decline slip àti debit alert rẹ; support team wa yóò lo àwọn details yẹn láti tọpinpin POS double debit náà.",
                "yo",
            )
        return _local_response(
            "I understand it is urgent. Keep the decline slip and debit alert available; those details are what support uses to follow the POS double debit.",
            "en",
        )

    if issue_type == "kyc_restriction":
        if language == "yo":
            return _local_response(
                "Mo mọ̀ pé ọ̀rọ̀ yìí kánjú. KYC review nílò kí àlàyé account rẹ bára mu pẹ̀lú BVN tàbí NIN; tí ticket rẹ bá ti wà ní review, jọ̀wọ́ fi sùúrù dúró kí review team wa parí yẹ̀wò rẹ̀.",
                "yo",
            )
        return _local_response(
            "I understand. KYC review depends on matching the account details with BVN/NIN records; if the ticket is under review, wait for the review team to complete it.",
            "en",
        )

    return _local_response(
        "I understand. Please send the specific issue you want me to check next.",
        language,
    )


def build_support_context(query, history, session_id=None):
    history = history or []
    
    state = get_session_state(session_id)
    explicit_new_case = is_explicit_new_case_request(query)

    # Resolution is session context, not a reset. It helps followups answer from the latest
    # known case, but we keep the full conversation until the browser creates a new session.
    phrase_resolved_index = -1
    # Use robust keyword indicators instead of exact phrases.
    # If any assistant message contains multiple resolution indicators,
    # treat it as the resolution boundary.
    _resolution_keywords = [
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
    for i in range(len(history) - 1, -1, -1):
        msg = history[i]
        if msg.get("role") == "assistant":
            content = strip_diacritics(msg.get("content", "")).lower()
            match_count = sum(1 for kw in _resolution_keywords if kw in content)
            if match_count >= 2:
                phrase_resolved_index = i
                break

    if state.get("resolved") and explicit_new_case:
        set_session_resolved(session_id, False, state.get("resolved_index", -1), state.get("last_plan_context"))
        state = get_session_state(session_id)

    active_history = history
    if explicit_new_case:
        active_history = []
    elif not session_id and phrase_resolved_index != -1:
        active_history = history[phrase_resolved_index + 1:]

    user_messages = [msg["content"] for msg in active_history if msg.get("role") == "user"]
    if not user_messages or user_messages[-1] != query:
        user_messages.append(query)

    tx_id = None
    amount = None
    time_val = None
    cust_id = None

    # Scan user messages backwards so newer details/corrections override older ones
    for msg in reversed(user_messages):
        if not tx_id:
            tx_id = extract_transaction_id(msg)
        if not amount:
            amount = extract_amount(msg)
        if not time_val:
            time_val = extract_time(msg)
        if not cust_id:
            cust_id = extract_customer_identifier(msg)

    active_issue = None
    for msg in reversed(user_messages):
        inferred = infer_issue(msg)
        if inferred != "needs_more_info":
            active_issue = inferred
            break
    if not active_issue:
        active_issue = state.get("active_issue")

    tx_record = get_transaction_by_reference(tx_id) if tx_id else None
    if tx_record:
        active_issue = active_issue or issue_from_transaction(tx_record)
        time_val = time_val or tx_record.get("reported_time")
        amount = amount or str(tx_record.get("amount"))

    lines = []
    if active_issue:
        lines.append(f"Active issue: {active_issue}")
    else:
        lines.append("Active issue: unknown")

    lines.append("Known details:")
    if tx_id:
        lines.append(f"- transaction ID: {tx_id}")
    if time_val:
        lines.append(f"- time: {time_val}")
    if amount:
        lines.append(f"- amount: {amount}")
    if cust_id:
        lines.append(f"- phone/customer: {cust_id}")

    lines.append(f"Latest user message: {query}")
    planning_text = "\n".join(lines)

    return {
        "active_issue": active_issue,
        "transaction_id": tx_id,
        "amount": amount,
        "time": time_val,
        "customer_identifier": cust_id,
        "after_resolution": bool(state.get("resolved") or phrase_resolved_index != -1),
        "transaction_found": bool(tx_record),
        "planning_text": planning_text,
    }


def should_plan(query, history, support_context, session_id=None):
    state = get_session_state(session_id)
    if state.get("active_issue") == "kyc_restriction" and extract_customer_identifier(query):
        return True
    if state.get("resolved"):
        if is_explicit_new_case_request(query):
            return True
        if extract_transaction_id(query):
            return True
        if support_context.get("active_issue") == "kyc_restriction" and extract_customer_identifier(query):
            return True
        return False
    if support_context.get("after_resolution") and is_standalone_customer_identifier(query):
        return False
        
    if looks_like_support_request(query):
        return True
    if support_context.get("active_issue") and support_context["active_issue"] != "needs_more_info":
        return True
    if extract_transaction_id(query) or extract_customer_identifier(query) or extract_amount(query) or extract_time(query):
        return True
    return False


def chat_response(query, use_live=False, history=None, voice="femi", session_id=None):
    cached = cached_response_for(query)
    if cached:
        response = {
            "mode": "cached_response",
            **cached,
            "plan_context": None,
        }
        return _attach_audio(response, voice)

    support_context = build_support_context(query, history, session_id)
    if wants_yoruba_explanation(query):
        return _attach_audio(_yoruba_explanation_response(history), voice)

    state = get_session_state(session_id)
    if state.get("resolved") and is_post_resolution_followup(query):
        return _attach_audio(_post_resolution_followup_response(query, history, state.get("last_plan_context")), voice)
    if support_context.get("after_resolution") and is_post_resolution_followup(query):
        return _attach_audio(_post_resolution_followup_response(query, history), voice)

    plan_context = None
    if should_plan(query, history, support_context, session_id):
        planning_text = support_context["planning_text"]
        try:
            plan_context = live_plan(planning_text) if use_live else heuristic_plan(planning_text)
        except Exception:
            plan_context = heuristic_plan(planning_text)
        cached_details = cached_missing_details_response(query, plan_context)
        if cached_details:
            response = {
                "mode": "cached_response",
                **cached_details,
                "plan_context": plan_context,
            }
            return _attach_audio(response, voice)
            
    if not plan_context:
        response = _standalone_identifier_response(query, history)
        if response:
            return _attach_audio(response, voice)


            
    response = build_mock_chat_response(
        query,
        plan_context=plan_context,
        history=history or [],
        use_live=bool(os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")),
    )

    
    # Check if this response resolved or escalated the case
    if plan_context:
        decision = plan_context.get("validated_plan", {}).get("validation", {}).get("decision")
        issue_type = plan_context.get("validated_plan", {}).get("issue_type")
        pending = plan_context.get("validated_plan", {}).get("needed_identifiers", [])
        set_session_case(session_id, issue_type, pending, plan_context)
        if decision in ("execute", "escalate"):
            set_session_resolved(session_id, True, len(history or []), plan_context)
            
    return _attach_audio(response, voice)


def _attach_audio(response, voice):
    try:
        audio = synthesize_response(response.get("reply", ""), voice)
        response["audio"] = audio
    except Exception as exc:
        response["audio"] = {"error": str(exc)}
    return response


def live_plan(query):
    if plan_with_groq is None:
        raise RuntimeError("Groq planner is not importable in this environment.")
    corrected = correct_entities(query)
    raw_plan = plan_with_groq(query)
    validated = validate_plan(raw_plan, corrected["corrected_transcript"])
    dry_run = os.environ.get("DEMO_DRY_RUN", "false").lower() == "true"
    execution = execute_validated_plan(validated, corrected["corrected_transcript"], dry_run=dry_run)
    return {
        "mode": "live_groq",
        "raw_asr_output": query,
        "corrected_query": corrected["corrected_transcript"],
        "entity_corrections": corrected["corrections"],
        "groq_raw_plan": raw_plan,
        "gemini_raw_plan": raw_plan,
        "validated_plan": validated,
        "execution": execution,
    }


def synthesize_response(text, voice):
    clean_text = str(text or "").strip()
    clean_voice = voice if voice in TTS_VOICES else "femi"
    if not clean_text:
        raise ValueError("text is required")
    TTS_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(f"{clean_voice}\n{clean_text}".encode("utf-8")).hexdigest()[:20]
    output_path = TTS_DIR / f"mafita_{clean_voice}_{digest}.wav"
    meta_path = output_path.with_suffix(".json")
    stale_fallback = False
    if meta_path.exists():
        try:
            stale_fallback = bool(json.loads(meta_path.read_text(encoding="utf-8")).get("fallback"))
        except Exception:
            stale_fallback = False
    needs_generation = stale_fallback or not output_path.exists() or output_path.stat().st_size == 0
    if output_path.exists() and output_path.stat().st_size > 0 and meta_path.exists() and not stale_fallback:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        metadata["cached"] = True
        return metadata
    if needs_generation:
        if stale_fallback:
            output_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
        try:
            from src.voice import YorubaVoiceGenerator

            generator = YorubaVoiceGenerator()
            generator.generate_speech(clean_text, output_file=str(output_path), voice=clean_voice)
        except Exception as exc:
            metadata = {
                "voice": clean_voice,
                "cached": False,
                "error": f"Voice provider failed: {exc}",
            }
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            return metadata
        metadata = {
            "audio_url": f"/tts/{output_path.name}",
            "voice": clean_voice,
            "cached": False,
        }
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return metadata
    return {
        "audio_url": f"/tts/{output_path.name}",
        "voice": clean_voice,
        "cached": True,
    }


def _write_placeholder_wav(path, duration_seconds=0.45, sample_rate=16000):
    frame_count = int(duration_seconds * sample_rate)
    silence = b"\x00\x00" * frame_count
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(silence)


ASR_PIPELINE = None

def transcribe_audio(audio_bytes, ext):
    global ASR_PIPELINE
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = Path(tmp.name)
        
    try:
        import shutil
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found on system (required for local audio decoding)")

        if ASR_PIPELINE is None:
            print("Loading NCAIR1/Yoruba-ASR model for transcription...")
            from transformers import pipeline
            import torch
            device = 0 if torch.cuda.is_available() else -1
            ASR_PIPELINE = pipeline(
                "automatic-speech-recognition",
                model="NCAIR1/Yoruba-ASR",
                device=device
            )
            
        print(f"Transcribing audio with N-ATLaS ASR: {tmp_path}")
        result = ASR_PIPELINE(str(tmp_path))
        transcription = result.get("text", "").strip()
        print(f"ASR Output: {transcription}")
        return transcription
    except Exception as exc:
        print(f"N-ATLaS ASR failed: {exc}. Trying Groq Whisper fallback...")
        try:
            import httpx
            key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
            if not key:
                try:
                    from src.groq_client import groq_key
                    key = groq_key()
                except Exception:
                    pass
            if key:
                base_url = None
                try:
                    from src.groq_client import GROQ_BASE_URL
                    base_url = GROQ_BASE_URL
                except Exception:
                    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
                    
                headers = {"Authorization": f"Bearer {key}"}
                data = {
                    "model": "whisper-large-v3",
                    "language": "yo",
                    "response_format": "json",
                    "prompt": "Àwọn ìbéèrè ati ìsòro nípa gbigbe owo, account restriction, KYC, gbigbe owo to kuna, ati gbigbe owo si eyan miiran lori OPay, PalmPay, Moniepoint."
                }
                with open(tmp_path, "rb") as f:
                    response = httpx.post(
                        f"{base_url}/audio/transcriptions",
                        headers=headers,
                        data=data,
                        files={"file": (tmp_path.name, f, f"audio/{ext}")},
                        timeout=60
                    )
                response.raise_for_status()
                return response.json().get("text", "").strip()
        except Exception as fallback_exc:
            print(f"Groq Whisper fallback also failed: {fallback_exc}")
        raise exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()



class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(fmt % args)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type=None):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/api/examples":
            self.send_json(load_examples())
            return
        if parsed.path == "/api/run-example":
            case_id = parse_qs(parsed.query).get("id", [""])[0]
            match = next((item for item in load_examples() if item["id"] == case_id), None)
            self.send_json(match or {"error": "unknown_case"}, 200 if match else 404)
            return
        if parsed.path.startswith("/audio/"):
            name = Path(unquote(parsed.path.removeprefix("/audio/"))).name
            self.send_file(AUDIO_DIR / name, "audio/wav")
            return
        if parsed.path.startswith("/tts/"):
            name = Path(unquote(parsed.path.removeprefix("/tts/"))).name
            self.send_file(TTS_DIR / name, "audio/wav")
            return
        if parsed.path.startswith("/static/"):
            name = parsed.path.removeprefix("/static/")
            self.send_file(STATIC_DIR / name)
            return
        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/run-text", "/api/tts", "/api/chat", "/api/stt"}:
            self.send_error(404)
            return

        content_type = self.headers.get("Content-Type", "")
        if parsed.path == "/api/stt" or content_type.startswith("audio/"):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                audio_bytes = self.rfile.read(length)
                
                ext = "wav"
                if "webm" in content_type:
                    ext = "webm"
                elif "ogg" in content_type:
                    ext = "ogg"
                elif "mp4" in content_type:
                    ext = "mp4"
                elif "mpeg" in content_type or "mp3" in content_type:
                    ext = "mp3"
                
                text = transcribe_audio(audio_bytes, ext)
                self.send_json({"text": text})
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.send_json({"error": str(exc)}, 500)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        if parsed.path == "/api/tts":
            try:
                self.send_json(synthesize_response(payload.get("text"), payload.get("voice", "femi")))
            except Exception as exc:
                self.send_json({"error": str(exc)}, 500)
            return

        query = str(payload.get("query", "")).strip()
        use_live = payload.get("use_live_groq")
        if use_live is None:
            use_live = payload.get("use_live_gemini")
        if use_live is None:
            use_live = True
        use_live = bool(use_live)
        history = payload.get("history", [])
        voice = str(payload.get("voice", "femi"))
        session_id = payload.get("session_id")
        if not query:
            self.send_json({"error": "query is required"}, 400)
            return
        if parsed.path == "/api/chat":
            try:
                self.send_json(chat_response(query, use_live, history, voice, session_id))
            except Exception as exc:
                fallback = chat_response(query, False, history, voice, session_id)
                fallback["mode"] = "local_heuristic_fallback"
                fallback["live_error"] = str(exc)
                self.send_json(fallback)
            return
        try:
            result = live_plan(query) if use_live else heuristic_plan(query)
        except Exception as exc:
            fallback = heuristic_plan(query)
            fallback["mode"] = "local_heuristic_fallback"
            fallback["live_error"] = str(exc)
            result = fallback
        self.send_json(result)


def main():
    parser = argparse.ArgumentParser(description="Run the Mafita operational web demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Mafita web demo running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
