# pipeline/filter.py
import json
from pathlib import Path

RAW = Path("pipeline/raw_news.jsonl")
OUT = Path("pipeline/filtered_news.jsonl")

MIN_CHARS = 300   # keep items with at least this many characters in text

def is_ok(item):
    if not item.get("url") or not item.get("text"):
        return False
    txt = item["text"].strip()
    if len(txt) < MIN_CHARS:
        return False
    if "example.com" in item.get("url",""):
        return False
    return True

def main():
    seen_ids = set()
    out = OUT.open("w", encoding="utf-8")
    if not RAW.exists():
        print("No raw file found:", RAW)
        return

    total = 0
    kept = 0
    for line in open(RAW, encoding="utf-8"):
        total += 1
        try:
            item = json.loads(line)
        except Exception:
            continue
        if item.get("id") in seen_ids:
            continue
        if not is_ok(item):
            continue
        seen_ids.add(item.get("id"))
        out.write(json.dumps(item, ensure_ascii=False) + "\n")
        kept += 1

    out.close()
    print(f"Filtered: kept {kept}/{total}. Saved to {OUT}")

if __name__ == "__main__":
    main()
