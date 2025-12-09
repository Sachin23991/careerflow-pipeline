# pipeline/push_to_hf.py
import os
import sys
from huggingface_hub import HfApi, list_repo_files

HF_TOKEN = os.getenv("HF_TOKEN")
HF_REPO = os.getenv("HF_REPO")

if not HF_TOKEN:
    print("❌ Missing HF_TOKEN")
    sys.exit(1)

if not HF_REPO:
    print("❌ Missing HF_REPO environment variable")
    sys.exit(1)

api = HfApi()

# ----------------------------------------------------
# CHECK CURRENT HF REPO SIZE
# ----------------------------------------------------
def get_repo_size(repo_id):
    try:
        files = list_repo_files(repo_id, repo_type="dataset", token=HF_TOKEN)
        total = 0
        for f in files:
            try:
                info = api.repo_file_info(
                    repo_id=repo_id,
                    path_in_repo=f,
                    repo_type="dataset",
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
print(f"📦 Current repo size: {repo_size_mb:.2f} MB")

# ----------------------------------------------------
# DECIDE DESTINATION FOLDER (100MB VERSIONING)
# ----------------------------------------------------
if repo_size_mb >= 90:
    # Find existing version folders
    files = list_repo_files(HF_REPO, repo_type="dataset", token=HF_TOKEN)
    version_nums = []

    for f in files:
        if f.startswith("rag_storage_v"):
            try:
                num = int(f.split("/")[0].replace("rag_storage_v", ""))
                version_nums.append(num)
            except:
                pass

    next_ver = (max(version_nums) + 1) if version_nums else 2
    DEST = f"rag_storage_v{next_ver}"
    print(f"🔄 Repo > 100MB → creating new version folder: {DEST}/")
else:
    DEST = "rag_storage"
    print(f"👍 Repo < 100MB → using folder: {DEST}/")

# ----------------------------------------------------
# FILES TO UPLOAD
# ----------------------------------------------------
FILES = {
    "pipeline/rag_docs.jsonl": f"{DEST}/rag_docs.jsonl",
    "pipeline/embeddings.npy": f"{DEST}/embeddings.npy",
    "pipeline/emb_ids.jsonl": f"{DEST}/emb_ids.jsonl",
}

# Ensure repo exists
api.create_repo(
    repo_id=HF_REPO,
    repo_type="dataset",
    exist_ok=True,
    token=HF_TOKEN
)

# ----------------------------------------------------
# UPLOAD FILES TO HUGGINGFACE
# ----------------------------------------------------
for local, remote in FILES.items():
    if not os.path.exists(local):
        print(f"⏭ Skipped missing: {local}")
        continue

    print(f"⬆ Uploading {local} → {remote}")

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
        print(f"❌ Upload failed for {local}: {e}")

print("🎉 Upload complete.")
