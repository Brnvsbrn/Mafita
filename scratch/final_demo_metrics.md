# Bank0 Final Demo Metrics

Updated: 2026-06-05

## Core Pipeline

```text
Yoruba audio
-> N-ATLaS ASR
-> entity correction
-> Gemini planner
-> Bank0 validator
-> Bank0 executor
-> Yoruba response
```

The pipeline no longer uses a translation-first step. Gemini receives both:

```text
raw N-ATLaS transcript
entity-normalized hint transcript
entity correction list
```

The raw transcript preserves user wording. The correction layer supplies fintech entity hints.

## ASR Results

Original 20-sample benchmark:

```text
N-ATLaS avg latency:      ~0.630s
N-ATLaS WER:              ~0.2268
N-ATLaS CER:              ~0.0973
Whisper Large-v3 latency: ~1.028s
Whisper Large-v3 WER:     ~0.7969
Whisper Large-v3 CER:     ~0.2622
```

Conclusion:

```text
N-ATLaS is the better STT backbone for Yoruba fintech audio.
```

## Entity Correction

Original benchmark:

```text
Raw entity preservation:       0.5375
Corrected entity preservation: 0.9875
Lift:                          +0.4500
```

Expanded benchmark:

```text
Raw entity preservation:       0.2908
Corrected entity preservation: 0.8504
Lift:                          +0.5596
```

Entity Stress v2:

```text
Samples:                       86
Canonical lexicon terms:       99
Raw entity preservation:       0.3236
Corrected entity preservation: 0.8682
Lift:                          +0.5446
Perfect samples:               52 / 86
Avg correction latency:        ~3.95ms
```

## Planner And Validator

Synthetic Bank0 planner set, Gemini 3.5 batch:

```text
Raw Gemini planner score:       0.7775
Raw issue accuracy:             0.7000
Raw tool recall:                0.6100
Raw safety pass rate:           1.0000

Validated score:                0.9587
Validated issue accuracy:       0.9000
Validated tool recall:          0.9750
Validated safety pass rate:     1.0000
```

Actual ASR end-to-end planner set:

```text
Raw Gemini planner score:       0.7208
Raw issue accuracy:             0.8750
Raw tool recall:                0.4583
Raw safety pass rate:           1.0000

Validated score:                0.9609
Validated issue accuracy:       1.0000
Validated tool recall:          0.8438
Validated safety pass rate:     1.0000
Missing-info pass rate:         1.0000
```

## Model Access Notes

Gemini:

```text
gemini-3.5-flash works for single/batch calls, but has tight rate limits.
gemini-3.1-flash-lite works more reliably for smaller evals.
```

NVIDIA Build/NIM:

```text
meta/llama-3.1-8b-instruct: callable
meta/llama-3.1-70b-instruct: callable
qwen/qwen3-next-80b-a3b-instruct: callable
nvidia/llama-3.3-nemotron-super-49b-v1.5: callable for simple probes
```

Cencori:

```text
Model listing works.
Some Gemini/OpenAI routes are rate-limited.
Some providers require separate provider setup/credits.
```

## Demo Cases

Use:

```text
S001 pending transfer / reversal
S043 KYC BVN/NIN
S056 POS/NIP timeout misclassified by Gemini then repaired by validator
S077 Session ID request
S085 double debit on POS
```

Run:

```powershell
.\venv\Scripts\python.exe .\scratch\run_final_demo.py
```

## Frontend Plan

Build a web app after the backend demo is stable.

Recommended first frontend:

```text
Single-page operational demo, not a landing page.
Left column: audio/sample input and transcript stages.
Middle column: Gemini plan and Bank0 validator repair.
Right column: executed tools, final Yoruba response, optional TTS playback.
```

Do not overbuild auth or a database for the hackathon demo. Use the existing mock Bank0 backend.
