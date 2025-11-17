import feedparser
import json

RSS = [
    # -----------------------------
    # EDUCATION & EXAMS (Core)
    # -----------------------------
    "https://timesofindia.indiatimes.com/education/rssfeedss.cms",
    "https://www.hindustantimes.com/education/rssfeed",
    "https://indianexpress.com/section/education/feed/",
    "https://www.ndtv.com/education/rss",
    "https://www.jagranjosh.com/rss/latest-news.xml",
    "https://www.jagranjosh.com/rss/exams.xml",
    "https://www.jagranjosh.com/rss/jobs.xml",
    "https://www.freejobalert.com/feed/",

    # -----------------------------
    # GOVERNMENT JOBS & OPPORTUNITIES
    # -----------------------------
    "https://www.sarkariresult.com/feed/",
    "https://www.employmentnews.gov.in/RSS.aspx",   # Official Govt News
    "https://www.upsc.gov.in/whats-new/all/rss",
    "https://www.staff-selection-commission.in/rss", 
    "https://pscnotes.in/feed/",

    # -----------------------------
    # IT / TECH CAREER NEWS
    # -----------------------------
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "https://gadgets360.com/rss/news",

    # -----------------------------
    # BUSINESS / ECONOMY (Affects career growth)
    # -----------------------------
    "https://economictimes.indiatimes.com/news/economy/rssfeeds/1715249553.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.livemint.com/rss/news",

    # -----------------------------
    # SKILLS, CERTIFICATIONS, COURSES
    # (Skill-based career improvements)
    # -----------------------------
    "https://www.coursera.org/learn/feed",
    "https://www.udemy.com/courses/feed/",
    "https://www.edx.org/rss", 
    "https://www.futurelearn.com/info/blog/feed",

    # -----------------------------
    # STARTUP / ENTREPRENEURSHIP JOBS
    # -----------------------------
    "https://yourstory.com/feed",
    "https://inc42.com/feed/",
    "https://www.startupindia.gov.in/content/sih/en/rss.html",

    # -----------------------------
    # INTERNATIONAL CAREERS
    # -----------------------------
    "https://www.studyabroad.com/rss",
    "https://www.scholarshipsads.com/feed/",
    "https://www.opportunitiesforafricans.com/feed/",
    "https://www.opportunitydesk.org/feed/",
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
