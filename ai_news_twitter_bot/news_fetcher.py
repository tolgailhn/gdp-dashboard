"""Fetch recent AI news from RSS feeds."""

import feedparser
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from config import AI_NEWS_FEEDS, AI_KEYWORDS


@dataclass
class Article:
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    relevance_score: float = 0.0
    tags: list[str] = field(default_factory=list)


def _parse_published(entry) -> datetime | None:
    """Extract publication datetime from a feed entry."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        value = getattr(entry, attr, None)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def _is_ai_related(title: str, summary: str) -> tuple[bool, list[str]]:
    """Check if an article is AI-related and return matched keywords."""
    text = (title + " " + summary).lower()
    matched = [kw for kw in AI_KEYWORDS if kw in text]
    return bool(matched), matched


def _score_article(title: str, summary: str, matched_keywords: list[str]) -> float:
    """Score article relevance (higher = more important)."""
    score = len(matched_keywords) * 1.0

    # Bonus for high-signal words
    high_signal = [
        "breakthrough", "launch", "release", "announce", "new model",
        "state of the art", "sota", "beats", "surpasses", "acqui",
        "funding", "billion", "open source", "gpt-5", "claude 4",
        "gemini", "regulation", "ban", "law",
    ]
    text = (title + " " + summary).lower()
    score += sum(2.0 for hw in high_signal if hw in text)

    # Title matches are weighted more
    title_lower = title.lower()
    score += sum(1.5 for kw in AI_KEYWORDS if kw in title_lower)

    return score


def fetch_recent_articles(hours: int = 24) -> list[Article]:
    """
    Fetch AI news articles published within the last `hours` hours.

    Args:
        hours: Time window in hours (6, 12, or 24 recommended).

    Returns:
        List of Article objects sorted by relevance score descending.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles: list[Article] = []

    for feed_url in AI_NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": "ai-news-bot/1.0"})
            source = feed.feed.get("title", feed_url)

            for entry in feed.entries:
                published = _parse_published(entry)
                if published is None or published < cutoff:
                    continue

                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                url = entry.get("link", "")

                if not title or not url:
                    continue

                is_ai, matched_keywords = _is_ai_related(title, summary)
                if not is_ai:
                    continue

                score = _score_article(title, summary, matched_keywords)

                articles.append(
                    Article(
                        title=title,
                        summary=summary[:500],  # Truncate long summaries
                        url=url,
                        source=source,
                        published_at=published,
                        relevance_score=score,
                        tags=matched_keywords,
                    )
                )

            time.sleep(0.3)  # Polite crawling
        except Exception as e:
            print(f"[WARN] Failed to fetch {feed_url}: {e}")
            continue

    # Deduplicate by URL, sort by relevance
    seen_urls: set[str] = set()
    unique_articles: list[Article] = []
    for article in sorted(articles, key=lambda a: a.relevance_score, reverse=True):
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)

    return unique_articles


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch recent AI news")
    parser.add_argument("--hours", type=int, default=24, choices=[6, 12, 24])
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    print(f"Fetching AI news from the last {args.hours} hours...\n")
    articles = fetch_recent_articles(hours=args.hours)

    print(f"Found {len(articles)} AI-related articles.\n")
    for i, a in enumerate(articles[: args.top], 1):
        print(f"{i}. [{a.source}] {a.title}")
        print(f"   Score: {a.relevance_score:.1f} | Published: {a.published_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   URL: {a.url}\n")
