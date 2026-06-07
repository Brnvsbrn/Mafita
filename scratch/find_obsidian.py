import os

possible_roots = [
    "C:/Users/LENOVO 13/Documents",
    "C:/Users/LENOVO 13/iCloudDrive",
    "C:/Users/LENOVO 13/iCloud Drive",
    "C:/Users/LENOVO 13"
]

found_paths = []
for root in possible_roots:
    if os.path.exists(root):
        try:
            for item in os.listdir(root):
                full_path = os.path.join(root, item)
                if os.path.isdir(full_path) and ("obsidian" in item.lower() or "icloud" in item.lower()):
                    found_paths.append(full_path)
        except Exception as e:
            found_paths.append(f"Error reading {root}: {e}")

output = "Roots checked:\n"
for root in possible_roots:
    output += f"- {root}: {'EXISTS' if os.path.exists(root) else 'MISSING'}\n"

output += "\nFound directories:\n"
for path in found_paths:
    output += f"- {path}\n"

# Also scan one level deeper inside Documents for iCloud or Obsidian
docs_path = "C:/Users/LENOVO 13/Documents"
if os.path.exists(docs_path):
    try:
        output += f"\nContents of Documents:\n"
        for item in os.listdir(docs_path):
            full_path = os.path.join(docs_path, item)
            is_dir = os.path.isdir(full_path)
            output += f"- {item} ({'DIR' if is_dir else 'FILE'})\n"
    except Exception as e:
        output += f"Error scanning Documents: {e}\n"

with open("C:/Users/LENOVO 13/.gemini/antigravity/scratch/obsidian_path.txt", "w", encoding="utf-8") as f:
    f.write(output)
print("Done")
