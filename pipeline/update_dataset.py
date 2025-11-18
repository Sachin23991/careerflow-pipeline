import pandas as pd
from huggingface_hub import HfApi, upload_file
import os, sys, time

DATASET_REPO = "Sachin21112004/DreamFlow-AI-Data"
LOCAL_FILE = "train.jsonl"

print("🔄 Always running in APPEND mode (overwrite disabled).")

# -------- 1. NEW INCOMING DATA --------
# Replace this with your real scraper logic
new_record = {
    "timestamp": str(time.time()),
    "text": f"New scraped data at {time.time()}",
}
new_df = pd.DataFrame([new_record])


# -------- 2. DOWNLOAD EXISTING DATASET --------
api = HfApi()
try:
    print("⬇️ Downloading existing dataset...")
    api.hf_hub_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        filename=LOCAL_FILE,
        local_dir=".",
        token=os.environ["HF_TOKEN"]
    )
    old_df = pd.read_json(LOCAL_FILE, lines=True)
    print(f"Loaded {len(old_df)} old rows.")
except Exception as e:
    print("⚠️ No existing dataset found, starting new.")
    old_df = pd.DataFrame()


# -------- 3. APPEND ONLY --------
combined_df = pd.concat([old_df, new_df], ignore_index=True)
combined_df.to_json(LOCAL_FILE, lines=True, orient="records")
print(f"➕ Added {len(new_df)} rows → Total: {len(combined_df)} rows")


# -------- 4. UPLOAD UPDATED DATASET --------
print("⬆️ Uploading updated dataset...")
upload_file(
    path_or_fileobj=LOCAL_FILE,
    path_in_repo=LOCAL_FILE,
    repo_id=DATASET_REPO,
    repo_type="dataset",
    token=os.environ["HF_TOKEN"]
)

print("✅ Dataset updated & uploaded successfully.")
