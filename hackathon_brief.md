# AFH Hackathon Project Brief
## Nigerian Fintech Multilingual Support Agent
### Artificial Future Hackathon — Local Language & Culture Track
**Prepared: May 2026**

---

## CONTEXT & BACKGROUND

This document captures all research, decisions, and technical planning for the AFH hackathon project. The builder is Barin Adegboye — law graduate, product designer, transitioning into AI engineering with a specific long-term interest in safety and standards frameworks for autonomous economic AI agents.

**Hackathon dates:** May 30 – June 6, 2026
**Main conference:** June 13, The Civic Centre, Lagos
**Track selected:** Local Language & Culture (accessibility focus)

---

## THE CORE PROBLEM

### Why This Exists

The language gap in AI systems is not evenly distributed. For Nigerian language speakers — Yoruba, Hausa, Igbo — the gap is most consequential in high-stakes domains where no workaround exists. In fintech specifically:

- PalmPay has 35M+ users processing 15M+ transactions daily
- Moniepoint processes 26M payments daily with 10M+ users
- A significant portion of these users are not English-first
- Support infrastructure for these companies currently requires English literacy or access to a human agent
- Failed transactions, disputes, and account queries — when unresolved — cause real financial harm

### The Research Gap We Found

From the MAPS benchmark (arxiv.org/abs/2505.15935) — the first standardized evaluation framework for multilingual agentic AI:
- Consistent performance and safety degradation when transitioning from English to other languages
- Degradation compounds across multi-step agentic tasks
- No published MAPS-equivalent results exist for Yoruba, Hausa, or Igbo in agentic settings
- The intersection of African languages + agentic performance is essentially unmeasured territory

From the LSR (Linguistic Safety Robustness) benchmark:
- English refusal rates: ~90%
- West African language refusal rates: 35–55%
- Igala shows the most severe degradation
- Same model that refuses a harmful prompt in English will comply with it in Igbo or Igala over half the time

From AfroBench (most comprehensive African language benchmark):
- Covers 64 African languages across 15 tasks and 22 datasets
- Integrated with EleutherAI's LM-Evaluation-Harness
- Does NOT cover agentic tasks — static benchmarking only

**The gap:** Nobody has measured agentic performance in Nigerian languages in a financial context. This project fills that gap while building something practically useful.

---

## THE PROJECT

### What We Are Building

A multilingual financial support agent for Nigerian fintech users — specifically handling failed transaction dispute resolution in Yoruba (primary) with data collected across PalmPay, Moniepoint, Paystack, and Flutterwave.

### The Strategic Framing

This is not just a product demo. It is simultaneously:
1. A working agent demonstrating the Sierra-equivalent use case for Nigerian fintech
2. An evaluation contribution measuring agentic performance degradation in Yoruba vs English in a financial context

The product layer demonstrates the use case. The evaluation layer is the research contribution.

### Why PalmPay + Dispute Resolution + Yoruba

- PalmPay has the largest user base (35M) and highest daily transaction volume (15M/day)
- Failed transaction disputes are the highest-volume, highest-stakes, most language-dependent support scenario
- Yoruba has the most available open-source TTS/STT tooling for Nigerian languages
- Nairaland community data on PalmPay disputes is rich and accessible

---

## SCOPE STRATEGY

**Collect data for all companies. Build for one.**

- Scrape/collect data: PalmPay, Moniepoint, Paystack, Flutterwave
- Build and demo: PalmPay dispute resolution in Yoruba
- If time allows: expand to Moniepoint and/or second language

This avoids the hackathon failure mode of building something shallow across too many targets.

---

## TECHNICAL ARCHITECTURE

### What This Is NOT

This is NOT a fine-tuning or post-training project. No model training. No GPU costs beyond free tier. The approach is RAG (Retrieval Augmented Generation).

### What RAG Means Here

Instead of training the model on new information, we give it a structured knowledge base it searches at query time:

1. User sends query in Yoruba
2. System embeds the query using a multilingual embedding model
3. System retrieves most relevant resolution steps from the knowledge base
4. Retrieved context + user query passed to LLM
5. LLM generates response in Yoruba
6. (Optional) TTS layer reads response aloud in Yoruba

### The Full Pipeline

