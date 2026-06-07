# YPIT Hackathon Project Update - Bank0 Yoruba Voice Support Agent

Date: 2026-06-05

This document explains everything we have built and tested so far for the hackathon project. It is written so a teammate can understand the work even if they have not followed the technical build process.

---

## 1. What We Are Building

We are building a Yoruba-first AI customer support agent for Nigerian fintech users.

The core idea is simple:

> A user speaks in Yoruba about a financial support issue, such as a failed transfer, double debit, missing Session ID, KYC restriction, or pending reversal. The system transcribes the audio, understands the complaint, checks the right support workflow, and responds safely in Yoruba.

The project is focused on fintech support because financial complaints are high-stakes. If a user says their money left their wallet but the recipient did not receive it, the AI must not guess. It must ask for the right details, check the right backend tools, and follow policy.

---

## 2. Why This Matters

Most fintech support systems in Nigeria still assume the customer can explain their issue clearly in English or navigate app menus. That excludes many users who are more comfortable speaking Yoruba, Hausa, Igbo, Pidgin, or code-switched language.

This project tests whether an AI agent can safely handle customer support workflows from Nigerian-language speech.

The project is not only a demo product. It also behaves like a small evaluation benchmark:

1. Can speech-to-text systems correctly transcribe Yoruba fintech complaints?
2. Can an AI model understand the complaint after transcription?
3. Can it choose the right customer-support workflow?
4. Can a deterministic safety layer prevent wrong or unsafe actions?

---

## 3. Important Terms Explained

### Bank0

Bank0 is the fictional fintech company we created for the demo.

It is not a real company. It represents a Nigerian wallet/fintech platform that has customers, wallets, transactions, KYC records, disputes, reversals, cards, POS terminals, and support tickets.

The AI agent acts as a support agent for Bank0.

### ASR / STT

ASR means Automatic Speech Recognition.

STT means Speech-to-Text.

They both mean the same thing in this project: converting spoken audio into written text.

Example:

```text
User speaks Yoruba audio:
"Mo lo OPay lati ran owo si Access Bank..."

ASR output:
"mo lo pe lati ran owo si access bank..."
```

### N-ATLaS

N-ATLaS is a Nigerian/African language speech model. In our project, we used `NCAIR1/Yoruba-ASR`, a Yoruba speech-to-text model from Hugging Face.

It is currently our best-performing Yoruba ASR model.

### Whisper

Whisper is OpenAI's open-source multilingual speech-to-text model.

We tested Whisper Large-v3 against N-ATLaS to see which one transcribes Yoruba fintech audio better.

Whisper is strong generally, but in our Yoruba fintech benchmark, N-ATLaS performed better.

### Google STT

Google STT means Google Cloud Speech-to-Text.

Google Cloud Speech-to-Text V2 supports Nigerian languages such as Yoruba (`yo-NG`), Hausa (`ha-NG`), and Igbo (`ig-NG`). We have not made it the main ASR system yet because N-ATLaS is already working and we do not want to derail the current pipeline. Google STT can be tested later as a third ASR baseline.

### TTS

TTS means Text-to-Speech.

It converts written text into spoken audio.

For our project, we are using SpitchAI for Yoruba voice output.

### SpitchAI

SpitchAI is the voice provider we are using for Yoruba text-to-speech.

It can generate Yoruba audio from Yoruba text. We used it to create Yoruba audio samples for testing, and it is our planned voice-output layer for the final demo.

### LLM

LLM means Large Language Model.

Examples are Gemini, GPT, Claude, Llama, Qwen, and DeepSeek.

In this project, the LLM is not trusted to directly change customer accounts. It helps interpret the user's complaint and suggest a support workflow.

### Gemini

Gemini is Google's LLM family.

We used Gemini 3.5 Flash for planner evaluation. It can understand the corrected Yoruba/code-switched transcripts fairly well.

### Planner

The planner is the part of the AI workflow where the model decides:

```text
What issue is the user reporting?
What details are missing?
Which support tools should be used?
What should happen next?
```

Example planner output:

```json
{
  "issue_type": "pending_transfer",
  "recommended_tools": [
    "get_recent_transactions",
    "check_transfer_status"
  ],
  "needed_identifiers": []
}
```

