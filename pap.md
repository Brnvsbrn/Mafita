# Pinned Items (PAP Tracker)

This document tracks design decisions, research topics, and ideas that have been "pinned" (PAP - Put A Pin) for deeper investigation or inclusion in the final project.

---

## 📌 1. Translation-First vs. Direct Yoruba Comparative Evaluation
*   **Context:** While the primary architecture uses a Translation-First approach (Yoruba $\rightarrow$ English translation $\rightarrow$ English agent reasoning/RAG $\rightarrow$ English-to-Yoruba translation), we need to document the trade-offs.
*   **Action Item:** In the evaluation phase, include 2–3 dedicated test cases that run using the *Direct Yoruba* pipeline (embedding and generating in Yoruba natively) to compare performance directly against the *Translation-First* pipeline.
*   **Metrics to Compare:**
    *   Resolution accuracy
    *   Linguistic/cultural safety (checking if the direct pipeline complies with malicious prompts that the translation pipeline blocks)
    *   Translation error propagation
    *   Latency difference

---

## 📌 2. Translation & Latency Bottlenecks
*   **Context:** The translation-first pipeline adds two translation steps (input translation and output translation). This introduces:
    *   **Latency:** Multiple API roundtrips (or local model invocations) will slow down real-time voice chat.
    *   **Failure Propagation:** If the Yoruba $\rightarrow$ English translation fails to capture an idiom, a key number, or a code-switched term (e.g., English words mixed with Yoruba), the subsequent agent tools will fail or act on wrong info.
*   **Action Item:** Document the exact latency of each pipeline stage in the final evaluation report. List mitigation strategies (e.g., caching translations, lightweight local translation models, or using single-request joint translation + reasoning prompts).

---

## 📌 3. Nigerian Fintech System Simulations
*   **Context:** The agent needs to query simulated databases representing PalmPay, OPay, and Moniepoint transaction ledgers.
*   **User Action Item (PAP):** Research how the live systems of these fintechs (PalmPay, OPay, Moniepoint, Paystack, Flutterwave) operate in production to ensure our mock transaction databases and dispute flows are highly realistic simulations.
*   **Simulation requirements:**
    *   User records (account number, balance, status, KYC level, phone number).
    *   Transaction records (reference, source bank, destination bank, amount, timestamp, status `SUCCESS`/`FAILED`/`PENDING`, reversal status).
    *   Dispute logs (dispute ID, transaction reference, reason, current resolution status, escalation timeline).

---

## 📌 4. Virtual Compute & Speech Models (Whisper, N-ATLAS, YarnGPT)
*   **Context:** Whisper large-v3 and N-ATLAS ASR are too heavy for the local CPU/disk (~5GB space remaining). Additionally, the user wants a real-time way to interact with the speech models (YarnGPT/ASR) without downloading files locally.
*   **Action Item:** Move all heavy speech models (ASR and TTS) to virtual compute (Google Colab / Kaggle). Set up a Gradio web interface running on the virtual compute instance that outputs a public `.gradio.live` link, allowing real-time text-to-speech and speech-to-text testing in the browser.
*   **User Research Note:** The user is researching Whisper models independently; integrate their findings when ready.

---

## 📌 5. Spitch AI Integration & Latency Benchmarks
*   **Context:** Following our evaluation, we pivot to **Spitch AI** (spitch.app) as the primary cloud neural voice generator to achieve natural, tonal, non-rushed Yoruba speech.
*   **Action Item:**
    *   Integrate `spitch-python` client library to handle TTS.
    *   Measure API request roundtrip latency and investigate Spitch's streaming response mechanism to stream audio chunks as they arrive for low-latency conversations.
    *   Design clean fallbacks (e.g. mock responses or standard log warnings) in the local source code to keep the project executable without an active API key.

