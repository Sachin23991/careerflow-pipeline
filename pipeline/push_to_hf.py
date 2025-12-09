# pipeline/push_to_hf.py
import os
import sys
from huggingface_hub import HfApi, repo_file_download, list_repo_files

HF_TOKEN = os.getenv("HF_TOKEN")
HF_REPO = os.getenv("HF_REPO")

if not HF_TOKEN:
    print("❌ Missing HF_TOKEN")
    sys.exit(1)

if not HF_REPO:
    print("❌ Missing HF_REPO (expected: username/repo)")
    sys.exit(1)

api = HfApi()

# ----------------------------------------------------
# STEP 1: CHECK EXISTING FILES & TOTAL SIZE
# ----------------------------------------------------
def get_repo_size(repo_id):
    try:
        files = list_repo_files(repo_id=repo_id, repo_type="dataset", token=HF_TOKEN)
        total_bytes = 0
        for f in files:
            try:
                info = api.repo_file_info(
                    repo_id=repo_id, path_in_repo=f, repo_type="dataset", token=HF_TOKEN
                )
                total_bytes += info.size or 0
            except:
                pass
        return total_bytes
    except Exception as e:
        print("⚠ Could not list repo files:", e)
        return 0


repo_size = get_repo_size(HF_REPO)
print(f"📦 Current HF repo size: {repo_size / (1024*1024):.2f} MB")

# ----------------------------------------------------
# STEP 2: Compute destination folder based on size
# ----------------------------------------------------
if repo_size >= 90 * 1024 * 1024:   # 100 MB
    # Find existing version folders
    files = list_repo_files(repo_id=HF_REPO, repo_type="dataset", token=HF_TOKEN)
    version_numbers = [
        int(f.split("/")[1].replace("rag_storage_v", ""))
        for f in files
        if f.startswith("rag_storage_v")
    ]
    next_version = (max(version_numbers) + 1) if version_numbers else 2

    DEST_FOLDER = f"rag_storage_v{next_version}"
    print(f"🔄 Repo > 100 MB → creating new version folder: {DEST_FOLDER}/")
else:
    DEST_FOLDER = "rag_storage"
    print(f"👍 Repo < 100 MB → using folder: {DEST_FOLDER}/")

# ----------------------------------------------------
# STEP 3: Files to upload
# ----------------------------------------------------
FILES = {
    "pipeline/rag_docs.jsonl": f"{DEST_FOLDER}/rag_docs.jsonl",
    "pipeline/embeddings.npy": f"{DEST_FOLDER}/embeddings.npy",
    "pipeline/emb_ids.jsonl": f"{DEST_FOLDER}/emb_ids.jsonl"
}

# ----------------------------------------------------
# STEP 4: Upload files using new HF API
# ----------------------------------------------------
api.create_repo(
    repo_id=HF_REPO, repo_type="dataset", exist_ok=True, token=HF_TOKEN
)

for local_path, remote_path in FILES.items():
    if not os.path.exists(local_path):
        print(f"⏭ Skipping missing file: {local_path}")
        continue

    print(f"⬆ Uploading {local_path} → {remote_path}")

    try:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=remote_path,
            repo_id=HF_REPO,
            repo_type="dataset",
            token=HF_TOKEN
        )
        print(f"✅ Uploaded: {remote_path}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

print("🎉 Upload complete.")
