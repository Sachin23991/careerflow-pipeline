# pipeline/dataset_builder.py
import json
from pathlib import Path
import math
import os

FILTERED = Path("pipeline/filtered_news.jsonl")
OUT = Path("pipeline/rag_docs.jsonl")

# chunk settings (characters)
CHUNK_SIZE = 2500
OVERLAP = 300

# Embeddings: set to True if you installed sentence-transformers in requirements
EMBEDDINGS = True if os.getenv("COMPUTE_EMBEDDINGS", "1") == "1" else False

def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(L, start + size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == L:
            break
        start = end - overlap
    return chunks

def build():
    if not FILTERED.exists():
        print("No filtered file:", FILTERED)
        return

    docs = []
    for line in open(FILTERED, encoding="utf-8"):
        it = json.loads(line)
        text = it.get("text", "")
        chunks = chunk_text(text)
        for i, ch in enumerate(chunks):
            doc = {
                "doc_id": f"{it['id']}_c{i}",
                "source_id": it["id"],
                "url": it.get("url"),
                "title": it.get("title"),
                "published": it.get("published"),
                "feed": it.get("feed"),
                "chunk_index": i,
                "text": ch
            }
            docs.append(doc)

    print(f"Built {len(docs)} document chunks.")
    # write rag jsonl
    with OUT.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # optionally compute embeddings
    if EMBEDDINGS:
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            model = SentenceTransformer("all-MiniLM-L6-v2")
            texts = [d["text"] for d in docs]
            print("Computing embeddings for", len(texts), "chunks...")
            embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
            np.save("pipeline/embeddings.npy", embeddings)
            # save mapping of doc ids
            with open("pipeline/emb_ids.jsonl", "w", encoding="utf-8") as idf:
                for d in docs:
                    idf.write(json.dumps({"doc_id": d["doc_id"], "source_id": d["source_id"]}) + "\n")
            print("Saved embeddings -> pipeline/embeddings.npy and pipeline/emb_ids.jsonl")
        except Exception as e:
            print("Embedding computation failed:", e)

if __name__ == "__main__":
    build()
