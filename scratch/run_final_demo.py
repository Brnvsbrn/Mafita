import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_PATH = ROOT / "scratch" / "e2e_workflow_examples.json"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    print("Bank0 Yoruba Voice Support Agent - Final Demo")
    print("=" * 72)
    print("Pipeline: N-ATLaS ASR -> entity correction -> Gemini planner -> Bank0 validator -> executor")

    for index, item in enumerate(examples, 1):
        raw_plan = item["gemini_raw_plan"]
        validated = item["validated_plan"]
        execution = item["execution"]
        validation = validated.get("validation", {})

        print("\n" + "-" * 72)
        print(f"Demo {index}: {item['id']}")
        print(f"Reference: {item['reference_text']}")
        print(f"Raw ASR: {item['raw_asr_output']}")
        print(f"Entity-corrected hint: {item['corrected_query']}")
        print()
        print(f"Gemini planner: {raw_plan.get('issue_type')} -> {raw_plan.get('recommended_tools')}")
        print(f"Bank0 validator: {validated.get('issue_type')} -> {validated.get('recommended_tools')}")
        if validation.get("original_issue_type") != validation.get("inferred_issue_type"):
            print(f"Validator override: {validation.get('original_issue_type')} -> {validation.get('inferred_issue_type')}")
        if validation.get("added_tools"):
            print(f"Validator added tools: {validation.get('added_tools')}")
        if validated.get("needed_identifiers"):
            print(f"Missing identifiers: {validated.get('needed_identifiers')}")
        print(f"Executor decision: {execution['decision']}")
        print(f"Tools executed: {execution['tools_executed']}")
        print(f"English response: {execution['final_response']['english']}")
        print(f"Yoruba response: {execution['final_response']['yoruba']}")


if __name__ == "__main__":
    main()
