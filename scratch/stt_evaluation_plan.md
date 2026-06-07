# YPIT — Yoruba Speech-to-Text (ASR) Comparative Evaluation Plan

This document maps out our evaluation plan for Option A: finding the best Yoruba Speech-to-Text (STT) model. We compare **N-ATLaS ASR** (localized low-resource model) against **OpenAI Whisper Large-v3** (global multilingual standard).

---

## 🔬 The Evaluation Protocol

### 1. Test Dataset
We will construct a benchmark of **20 Yoruba financial support queries**. The benchmark covers:
*   Standard queries (e.g. failed transfers, debit issues, KYC upgrades).
*   High-noise queries (simulating crowded markets, street noise).
*   Code-switching queries (Yoruba heavily mixed with English and Pidgin terms like *OPay*, *debit card*, *transfer*).

### 2. Models to Compare

| Model | Architecture | Size | Deployment | Pros/Cons |
| :--- | :--- | :--- | :--- | :--- |
| **N-ATLaS ASR** | Whisper Small (Fine-tuned) | ~480MB | Virtual Compute (Kaggle GPU) | Trained on native Nigerian speech; excellent with local accents and regional idioms. |
| **OpenAI Whisper Large-v3** | Whisper Large (Zero-shot) | ~3.0GB | Virtual Compute (Kaggle GPU) | Massive multilingual baseline. Needs explicit `{"language": "yoruba"}` parameter to prevent translation drift. |

### 3. Evaluation Metrics

To scientifically declare the winner, we will run our automated script on Kaggle to calculate three core metrics for every test sample:

1.  **Word Error Rate (WER):**
    $$WER = \frac{Substitutions + Deletions + Insertions}{Total\ Words\ in\ Reference}$$
    *The lower the WER, the more accurate the transcription.*
2.  **Entity Preservation Accuracy (EPA):**
    *   Do the models correctly transcribe critical numeric sequences (account numbers, transaction amounts, Session IDs) and brand names (*PalmPay*, *OPay*, *Moniepoint*)? Missing a digit in a transaction ID completely breaks the agent's ability to help.
3.  **Inference Latency:**
    *   The execution time (in seconds) taken to generate the transcription. For real-time economic agents, latency must remain under **1.5 seconds** to prevent conversational lag.

---

## 🛠️ Automated Evaluation Harness (`run_asr_eval.py`)

Below is the structured Python script designed to run inside our virtual Kaggle notebook to perform the head-to-head comparison automatically.

```python
import time
import json
import torch
from transformers import pipeline

# 1. Initialize Test Dataset (20 Yoruba support queries)
test_queries = [
    {
        "id": "Q01",
        "audio_path": "yoruba_dispute_1.wav",
        "reference_text": "Ẹ jọọ gbigbe owo mi kuna lori OPay owo mi si ti senu"
    },
    {
        "id": "Q02",
        "audio_path": "yoruba_dispute_2.wav",
        "reference_text": "PalmPay mi ti dina nitori KYC mi o le gbe owo jade"
    }
    # Remaining 18 benchmark samples are fed here
]

# 2. Initialize Models on Kaggle GPU
device = 0 if torch.cuda.is_available() else -1
print(f"Loading models on device: {'GPU' if device == 0 else 'CPU'}...")

models = {
    "N-ATLaS ASR": pipeline(
        "automatic-speech-recognition",
        model="NCAIR1/Yoruba-ASR",
        device=device
    ),
    "OpenAI Whisper Large-v3": pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3",
        device=device
    )
}

# 3. Execution Loop
evaluation_results = []

for query in test_queries:
    sample_id = query["id"]
    audio = query["audio_path"]
    ref_text = query["reference_text"]
    
    query_result = {
        "id": sample_id,
        "reference": ref_text,
        "transcriptions": {}
    }
    
    for name, pipe in models.items():
        print(f"Running {name} on sample {sample_id}...")
        
        # Capture metrics
        start_time = time.time()
        
        # Explicit parameters for Whisper to force transcription in Yoruba
        gen_kwargs = {}
        if "Whisper" in name:
            gen_kwargs = {"language": "yoruba", "task": "transcribe"}
            
        result = pipe(audio, generate_kwargs=gen_kwargs)
        end_time = time.time()
        
        transcribed_text = result.get("text", "")
        latency = end_time - start_time
        
        # Calculate naive word overlap matching as proxy for WER before heavy libraries
        ref_words = set(ref_text.lower().split())
        trans_words = set(transcribed_text.lower().split())
        intersection = ref_words.intersection(trans_words)
        word_accuracy = len(intersection) / max(len(ref_words), 1)
        
        query_result["transcriptions"][name] = {
            "text": transcribed_text,
            "latency": round(latency, 3),
            "approximate_accuracy": round(word_accuracy * 100, 2)
        }
        
    evaluation_results.append(query_result)

# 4. Save results to JSON file
with open("asr_evaluation_report.json", "w", encoding="utf-8") as f:
    json.dump(evaluation_results, f, indent=2, ensure_ascii=False)
    
print("ASR Head-to-Head evaluation complete! Results saved to asr_evaluation_report.json.")
```

---

## Updated Runnable Harness

The runnable version now lives at `scratch/run_asr_eval.py`; the Kaggle-ready bundle is `scratch/ypit_asr_eval_bundle.zip`.

### Important distinction
N-ATLaS is a Yoruba ASR model, so it produces Yoruba transcription. Whisper Large-v3 can be run in two modes:

1. `task="transcribe"`: produces Yoruba transcription. This is the fair ASR head-to-head against N-ATLaS.
2. `task="translate"`: produces English directly. This measures the native-audio-to-English path.

For the final report, treat these as two related scores:

| Question | Compared Models | Metric |
| :--- | :--- | :--- |
| Which model best hears Yoruba fintech speech? | N-ATLaS ASR vs Whisper transcribe | Yoruba WER/CER + entity preservation |
| How good is direct native audio to English? | Whisper translate baseline | English token-F1 + entity preservation |
| Can N-ATLaS support English output? | N-ATLaS transcript + separate translator | Evaluate after adding translation layer |

### Kaggle run commands

```bash
unzip ypit_asr_eval_bundle.zip
pip install -q transformers accelerate datasets soundfile jiwer
python run_asr_eval.py --audio-dir dispute_audio_fixed --metadata dispute_metadata.json
```

For a quick smoke test:

```bash
python run_asr_eval.py --audio-dir dispute_audio_fixed --metadata dispute_metadata.json --limit 2
```

Outputs:

- `asr_evaluation_report.json`: full per-sample report and model summaries.
- `asr_evaluation_report.csv`: spreadsheet-friendly results.
