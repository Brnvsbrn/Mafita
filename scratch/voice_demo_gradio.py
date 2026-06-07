import os
import sys
import urllib.request
import torch
import torchaudio
import gradio as gr
from transformers import AutoModelForCausalLM, pipeline

# 1. Download dependencies if we are running in Colab/Kaggle
# We will download the YarnGPT repo structure to use their default speaker files.
if not os.path.exists("yarngpt"):
    print("Cloning YarnGPT repository for speaker files and assets...")
    os.system("git clone https://github.com/saheedniyi02/yarngpt.git")

# Add the cloned yarngpt directory to python path
sys.path.append(os.path.abspath("yarngpt"))

try:
    from yarngpt.audiotokenizer import AudioTokenizerV2
except ImportError:
    # Fallback to local import if structure is different
    try:
        from src.audiotokenizer import AudioTokenizerV2
    except ImportError:
        raise ImportError("Cannot find yarngpt/audiotokenizer.py. Please make sure the yarngpt repo is cloned or src directory is present.")

# 2. Check and download WavTokenizer configuration and weights
yaml_url = "https://huggingface.co/novateur/WavTokenizer-medium-speech-75token/resolve/main/wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml"
yaml_path = "wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml"
ckpt_path = "wavtokenizer_large_speech_320_24k.ckpt"

if not os.path.exists(yaml_path):
    print("Downloading WavTokenizer config YAML...")
    urllib.request.urlretrieve(yaml_url, yaml_path)

if not os.path.exists(ckpt_path):
    print("Downloading WavTokenizer checkpoint from Google Drive...")
    try:
        import gdown
    except ImportError:
        print("Installing gdown...")
        os.system("pip install gdown")
        import gdown
    gdown.download(id="1-ASeEkrn4HY49yZWHTASgfGFNXdVnLTt", output=ckpt_path, quiet=False)

# 3. Model Initializations
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Initialize Audio Tokenizer
print("Initializing AudioTokenizer...")
audio_tokenizer = AudioTokenizerV2(
    tokenizer_path="saheedniyi/YarnGPT2",
    wav_tokenizer_model_path=ckpt_path,
    wav_tokenizer_config_path=yaml_path
)

# Load YarnGPT2 TTS model
print("Loading YarnGPT2 TTS model (saheedniyi/YarnGPT2)...")
tts_model = AutoModelForCausalLM.from_pretrained(
    "saheedniyi/YarnGPT2",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

# Load Yoruba ASR model (N-ATLaS Yoruba ASR based on Whisper Small)
print("Loading NCAIR1/Yoruba-ASR model...")
try:
    asr_pipe = pipeline(
        "automatic-speech-recognition",
        model="NCAIR1/Yoruba-ASR",
        device=0 if device == "cuda" else -1
    )
except Exception as e:
    print(f"Could not load NCAIR1/Yoruba-ASR directly: {e}. Falling back to loading manually or using general Whisper.")
    asr_pipe = None

# Define generation functions
def generate_yoruba_speech(text, speaker, lang):
    """Generates audio speech from Yoruba text."""
    try:
        prompt = audio_tokenizer.create_prompt(text=text, lang=lang, speaker_name=speaker)
        input_ids = audio_tokenizer.tokenize_prompt(prompt)
        
        with torch.no_grad():
            output = tts_model.generate(
                input_ids=input_ids,
                temperature=0.1,
                repetition_penalty=1.1,
                max_length=4000
            )
            
        codes = audio_tokenizer.get_codes(output)
        audio = audio_tokenizer.get_audio(codes)
        
        # Save audio temporarily for Gradio
        temp_wav_path = "temp_generated.wav"
        torchaudio.save(temp_wav_path, audio, sample_rate=24000)
        return temp_wav_path, f"Speech generated successfully using {speaker}!"
    except Exception as e:
        return None, f"Error generating speech: {str(e)}"

def transcribe_yoruba_speech(audio_file):
    """Transcribes audio file to Yoruba text."""
    if asr_pipe is None:
        return "ASR Model could not be loaded. Please check model path or connection."
    if audio_file is None:
        return "Please upload or record an audio file first."
    try:
        print(f"Transcribing audio: {audio_file}")
        result = asr_pipe(audio_file)
        return result.get("text", "Transcription failed (no text returned).")
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

# 4. Build Gradio UI
with gr.Blocks(theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="indigo")) as demo:
    gr.Markdown(
        """
        # 🎙️ YPIT Hackathon — Yoruba Multilingual Voice Sandbox
        This sandbox runs on virtual compute (Kaggle/Colab) to test Yoruba Speech Models in real-time.
        """
    )
    
    with gr.Tab("🗣️ Text-To-Speech (YarnGPT2)"):
        gr.Markdown("Generate high-quality Yoruba speech using saheedniyi/YarnGPT2.")
        with gr.Row():
            with gr.Column():
                tts_text_input = gr.Textbox(
                    label="Yoruba Text",
                    placeholder="E joo, gbigbe owo mi kuna lori OPay...",
                    value="E joo, gbigbe owo mi kuna lori OPay, owo mi si ti senu.",
                    lines=3
                )
                tts_speaker = gr.Dropdown(
                    choices=[
                        "yoruba_female1", "yoruba_female2",
                        "yoruba_male1", "yoruba_male2",
                        "hausa_female1", "hausa_female2",
                        "hausa_male1", "hausa_male2",
                        "igbo_female1", "igbo_female2",
                        "igbo_male2"
                    ],
                    label="Speaker Profile",
                    value="yoruba_female1"
                )
                tts_lang = gr.Radio(
                    choices=["yoruba", "hausa", "igbo", "english"],
                    label="Language Mode",
                    value="yoruba"
                )
                tts_submit = gr.Button("⚡ Generate Speech", variant="primary")
            
            with gr.Column():
                tts_audio_output = gr.Audio(label="Generated Audio Output", type="filepath")
                tts_status = gr.Textbox(label="Status Log", interactive=False)
                
        tts_submit.click(
            generate_yoruba_speech,
            inputs=[tts_text_input, tts_speaker, tts_lang],
            outputs=[tts_audio_output, tts_status]
        )
        
    with gr.Tab("🎧 Speech-To-Text (N-ATLaS Yoruba ASR)"):
        gr.Markdown("Transcribe Yoruba audio using NCAIR1/Yoruba-ASR (Whisper Small fine-tuned).")
        with gr.Row():
            with gr.Column():
                asr_audio_input = gr.Audio(
                    label="Record or Upload Yoruba Speech",
                    type="filepath",
                    sources=["microphone", "upload"]
                )
                asr_submit = gr.Button("⚡ Transcribe Audio", variant="primary")
                
            with gr.Column():
                asr_text_output = gr.Textbox(
                    label="Transcribed Yoruba Text",
                    placeholder="Transcription will appear here...",
                    lines=4,
                    interactive=False
                )
                
        asr_submit.click(
            transcribe_yoruba_speech,
            inputs=[asr_audio_input],
            outputs=[asr_text_output]
        )

# Launch Gradio app
# share=True creates a public URL (like *.gradio.live) so you can access it anywhere!
if __name__ == "__main__":
    demo.launch(share=True, debug=True)
