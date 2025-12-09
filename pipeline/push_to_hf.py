# pipeline/push_to_hf.py

import os
import sys
from huggingface_hub import HfApi, list_repo_files

HF_TOKEN = os.getenv("HF_TOKEN")

# Hardcoded repo ID (NO SECRET NEEDED)
HF_REPO = "Sachin21112004/carrerflow-ai"
REPO_TYPE = "dataset"

if not HF_TOKEN:
    print("❌ ERROR: HF_TOKEN is missing")
    sys.exit(1)

api = HfApi()

# ----------------------------------------------------
# STEP 1 — Compute existing repo size
# ----------------------------------------------------
def get_repo_size(repo_id):
    try:
        files = list_repo_files(repo_id, repo_type=REPO_TYPE, token=HF_TOKEN)
        total = 0
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
    except Exception as e:
        print("⚠ Could not get repo size:", e)
        return 0


repo_size = get_repo_size(HF_REPO)
repo_size_mb = repo_size / (1024 * 1024)
print(f"📦 HF Repo current size: {repo_size_mb:.2f} MB")

# ----------------------------------------------------
# STEP 2 — Decide upload folder (auto-versioning)
# ----------------------------------------------------
if repo_size_mb >= 90:
    files = list_repo_files(HF_REPO, repo_type=REPO_TYPE, token=HF_TOKEN)

    versions = []
    for f in files:
        if f.startswith("rag_storage_v"):
            try:
                v = int(f.split("/")[0].replace("rag_storage_v", ""))
                versions.append(v)
            except:
                pass

    next_ver = max(versions) + 1 if versions else 2
    DEST = f"rag_storage_v{next_ver}"
    print(f"🔄 Repo >100MB → Creating new version folder: {DEST}/")

else:
    DEST = "rag_storage"
    print(f"👍 Repo <100MB → Using folder: {DEST}/")

# ----------------------------------------------------
# STEP 3 — Files to upload
# ----------------------------------------------------
FILES = {
    "pipeline/rag_docs.jsonl": f"{DEST}/rag_docs.jsonl",
    "pipeline/embeddings.npy": f"{DEST}/embeddings.npy",
    "pipeline/emb_ids.jsonl": f"{DEST}/emb_ids.jsonl",
}

# Ensure repo exists
api.create_repo(
    repo_id=HF_REPO,
    repo_type=REPO_TYPE,
    exist_ok=True,
    token=HF_TOKEN
)

# ----------------------------------------------------
# STEP 4 — Upload files
# ----------------------------------------------------
for local, remote in FILES.items():
    if not os.path.exists(local):
        print(f"⏭ Skipping missing file: {local}")
        continue

    print(f"⬆ Uploading {local} → {remote}")
    try:
        api.upload_file(
            path_or_fileobj=local,
            path_in_repo=remote,
            repo_id=HF_REPO,
            repo_type=REPO_TYPE,
            token=HF_TOKEN
        )
        print(f"✅ Uploaded: {remote}")
    except Exception as e:
        print(f"❌ Upload failed for {local}: {e}")

print("🎉 Upload complete.")
