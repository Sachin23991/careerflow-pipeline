# pipeline/push_to_hf.py
import os, sys, json
from huggingface_hub import HfApi, hf_hub_upload, create_repo

HF_TOKEN = os.getenv("HF_TOKEN")
HF_REPO = os.getenv("HF_REPO")  # e.g. "yourusername/rag-news"
if not HF_TOKEN:
    print("Missing HF_TOKEN env var", file=sys.stderr)
    sys.exit(1)

api = HfApi()

if not HF_REPO:
    user = api.whoami(token=HF_TOKEN).get("name")
    if not user:
        print("Set HF_REPO env var to something like 'username/rag-news'", file=sys.stderr)
        sys.exit(1)
    HF_REPO = f"{user}/rag-news"

print("Uploading to:", HF_REPO)
try:
    api.create_repo(repo_id=HF_REPO, repo_type="dataset", token=HF_TOKEN, exist_ok=True)
except Exception as e:
    print("repo create warning:", e)

files_to_upload = [
    ("pipeline/rag_docs.jsonl", "rag_docs.jsonl")
]
if os.path.exists("pipeline/embeddings.npy"):
    files_to_upload.append(("pipeline/embeddings.npy", "embeddings.npy"))
if os.path.exists("pipeline/emb_ids.jsonl"):
    files_to_upload.append(("pipeline/emb_ids.jsonl", "emb_ids.jsonl"))

for src, dest in files_to_upload:
    try:
        print("Uploading", src, "->", dest)
        hf_hub_upload(path_or_fileobj=src, path_in_repo=dest, repo_id=HF_REPO, repo_type="dataset", token=HF_TOKEN, create_pr=False)
        print("Uploaded", dest)
    except Exception as e:
        print("Upload failed", e)
print("Done")
