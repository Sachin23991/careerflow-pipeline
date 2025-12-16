# pipeline/push_to_hf.py

import os
import sys
import json
import numpy as np
import faiss
from huggingface_hub import HfApi, list_repo_files

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
HF_TOKEN = os.getenv("HF_TOKEN")
HF_REPO = "Sachin21112004/carrerflow-ai"
REPO_TYPE = "dataset"

EMB_PATH = "pipeline/embeddings.npy"
IDS_PATH = "pipeline/emb_ids.jsonl"

if not HF_TOKEN:
    print("❌ ERROR: HF_TOKEN is missing")
    sys.exit(1)

if not os.path.exists(EMB_PATH) or not os.path.exists(IDS_PATH):
    print("❌ ERROR: embeddings or ids file missing")
    sys.exit(1)

api = HfApi()

# ----------------------------------------------------
# STEP 1 — Compute repo size (best-effort)
# ----------------------------------------------------
def get_repo_size(repo_id):
    try:
        total = 0
        files = list_repo_files(repo_id, repo_type=REPO_TYPE, token=HF_TOKEN)
        for f in files:
            try:
                info = api.repo_file_info(
                    repo_id=repo_id,
                    path_in_repo=f,
                    repo_type=REPO_TYPE,
                    token=HF_TOKEN
                )
                if info.size:
                    total += info.size
            except:
                pass
        return total
    except:
        return 0

repo_size_mb = get_repo_size(HF_REPO) / (1024 * 1024)
print(f"📦 HF Repo current size: {repo_size_mb:.2f} MB")

# ----------------------------------------------------
# STEP 2 — Decide destination folder
# ----------------------------------------------------
if repo_size_mb >= 90:
    files = list_repo_files(HF_REPO, repo_type=REPO_TYPE, token=HF_TOKEN)
    versions = []
    for f in files:
        if f.startswith("rag_storage_v"):
            try:
                versions.append(int(f.split("/")[0].replace("rag_storage_v", "")))
            except:
                pass
    next_ver = max(versions) + 1 if versions else 2
    DEST = f"rag_storage_v{next_ver}"
    print(f"🔄 Using new version folder: {DEST}/")
else:
    DEST = "rag_storage"
    print(f"👍 Using folder: {DEST}/")

# ----------------------------------------------------
# STEP 3 — Build FAISS index
# ----------------------------------------------------
print("🔧 Building FAISS index...")

embeddings = np.load(EMB_PATH).astype("float32")
dim = embeddings.shape[1]

index = faiss.IndexFlatL2(dim)
index.add(embeddings)

os.makedirs("pipeline/faiss_out", exist_ok=True)
FAISS_INDEX = "pipeline/faiss_out/index.faiss"
faiss.write_index(index, FAISS_INDEX)

print(f"✅ FAISS index built ({index.ntotal} vectors)")

# ----------------------------------------------------
# STEP 4 — Build metadata.json
# ----------------------------------------------------
metadata = []
with open(IDS_PATH, "r") as f:
    for line in f:
        metadata.append(json.loads(line))

META_PATH = "pipeline/faiss_out/metadata.json"
with open(META_PATH, "w") as f:
    json.dump(metadata, f, ensure_ascii=False)

print("✅ Metadata file written")

# ----------------------------------------------------
# STEP 5 — Ensure repo exists
# ----------------------------------------------------
api.create_repo(
    repo_id=HF_REPO,
    repo_type=REPO_TYPE,
    exist_ok=True,
    token=HF_TOKEN
)

# ----------------------------------------------------
# STEP 6 — Upload ONLY production files
# ----------------------------------------------------
UPLOADS = {
    FAISS_INDEX: f"{DEST}/index.faiss",
    META_PATH: f"{DEST}/metadata.json",
}

for local, remote in UPLOADS.items():
    print(f"⬆ Uploading {local} → {remote}")
    api.upload_file(
        path_or_fileobj=local,
        path_in_repo=remote,
        repo_id=HF_REPO,
        repo_type=REPO_TYPE,
        token=HF_TOKEN
    )
    print(f"✅ Uploaded: {remote}")

print("🎉 RAG index update complete.")
