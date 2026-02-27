"""
AI News Twitter Bot - Main Orchestrator

Fetches recent AI news, selects the most important articles,
rewrites them in Tolga İlhan's voice, and posts to Twitter/X.

Usage:
    python main.py                    # Run with defaults (last 24h, post live)
    python main.py --hours 6          # Last 6 hours only
    python main.py --hours 12         # Last 12 hours
    python main.py --dry-run          # Preview tweets without posting
    python main.py --dry-run --hours 6
"""

import argparse
import sys
from datetime import datetime, timezone

from news_fetcher import fetch_recent_articles
from tweet_writer import generate_tweets
from twitter_poster import post_tweets
from config import TOP_N_ARTICLES


def run(hours: int = 24, dry_run: bool = False) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{now}] Starting AI News Twitter Bot")
    print(f"  Mode    : {'DRY RUN (no posting)' if dry_run else 'LIVE'}")
    print(f"  Window  : Last {hours} hours")
    print(f"  Articles: Top {TOP_N_ARTICLES}\n")

    # 1. Fetch articles
    print("Step 1/3: Fetching AI news...")
    articles = fetch_recent_articles(hours=hours)

    if not articles:
        print("No AI articles found in this time window. Exiting.")
        sys.exit(0)

    selected = articles[:TOP_N_ARTICLES]
    print(f"  Found {len(articles)} articles, selected top {len(selected)}:")
    for i, a in enumerate(selected, 1):
        print(f"  {i}. [{a.source}] {a.title[:70]}...")

    # 2. Generate tweets in Tolga İlhan's voice
    print("\nStep 2/3: Generating tweets via Claude (Tolga İlhan sesi)...")
    tweet_results = generate_tweets(selected)

    if not tweet_results:
        print("No tweets generated. Exiting.")
        sys.exit(1)

    tweet_texts = [r["tweet"] for r in tweet_results]

    # 3. Post to Twitter
    print(f"\nStep 3/3: {'Previewing' if dry_run else 'Posting'} tweets...\n")
    post_results = post_tweets(tweet_texts, dry_run=dry_run)

    # Summary
    print("\n--- Summary ---")
    print(f"Articles fetched : {len(articles)}")
    print(f"Tweets generated : {len(tweet_results)}")
    posted = sum(1 for r in post_results if "error" not in r)
    print(f"Tweets posted    : {posted}/{len(tweet_texts)}")

    if not dry_run:
        for r in post_results:
            if "url" in r and r["url"] != "N/A (dry run)":
                print(f"  -> {r['url']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI News Twitter Bot - Post AI news as Tolga İlhan"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        choices=[6, 12, 24],
        help="Time window for news (default: 24)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview tweets without posting to Twitter",
    )
    args = parser.parse_args()

    run(hours=args.hours, dry_run=args.dry_run)
