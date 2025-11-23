import json
import os

GLOBAL_FILE = "train.jsonl"                  # final dataset for HF upload
NEW_FILE = "pipeline/train.jsonl"            # newly scraped items

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def write_jsonl(path, data):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

# -----------------------------------------------
# Load existing + new data
# -----------------------------------------------
old_items = read_jsonl(GLOBAL_FILE)
new_items = read_jsonl(NEW_FILE)

# Convert IDs to a set for fast lookup
old_ids = {item["id"] for item in old_items}

# -----------------------------------------------
# Filter new unique items
# -----------------------------------------------
unique_new = [item for item in new_items if item["id"] not in old_ids]

print(f"🔍 Found {len(unique_new)} NEW unique items.")

# -----------------------------------------------
# Append unique items
# -----------------------------------------------
merged = old_items + unique_new

write_jsonl(GLOBAL_FILE, merged)

print(f"✅ Updated train.jsonl → {len(merged)} total items.")
