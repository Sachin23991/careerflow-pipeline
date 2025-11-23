import json
import os

GLOBAL_FILE = "train.jsonl"                  # final dataset for HF upload
NEW_FILE = "pipeline/train.jsonl"            # newly scraped items

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    items.append(obj)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping invalid JSON line: {line}")
    return items

def write_jsonl(path, data):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

# -----------------------------------------------
# Load existing + new data
# -----------------------------------------------
old_items = read_jsonl(GLOBAL_FILE)
new_items = read_jsonl(NEW_FILE)

# -----------------------------------------------
# Build a set of existing IDs (skip missing-id rows)
# -----------------------------------------------
old_ids = {item["id"] for item in old_items if "id" in item}

# -----------------------------------------------
# Filter new unique items safely
# Skip objects that do NOT contain an "id"
# -----------------------------------------------
unique_new = []

for item in new_items:
    if "id" not in item:
        print("⚠️ Skipping item without 'id':", item)
        continue
    if item["id"] not in old_ids:
        unique_new.append(item)

print(f"🔍 Found {len(unique_new)} NEW unique items.")

# -----------------------------------------------
# Append unique items
# -----------------------------------------------
merged = old_items + unique_new

write_jsonl(GLOBAL_FILE, merged)

print(f"✅ Updated train.jsonl → {len(merged)} total items.")