### Validator

The validator is a deterministic safety layer.

It checks the LLM's plan before anything is executed.

This matters because LLMs can miss steps or choose the wrong workflow. The validator adds missing tools, blocks unsafe tools, asks for missing details, and overrides obvious misclassifications.

Example:

```text
Gemini says:
card_pos_issue

But the transcript contains:
Moniepoint POS + timeout + NIP transfer

Validator changes it to:
pending_transfer
```

### Executor

The executor runs the approved Bank0 tools after the validator has checked the plan.

If required information is missing, the executor does not run risky backend actions. It asks the user for clarification instead.

### Entity Correction

Entity correction fixes fintech names and support terms that ASR models mistranscribe.

Example:

```text
Raw ASR:
"mo lo pe lati ran owo si access bank..."

Correction layer understands:
"mo lo pe" likely means "OPay"

Entity-corrected hint:
"OPay lati ran owo si Access Bank..."
```

Important: the corrected transcript is not meant to be a polished final transcript. It is a working hint for the AI planner.

### WER

WER means Word Error Rate.

It measures how many words in the transcription are wrong compared to the reference text.

Lower is better.

### CER

CER means Character Error Rate.

It measures errors at the character level instead of the word level.

Lower is better.

### Entity Preservation

Entity preservation measures whether important fintech entities were preserved in the transcript.

Entities include things like:

```text
OPay
PalmPay
Moniepoint
Access Bank
GTBank
BVN
NIN
KYC
Session ID
POS
NIP
reversal
double debit
```

If the ASR writes `pampe` instead of `PalmPay`, the entity is not preserved until the correction layer fixes it.

### RAG

RAG means Retrieval-Augmented Generation.

It means the AI does not rely only on memory. It retrieves relevant policy documents before responding.

For Bank0, the policy documents include things like:

```text
failed transfer policy
pending transfer policy
double debit policy
unauthorized debit policy
KYC restriction policy
wrong recipient policy
card/POS issue policy
escalation rules
```

---

## 4. Current Pipeline

The current working backend pipeline is:

```text
Yoruba audio
-> N-ATLaS ASR
-> entity correction
-> Gemini planner
-> Bank0 validator
-> Bank0 executor
-> Yoruba response
```

In plain English:

1. The user speaks a Yoruba complaint.
2. N-ATLaS converts the speech to text.
3. The correction layer fixes likely fintech entity errors.
4. Gemini reads the raw transcript plus correction hints.
5. Gemini suggests what kind of issue it is and what tools should be used.
6. Bank0 validator checks and repairs Gemini's plan.
7. Bank0 executor either runs safe support tools or asks for missing details.
8. The system returns a Yoruba response to the user.

---

## 5. Important Architecture Decision

We originally considered a translation-first pipeline:

```text
Yoruba -> English translation -> English agent -> Yoruba translation
```

We have moved away from that as the main path.

The current approach is:

```text
Raw Yoruba ASR transcript + entity correction hints -> Gemini planner
```

This reduces latency and avoids translation errors.

Gemini was able to understand corrected Yoruba/code-switched ASR well enough that translation is not currently necessary.

---

## 6. What We Tested

### 6.1 N-ATLaS vs Whisper

We tested both models on Yoruba fintech audio.

Both models listened to the audio files and transcribed them.

