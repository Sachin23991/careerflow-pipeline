# pipeline/scrape.py
import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document
import json
import time
from hashlib import sha256
from datetime import datetime

OUT = "pipeline/raw_news.jsonl"

# Curated list of trusted RSS feeds (global, multi-field)
FEEDS = [
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.reuters.com/reuters/businessNews",
    "http://feeds.reuters.com/Reuters/worldNews",
    "https://www.bbc.co.uk/feeds/rss/news/rss.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.theguardian.com/business/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.economist.com/latest/rss.xml",
    "https://www.ft.com/?format=rss",
    "https://www.washingtonpost.com/rss/",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://www.hindustantimes.com/feeds/rss/homepage/rssfeed.xml",
    # Add more trusted feeds here
]

USER_AGENT = "CareerFlowNewsBot/1.0 (+https://example.com)"

def fetch_url(url, timeout=15):
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_full_text(url, html):
    try:
        doc = Document(html)
        content_html = doc.summary()
        soup = BeautifulSoup(content_html, "lxml")
        text = soup.get_text(separator="\n").strip()
        return text
    except Exception:
        # fallback: parse body text with soup
        soup = BeautifulSoup(html, "lxml")
        body = soup.body
        if body:
            return body.get_text(separator="\n").strip()
        return ""

def normalize_item(entry, feed_url):
    url = entry.get("link") or entry.get("id") or ""
    title = entry.get("title", "").strip()
    published = entry.get("published") or entry.get("updated") or ""
    summary = entry.get("summary", "") or entry.get("description", "")
    return {
        "id": sha256((url + title).encode("utf-8")).hexdigest(),
        "url": url,
        "title": title,
        "published": published,
        "summary": BeautifulSoup(summary, "lxml").get_text().strip(),
        "feed": feed_url,
        "scraped_at": datetime.utcnow().isoformat() + "Z"
    }

def main():
    out = open(OUT, "w", encoding="utf-8")
    seen_urls = set()
    for feed in FEEDS:
        try:
            d = feedparser.parse(feed)
        except Exception as e:
            print("Feed parse error:", feed, e)
            continue

        for entry in d.entries:
            try:
                item = normalize_item(entry, feed)
                if not item["url"]:
                    continue
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])

                # fetch article HTML and extract full text
                try:
                    html = fetch_url(item["url"])
                    full_text = extract_full_text(item["url"], html)
                except Exception as e:
                    print("Failed to fetch/extract:", item["url"], e)
                    full_text = item.get("summary", "")

                # ensure minimum length
                if not full_text or len(full_text) < 200:
                    # fallback to summary (some feeds only have summary)
                    full_text = item.get("summary", "")

                # Compose raw payload
                payload = {
                    "id": item["id"],
                    "url": item["url"],
                    "title": item["title"],
                    "published": item["published"],
                    "feed": item["feed"],
                    "scraped_at": item["scraped_at"],
                    "text": full_text
                }

                out.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except Exception as e:
                print("Entry skip error:", e)
        # polite pause
        time.sleep(1)

    out.close()
    print("Saved raw items to", OUT)

if __name__ == "__main__":
    main()
