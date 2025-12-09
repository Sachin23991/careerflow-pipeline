# pipeline/filter.py
import json
from pathlib import Path
import sqlite3

RAW = Path("pipeline/raw_news.jsonl")
OUT = Path("pipeline/filtered_news.jsonl")
DB = Path("pipeline/seen.db")
MIN_CHARS = 300

def ensure_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS seen(id TEXT PRIMARY KEY, url TEXT, added_at TEXT)")
    conn.commit()
    return conn

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    conn = ensure_db()
    c = conn.cursor()

    kept = 0
    total = 0
    with OUT.open("w", encoding="utf-8") as outf:
        if not RAW.exists():
            print("No raw file:", RAW)
            return
        for line in RAW.open(encoding="utf-8"):
            total += 1
            try:
                it = json.loads(line)
            except:
                continue
            id_ = it.get("id")
            if not id_:
                continue
            # skip previously seen
            c.execute("SELECT 1 FROM seen WHERE id = ?", (id_,))
            if c.fetchone():
                continue
            text = (it.get("text") or "").strip()
            if len(text) < MIN_CHARS:
                continue
            # keep
            outf.write(json.dumps(it, ensure_ascii=False) + "\n")
            c.execute("INSERT INTO seen(id,url,added_at) VALUES (?, ?, datetime('now'))", (id_, it.get("url")))
            kept += 1
    conn.commit()
    conn.close()
    print(f"Filtered: kept {kept} of {total}")
if __name__ == "__main__":
    main()
