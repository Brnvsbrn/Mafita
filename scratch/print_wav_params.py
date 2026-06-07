import os
import wave

scratch_dir = os.path.dirname(__file__)
audio_path = os.path.join(scratch_dir, "dispute_audio", "Q01_femi_failed_transfer_opay.wav")

if os.path.exists(audio_path):
    with wave.open(audio_path, "rb") as wav:
        params = wav.getparams()
        print("WAV parameters:")
        print("Channels:", params.nchannels)
        print("Sample Width (bytes):", params.sampwidth)
        print("Frame Rate (Hz):", params.framerate)
        print("Total Frames:", params.nframes)
        print("Compression Type:", params.comptype)
        print("Compression Name:", params.compname)
        duration = params.nframes / params.framerate
        print("Calculated Duration (seconds):", duration)
else:
    print("File not found.")
