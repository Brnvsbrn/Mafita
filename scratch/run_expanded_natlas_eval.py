import argparse
import json
import os
import time
from pathlib import Path

import librosa
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor


def get_hf_token():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if token:
        return token
    try:
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret("HF_TOKEN")
    except Exception:
        return None


def parse_args():
    parser = argparse.ArgumentParser(description="Run direct N-ATLaS ASR on the expanded YPIT entity benchmark.")
    parser.add_argument("--metadata", default="expanded_entity_metadata.json", type=Path)
    parser.add_argument("--audio-dir", default="expanded_entity_audio_fixed", type=Path)
    parser.add_argument("--out", default="expanded_natlas_full_results.json", type=Path)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    hf_token = get_hf_token()
    if not hf_token:
        raise RuntimeError("HF_TOKEN not found. Add it as a Kaggle Secret or environment variable.")

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    if args.limit:
        metadata = metadata[: args.limit]

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    print("Device:", device)
    print("Samples:", len(metadata))

    model_id = "NCAIR1/Yoruba-ASR"
    processor = AutoProcessor.from_pretrained(model_id, token=hf_token)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        token=hf_token,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=False,
    ).to(device)

    results = []
    forced_ids = None
    if hasattr(processor, "get_decoder_prompt_ids"):
        forced_ids = processor.get_decoder_prompt_ids(language="yoruba", task="transcribe")

    for index, row in enumerate(metadata, start=1):
        audio_path = args.audio_dir / row["audio_filename"]
        print(f"\n[{index:02d}/{len(metadata)}] {row['id']} {row['audio_filename']}")
        audio, _ = librosa.load(audio_path, sr=16000, mono=True)
        inputs = processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt",
            return_attention_mask=True,
        )
        input_features = inputs.input_features.to(device, dtype=dtype)

        start = time.perf_counter()
        generated_ids = model.generate(
            input_features,
            forced_decoder_ids=forced_ids,
            max_new_tokens=128,
        )
        latency = time.perf_counter() - start
        output = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        print(f"natlas [{latency:.2f}s]: {output}")

        results.append(
            {
                "id": row["id"],
                "audio_filename": row["audio_filename"],
                "reference": row.get("tone_marked_text") or row["text"],
                "output": output,
                "latency_seconds": round(latency, 3),
            }
        )

    args.out.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved {args.out}")


if __name__ == "__main__":
    main()
