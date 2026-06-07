import json

log_path = r"C:\Users\LENOVO 13\.gemini\antigravity\brain\db29f674-0a44-4a8e-aa4d-40fadb79b225\.system_generated\logs\transcript.jsonl"
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(718, min(735, len(lines))):
    try:
        obj = json.loads(lines[idx])
        print(f"--- Line {idx} ({obj.get('type')}, {obj.get('source')}) ---")
        content = obj.get('content', '')
        if content:
            print(content[:500] + "...")
        if 'tool_calls' in obj:
            print(f"Tool calls: {obj['tool_calls']}")
    except Exception as e:
        print(f"Error parsing line {idx}: {e}")
