# api/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import json
import os
import uvicorn
import requests

# ---------------------------------------------------------
# Load RAG Documents + Embeddings
# ---------------------------------------------------------
EMB = "pipeline/embeddings.npy"
EMB_IDS = "pipeline/emb_ids.jsonl"
RAG_FILE = "pipeline/rag_docs.jsonl"

embeddings = np.load(EMB) if os.path.exists(EMB) else None
ids = [json.loads(l)["doc_id"] for l in open(EMB_IDS, "r", encoding="utf-8")] if embeddings is not None else []

docs = {}
if os.path.exists(RAG_FILE):
    for l in open(RAG_FILE, "r", encoding="utf-8"):
        obj = json.loads(l)
        docs[obj["doc_id"]] = obj


# ---------------------------------------------------------
# Embedding Model
# ---------------------------------------------------------
from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine(a, b):
    return np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) + 1e-10)


# ---------------------------------------------------------
# API Request Model
# ---------------------------------------------------------
class Query(BaseModel):
    query: str
    top_k: int = 5


app = FastAPI()


# ---------------------------------------------------------
# Retrieve top-k chunks
# ---------------------------------------------------------
@app.post("/retrieve")
def retrieve(q: Query):
    if embeddings is None:
        return {"error": "No embeddings found. Run dataset_builder.py"}

    q_emb = embed_model.encode(q.query, convert_to_numpy=True)

    similarities = [
        (i, cosine(q_emb, embeddings[i])) for i in range(len(embeddings))
    ]

    similarities.sort(key=lambda x: x[1], reverse=True)
    top = similarities[:q.top_k]

    hits = []
    for idx, score in top:
        doc_id = ids[idx]
        d = docs.get(doc_id, {})
        hits.append({
            "doc_id": doc_id,
            "score": float(score),
            "title": d.get("title"),
            "text": d.get("text"),
            "url": d.get("url"),
            "published": d.get("published")
        })

    return {"hits": hits}


# ---------------------------------------------------------
# Build final LLM prompt
# ---------------------------------------------------------
def build_prompt(query, hits):
    context = "\n\n---\n\n".join(
        f"Title: {h['title']}\n{h['text']}"
        for h in hits
    )
    return f"""
You are a factual AI assistant. Use ONLY the following news documents as context:

{context}

User question: {query}

Give a correct, grounded answer with citations (URLs) at the end.
""".strip()


# ---------------------------------------------------------
# BYTEZ.COM model call (PRIMARY)
# ---------------------------------------------------------
def call_bytez(prompt):
    BYTEZ_API_KEY = os.getenv("BYTEZ_API_KEY")
    if not BYTEZ_API_KEY:
        return None  # Not available → fallback

    url = "https://api.bytez.com/v1/chat/completions"

    payload = {
        "model": "mixtral-8x7b-instruct",  # You can change to ANY Bytez model
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700,
        "temperature": 0.2
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {BYTEZ_API_KEY}"}
        ).json()

        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print("Bytez API Error:", e)
        return None


# ---------------------------------------------------------
# GEMINI LLM CALL (SECOND PRIORITY)
# ---------------------------------------------------------
def call_gemini(prompt):
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        print("Gemini Error:", e)
        return None


# ---------------------------------------------------------
# HUGGINGFACE INFERENCE CALL (THIRD PRIORITY)
# ---------------------------------------------------------
def call_hf(prompt):
    HF_API_KEY = os.getenv("HF_API_KEY")
    if not HF_API_KEY:
        return None

    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=HF_API_KEY)
        return client.text_generation(
            prompt,
            model="meta-llama/Llama-3-8b-chat"
        )
    except Exception as e:
        print("HF Error:", e)
        return None


# ---------------------------------------------------------
# LLM Controller – chooses best available model
# ---------------------------------------------------------
def call_llm(prompt):
    # 1️⃣ Bytez.com
    result = call_bytez(prompt)
    if result:
        return f"[Bytez Model]\n\n{result}"

    # 2️⃣ Gemini
    result = call_gemini(prompt)
    if result:
        return f"[Gemini]\n\n{result}"

    # 3️⃣ HuggingFace
    result = call_hf(prompt)
    if result:
        return f"[HuggingFace]\n\n{result}"

    return "❌ No AI provider available. Set BYTEZ_API_KEY or GOOGLE_API_KEY or HF_API_KEY."


# ---------------------------------------------------------
# Full RAG Answer
# ---------------------------------------------------------
@app.post("/ask")
def ask(q: Query):
    ret = retrieve(q)
    hits = ret["hits"]

    prompt = build_prompt(q.query, hits)
    answer = call_llm(prompt)

    return {
        "query": q.query,
        "prompt_used": prompt,
        "retrieved_docs": hits,
        "answer": answer
    }


# ---------------------------------------------------------
# Local run
# ---------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
