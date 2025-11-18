import pandas as pd
from huggingface_hub import HfApi, upload_file
import os, sys, time

DATASET_REPO = "Sachin21112004/DreamFlow-AI-Data"

LOCAL_FILE = "train.jsonl"

# detect mode based on GitHub CRON
mode = sys.argv[1] if len(sys.argv) > 1 else "APPEND"
print("Mode:", mode)

# -------- 1. NEW DATA (your scraper/filter pipeline must generate this) --------
# For now we simulate 1-row data to demonstrate
new_record = {
    "timestamp": str(time.time()),
    "text": f"New scraped data at {time.time()}",
}
new_df = pd.DataFrame([new_record])

# -------- 2. APPEND MODE (default every 40min) --------
if mode == "APPEND":
    print("➕ Appending new data to dataset...")

    # Try downloading existing dataset
    api = HfApi()
    try:
        api.hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            filename=LOCAL_FILE,
            local_dir=".",
            token=os.environ["HF_TOKEN"]
        )
        old_df = pd.read_json(LOCAL_FILE, lines=True)
    except:
        print("No old dataset found, starting fresh.")
        old_df = pd.DataFrame()

    combined = pd.concat([old_df, new_df], ignore_index=True)
    combined.to_json(LOCAL_FILE, lines=True, orient="records")

# -------- 3. OVERWRITE MODE (daily at 00:00) --------
else:
    print("📌 Daily overwrite: replacing full dataset")
    new_df.to_json(LOCAL_FILE, lines=True, orient="records")

# -------- 4. Upload to HuggingFace Dataset Repo --------
upload_file(
    path_or_fileobj=LOCAL_FILE,
    path_in_repo=LOCAL_FILE,
    repo_id=DATASET_REPO,
    repo_type="dataset",
    token=os.environ["HF_TOKEN"]
)

print("✅ Dataset updated successfully.")
