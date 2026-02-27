"""
Deep Research Module
Gathers context from web search and Twitter before writing tweets.
Flow: Tweet URL → Fetch tweet → Web search → Twitter search → Compile research → Generate tweet
"""
import re
import datetime
from dataclasses import dataclass, field
from duckduckgo_search import DDGS


@dataclass
class ResearchResult:
    """Compiled research data for tweet generation"""
    original_tweet_text: str = ""
    original_tweet_author: str = ""
    original_tweet_id: str = ""
    web_results: list = field(default_factory=list)
    related_tweets: list = field(default_factory=list)
    summary: str = ""


def extract_tweet_id(url_or_id: str) -> str | None:
    """Extract tweet ID from a URL or raw ID string"""
    url_or_id = url_or_id.strip()

    # Direct ID
    if url_or_id.isdigit():
        return url_or_id

    # URL patterns: x.com/user/status/123 or twitter.com/user/status/123
    match = re.search(r'(?:twitter\.com|x\.com)/\w+/status/(\d+)', url_or_id)
    if match:
        return match.group(1)

    return None


def web_search(query: str, max_results: int = 8) -> list[dict]:
    """
    Search the web using DuckDuckGo (free, no API key needed)

    Returns list of {title, url, body}
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "body": r.get("body", ""),
                })
    except Exception as e:
        print(f"Web search error: {e}")

    return results


def web_search_news(query: str, max_results: int = 5) -> list[dict]:
    """Search recent news using DuckDuckGo"""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "body": r.get("body", ""),
                    "date": r.get("date", ""),
                    "source": r.get("source", ""),
                })
    except Exception as e:
        print(f"News search error: {e}")

    return results


def extract_keywords_from_tweet(tweet_text: str) -> list[str]:
    """Extract meaningful search keywords from a tweet"""
    # Remove URLs
    text = re.sub(r'https?://\S+', '', tweet_text)
    # Remove mentions
    text = re.sub(r'@\w+', '', text)
    # Remove hashtags but keep the word
    text = re.sub(r'#(\w+)', r'\1', text)
    # Remove emoji
    text = re.sub(r'[^\w\s\-./]', '', text)

    # Known AI terms to prioritize
    ai_terms = [
        "GPT", "Claude", "Gemini", "Llama", "Qwen", "Mistral", "DeepSeek",
        "MiniMax", "OpenAI", "Anthropic", "Google", "Meta", "Microsoft",
        "AI", "LLM", "model", "benchmark", "open-source", "fine-tuning",
        "reasoning", "coding", "multimodal", "AGI", "transformer", "agent",
        "SOTA", "release", "launch", "update", "API", "token", "context",
    ]

    # Find AI terms present in text
    found_terms = []
    for term in ai_terms:
        if term.lower() in text.lower():
            found_terms.append(term)

    # Get remaining significant words (>3 chars)
    words = text.split()
    significant = [w for w in words if len(w) > 3 and w.lower() not in
                   {"this", "that", "with", "from", "have", "been", "will",
                    "just", "about", "more", "than", "very", "also", "some",
                    "into", "they", "their", "there", "here", "what", "when",
                    "like", "been", "does", "didn", "isn", "aren"}]

    # Combine: AI terms first, then significant words
    keywords = found_terms + [w for w in significant if w not in found_terms]
    return keywords[:8]


def research_topic(tweet_text: str, tweet_author: str = "",
                   tweet_id: str = "", scanner=None,
                   progress_callback=None) -> ResearchResult:
    """
    Perform deep research on a tweet topic.

    Args:
        tweet_text: The original tweet text
        tweet_author: Author username
        tweet_id: Tweet ID (if available)
        scanner: TwitterScanner instance (optional, for Twitter search)
        progress_callback: Callable for progress updates (streamlit spinner text)

    Returns:
        ResearchResult with all gathered context
    """
    result = ResearchResult(
        original_tweet_text=tweet_text,
        original_tweet_author=tweet_author,
        original_tweet_id=tweet_id,
    )

    keywords = extract_keywords_from_tweet(tweet_text)
    search_query = " ".join(keywords[:5])

    # Step 1: Web search for general context
    if progress_callback:
        progress_callback("Web'de araştırılıyor...")

    web_results = web_search(f"{search_query} AI", max_results=6)
    result.web_results.extend(web_results)

    # Step 2: News search for recent developments
    if progress_callback:
        progress_callback("Son haberler taranıyor...")

    news_results = web_search_news(search_query, max_results=4)
    for nr in news_results:
        result.web_results.append({
            "title": f"[HABER] {nr['title']}",
            "url": nr["url"],
            "body": nr["body"],
            "source": nr.get("source", ""),
        })

    # Step 3: Search Twitter for related tweets (if scanner available)
    if scanner and progress_callback:
        progress_callback("X'te ilgili tweet'ler aranıyor...")

    if scanner:
        try:
            search_q = f"({' OR '.join(keywords[:3])}) -is:retweet lang:en"
            start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)
            related = scanner._search_tweets(search_q, start_time, 10)
            # Filter out the original tweet and low-quality ones
            for t in related:
                if t.id != tweet_id and len(t.text) > 50:
                    result.related_tweets.append({
                        "text": t.text,
                        "author": t.author_username,
                        "likes": t.like_count,
                        "url": t.url,
                    })
            # Sort by engagement
            result.related_tweets.sort(key=lambda x: x["likes"], reverse=True)
            result.related_tweets = result.related_tweets[:5]
        except Exception as e:
            print(f"Twitter search error: {e}")

    # Step 4: Compile summary
    if progress_callback:
        progress_callback("Araştırma derleniyor...")

    result.summary = compile_research_summary(result)

    return result


def compile_research_summary(research: ResearchResult) -> str:
    """Compile all research into a structured summary for the AI"""
    parts = []

    parts.append(f"## Orijinal Tweet\n@{research.original_tweet_author}: \"{research.original_tweet_text}\"")

    if research.web_results:
        parts.append("\n## Web Araştırma Sonuçları")
        for i, wr in enumerate(research.web_results[:8], 1):
            source = wr.get("source", "")
            source_str = f" ({source})" if source else ""
            parts.append(f"{i}. **{wr['title']}**{source_str}\n   {wr['body'][:200]}")

    if research.related_tweets:
        parts.append("\n## İlgili X/Twitter Paylaşımları")
        for i, rt in enumerate(research.related_tweets[:5], 1):
            parts.append(f"{i}. @{rt['author']} ({rt['likes']} beğeni): \"{rt['text'][:150]}\"")

    return "\n".join(parts)
