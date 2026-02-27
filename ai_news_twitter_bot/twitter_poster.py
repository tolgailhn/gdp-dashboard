"""Post tweets to Twitter/X using Tweepy v2."""

import os
import tweepy


def get_twitter_client() -> tweepy.Client:
    """Create and return a Tweepy v2 client using environment variables."""
    required = {
        "TWITTER_API_KEY": os.environ.get("TWITTER_API_KEY"),
        "TWITTER_API_SECRET": os.environ.get("TWITTER_API_SECRET"),
        "TWITTER_ACCESS_TOKEN": os.environ.get("TWITTER_ACCESS_TOKEN"),
        "TWITTER_ACCESS_SECRET": os.environ.get("TWITTER_ACCESS_SECRET"),
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Missing Twitter credentials: {', '.join(missing)}")

    return tweepy.Client(
        consumer_key=required["TWITTER_API_KEY"],
        consumer_secret=required["TWITTER_API_SECRET"],
        access_token=required["TWITTER_ACCESS_TOKEN"],
        access_token_secret=required["TWITTER_ACCESS_SECRET"],
    )


def post_tweet(text: str) -> dict:
    """
    Post a single tweet.

    Args:
        text: Tweet content (max 280 chars).

    Returns:
        Dict with tweet id and url.
    """
    client = get_twitter_client()
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return {
        "id": tweet_id,
        "text": text,
        "url": f"https://x.com/i/web/status/{tweet_id}",
    }


def post_tweets(tweet_texts: list[str], dry_run: bool = False) -> list[dict]:
    """
    Post multiple tweets.

    Args:
        tweet_texts: List of tweet content strings.
        dry_run: If True, print instead of posting.

    Returns:
        List of result dicts.
    """
    results = []

    if dry_run:
        for i, text in enumerate(tweet_texts, 1):
            print(f"\n[DRY RUN] Tweet {i}/{len(tweet_texts)}:")
            print(text)
            print(f"({len(text)} chars)")
            results.append({"id": f"dry_run_{i}", "text": text, "url": "N/A (dry run)"})
        return results

    for i, text in enumerate(tweet_texts, 1):
        try:
            result = post_tweet(text)
            print(f"[OK] Posted tweet {i}/{len(tweet_texts)}: {result['url']}")
            results.append(result)
        except tweepy.TweepyException as e:
            print(f"[ERROR] Failed to post tweet {i}: {e}")
            results.append({"error": str(e), "text": text})

    return results
