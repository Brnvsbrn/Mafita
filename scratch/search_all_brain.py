import os
import glob

brain_dir = r"C:\Users\LENOVO 13\.gemini\antigravity\brain"

# Find any file containing styles in its name
print("Searching for files with 'styles' in name...")
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if "styles" in f.lower():
            print(f"FOUND: {os.path.join(root, f)}")

# Let's search all files for the string "color-scheme: light;" or similar styles.css contents
print("\nSearching all transcript/text files for styles.css content...")
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f.endswith(".jsonl") or f.endswith(".json") or f.endswith(".txt") or f.endswith(".md"):
            fpath = os.path.join(root, f)
            try:
                # Read a small chunk or search
                with open(fpath, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
                    if "Showing lines 1 to 641" in content or "--ink: #111111" in content or "color-scheme: light" in content:
                        print(f"FOUND MATCHING STRING IN: {fpath} (size {len(content)})")
                        # Write out matches
                        out_path = f"scratch/matched_{f.replace('.', '_')}_{os.path.basename(root)}.txt"
                        with open(out_path, "w", encoding="utf-8") as out:
                            out.write(content)
                        print(f"Wrote match content to {out_path}")
            except Exception as e:
                pass

print("Search done.")
