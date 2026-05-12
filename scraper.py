import feedparser
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# Aviation-focused RSS feeds
NEWS_FEEDS = [
    {
        "name": "Simple Flying",
        "url": "https://simpleflying.com/feed/",
    },
    {
        "name": "AirlineGeeks",
        "url": "https://airlinegeeks.com/feed/",
    },
    {
        "name": "The Points Guy",
        "url": "https://thepointsguy.com/feed/",
        "keywords": ["airline", "aviation", "flight", "aircraft", "airport", "boeing", "airbus"],
    },
    {
        "name": "Reuters Business (aviation filter)",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "keywords": ["airline", "aviation", "aircraft", "airport", "boeing", "airbus", "iata", "faa", "easa"],
    },
    {
        "name": "Google News – Airline",
        "url": "https://news.google.com/rss/search?q=airline&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Google News – Aviation",
        "url": "https://news.google.com/rss/search?q=aviation&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Aviation Week",
        "url": "https://aviationweek.com/rss.xml",
    },
]

AVIATION_KEYWORDS = [
    "airline", "airlines", "aviation", "aircraft", "airport", "flight",
    "boeing", "airbus", "embraer", "bombardier", "iata", "faa", "easa",
    "runway", "pilot", "cabin crew", "fleet", "route", "cargo", "jetblue",
    "delta", "united", "american airlines", "southwest", "ryanair", "easyjet",
    "lufthansa", "air france", "british airways", "emirates", "qatar airways",
    "singapore airlines", "cathay", "aeromexico", "latam", "avianca",
]

HOURS_BACK = 24


def _is_recent(entry) -> bool:
    try:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if pub is None:
            return True  # include if no date available
        pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
        return pub_dt >= cutoff
    except Exception:
        return True


def _is_aviation_relevant(entry, feed_keywords=None) -> bool:
    text = (
        (entry.get("title") or "") + " " + (entry.get("summary") or "")
    ).lower()
    keywords = feed_keywords or AVIATION_KEYWORDS
    return any(kw in text for kw in keywords)


def _clean_summary(raw: str, max_chars: int = 300) -> str:
    soup = BeautifulSoup(raw or "", "html.parser")
    text = soup.get_text(separator=" ").strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"
    return text


def fetch_aviation_news(max_per_feed: int = 5, total_max: int = 12) -> list[dict]:
    seen_titles = set()
    articles = []

    for feed_cfg in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
        except Exception as e:
            print(f"  [scraper] Could not fetch {feed_cfg['name']}: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= max_per_feed:
                break
            if not _is_recent(entry):
                continue
            if not _is_aviation_relevant(entry, feed_cfg.get("keywords")):
                continue

            title = (entry.get("title") or "").strip()
            if not title or title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            articles.append({
                "source": feed_cfg["name"],
                "title": title,
                "summary": _clean_summary(entry.get("summary", "")),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            })
            count += 1

        if len(articles) >= total_max:
            break

    # Deduplicate further by very similar titles
    return articles[:total_max]
