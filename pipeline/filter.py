import json
import re

RAW_FILE = "pipeline/raw_news.jsonl"
FILTERED_FILE = "pipeline/filtered_news.jsonl"

# Keywords to keep — career relevant
keep_keywords = [
    "exam", "result", "admission", "upsc", "ssc", "govt job", "government job",
    "hiring", "salary", "layoff", "career", "recruitment", "vacancy",
    "neet", "jee", "education", "university", "college", "course",
    "certificate", "scholarship", "abroad", "master", "btech", "mtech",
    "skills", "internship", "training", "job", "employment",
    "startup", "industry", "technology", "ai", "machine learning",
    "data science", "developer", "economy", "business",
]

# Blacklist (remove irrelevant content)
remove_keywords = [
    "crime", "murder", "politics", "election",
    "bollywood", "actor", "actress",
    "sports", "football", "cricket",
    "weather", "flood", "earthquake",
]


def is_career_related(text):
    text_l = text.lower()

    if any(bad in text_l for bad in remove_keywords):
        return False

    return any(k in text_l for k in keep_keywords)


# -------------------------------------------------------
# Filter out irrelevant news
# -------------------------------------------------------
def filter_news():
    print("🎯 Filtering news to keep only career-related items...")

    filtered = []

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            combined_text = (
                item["title"] + " " + item["summary"] + " " + item["content"]
            ).lower()

            if is_career_related(combined_text):
                filtered.append(item)

    with open(FILTERED_FILE, "w", encoding="utf-8") as f:
        for it in filtered:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"✅ Filtering complete. Kept {len(filtered)} useful career articles.")


if __name__ == "__main__":
    filter_news()
