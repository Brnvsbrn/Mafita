import json
import os
import wave
import zipfile
from pathlib import Path

from dotenv import load_dotenv
from spitch import Spitch

SCRATCH = Path(__file__).resolve().parent
PROJECT_ROOT = SCRATCH.parent
QUERY_PATH = SCRATCH / "expanded_entity_queries.json"
METADATA_PATH = SCRATCH / "expanded_entity_metadata.json"
AUDIO_DIR = SCRATCH / "expanded_entity_audio"
FIXED_AUDIO_DIR = SCRATCH / "expanded_entity_audio_fixed"
ZIP_PATH = SCRATCH / "expanded_entity_benchmark_kaggle.zip"
RUNNER_PATH = SCRATCH / "run_expanded_natlas_eval.py"


def fix_wav_header(src_path, dst_path):
    raw = src_path.read_bytes()
    header_size = 44
    data_bytes = raw[header_size:]
    with wave.open(str(dst_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(data_bytes)


def build_kaggle_zip():
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(METADATA_PATH, "expanded_entity_metadata.json")
        zf.write(RUNNER_PATH, "run_expanded_natlas_eval.py")
        for path in sorted(FIXED_AUDIO_DIR.glob("*.wav")):
            zf.write(path, f"expanded_entity_audio_fixed/{path.name}")


def main():
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("SPITCH_API_KEY")
    if not api_key:
        raise RuntimeError("SPITCH_API_KEY is not set.")

    client = Spitch(api_key=api_key)
    queries = json.loads(QUERY_PATH.read_text(encoding="utf-8"))
    AUDIO_DIR.mkdir(exist_ok=True)
    FIXED_AUDIO_DIR.mkdir(exist_ok=True)

    metadata = []
    for index, query in enumerate(queries, start=1):
        filename = f"{query['id']}_{query['voice']}_{query['category']}.wav"
        audio_path = AUDIO_DIR / filename
        fixed_path = FIXED_AUDIO_DIR / filename
        print(f"[{index:02d}/{len(queries)}] {query['id']} {query['category']} ({query['voice']})")

        if not audio_path.exists():
            text = query["text"]
            try:
                toned = client.text.tone_mark(language="yo", text=text)
                text = toned.text
            except Exception as exc:
                print(f"  tone_mark skipped: {exc}")

            response = client.speech.generate(
                language="yo",
                text=text,
                voice=query["voice"],
            )
            audio_path.write_bytes(response.read())
            query["tone_marked_text"] = text
        else:
            query["tone_marked_text"] = query.get("tone_marked_text", query["text"])

        fix_wav_header(audio_path, fixed_path)
        query["audio_filename"] = filename
        metadata.append(query)

    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    build_kaggle_zip()
    print(f"Wrote {METADATA_PATH}")
    print(f"Wrote {ZIP_PATH}")


if __name__ == "__main__":
    main()
