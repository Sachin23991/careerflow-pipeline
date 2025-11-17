from huggingface_hub import upload_file
import os

DATASET_REPO = "Sachin21112004/DreamFlow-AI-Data"
TRAIN_FILE = "pipeline/train.jsonl"

def push_to_hf():
    print("⬆️ Uploading updated dataset to HuggingFace...")

    upload_file(
        path_or_fileobj=TRAIN_FILE,
        path_in_repo="train.jsonl",
        repo_id=DATASET_REPO,
        token=os.getenv("HF_TOKEN")
    )

    print("🎉 Dataset uploaded successfully!")

if __name__ == "__main__":
    push_to_hf()
