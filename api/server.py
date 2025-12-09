# api/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import os, json, numpy as np
from typing import List
import uvicorn

# Simple cosine retrieval fallback
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)

class Query(BaseModel):
    query: str
    top_k: int = 5

app = FastAPI()

# If Chroma is present, use it
USE_CHROMA = os.getenv("USE_CHROMA", "0") == "1"
if USE_CHROMA:
    import chromadb
    from chromadb.config import Settings
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="pipeline/chroma_db"))
    collection = client.get_collection("news_rag")
else:
    EMB = "pipeline/embeddings.npy"
    EMB_IDS = "pipeline/emb_ids.jsonl"
    RAG_JSONL = "pipeline/rag_docs.jsonl"
    if os.path.exists(EMB):
        embeddings = np.load(EMB)
        ids = [json.loads(line)["doc_id"] for line in open(EMB_IDS, encoding="utf-8")]
        docs = { json.loads(l)["doc_id"]: json.loads(l) for l in open(RAG_JSONL, encoding="utf-8") }
    else:
        embeddings = None
        ids = []
        docs = {}

# Simple re-ranker: if you have an embeddings model, encode query to same space.
from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

@app.post("/retrieve")
def retrieve(q: Query):
    query_vec = embed_model.encode(q.query, convert_to_numpy=True)
    if USE_CHROMA:
        results = collection.query(query_texts=[q.query], n_results=q.top_k)
        hits = []
        for doclist, metadatalist in zip(results["documents"], results["metadatas"]):
            for doc, meta in zip(doclist, metadatalist):
                hits.append({"text": doc, "meta": meta})
        return {"hits": hits}
    else:
        if embeddings is None:
            return {"error": "no embeddings found"}
        sims = []
        for i, v in enumerate(embeddings):
            sims.append((i, float(np.dot(query_vec, v) / ((np.linalg.norm(query_vec) * np.linalg.norm(v)) + 1e-10))))
        sims.sort(key=lambda x: x[1], reverse=True)
        top = sims[:q.top_k]
        hits = []
        for idx, score in top:
            doc_id = ids[idx]
            d = docs.get(doc_id, {})
            hits.append({"doc_id": doc_id, "score": score, "title": d.get("title"), "text": d.get("text"), "url": d.get("url")})
        return {"hits": hits}

@app.post("/ask")
def ask(q: Query):
    # retrieve
    res = retrieve(q)
    if "error" in res:
        return res
    hits = res["hits"]
    # Compose system prompt: we include top-k texts as grounding
    context = "\n\n---\n\n".join([f"{h.get('title','')}\n{h.get('text','')}" for h in hits])
    prompt = f"You are an assistant. Base your answer on the following documents:\n\n{context}\n\nUser query: {q.query}\nProvide a concise answer and cite relevant URLs.\n"
    # Here you should call your LLM of choice (OpenAI, HF Inference, or local)
    # We'll return the prompt to be sent to the LLM (so you can plug your API call)
    return {"prompt_for_llm": prompt, "retrieved": hits}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
