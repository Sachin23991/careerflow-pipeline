from huggingface_hub import HfApi
import os

api = HfApi()
repo_id = "Sachin21112004/DreamFlow-AI-Data"


api.upload_file(
    path_or_fileobj="pipeline/train.jsonl",
    path_in_repo="train.jsonl",
    repo_id=repo_id,
    repo_type="dataset",
    token=os.environ["HF_TOKEN"]
)