```
User query (Yoruba text or voice)
    ↓
[Optional: Whisper/N-ATLAS speech-to-text]
    ↓
Multilingual embedding (mE5-large or LaBSE)
    ↓
Vector database retrieval (ChromaDB or FAISS)
    ↓
LLM generation in Yoruba (GPT-4o / Gemini 1.5 Pro)
    ↓
Response text in Yoruba
    ↓
[Optional: YarnGPT text-to-speech]
    ↓
Audio response in Yoruba
```

### Interface

Text-first. Streamlit chat interface (~30 lines Python). Voice as stretch goal added at end if time allows.

---

## MODEL DECISIONS

### LLM Options (ranked by African language performance)

1. **GPT-4o** — best multilingual performance, costs money per API call
2. **Gemini 1.5 Pro** — strong multilingual, free tier available
3. **Aya Expanse (Cohere)** — IMPORTANT NOTE: Aya Expanse 8B and 32B support 23 languages but Yoruba, Hausa, and Igbo are NOT on the list. Tiny Aya (3.35B) claims 70 language support — worth testing. Strategic value: using a Cohere model connects to the Cohere Scholars application narrative. Test on HuggingFace before committing.
4. **LLaMA 3.1** — open source, runs on Kaggle free GPU, weakest on African languages

**Recommended:** Test Gemini 1.5 Pro and Tiny Aya on sample Yoruba prompts. Use whichever performs better on coherent Yoruba generation.

### Embedding Model

- **mE5-large** — standard multilingual embeddings, good African language coverage
- **LaBSE** — Language-agnostic BERT Sentence Embeddings, alternative option

### Vector Database

- **ChromaDB** — easiest setup, free, local
- **FAISS** — Facebook's similarity search, also free and local

### Text-to-Speech (Nigerian Languages)

**YarnGPT** — primary choice
- Built by Saheed Azeez, trained on Nollywood audio
- Supports Yoruba, Igbo, Hausa with Nigerian accents
- Open source, free
- URL: yarngpt.ai

**Abena AI** — backup
- Supports Yoruba, Hausa, Swahili, Twi, others
- Works offline
- URL: abena.mobobi.com/playground/tts/

### Speech-to-Text (for voice input — stretch goal)

**N-ATLAS** — Nigerian government open-source model
- Recognises and transcribes Yoruba, Hausa, Igbo, and Nigerian-accented English
- Released September 2025
- Open source

**OpenAI Whisper** — fallback
- Has some Yoruba and Hausa capability
- Free, open source, runs on Kaggle

---

## DATA STRATEGY

### Sources to Scrape/Collect

**Official documentation (clean, thin):**
- support.paystack.com
- paystack.com/docs
- flutterwave.com/docs
- PalmPay help center (whatever is publicly accessible)
- Moniepoint help center

**Community data (rich, noisy):**
- Nairaland fintech threads — search "PalmPay failed transaction", "Moniepoint dispute", etc.
- Twitter/X — complaint and resolution threads tagged @PalmPay, @Moniepoint etc.
- Reddit r/Nigeria fintech threads

### Why the Community Data is Noisy

- Unverified resolutions — complaints documented, fixes not
- Contradictory information — different policies at different times
- Code-switching — Pidgin/English/Yoruba mixed in same sentence
- Outdated information — policies change after licensing upgrades
- Emotional venting without actionable content

### Data Cleaning Pipeline

Raw scraped content → filter for posts containing actual resolution steps → verify against official docs → format as clean QA pairs

**Target format:**
```
{problem_description}: "my transfer failed, money deducted but not received"
{verified_resolution_steps}: ["1. Wait 24 hours for automatic reversal", "2. If not reversed, open PalmPay app → Help → Failed Transaction", "3. Provide transaction reference number", "4. Escalation timeline: 24-72 hours"]
```

**Target volume:** 50–100 high-quality verified QA pairs for the demo scenario. Quality over quantity. Unverified data actively makes the agent worse in a financial context.

---

## EVALUATION LAYER

This is what makes the project more than a demo.

### The Test Protocol

For each of 20 test queries:
1. Run query in English → record response
2. Run same query in Yoruba → record response
3. Compare: same resolution? consistent refusal behavior? coherent multi-step reasoning?

### What We're Measuring

