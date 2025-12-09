# pipeline/push_to_hf.py
import os
import sys
from huggingface_hub import HfApi, hf_hub_upload, create_repo, HfFolder, Repository
from pathlib import Path

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
if not HF_TOKEN:
    print("Missing HF_TOKEN environment variable", file=sys.stderr)
    sys.exit(1)

REPO_ID = os.getenv("HF_REPO", None)  # optional: set HF_REPO=yourusername/rag-news
if not REPO_ID:
    # default to username/rag-news
    api = HfApi()
    user = api.whoami(token=HF_TOKEN).get("name")
    if not user:
        print("Cannot determine HF username automatically. Set HF_REPO env to 'username/repo'.", file=sys.stderr)
        sys.exit(1)
    REPO_ID = f"{user}/rag-news"

print("Target repo:", REPO_ID)

api = HfApi()
# create repo if not exists
try:
    api.create_repo(repo_id=REPO_ID, repo_type="dataset", token=HF_TOKEN, exist_ok=True)
    print("Repo ensured:", REPO_ID)
except Exception as e:
    print("create_repo warning:", e)

# files to upload
files = [
    ("pipeline/rag_docs.jsonl", "rag_docs.jsonl"),
]
if Path("pipeline/embeddings.npy").exists():
    files.append(("pipeline/embeddings.npy", "embeddings.npy"))
if Path("pipeline/emb_ids.jsonl").exists():
    files.append(("pipeline/emb_ids.jsonl", "emb_ids.jsonl"))

# upload files
for src, dest in files:
    try:
        print(f"Uploading {src} -> {REPO_ID}/{dest}")
        # upload to the dataset repo root
        hf_hub_upload(
            path_or_fileobj=src,
            path_in_repo=dest,
            repo_id=REPO_ID,
            repo_type="dataset",
            token=HF_TOKEN,
            create_pr=False,
            repo_type_check=False,
            max_retries=3
        )
        print("Uploaded", dest)
    except Exception as e:
        print("Upload failed for", src, e)

print("Push step done.")
