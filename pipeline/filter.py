import json

keywords = [
    "career","job","hiring","exam","neet","jee","placement",
    "degree","education","upsc","admission","university",
    "salary","intern","skill","technology","course"
]

raw = json.load(open("pipeline/raw_news.json"))
filtered = []

for n in raw:
    text = (n["title"] + " " + n["summary"]).lower()
    if any(k in text for k in keywords):
        filtered.append(n)

with open("pipeline/filtered.json", "w") as f:
    json.dump(filtered, f, indent=2)

