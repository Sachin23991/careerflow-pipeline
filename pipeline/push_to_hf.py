# pipeline/push_to_hf.py
import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_upload

HF_TOKEN = os.getenv("HF_TOKEN")
HF_REPO = os.getenv("HF_REPO")  # example: "Sachin21112004/carrerflow-ai"

if not HF_TOKEN:
    print("❌ ERROR: Missing HF_TOKEN environment variable", file=sys.stderr)
    sys.exit(1)

if not HF_REPO:
    print("❌ ERROR: Missing HF_REPO environment variable. Example value:")
    print("HF_REPO=Sachin21112004/carrerflow-ai")
    sys.exit(1)

print(f"🚀 Uploading to HuggingFace repo: {HF_REPO}")
api = HfApi()

# Ensure repo exists (dataset-type)
try:
    api.create_repo(
        repo_id=HF_REPO,
        repo_type="dataset",
        exist_ok=True,
        token=HF_TOKEN
    )
    print("✅ Repo verified / created:", HF_REPO)
except Exception as e:
    print("⚠️ Repo create warning:", e)

# ----------------------------
# FILES WE WANT TO UPLOAD
# ----------------------------
FILES = {
    "pipeline/rag_docs.jsonl": "rag_storage/rag_docs.jsonl",
    "pipeline/embeddings.npy": "rag_storage/embeddings.npy",
    "pipeline/emb_ids.jsonl": "rag_storage/emb_ids.jsonl"
}

# ----------------------------
# UPLOAD LOGIC
# ----------------------------
for local_path, dest_path in FILES.items():
    if not Path(local_path).exists():
        print(f"⏭️ Skipped (file missing): {local_path}")
        continue

    try:
        print(f"⬆️ Uploading {local_path} → {HF_REPO}/{dest_path}")
        hf_hub_upload(
            path_or_fileobj=local_path,
            path_in_repo=dest_path,       # <- IMPORTANT: upload to subfolder rag_storage/
            repo_id=HF_REPO,
            repo_type="dataset",
            token=HF_TOKEN,
            create_pr=False
        )
        print(f"✅ Uploaded: {dest_path}")

    except Exception as e:
        print(f"❌ Failed upload for {local_path}: {e}")

print("🎉 Push to HuggingFace completed.")