- **Accuracy degradation:** Does the agent give correct resolution steps in Yoruba vs English?
- **Safety consistency:** Does the agent maintain appropriate refusal behavior in Yoruba? (The LSR finding suggests it won't)
- **Reasoning coherence:** Does multi-step resolution logic hold in Yoruba across a full conversation?
- **Confidence calibration:** Does the agent express appropriate uncertainty when it doesn't know?

### Why This Matters

This is a MAPS-equivalent contribution for Nigerian languages in a financial agentic context. Even 20 documented test cases is a data point that doesn't exist in published literature. Document everything. This becomes:
- A portfolio artifact for the Cohere Scholars application (August 2026)
- Evidence of evaluation design capability for MATS 2028 application
- A publishable contribution if extended post-hackathon

---

## WEEK PLAN

| Day | Focus |
|-----|-------|
| Day 1–2 | Data collection and cleaning. Most important. Do not rush. |
| Day 3 | Build knowledge base, set up ChromaDB, test retrieval |
| Day 4 | Connect LLM, test full RAG pipeline in English first, then Yoruba |
| Day 5 | Evaluation layer — 20 test cases, document results |
| Day 6 | Streamlit interface, end-to-end testing, fix what breaks |
| Day 7 | Write-up, documentation, submission |

**Compute:** Kaggle free tier (30 GPU hours/week) for embedding. Inference via API (Gemini free tier or GPT-4o). No training required.

---

## RELEVANT RESEARCH & RESOURCES

| Resource | URL | Why relevant |
|----------|-----|--------------|
| MAPS benchmark paper | arxiv.org/abs/2505.15935 | First multilingual agentic eval framework |
| AfroBench | GitHub: masakhane-io/afrobench | Most comprehensive African language benchmark |
| LSR paper | Search: "Linguistic Safety Robustness West African" | Refusal degradation in Nigerian languages |
| FinVault paper | arxiv.org/abs/2601.07853 | Financial agent safety benchmark |
| YarnGPT | yarngpt.ai | Nigerian TTS — Yoruba/Igbo/Hausa |
| Abena AI TTS | abena.mobobi.com/playground/tts | African language TTS backup |
| Aya Expanse | huggingface.co/CohereLabs/aya-expanse-8b | Cohere multilingual model |
| Tiny Aya | huggingface.co/CohereLabs | 70-language model — test for Yoruba |
| WAXAL dataset | Google speech dataset — 21 African languages | 11,000+ hours speech data |
| N-ATLAS | Nigerian government open-source ASR | Yoruba/Hausa/Igbo speech recognition |
| LM-Eval Harness | github.com/EleutherAI/lm-evaluation-harness | Standard eval framework (AfroBench integrated) |

---

## CONNECTIONS TO BROADER ROADMAP

This project is not standalone. It feeds directly into:

1. **Cohere Scholars August 2026 application** — demonstrates: open source project, technical build, African language ML work, evaluation design, familiarity with Cohere's Aya research agenda
2. **Adaption Labs Ambassador application (post-August)** — community artifact demonstrating building for underserved African AI contexts
3. **Nigerian legal reasoning benchmark (July–August)** — same RAG + eval methodology applied to legal domain
4. **MATS 2028 application** — evaluation design track contribution
5. **Long-term thesis** — safety and standards for autonomous economic AI agents. This project demonstrates: what happens when agents operate in high-stakes financial contexts in non-English languages? The LSR finding (safety behavior degrades in Nigerian languages) is a preview of what happens at higher autonomy levels with higher stakes.

---

## OPEN DECISIONS

1. **Which language to anchor in** — Yoruba recommended based on TTS tooling availability, but not yet confirmed
2. **Aya vs Gemini** — test both on sample Yoruba prompts before committing
3. **Voice input** — treat as stretch goal, not core feature
4. **Team** — solo or with others? This affects scope realism
5. **Compute for Aya** — if running locally, Kaggle free GPU. If using Cohere API, check free tier limits

---

## WHAT THE SUBMISSION SHOULD SHOW

1. Working RAG pipeline handling Nigerian fintech dispute queries in Yoruba
2. Evaluation results — English vs Yoruba performance comparison across 20 test cases
3. Clean GitHub repo with documented methodology
4. Write-up connecting findings to the MAPS research gap and LSR safety findings
5. Clear framing: this is not just a product — it is the first documented evaluation of agentic performance in Nigerian languages in a financial context

---

*This document was prepared to continue the project planning with another model or collaborator. All decisions above reflect research conducted May 21, 2026. Continue from the Open Decisions section.*
