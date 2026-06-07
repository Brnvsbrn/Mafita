import os
import wave
import json

def analyze_wav(filepath):
    if not os.path.exists(filepath):
        return f"File {os.path.basename(filepath)} does not exist."
        
    with wave.open(filepath, "rb") as wav:
        params = wav.getparams()
        frames = wav.readframes(params.nframes)
        
        # Audio parameters
        sample_rate = params.framerate
        num_channels = params.nchannels
        sampwidth = params.sampwidth
        total_frames = params.nframes
        duration = total_frames / sample_rate
        
        # Simple energy calculation to find silent regions (pauses)
        # Convert raw bytes to integers depending on sample width (assume 16-bit PCM)
        import struct
        fmt = f"<{total_frames * num_channels}h"
        try:
            samples = struct.unpack(fmt, frames)
            # Normalise samples
            max_val = float(2**(8*sampwidth - 1))
            normalized = [abs(s) / max_val for s in samples]
            
            # Count silent frames (amplitude below a low threshold, e.g., 0.01)
            silence_threshold = 0.01
            silent_samples = sum(1 for s in normalized if s < silence_threshold)
            silence_percent = (silent_samples / len(normalized)) * 100
        except Exception as e:
            silence_percent = "N/A"
            
        return {
            "filename": os.path.basename(filepath),
            "channels": num_channels,
            "sample_rate": sample_rate,
            "duration_seconds": round(duration, 3),
            "silence_percentage": round(silence_percent, 2) if isinstance(silence_percent, float) else silence_percent
        }

scratch_dir = os.path.dirname(__file__)
audio_path = os.path.join(scratch_dir, "dispute_audio", "Q01_femi_failed_transfer_opay.wav")

if os.path.exists(audio_path):
    metrics = analyze_wav(audio_path)
    print("Acoustic Analysis Results:")
    print(json.dumps(metrics, indent=2))
else:
    # Just list file if present
    print(f"File not found at: {audio_path}")
