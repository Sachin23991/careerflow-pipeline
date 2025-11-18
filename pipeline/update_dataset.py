import pandas as pd
from huggingface_hub import HfApi, upload_file
import os, sys, time

DATASET_REPO = "Sachin21112004/DreamFlow-AI-Data"
LOCAL_FILE = "train.jsonl"

# Detect mode from CLI argument
MODE = sys.argv[1].upper() if len(sys.argv) > 1 else "APPEND"
print(f"🔄 Running mode: {MODE}")

# -------- 1. NEW INCOMING DATA (DUMMY SCRAPER) --------
new_record = {
    "timestamp": str(time.time()),
    "text": f"New scraped data at {time.time()}",
}
new_df = pd.DataFrame([new_record])

# API Init
api = HfApi()

# -------- 2. HANDLE APPEND / OVERWRITE LOGIC --------
if MODE == "OVERWRITE":
    print("🗑️ OVERWRITE MODE → Removing old file & starting fresh dataset")

    # Create new dataset file
    new_df.to_json(LOCAL_FILE, lines=True, orient="records")

else:  # APPEND
    print("➕ APPEND MODE → Adding new records")

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
    except Exception:
        print("⚠️ No existing dataset found → starting new.")
        old_df = pd.DataFrame()

    combined_df = pd.concat([old_df, new_df], ignore_index=True)
    combined_df.to_json(LOCAL_FILE, lines=True, orient="records")
    print(f"➕ Added {len(new_df)} rows → Total: {len(combined_df)} rows")

# -------- 3. UPLOAD --------
print("⬆️ Uploading dataset update → HuggingFace Hub...")

upload_file(
    path_or_fileobj=LOCAL_FILE,
    path_in_repo=LOCAL_FILE,
    repo_id=DATASET_REPO,
    repo_type="dataset",
    token=os.environ["HF_TOKEN"]
)

print("✅ Upload complete.")
