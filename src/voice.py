import os
import re
import unicodedata
from dotenv import load_dotenv

# Load environment variables from the secure .env file
load_dotenv()

try:
    from spitch import Spitch
    SPITCH_INSTALLED = True
except ImportError:
    SPITCH_INSTALLED = False

class YorubaVoiceGenerator:
    """Manages Yoruba Text-to-Speech using the high-fidelity Spitch AI platform."""
    
    def __init__(self, api_key=None):
        if not SPITCH_INSTALLED:
            raise ImportError(
                "The 'spitch' Python library is missing. "
                "Please run: pip install spitch python-dotenv"
            )
            
        if api_key:
            self.keys = [api_key]
        else:
            raw_keys = [
                os.environ.get("SPITCH_API_KEY4"),
                os.environ.get("SPITCH_API_KEY3"),
                os.environ.get("SPITCH_API_KEY2"),
                os.environ.get("SPITCH_API_KEY1"),
                os.environ.get("SPITCH_API_KEY"),
            ]
            self.keys = [k for k in raw_keys if k]
                
        if not self.keys:
            raise ValueError(
                "No Spitch API keys are defined. "
                "Ensure you have set SPITCH_API_KEY2 or SPITCH_API_KEY3 in your secure .env file."
            )
            
        print(f"[Spitch TTS] Client initialized with {len(self.keys)} active keys.")

    def generate_speech(self, text, output_file="output.mp3", voice="femi"):
        """Converts Yoruba text to natural, high-fidelity neural speech.
        
        Args:
            text (str): The Yoruba text to synthesize.
            output_file (str): The filename where the resulting audio will be saved.
            voice (str): The chosen voice profile (defaults to 'femi').
            
        Returns:
            str: Path to the generated audio file.
        """
        last_error = None
        for i, api_key in enumerate(self.keys, start=1):
            try:
                print(f"[Spitch TTS API] Trying key #{i} (starts with {api_key[:8]})...")
                client = Spitch(api_key=api_key)
                
                print(f"[Spitch TTS API] Requesting generation for Yoruba text (length: {len(text)}) using voice: {voice}...")
                language = _detect_tts_language(text)
                request = {"text": text, "voice": voice, "format": "wav"}
                if language:
                    request["language"] = language
                
                try:
                    response = client.speech.generate(**request)
                except Exception as first_error:
                    fallback_text = _speech_safe_text(text)
                    if fallback_text == text:
                        raise first_error
                    print("[Spitch TTS API] Retrying with speech-safe normalized Yoruba text...")
                    response = client.speech.generate(
                        text=fallback_text,
                        voice=voice,
                        format="wav",
                    )
                
                if hasattr(response, "write_to_file"):
                    response.write_to_file(output_file)
                else:
                    audio_data = response.read()
                    if not audio_data:
                        raise RuntimeError("Spitch returned an empty audio response.")
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    raise RuntimeError("Spitch returned an empty audio response.")
                    
                print(f"[Spitch TTS API] Audio saved successfully using key #{i} to: {output_file}")
                return output_file
                
            except Exception as e:
                print(f"[Spitch TTS API] Key #{i} failed: {str(e)}")
                last_error = e
                
        raise last_error


def _speech_safe_text(text):
    replacements = {
        "Mafita": "Mafita",
        "BVN": "B V N",
        "NIN": "N I N",
        "OTP": "O T P",
        "POS": "P O S",
        "NIP": "N I P",
        "Session ID": "Session I D",
    }
    safe = str(text or "")
    for old, new in replacements.items():
        safe = safe.replace(old, new)
    safe = unicodedata.normalize("NFKD", safe)
    safe = "".join(ch for ch in safe if not unicodedata.combining(ch))
    return safe


def _detect_tts_language(text):
    clean = str(text or "").lower()
    if re.search(r"[àáèéẹ̀ẹ́ẹìíòóọ̀ọ́ọùúṣ]", clean):
        return "yo"
    if re.search(r"\b(hello|how can i help|pending transfer|card|wallet|balance|session id)\b", clean):
        return "en"
    return None
