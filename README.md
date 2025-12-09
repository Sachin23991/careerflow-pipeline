# 🌍 CareerFlow AI — Global News → RAG Pipeline  
### *Real-time automated knowledge engine powering CareerFlow AI*

---

## 📌 Introduction

CareerFlow AI requires **fresh, reliable, up-to-date knowledge** to answer questions across careers, technology, world events, economy, business, education, and emerging trends.

Large Language Models (LLMs) cannot stay up-to-date by themselves.  
So this repository provides a **complete automated Retrieval-Augmented Generation (RAG) pipeline** that:

1. Scrapes global news every hour  
2. Extracts full article content  
3. Filters + deduplicates + cleans  
4. Splits into semantic chunks  
5. Computes embeddings incrementally  
6. Stores final RAG datasets on HuggingFace  
7. Auto-creates new versions when size > 100 MB  
8. Powers CareerFlow’s retrieval engine + LLM reasoning  

This README explains **EVERYTHING** about the system architecture, workflow design, datasets, API endpoints, and complete logic behind the entire repo.

---

# 🧠 What This Repository Provides

### ✔ Fully autonomous RAG pipeline  
### ✔ Hourly GitHub Actions automation  
### ✔ Trusted multi-source news ingestion  
### ✔ Clean structured dataset output  
### ✔ Incremental embeddings  
### ✔ HuggingFace auto-upload  
### ✔ Multi-version dataset rotation  
### ✔ Retrieval API + LLM answering  

This README documents everything end-to-end.

---

# 🔥 Why this matters

CareerFlow AI aims to become a **Perplexity-level assistant**, capable of:

- Understanding latest career trends  
- Summarizing fresh global news  
- Giving guidance with updated industry insights  
- Using RAG to avoid hallucinations  
- Staying current **every single hour**  

This pipeline ensures the AI is ALWAYS up-to-date.

---

# 🏗 System Architecture Overview

```
 ┌──────────────────────────────┐
 │  Trusted Global News Sources │
 │  (RSS + HTML extraction)     │
 └───────────────┬──────────────┘
                 │ raw news
                 ▼
 ┌──────────────────────────────┐
 │      Scraper (scrape.py)     │
 │ Extracts + normalizes text    │
 └───────────────┬──────────────┘
                 │ raw_news.jsonl
                 ▼
 ┌──────────────────────────────┐
 │     Filter Engine (filter.py)│
 │ Dedupes + cleans + validates │
 └───────────────┬──────────────┘
                 │ filtered_news.jsonl
                 ▼
 ┌──────────────────────────────┐
 │ Chunk Builder + Embedder     │
 │  dataset_builder.py          │
 │ (incremental embeddings)     │
 └───────────────┬──────────────┘
                 │ rag_docs + embeddings
                 ▼
 ┌──────────────────────────────┐
 │   push_to_hf.py (auto-upload)│
 │ Decides folder:              │
 │  rag_storage or rag_storage_v2, v3… │
 └───────────────┬──────────────┘
                 │ HF upload
                 ▼
 ┌──────────────────────────────┐
 │ HuggingFace Dataset Repo     │
 │   /rag_storage               │
 │   /rag_storage_v2            │
 │   /rag_storage_v3            │
 └──────────────────────────────┘
```

---

# 📦 HuggingFace Dataset Explained

Dataset location:

https://huggingface.co/Sachin21112004/carrerflow-ai/tree/main/rag_storage

The pipeline auto-manages:

- rag_storage/  
- rag_storage_v2/  
- rag_storage_v3/  
- … (new versions when size > 100 MB)

Each folder contains:

### rag_docs.jsonl
Each line is a chunk:

```
{
  "doc_id": "bbc_2025-12-09_34_chunk3",
  "url": "...",
  "title": "...",
  "published": "2025-12-09T12:34:00",
  "source": "BBC",
  "text": "chunk of article..."
}
```

### embeddings.npy  
A float32 array of shape:

```
(num_chunks, embedding_dim)
```

### emb_ids.jsonl  
Maps each embedding row to a chunk:

```
{"doc_id": "bbc_2025-12-09_34_chunk3"}
```

---

# 📁 Full Repository Structure (Explained)

