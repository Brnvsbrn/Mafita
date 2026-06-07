import os
import inspect
from pathlib import Path
from dotenv import load_dotenv
from spitch import Spitch

load_dotenv()
api_key = os.getenv("SPITCH_API_KEY")
client = Spitch(api_key=api_key)

print("Signature of client.speech.transcribe:")
print(inspect.signature(client.speech.transcribe))

scratch_dir = os.path.dirname(__file__)
audio_path = os.path.join(scratch_dir, "dispute_audio", "Q02_sade_failed_transfer_palmpay.wav")

if os.path.exists(audio_path):
    print(f"\nTranscribing {os.path.basename(audio_path)} using Spitch ASR...")
    try:
        response = client.speech.transcribe(
            content=Path(audio_path)
        )
        print("Success! Response type:", type(response))
        print("Response attributes:", dir(response))
        
        # Check for transcription text or segments
        if hasattr(response, "text"):
            # We will save the stdout to a UTF-8 log to prevent charmap errors on printing
            output_log = os.path.join(scratch_dir, "transcribe_debug.txt")
            with open(output_log, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Transcription text successfully saved to: {output_log}")
            # print first 50 chars safely
            print("First 50 chars of transcription:", response.text[:50].encode('ascii', errors='replace').decode('ascii'))
        else:
            print("Response:", response)
            
    except Exception as e:
        print("Error calling transcribe:", e)
else:
    print("Audio file not found.")
