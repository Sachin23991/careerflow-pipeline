# pipeline/push_to_hf.py
import os
import sys
from pathlib import Path
from huggingface_hub import HfApi

HF_TOKEN = os.getenv("HF_TOKEN")
HF_REPO = os.getenv("HF_REPO")  # Example: "Sachin21112004/carrerflow-ai"

if not HF_TOKEN:
    print("❌ ERROR: HF_TOKEN missing")
    sys.exit(1)

if not HF_REPO:
    print("❌ ERROR: HF_REPO missing (expected format: username/repo)")
    sys.exit(1)

api = HfApi()

# Create repo if not exists
try:
    api.create_repo(
        repo_id=HF_REPO,
        repo_type="dataset",
        exist_ok=True,
        token=HF_TOKEN
    )
    print("✅ HF repo ready:", HF_REPO)
except Exception as e:
    print("⚠️ Repo create skipped:", e)

# Files and their remote paths
FILES = {
    "pipeline/rag_docs.jsonl": "rag_storage/rag_docs.jsonl",
    "pipeline/embeddings.npy": "rag_storage/embeddings.npy",
    "pipeline/emb_ids.jsonl": "rag_storage/emb_ids.jsonl"
}

for local, remote in FILES.items():
    if not Path(local).exists():
        print(f"⏭️ Skipped missing: {local}")
        continue

    print(f"⬆️ Uploading {local} → {HF_REPO}/{remote}")

    try:
        api.upload_file(
            path_or_fileobj=local,
            path_in_repo=remote,
            repo_id=HF_REPO,
            repo_type="dataset",
            token=HF_TOKEN
        )
        print(f"✅ Uploaded: {remote}")
    except Exception as e:
        print(f"❌ Upload failed for {local} → {e}")

print("🎉 Upload complete.")
