matched_files = [
    "scratch/matched_content_md_1117.txt",
    "scratch/matched_transcript_jsonl_logs.txt"
]

for fpath in matched_files:
    print(f"\n--- Checking {fpath} ---")
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    for pat in ["Showing lines 1 to 641", "--ink: #111111", "color-scheme: light", "@import"]:
        idx = content.find(pat)
        if idx != -1:
            print(f"FOUND string '{pat}' at index {idx}")
            print("Snippet:")
            print(content[idx:idx+400])
        else:
            print(f"NOT FOUND: '{pat}'")
