import argparse
import json
import sys

from src.agent import handle_query
from src.cencori_client import MissingCencoriKey
from src.bank0_llm import plan_with_cencori, stream_cencori_plan


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the YPIT text-first support agent demo.")
    parser.add_argument("query", help="Customer query in Yoruba, English, or code-switched Nigerian usage.")
    parser.add_argument("--no-create", action="store_true", help="Do not create a mock dispute record.")
    parser.add_argument("--llm", action="store_true", help="Ask Cencori for an LLM tool plan before running the deterministic Bank0 agent.")
    parser.add_argument("--stream-llm", action="store_true", help="Stream the Cencori planner response instead of printing parsed JSON.")
    parser.add_argument("--model", default=None, help="Cencori model ID. Defaults to CENCORI_MODEL or gemini-2.5-flash.")
    args = parser.parse_args()

    if args.llm or args.stream_llm:
        try:
            print("=== Cencori LLM Planner ===")
            if args.stream_llm:
                for chunk in stream_cencori_plan(args.query, model=args.model):
                    print(chunk.delta, end="", flush=True)
                print("\n")
            else:
                print(json.dumps(plan_with_cencori(args.query, model=args.model), indent=2, ensure_ascii=False))
                print()
        except MissingCencoriKey:
            print("CENCORI_API_KEY is not set; skipping Cencori planner and using deterministic Bank0 agent.")
            print()

    response = handle_query(args.query, auto_create_dispute=not args.no_create)

    print("=== English Agent Output ===")
    print(response.english)
    print()
    print("=== Yoruba User Output ===")
    print(response.yoruba)
    print()
    print(f"Intent: {response.intent}")
    print(f"Provider: {response.provider or 'unknown'}")


if __name__ == "__main__":
    main()
