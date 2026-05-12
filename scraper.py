import json
import feedparser
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from pathlib import Path

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


def _load_preferences() -> dict:
    prefs_path = Path(__file__).parent / "preferences.json"
    if prefs_path.exists():
        with open(prefs_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _is_recent(entry) -> bool:
    try:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if pub is None:
            return True
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


def _score_article(article: dict, prefs: dict) -> int:
    """Higher score = shown first. Excluded articles get -999."""
    text = (article["title"] + " " + article["summary"]).lower()
    source = article["source"]

    excluded_kw = [k.lower() for k in prefs.get("excluded_keywords", [])]
    if any(kw in text for kw in excluded_kw):
        return -999

    excluded_src = [s.lower() for s in prefs.get("excluded_sources", [])]
    if any(s in source.lower() for s in excluded_src):
        return -999

    score = 0
    preferred_kw = [k.lower() for k in prefs.get("preferred_keywords", [])]
    score += sum(3 for kw in preferred_kw if kw in text)

    preferred_src = [s.lower() for s in prefs.get("preferred_sources", [])]
    score += sum(2 for s in preferred_src if s in source.lower())

    return score


def fetch_aviation_news(max_per_feed: int = 5, total_max: int = 12) -> list[dict]:
    prefs = _load_preferences()
    seen_titles = set()
    articles = []

    for feed_cfg in NEWS_FEEDS:
        if any(feed_cfg["name"].lower() == s.lower() for s in prefs.get("excluded_sources", [])):
            continue
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

            article = {
                "source": feed_cfg["name"],
                "title": title,
                "summary": _clean_summary(entry.get("summary", "")),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            }
            article["_score"] = _score_article(article, prefs)

            if article["_score"] == -999:
                continue

            articles.append(article)
            count += 1

    # Sort by preference score (highest first), then trim
    articles.sort(key=lambda a: a["_score"], reverse=True)
    return articles[:total_max]