```
careerflow-pipeline/
│
├── pipeline/
│   ├── scrape.py                 → Fetches news from RSS feeds
│   ├── filter.py                 → Removes duplicates, bad content
│   ├── dataset_builder.py        → Chunking + incremental embeddings
│   ├── push_to_hf.py             → Uploads to HuggingFace (NO HF_REPO secret)
│   ├── raw_news.jsonl            → Generated automatically
│   ├── filtered_news.jsonl       → Cleaned articles
│   ├── rag_docs.jsonl            → Final chunked dataset
│   ├── embeddings.npy            → Embeddings file
│   └── emb_ids.jsonl             → Maps doc_ids → embedding indices
│
├── api/
│   └── server.py                 → Retrieval API + LLM answering
│
├── .github/workflows/
│   └── news.yml                  → Hourly pipeline workflow
│
├── requirements.txt              → All dependencies
└── README.md                     → This file
```

---

# 🧾 Detailed Breakdown of Every Component

---

## 1️⃣ scrape.py — Global News Scraper

Responsibilities:

- Load RSS feed list  
- Fetch each article  
- Extract readable content  
- Normalize HTML → clean text  
- Store results in `raw_news.jsonl`

Each line stored as:

```
{
  "title": "...",
  "url": "...",
  "published": "...",
  "source": "...",
  "text": "full extracted article..."
}
```

---

## 2️⃣ filter.py — Cleaning + Deduplication

Uses SQLite DB `seen.db` to track previously processed URLs.

Removes:

- Duplicate articles  
- Extremely short posts  
- Sponsored/ads  
- Non-English or low-quality text  

Output: `filtered_news.jsonl`.

---

## 3️⃣ dataset_builder.py — RAG Chunking + Incremental Embeddings

### Tasks:
- Split each article into chunks (300–500 characters)  
- Assign unique doc_ids  
- Check which chunks are **new**  
- Embed ONLY new chunks  
- Append new embeddings to `embeddings.npy`  
- Append mapping to `emb_ids.jsonl`  

### Why incremental?
Reduces embedding time from minutes → seconds.

---

## 4️⃣ push_to_hf.py — Upload to HuggingFace (Auto-Versioning)

### Logic:
1. Check repo size using HuggingFace Hub API  
2. If size < 100 MB:
   - Upload to `rag_storage/`
3. If size >= 100 MB:
   - Create or continue `rag_storage_v2/`, `rag_storage_v3/`, etc.
4. Upload:  
   - rag_docs.jsonl  
   - embeddings.npy  
   - emb_ids.jsonl  

### Important:
No `HF_REPO` secret is used — repo name is hardcoded inside script.

You only need:

- **HF_TOKEN** as GitHub secret

---

# ⏰ Hourly GitHub Actions Workflow (news.yml)

This workflow:

- Runs every hour  
- Installs dependencies  
- Executes pipeline  
- Uploads to HuggingFace  

Core steps:

```
checkout repo
setup python
install requirements
python scrape.py
python filter.py
python dataset_builder.py
python push_to_hf.py
```

---

# 🔥 Retrieval API (api/server.py)

Available endpoints:

### `/retrieve`
Returns top-k similar documents.

Request:

```
{
  "query": "What happened in AI this week?",
  "top_k": 5
}
```

Response:

```
[
  { "doc_id": "...", "text": "...", "score": 0.87 },
  ...
]
```

---

### `/ask`
Combines retrieval + LLM:

- Retrieves context  
- Builds augmented prompt  
- Calls:
  1. Bytez AI  
  2. Gemini  
  3. HuggingFace Inference  

Whichever works first.

---

# 🛠 Requirements

Main dependencies:

- sentence-transformers  
- numpy  
- huggingface_hub  
- fastapi  
- uvicorn  
- beautifulsoup4  
- readability-lxml  

---

# 🧪 Running Everything Locally

1 — Install:

    pip install -r requirements.txt

2 — Scrape:

    python pipeline/scrape.py

3 — Filter:

    python pipeline/filter.py

4 — Build dataset:

    COMPUTE_EMBEDDINGS=1 python pipeline/dataset_builder.py

5 — Push manually (optional):

    export HF_TOKEN=hf_xxx
    python pipeline/push_to_hf.py

6 — Start API:

    uvicorn api.server:app --reload

---

# ⚠️ Troubleshooting

### 1. "Repo Not Found"
Your HF_TOKEN does not have write permissions.

Solution:  
Go to → HuggingFace → Settings → Access Tokens → Create token (write).

---

### 2. "Cannot import huggingface_hub module"
Upgrade:

    pip install --upgrade huggingface_hub

---

### 3. "Nothing uploaded"
Make sure new chunks were generated.

---

# 🚀 Future Improvements

- Add FAISS for million-scale retrieval  
- Add embeddings quantization  
- Add source reputation scoring  
- Add additional non-news sources  
- Auto-summarization storage  
- Multi-language support  

---

# ❤️ Credits

Designed with care by **Sachin Rao (CareerFlow AI)**  


This system is now production-ready and scales automatically.

