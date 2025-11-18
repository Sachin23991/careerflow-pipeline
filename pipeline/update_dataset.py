import pandas as pd
from huggingface_hub import HfApi, upload_file
import os, sys, time

DATASET_REPO = "Sachin21112004/DreamFlow-AI-Data"
LOCAL_FILE = "train.jsonl"

# Detect mode (APPEND or OVERWRITE)
MODE = sys.argv[1].upper() if len(sys.argv) > 1 else "APPEND"
print(f"🔄 Running mode: {MODE}")

# -------- 1. NEW INCOMING DATA (Your real scraper goes here) --------
new_record = {
    "timestamp": str(time.time()),
    "text": f"New scraped data at {time.time()}",
}
new_df = pd.DataFrame([new_record])

api = HfApi()

# -------- 2. APPEND / OVERWRITE MODE --------
if MODE == "OVERWRITE":
    print("🗑️ OVERWRITE MODE → Starting fresh dataset")
    df = new_df

else:
    print("➕ APPEND MODE → Downloading and merging old + new data")
    try:
        api.hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            filename=LOCAL_FILE,
            local_dir=".",
            token=os.environ["HF_TOKEN"]
        )
        old_df = pd.read_json(LOCAL_FILE, lines=True)
        print(f"Loaded {len(old_df)} existing rows.")
    except Exception:
        print("⚠️ No existing file found → starting new")
        old_df = pd.DataFrame()

    df = pd.concat([old_df, new_df], ignore_index=True)
    print(f"📌 Raw combined rows: {len(df)}")

# -------- 3. AUTO CLEAN + DEDUPLICATION --------
print("🧹 Cleaning dataset...")

# Remove rows where 'text' is empty, None, or whitespace
df['text'] = df['text'].astype(str)
df = df[df['text'].str.strip() != ""]

# Remove exact duplicate rows
df = df.drop_duplicates()

# Remove duplicates based on "text"
df = df.drop_duplicates(subset=["text"])

# Remove duplicates based on timestamp
df = df.drop_duplicates(subset=["timestamp"])

# Optional: Keep only last 20,000 rows (log cleanup)
MAX_ROWS = 20000
if len(df) > MAX_ROWS:
    df = df.iloc[-MAX_ROWS:]
    print(f"🧽 Cleanup: Trimmed to last {MAX_ROWS} rows.")

print(f"✅ Cleaned rows: {len(df)}")

# -------- 4. SAVE & UPLOAD --------
df.to_json(LOCAL_FILE, lines=True, orient="records")

print("⬆️ Uploading cleaned dataset...")
upload_file(
    path_or_fileobj=LOCAL_FILE,
    path_in_repo=LOCAL_FILE,
    repo_id=DATASET_REPO,
    repo_type="dataset",
    token=os.environ["HF_TOKEN"]
)

print("🎉 Dataset cleaned, deduped & uploaded successfully!")
