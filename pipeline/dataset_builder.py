import json
import hashlib

FILTERED_FILE = "pipeline/filtered_news.jsonl"
OUTPUT_FILE = "pipeline/train.jsonl"

def build_dataset():
    print("🧱 Building training dataset...")

    seen = set()
    out = open(OUTPUT_FILE, "w", encoding="utf-8")

    with open(FILTERED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            # Deduplicate using URL hash
            uid = hashlib.md5(item["url"].encode()).hexdigest()
            if uid in seen:
                continue
            seen.add(uid)

            # Combine useful info
            text = item["content"] or item["summary"] or item["title"]

            prompt = (
                "Summarize and explain this career-related news for students:\n\n"
                f"{text}\n\n"
                "Answer:"
            )

            completion = " " + text.strip()

            out.write(json.dumps({
                "prompt": prompt,
                "completion": completion
            }, ensure_ascii=False) + "\n")

    out.close()
    print(f"✅ Dataset built successfully with {len(seen)} items.")

if __name__ == "__main__":
    build_dataset()
