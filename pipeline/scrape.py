import feedparser
import json

RSS = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://timesofindia.indiatimes.com/rss.cms",
]

items = []
for url in RSS:
    feed = feedparser.parse(url)
    for e in feed.entries:
        items.append({
            "title": e.title,
            "summary": e.get("summary", ""),
            "link": e.link
        })

with open("pipeline/raw_news.json", "w") as f:
    json.dump(items, f, indent=2)
