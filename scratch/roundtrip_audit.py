"""
Roundtrip Pronunciation Audit:
1. Fix the malformed WAV headers (streaming nframes placeholder)
2. Transcribe each fixed WAV using Spitch STT API
3. Compare transcription vs intended text to detect pronunciation drift
"""
import os
import io
import json
import wave
import struct
from pathlib import Path
from dotenv import load_dotenv
from spitch import Spitch

load_dotenv()
client = Spitch(api_key=os.getenv("SPITCH_API_KEY"))

scratch_dir = os.path.dirname(__file__)
audio_dir = os.path.join(scratch_dir, "dispute_audio")
fixed_dir = os.path.join(scratch_dir, "dispute_audio_fixed")
os.makedirs(fixed_dir, exist_ok=True)

# Load the metadata manifest
with open(os.path.join(scratch_dir, "dispute_metadata.json"), "r", encoding="utf-8") as f:
    metadata = json.load(f)

def fix_wav_header(src_path, dst_path):
    """Re-write WAV with correct nframes derived from actual file size."""
    with open(src_path, "rb") as f:
        raw = f.read()
    
    # Parse the raw bytes: standard WAV is 44-byte header + PCM data
    # We know: channels=1, sampwidth=2, framerate=24000
    header_size = 44
    data_bytes = raw[header_size:]
    num_frames = len(data_bytes) // 2  # 16-bit mono = 2 bytes per frame
    
    with wave.open(dst_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(data_bytes)
    
    return num_frames

audit_results = []

for entry in metadata:
    qid = entry["id"]
    intended_text = entry["text"]
    filename = entry.get("audio_filename", "")
    src_path = os.path.join(audio_dir, filename)
    fixed_path = os.path.join(fixed_dir, filename)
    
    if not os.path.exists(src_path):
        print(f"[{qid}] SKIP — file not found: {filename}")
        continue
    
    # Step 1: Fix WAV header
    print(f"[{qid}] Fixing WAV header for {filename}...")
    num_frames = fix_wav_header(src_path, fixed_path)
    duration_s = round(num_frames / 24000, 2)
    
    # Step 2: Transcribe using Spitch STT
    print(f"[{qid}] Transcribing ({duration_s}s audio)...")
    transcribed_text = ""
    try:
        response = client.speech.transcribe(
            content=Path(fixed_path),
            language="yo"
        )
        transcribed_text = response.text if hasattr(response, "text") else str(response)
    except Exception as e:
        transcribed_text = f"[TRANSCRIPTION ERROR: {e}]"
    
    # Step 3: Record result
    audit_results.append({
        "id": qid,
        "voice": entry.get("voice", ""),
        "intended": intended_text,
        "transcribed": transcribed_text,
        "duration_s": duration_s
    })
    print(f"[{qid}] Done.")

# Save full audit report
output_path = os.path.join(scratch_dir, "pronunciation_audit.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(audit_results, f, indent=2, ensure_ascii=False)

print(f"\nFull audit saved to {output_path}")
print(f"Total queries audited: {len(audit_results)}")
