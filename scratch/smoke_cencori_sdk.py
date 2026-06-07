import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cencori_client import cencori_chat


def load_dotenv():
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


def main():
    load_dotenv()
    if not os.getenv("CENCORI_API_KEY"):
        print("SKIP: CENCORI_API_KEY is not set.")
        return
    response = cencori_chat(
        [
            {"role": "system", "content": "Reply in one short sentence."},
            {"role": "user", "content": "Say Bank0 Cencori smoke test passed."},
        ],
        max_tokens=80,
    )
    print(response.content)


if __name__ == "__main__":
    main()
