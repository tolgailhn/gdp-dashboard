"""
Twitter Automation for GDP Dashboard

This module provides Twitter/X automation functionality to share GDP insights.
Uses Tweepy with Twitter API v2.

Required environment variables:
    TWITTER_API_KEY         - Twitter API Key (Consumer Key)
    TWITTER_API_SECRET      - Twitter API Key Secret (Consumer Secret)
    TWITTER_ACCESS_TOKEN    - Twitter Access Token
    TWITTER_ACCESS_SECRET   - Twitter Access Token Secret
    TWITTER_BEARER_TOKEN    - Twitter Bearer Token (for read-only ops)
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime


def get_gdp_data() -> pd.DataFrame:
    """Load and transform GDP data from CSV."""
    DATA_FILENAME = Path(__file__).parent / "data/gdp_data.csv"
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    gdp_df = raw_gdp_df.melt(
        ["Country Code"],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        "Year",
        "GDP",
    )
    gdp_df["Year"] = pd.to_numeric(gdp_df["Year"])
    return gdp_df


def get_top_gdp_countries(gdp_df: pd.DataFrame, year: int = 2022, top_n: int = 5) -> pd.DataFrame:
    """Return top N countries by GDP for a given year."""
    year_data = gdp_df[gdp_df["Year"] == year].dropna(subset=["GDP"])
    return year_data.nlargest(top_n, "GDP")[["Country Code", "GDP"]]


def generate_gdp_tweet(
    countries: list[str] | None = None,
    year: int = 2022,
    include_growth: bool = True,
) -> str:
    """
    Generate a tweet about GDP data.

    Args:
        countries: List of country codes to include. If None, uses top 5.
        year: Year to report on.
        include_growth: Whether to include growth comparison from 1960.

    Returns:
        Tweet text (max 280 characters).
    """
    gdp_df = get_gdp_data()

    if countries:
        year_data = gdp_df[
            (gdp_df["Year"] == year) & (gdp_df["Country Code"].isin(countries))
        ].dropna(subset=["GDP"])
    else:
        year_data = get_top_gdp_countries(gdp_df, year=year, top_n=5)
        countries = year_data["Country Code"].tolist()

    lines = [f"📊 Global GDP Snapshot ({year})"]

    for _, row in year_data.iterrows():
        code = row["Country Code"]
        gdp_b = row["GDP"] / 1_000_000_000

        if include_growth and year > 1960:
            start_data = gdp_df[
                (gdp_df["Year"] == 1960) & (gdp_df["Country Code"] == code)
            ]["GDP"]
            if not start_data.empty and not pd.isna(start_data.iat[0]):
                growth = row["GDP"] / start_data.iat[0]
                lines.append(f"• {code}: ${gdp_b:,.0f}B ({growth:.1f}x since 1960)")
            else:
                lines.append(f"• {code}: ${gdp_b:,.0f}B")
        else:
            lines.append(f"• {code}: ${gdp_b:,.0f}B")

    lines.append("")
    lines.append("Data: World Bank Open Data")
    lines.append("#GDP #Economics #WorldBank #Data")

    tweet = "\n".join(lines)

    # Truncate if over 280 chars
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    return tweet


def post_tweet(text: str) -> dict:
    """
    Post a tweet using Twitter API v2 via Tweepy.

    Args:
        text: Tweet text (max 280 characters).

    Returns:
        Dict with tweet id and text on success, or error info.

    Raises:
        ImportError: If tweepy is not installed.
        ValueError: If API credentials are missing.
    """
    try:
        import tweepy  # noqa: PLC0415
    except ImportError as e:
        raise ImportError(
            "tweepy is required for Twitter posting. Install it with: pip install tweepy"
        ) from e

    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET")

    missing = [
        name
        for name, val in {
            "TWITTER_API_KEY": api_key,
            "TWITTER_API_SECRET": api_secret,
            "TWITTER_ACCESS_TOKEN": access_token,
            "TWITTER_ACCESS_SECRET": access_secret,
        }.items()
        if not val
    ]
    if missing:
        raise ValueError(f"Missing Twitter API credentials: {', '.join(missing)}")

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )

    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return {"id": tweet_id, "text": text, "url": f"https://x.com/i/web/status/{tweet_id}"}


def post_daily_gdp_update(countries: list[str] | None = None) -> dict:
    """
    Generate and post a daily GDP update tweet.

    Args:
        countries: Optional list of country codes. Uses top 5 if not provided.

    Returns:
        Result dict from post_tweet().
    """
    tweet_text = generate_gdp_tweet(countries=countries)
    print(f"[{datetime.now().isoformat()}] Posting tweet:\n{tweet_text}\n")
    result = post_tweet(tweet_text)
    print(f"[{datetime.now().isoformat()}] Tweet posted: {result['url']}")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GDP Twitter Automation")
    parser.add_argument(
        "--countries",
        nargs="*",
        help="Country codes to include (e.g. USA CHN DEU). Defaults to top 5.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview the tweet without posting it.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2022,
        help="Year to report on (default: 2022).",
    )
    args = parser.parse_args()

    tweet_text = generate_gdp_tweet(countries=args.countries, year=args.year)

    if args.preview:
        print("--- Tweet Preview ---")
        print(tweet_text)
        print(f"\nLength: {len(tweet_text)}/280 characters")
    else:
        result = post_daily_gdp_update(countries=args.countries)
        print(f"Success! Tweet URL: {result['url']}")
