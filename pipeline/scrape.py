import feedparser
import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib

OUTPUT_FILE = "pipeline/raw_news.jsonl"

REQUEST_TIMEOUT = 8   # safe for GitHub Actions

# -------------------------------------------------------
#  ALL CAREER NEWS SOURCES
# -------------------------------------------------------
urls = [

    # -------------------- Education / Exams --------------------
    "https://timesofindia.indiatimes.com/education/rssfeedss.cms",
    "https://www.hindustantimes.com/education/rssfeed",
    "https://indianexpress.com/section/education/feed/",
    "https://www.ndtv.com/education/rss",
    "https://www.jagranjosh.com/rss/latest-news.xml",
    "https://www.jagranjosh.com/rss/exams.xml",
    "https://www.jagranjosh.com/rss/jobs.xml",
    "https://www.freejobalert.com/feed/",

    # -------------------- Government Job Updates --------------------
    "https://www.sarkariresult.com/feed/",
    "https://www.employmentnews.gov.in/RSS.aspx",
    "https://www.upsc.gov.in/whats-new/all/rss",
    "https://pscnotes.in/feed/",

    # -------------------- Tech / IT / Industry Trends --------------------
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "https://gadgets360.com/rss/news",

    # -------------------- Business / Economy --------------------
    "https://economictimes.indiatimes.com/news/economy/rssfeeds/1715249553.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.livemint.com/rss/news",

    # -------------------- Skills / Courses / Certifications --------------------
    "https://www.edx.org/rss",
    "https://www.futurelearn.com/info/blog/feed",

    # Udemy & Coursera do NOT have valid RSS feeds (removed — they hang)
    # "https://www.coursera.org/learn/feed",
    # "https://www.udemy.com/courses/feed/",

    # -------------------- Startups & Entrepreneurship --------------------
    "https://yourstory.com/feed",
    "https://inc42.com/feed/",
    "https://www.startupindia.gov.in/content/sih/en/rss.html",

    # -------------------- International Careers --------------------
    "https://www.studyabroad.com/rss",
    "https://www.scholarshipsads.com/feed/",
    "https://www.opportunitydesk.org/feed/",
]


# -------------------------------------------------------
# Helper: Safe full-text extraction with timeout
# -------------------------------------------------------
def fetch_full_text(url):
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove junk
        for tag in soup(["script", "style", "header", "footer"]):
            tag.extract()

        text = " ".join(t.get_text(" ", strip=True) for t in soup.find_all("p"))
        return text[:2000] if text else None
    except Exception:
        return None


# -------------------------------------------------------
# Safe RSS fetcher + parser
# -------------------------------------------------------
def fetch_feed_safe(url):
    try:
        print(f"⏳ Fetching feed: {url}")
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        return feedparser.parse(resp.content)
    except Exception as e:
        print(f"❌ Feed timeout/failure: {url} ({e})")
        return None


# -------------------------------------------------------
# SCRAPE ALL RSS FEEDS
# -------------------------------------------------------
def scrape_all():
    print("🔍 Scraping latest career news...")

    seen = set()
    all_items = []

    for url in urls:
        feed = fetch_feed_safe(url)
        if not feed or not feed.entries:
            continue

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip()

            if not title or not link:
                continue

            uid = hashlib.md5(link.encode()).hexdigest()
            if uid in seen:
                continue
            seen.add(uid)

            full_text = fetch_full_text(link) or summary

            item = {
                "id": uid,
                "title": title,
                "summary": summary,
                "content": full_text,
                "url": link,
                "timestamp": time.time(),
            }

            all_items.append(item)

    # Save output (overwrite)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for it in all_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"✅ Scraping complete. Saved {len(all_items)} raw articles.")


if __name__ == "__main__":
    scrape_all()
