# pipeline/dataset_builder.py
import json, os
from pathlib import Path
from math import ceil
import numpy as np
from sentence_transformers import SentenceTransformer

FILTERED = Path("pipeline/filtered_news.jsonl")
OUT = Path("pipeline/rag_docs.jsonl")
EMB_FILE = Path("pipeline/embeddings.npy")
EMB_IDS = Path("pipeline/emb_ids.jsonl")
CHUNK_SIZE = 2500
OVERLAP = 300

EMBED = os.getenv("COMPUTE_EMBEDDINGS", "1") == "1"

def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks

def load_existing_ids():
    if not EMB_IDS.exists():
        return set()
    s = set()
    for line in EMB_IDS.open(encoding="utf-8"):
        obj = json.loads(line)
        s.add(obj["doc_id"])
    return s

def append_embeds(existing_embeddings, new_embeddings):
    if existing_embeddings is None:
        return new_embeddings
    return np.vstack([existing_embeddings, new_embeddings])

def main():
    docs = []
    if not FILTERED.exists():
        print("no filtered file")
        return
    for line in FILTERED.open(encoding="utf-8"):
        it = json.loads(line)
        chunks = chunk_text(it.get("text",""))
        for i, ch in enumerate(chunks):
            docs.append({
                "doc_id": f"{it['id']}_c{i}",
                "source_id": it["id"],
                "url": it.get("url"),
                "title": it.get("title"),
                "published": it.get("published"),
                "text": ch
            })
    print("Total chunks:", len(docs))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # incremental embeddings
    if EMBED:
        print("Computing incremental embeddings...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        existing_ids = load_existing_ids()
        new_texts = []
        new_doc_ids = []
        for d in docs:
            if d["doc_id"] not in existing_ids:
                new_texts.append(d["text"])
                new_doc_ids.append(d["doc_id"])
        print("New chunks to embed:", len(new_texts))
        if new_texts:
            embs = model.encode(new_texts, show_progress_bar=True, convert_to_numpy=True)
            # append to existing arrays/files
            if EMB_FILE.exists():
                existing = np.load(EMB_FILE)
                combined = append_embeds(existing, embs)
            else:
                combined = embs
            np.save(EMB_FILE, combined)
            with EMB_IDS.open("a", encoding="utf-8") as idf:
                for did in new_doc_ids:
                    idf.write(json.dumps({"doc_id": did}) + "\n")
            print("Saved embeddings:", EMB_FILE, "ids:", EMB_IDS)
        else:
            print("No new docs to embed.")
    else:
        print("Skipping embeddings (COMPUTE_EMBEDDINGS != 1)")

if __name__ == "__main__":
    main()
