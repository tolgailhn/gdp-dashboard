"""
Generate tweets in Tolga İlhan's voice using Claude API.

Each article gets its own tweet, written as if Tolga İlhan is commenting
on it personally. Tweets are in Turkish, max 280 characters.
"""

import os
import anthropic

from config import TOLGA_ILHAN_PERSONA
from news_fetcher import Article


def _build_tweet_prompt(article: Article) -> str:
    return f"""
{TOLGA_ILHAN_PERSONA}

Aşağıdaki yapay zeka haberini Tolga İlhan olarak Twitter/X için tek bir tweet'e dönüştür.

Haber:
Başlık: {article.title}
Kaynak: {article.source}
Özet: {article.summary}
URL: {article.url}

Kurallar:
- Maksimum 240 karakter (URL için yer bırak)
- Türkçe yaz
- Kişisel ve özgün bir bakış açısı sun — sadece haberi özetleme, yorum kat
- Sonuna URL'yi ekle
- Sona soru işareti veya düşündürücü bir ifade koyabilirsin
- Fazla hashtag kullanma, varsa 1-2 yeterli (#YapayZeka #AI gibi)

Sadece tweet metnini yaz, başka açıklama ekleme.
""".strip()


def generate_tweet(article: Article, client: anthropic.Anthropic | None = None) -> str:
    """
    Generate a single tweet for the given article in Tolga İlhan's voice.

    Args:
        article: Article to tweet about.
        client: Optional pre-created Anthropic client.

    Returns:
        Tweet text (max 280 chars).
    """
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
        client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[
            {"role": "user", "content": _build_tweet_prompt(article)},
        ],
    )

    tweet = message.content[0].text.strip()

    # Safety truncation
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    return tweet


def generate_tweets(articles: list[Article]) -> list[dict]:
    """
    Generate tweets for a list of articles.

    Args:
        articles: List of articles to process.

    Returns:
        List of dicts with 'article' and 'tweet' keys.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    results = []

    for article in articles:
        try:
            tweet = generate_tweet(article, client=client)
            results.append({"article": article, "tweet": tweet})
            print(f"[OK] Generated tweet for: {article.title[:60]}...")
        except Exception as e:
            print(f"[WARN] Failed to generate tweet for '{article.title[:60]}': {e}")

    return results


if __name__ == "__main__":
    from news_fetcher import fetch_recent_articles
    from config import TOP_N_ARTICLES
    import argparse

    parser = argparse.ArgumentParser(description="Generate tweets in Tolga İlhan's voice")
    parser.add_argument("--hours", type=int, default=24, choices=[6, 12, 24])
    args = parser.parse_args()

    print(f"Fetching top {TOP_N_ARTICLES} AI articles from last {args.hours}h...\n")
    articles = fetch_recent_articles(hours=args.hours)[:TOP_N_ARTICLES]

    if not articles:
        print("No AI articles found.")
    else:
        results = generate_tweets(articles)
        print("\n--- Generated Tweets ---\n")
        for i, r in enumerate(results, 1):
            print(f"Tweet {i}:")
            print(r["tweet"])
            print(f"({len(r['tweet'])} chars)\n")
