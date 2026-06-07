# How to Run Yoruba Voice sandbox in Kaggle or Google Colab

Follow these steps to run the interactive voice sandbox (TTS & ASR) in Google Colab or Kaggle. This allows you to test both YarnGPT and N-ATLaS ASR models in real-time, completely offloading the compute and storage from your local machine.

---

## Option A: Google Colab (Recommended)

1. Open [Google Colab](https://colab.research.google.com/).
2. Create a new notebook.
3. Set the runtime to a GPU for faster execution:
   * Go to **Runtime** $\rightarrow$ **Change runtime type**.
   * Under **Hardware accelerator**, select **T4 GPU** (or any available GPU). Click **Save**.
4. In the first cell, install the necessary dependencies:
   ```python
   !pip install outetts uroman gradio transformers torchaudio soundfile gdown
   ```
5. Create a new code cell, copy the contents of the python file `scratch/voice_demo_gradio.py` from this project, and paste it into the cell.
6. Run the cell.
7. Once the cell finishes loading, it will output two links:
   * **Local URL:** `http://127.0.0.1:7860`
   * **Public URL:** `https://xxxxxxxxxxxx.gradio.live`
8. Click the **Public URL**. This opens a web page in your browser where you can:
   * Type Yoruba text, select a voice profile (like `yoruba_female1`), and generate speech. You can listen to it directly!
   * Record your voice or upload a WAV file to transcribe it to Yoruba text.

---

## Option B: Kaggle Notebooks

1. Open [Kaggle](https://www.kaggle.com/) and go to the **Code** tab.
2. Click **New Notebook**.
3. In the right panel under **Settings**, turn on **Accelerator** and choose **GPU T4 x2** (or GPU P100).
4. Turn on **Internet** (required to download models from Hugging Face).
5. In a cell, install the packages:
   ```python
   !pip install outetts uroman gradio transformers torchaudio soundfile gdown
   ```
6. Paste the contents of `scratch/voice_demo_gradio.py` in the next cell and run it.
7. Click the generated `.gradio.live` link in the output to access the sandbox interface.
