# pipeline/scrape.py
import feedparser, requests, time, json
from readability import Document
from bs4 import BeautifulSoup
from hashlib import sha256
from datetime import datetime
from pathlib import Path

OUT = Path("pipeline/raw_news.jsonl")
FEEDS = [
    # Global trusted
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.reuters.com/reuters/businessNews",
    "http://feeds.reuters.com/Reuters/worldNews",
    "https://www.bbc.co.uk/feeds/rss/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.xml",
    # India
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://www.hindustantimes.com/feeds/rss/homepage/rssfeed.xml",
    # Add more trusted feeds you trust
]

USER_AGENT = "CareerFlowNewsBot/1.0 (https://your.domain)"

def safe_get(url, timeout=12):
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_text_from_html(html):
    try:
        doc = Document(html)
        summary = doc.summary()
        soup = BeautifulSoup(summary, "lxml")
        txt = soup.get_text(separator="\n").strip()
        if txt:
            return txt
    except Exception:
        pass
    # fallback: naive body extraction
    soup = BeautifulSoup(html, "lxml")
    if soup.body:
        return soup.body.get_text(separator="\n").strip()
    return ""

def normalize_entry(entry):
    url = entry.get("link") or entry.get("id") or ""
    title = entry.get("title", "").strip()
    published = entry.get("published") or entry.get("updated") or ""
    summary = entry.get("summary") or entry.get("description") or ""
    uid = sha256((url + title).encode("utf-8")).hexdigest()
    return {
        "id": uid,
        "url": url,
        "title": title,
        "published": published,
        "summary": BeautifulSoup(summary, "lxml").get_text().strip()
    }

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen_urls = set()
    with OUT.open("w", encoding="utf-8") as out:
        for feed in FEEDS:
            try:
                d = feedparser.parse(feed)
            except Exception as e:
                print("Feed error:", feed, e)
                continue
            for e in d.entries:
                try:
                    it = normalize_entry(e)
                    url = it["url"]
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    # try to fetch full article
                    try:
                        html = safe_get(url, timeout=10)
                        text = extract_text_from_html(html)
                    except Exception as ex:
                        print("Fetch fail:", url, ex)
                        text = it.get("summary","")
                    if not text:
                        continue
                    payload = {
                        "id": it["id"],
                        "url": url,
                        "title": it["title"],
                        "published": it["published"],
                        "scraped_at": datetime.utcnow().isoformat() + "Z",
                        "text": text
                    }
                    out.write(json.dumps(payload, ensure_ascii=False) + "\n")
                except Exception as e:
                    print("Entry skip", e)
            time.sleep(0.8)
    print("done: wrote raw_news.jsonl")

if __name__ == "__main__":
    main()