Results:

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
N-ATLaS is currently the better STT backbone for Yoruba fintech audio.
```

### 6.2 Entity Correction

We built a robust fintech lexicon and correction layer.

The lexicon contains banks, fintech providers, payment processors, identity terms, card terms, support terms, and observed ASR mistranscriptions.

Examples:

```text
mo lo pe / ope / opi -> OPay
pampe / paunpe -> PalmPay
money point -> Moniepoint
asset bank / assess bank -> Access Bank
sesan id / sese naidi -> Session ID
giti bank -> GTBank
femony -> FairMoney
karbonar -> Carbon
```

We also track unsafe mistranscriptions that should not be auto-corrected.

Example:

```text
"the bank" -> VBank
```

This is unsafe because "the bank" could mean many things. The system records the observation but does not blindly replace it.

### 6.3 Entity Stress v2

We created a larger stress benchmark:

```text
86 audio samples
99 canonical lexicon terms covered
272 expected entity mentions
```

Results:

```text
Raw entity preservation:       0.3236
Corrected entity preservation: 0.8682
Lift:                          +0.5446
Perfect samples:               52 / 86
Avg correction latency:        ~3.95ms
```

This means the correction layer significantly improves entity recovery while adding only a few milliseconds of latency.

### 6.4 Gemini Planner

We tested Gemini's ability to read corrected ASR and propose a support workflow.

Raw Gemini planner on actual ASR:

```text
avg_score:              0.7208
issue_accuracy:         0.8750
safety_pass_rate:       1.0000
missing_info_pass_rate: 0.0000
tool_recall:            0.4583
```

Interpretation:

```text
Gemini usually understands the issue.
Gemini does not reliably ask for missing details.
Gemini misses some operational tool steps.
Gemini did not choose dangerous tools in our test.
```

### 6.5 Bank0 Validator

After adding the validator:

```text
avg_score:              0.9609
issue_accuracy:         1.0000
safety_pass_rate:       1.0000
missing_info_pass_rate: 1.0000
tool_recall:            0.8438
tool_precision:         1.0000
```

Interpretation:

```text
Gemini is useful for understanding.
Bank0 validator is necessary for safety and completeness.
```

---

## 7. Bank0 Mock Company Environment

We created a mock company called Bank0 with fake but realistic backend data.

Bank0 includes:

```text
customers
wallets
transactions
ledger entries
reversals
disputes
support tickets
account restrictions
cards
POS terminals
policy documents
```

The system has tools such as:

```text
lookup_customer
get_recent_transactions
get_transaction_by_reference
check_transfer_status
create_dispute
request_reversal
check_kyc_status
create_kyc_update_ticket
create_fraud_report
block_card
escalate_to_human
```

The agent does not directly invent answers. It uses these tools and policies.

---

## 8. Support Issues Covered

The current Bank0 system covers:

```text
failed transfer
pending transfer
double debit
unauthorized debit
wrong recipient
KYC restriction
wallet balance mismatch
card/POS issue
Session ID request
receipt / transaction reference trace
reversal status
```

For each issue, we created a schema that defines:

```text
required details
supporting details
required tools
forbidden tools
English clarification message
Yoruba clarification message
```

Example for double debit:

```text
Required:
- customer identifier
- transaction reference or Session ID

Supporting:
- duplicate amount
- merchant or POS terminal
- first debit time
- second debit time
```

If those details are missing, the system asks for them instead of pretending it can solve the issue.

---

## 9. Five Current Demo Examples

We have five end-to-end demo examples ready.

### Demo 1: Pending Transfer / Reversal

Reference:

```text
Mo lo OPay lati ran owo si Access Bank, sugbon transaction naa wa ni pending, mo fe reversal.
```

Raw ASR:

```text
mo lo pe lati ran owo si access bank ṣugun transcional wa ni pẹndin, mo fẹri faṣa o
```

Entity-corrected hint:

```text
OPay lati ran owo si Access Bank Bank sugun transcional wa ni pending mo reversal o
```

Gemini identifies:

```text
pending_transfer
```

Validator adds missing tool:

```text
lookup_customer
```

Executor decision:

```text
ask_clarification
```

Yoruba response:

```text
Jọwọ fi orukọ/nọmba foonu Bank0 rẹ ati transaction reference tabi Session ID ranṣẹ ki n le ṣayẹwo pending transfer ati reversal.
```

### Demo 2: KYC / BVN / NIN

Raw ASR:

```text
mo fẹ́ sọ bvn àti ni imọ-account mi fún kys, ṣùgbọ́n otp kò dé
```

Entity-corrected hint:

```text
mo fe so BVN ati NIN account mi fun KYC sugbon OTP ko de
```

Gemini identifies:

```text
kyc_restriction
```

Validator adds:

```text
lookup_customer
get_account_restrictions
```

Executor decision:

```text
execute
```

### Demo 3: POS/NIP Timeout

Reference:

```text
Moniepoint POS mi ni timeout lori NIP transfer.
```

Raw ASR:

```text
mọ́ní pọ́ǹt p.o.s.míní tíimọ̀tù lórí níbi tíránfà.
```

Entity-corrected hint:

```text
Moniepoint POS mini tiimotu lori NIP failed transfer
```

Gemini misclassifies:

```text
card_pos_issue
```

Validator repairs:

```text
pending_transfer
```

This is one of the strongest demo examples because it shows why the validator matters.

### Demo 4: Session ID Request

Raw ASR:

```text
níbo ni ṣẹ̀ṣàn-àdí wà lórí rí síìtì?
```

Entity-corrected hint:

```text
nibo ni Session ID wa lori receipt
```

Gemini identifies:

```text
session_id
```

Validator asks for:

```text
customer identifier
transaction reference or Session ID
```

### Demo 5: Double Debit

Raw ASR:

```text
dọ́bùdẹ̀ bí i ṣẹlẹ̀ lórí p.o.s.
```

Entity-corrected hint:

```text
dobude bi i sele lori POS
```

Gemini identifies:

```text
double_debit
```

Validator asks for issue-specific details:

```text
Bank0 phone/name
transaction reference or Session ID
duplicate amount
merchant/POS terminal
times of both debits
```

---

## 10. Model Access We Tested

### Gemini

We tested Gemini API.

Working:

```text
gemini-3.5-flash
gemini-3.1-flash-lite
gemini-2.5-flash-lite
```

Important note:

```text
gemini-3.5-flash works but has tight rate limits.
```

We solved this by batching multiple planner test cases into one API call.

### NVIDIA Build / NIM

The NVIDIA Build API key works.

Callable models include:

```text
meta/llama-3.1-8b-instruct
meta/llama-3.1-70b-instruct
qwen/qwen3-next-80b-a3b-instruct
nvidia/llama-3.3-nemotron-super-49b-v1.5
```

These may be useful as fallback LLMs.

### Cencori

Cencori works for model listing and some calls, but several routes are rate-limited or require provider-specific configuration/credits.

For now, native Gemini is the better route for our main planner.

---

## 11. Current Files That Matter

### Core Backend

```text
src/entity_lexicon.json
src/entity_correction.py
src/bank0_mock.json
src/bank0_tools.py
src/bank0_rag.py
src/bank0_policies/
src/bank0_issue_schemas.json
src/bank0_validator.py
src/bank0_executor.py
```

### Model Clients

```text
src/gemini_client.py
src/cencori_client.py
src/bank0_llm.py
```

### Demo / Evaluation

```text
scratch/run_final_demo.py
scratch/final_demo_metrics.md
scratch/e2e_workflow_examples.json
scratch/asr_planner_e2e_gemini35_validated.json
scratch/entity_stress_v2_correction_eval.json
scratch/bank0_planner_eval_gemini35_b32_batch10_validated.json
```

---

## 12. How To Run The Current Demo

From the project folder:

```powershell
.\venv\Scripts\python.exe .\scratch\run_final_demo.py
```

This prints five end-to-end examples showing:

```text
raw ASR
entity correction
Gemini plan
Bank0 validator repair
executor decision
final English/Yoruba response
```

---

## 13. What Is Next

The backend demo is now strong enough.

The next major step is to build a frontend web app.

Recommended frontend:

```text
Single-page operational demo
```

Not a marketing landing page.

Suggested layout:

```text
Left column:
- choose audio/sample
- show raw ASR
- show entity corrections

Middle column:
- show Gemini planner output
- show Bank0 validator repair

Right column:
- show executor decision
- show tools executed or clarification requested
- show final Yoruba response
- optional Spitch TTS playback
```

Optional later:

```text
Google STT comparison
Spitch TTS final voice playback
More demo cases
Cleaner UI
```

---

## 14. Current One-Sentence Pitch

Bank0 is a Yoruba-first fintech support agent that turns native-language voice complaints into safe customer-support workflows by combining N-ATLaS speech recognition, fintech entity correction, Gemini planning, and a deterministic Bank0 validator that prevents unsafe or incomplete actions.

