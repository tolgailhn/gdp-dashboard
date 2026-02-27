"""
Deep Research Module
Gathers context from web search and Twitter before writing tweets.
Flow: Tweet URL → Fetch tweet → Extract topic → Web search → Twitter search → Generate
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
    topic: str = ""
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
    """Search the web using DuckDuckGo (free, no API key needed)"""
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


def extract_topic_from_tweet(tweet_text: str) -> dict:
    """
    Extract the actual TOPIC from a tweet - what is it about?
    Returns {topic: str, product: str, company: str, search_queries: list[str]}
    """
    # Remove URLs
    text = re.sub(r'https?://\S+', '', tweet_text).strip()
    # Remove mentions but remember them
    mentions = re.findall(r'@(\w+)', text)
    text_clean = re.sub(r'@\w+', '', text).strip()
    # Remove hashtags but keep words
    hashtags = re.findall(r'#(\w+)', text)
    text_clean = re.sub(r'#(\w+)', r'\1', text_clean)

    # --- Known product/model names (exact match, case-insensitive) ---
    known_products = {
        # Models
        r'\bGPT[-\s]?4o?\b': 'GPT-4o',
        r'\bGPT[-\s]?5\b': 'GPT-5',
        r'\bGPT[-\s]?4\.?1\b': 'GPT-4.1',
        r'\bo1[\s-]?(pro|mini|preview)?\b': 'o1',
        r'\bo3[\s-]?(pro|mini)?\b': 'o3',
        r'\bClaude\s*([\d.]+|Opus|Sonnet|Haiku)?\b': 'Claude',
        r'\bGemini\s*([\d.]+|Pro|Ultra|Flash|Nano)?\b': 'Gemini',
        r'\bLlama\s*[\d.]*\b': 'Llama',
        r'\bQwen\s*[\d.]*\b': 'Qwen',
        r'\bMistral\s*[\w]*\b': 'Mistral',
        r'\bDeepSeek\s*[\w-]*\b': 'DeepSeek',
        r'\bGrok\s*[\d.]*\b': 'Grok',
        r'\bPhi[-\s]?[\d.]+\b': 'Phi',
        r'\bCommand\s*R\+?\b': 'Command R',
        r'\bCopilot\b': 'Copilot',
        r'\bCursor\b': 'Cursor',
        r'\bWindsurf\b': 'Windsurf',
        r'\bDevin\b': 'Devin',
        r'\bSora\b': 'Sora',
        r'\bDALL[-\s]?E\s*[\d]*\b': 'DALL-E',
        r'\bMidjourney\s*[\w]*\b': 'Midjourney',
        r'\bStable\s*Diffusion\b': 'Stable Diffusion',
        r'\bVeo\s*[\d]*\b': 'Veo',
        r'\bNotebookLM\b': 'NotebookLM',
        # Platforms
        r'\bChatGPT\b': 'ChatGPT',
        r'\bPerplexity\b': 'Perplexity',
        r'\bHugging\s*Face\b': 'Hugging Face',
    }

    known_companies = {
        r'\bOpenAI\b': 'OpenAI',
        r'\bAnthropic\b': 'Anthropic',
        r'\bGoogle\b': 'Google',
        r'\bMeta\b': 'Meta',
        r'\bMicrosoft\b': 'Microsoft',
        r'\bApple\b': 'Apple',
        r'\bNVIDIA\b': 'NVIDIA',
        r'\bAmazon\b': 'Amazon',
        r'\bxAI\b': 'xAI',
        r'\bCohere\b': 'Cohere',
        r'\bStability\s*AI\b': 'Stability AI',
        r'\bRunway\b': 'Runway',
        r'\bMistral\s*AI\b': 'Mistral AI',
        r'\bMiniMax\b': 'MiniMax',
    }

    # Find products mentioned
    found_products = []
    for pattern, name in known_products.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_products.append(name)

    # Find companies mentioned
    found_companies = []
    for pattern, name in known_companies.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_companies.append(name)

    # --- Detect what HAPPENED (action/event) ---
    action_patterns = {
        r'(?i)(releas|launch|announc|introduc|unveil|drop)': 'release',
        r'(?i)(updat|upgrad|improv|new version|patch)': 'update',
        r'(?i)(benchmark|outperform|beats?|surpass|SOTA)': 'benchmark',
        r'(?i)(open.?sourc|weight|github|huggingface)': 'open-source',
        r'(?i)(pric|cost|\$|free tier|API.?pric)': 'pricing',
        r'(?i)(acqui|fund|rais|billion|valuation|IPO|partner)': 'business',
        r'(?i)(paper|research|arxiv|study|finding)': 'research',
        r'(?i)(agent|autono|tool.?use|function.?call)': 'agents',
        r'(?i)(ban|regulat|safety|alignment|risk)': 'regulation',
    }

    detected_action = None
    for pattern, action in action_patterns.items():
        if re.search(pattern, text):
            detected_action = action
            break

    # --- Build smart search queries ---
    search_queries = []

    # Primary query: product + action
    if found_products:
        main_product = found_products[0]
        if detected_action == 'release':
            search_queries.append(f"{main_product} release announcement 2025")
            search_queries.append(f"{main_product} features capabilities")
        elif detected_action == 'benchmark':
            search_queries.append(f"{main_product} benchmark results comparison")
        elif detected_action == 'update':
            search_queries.append(f"{main_product} update new features 2025")
        elif detected_action == 'pricing':
            search_queries.append(f"{main_product} pricing API cost")
        else:
            search_queries.append(f"{main_product} AI 2025")

        if found_companies:
            search_queries.append(f"{found_companies[0]} {main_product}")

    # Fallback: company + action
    elif found_companies:
        company = found_companies[0]
        if detected_action:
            search_queries.append(f"{company} AI {detected_action} 2025")
        else:
            search_queries.append(f"{company} AI news 2025")

    # Last resort: use significant words from tweet
    if not search_queries:
        # Get capitalized words (likely proper nouns/names)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text_clean)
        # Get words >4 chars that aren't stopwords
        stopwords = {"this", "that", "with", "from", "have", "been", "will",
                     "just", "about", "more", "than", "very", "also", "some",
                     "into", "they", "their", "there", "here", "what", "when",
                     "like", "does", "which", "these", "those", "would", "could",
                     "should", "being", "every", "after", "before", "between"}
        significant = [w for w in text_clean.split()
                       if len(w) > 4 and w.lower() not in stopwords]

        query_words = proper_nouns[:3] + significant[:3]
        if query_words:
            search_queries.append(" ".join(query_words[:4]) + " AI")

    # Build topic string
    topic_parts = []
    if found_companies:
        topic_parts.extend(found_companies[:2])
    if found_products:
        topic_parts.extend(found_products[:2])
    if detected_action:
        topic_parts.append(detected_action)

    topic = " ".join(topic_parts) if topic_parts else text_clean[:80]

    return {
        "topic": topic,
        "products": found_products,
        "companies": found_companies,
        "action": detected_action,
        "search_queries": search_queries[:3],
        "hashtags": hashtags,
    }


def research_topic(tweet_text: str, tweet_author: str = "",
                   tweet_id: str = "", scanner=None,
                   progress_callback=None) -> ResearchResult:
    """
    Perform deep research on a tweet topic.
    """
    result = ResearchResult(
        original_tweet_text=tweet_text,
        original_tweet_author=tweet_author,
        original_tweet_id=tweet_id,
    )

    # Smart topic extraction
    topic_info = extract_topic_from_tweet(tweet_text)
    result.topic = topic_info["topic"]
    search_queries = topic_info["search_queries"]

    if not search_queries:
        # Absolute fallback
        search_queries = [tweet_text[:60]]

    # Step 1: Web search with targeted queries
    if progress_callback:
        progress_callback(f"Web'de araştırılıyor: {search_queries[0][:50]}...")

    for query in search_queries[:2]:
        web_results = web_search(query, max_results=5)
        result.web_results.extend(web_results)

    # Step 2: News search
    if progress_callback:
        progress_callback("Son haberler taranıyor...")

    news_query = search_queries[0]
    news_results = web_search_news(news_query, max_results=4)
    for nr in news_results:
        result.web_results.append({
            "title": f"[HABER] {nr['title']}",
            "url": nr["url"],
            "body": nr["body"],
            "source": nr.get("source", ""),
        })

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for wr in result.web_results:
        if wr["url"] not in seen_urls:
            seen_urls.add(wr["url"])
            unique_results.append(wr)
    result.web_results = unique_results

    # Step 3: Search Twitter for related tweets
    if scanner:
        if progress_callback:
            progress_callback("X'te ilgili tweet'ler aranıyor...")
        try:
            # Build targeted Twitter query from products/companies
            parts = topic_info["products"][:2] + topic_info["companies"][:1]
            if parts:
                twitter_q = f"({' OR '.join(parts)}) -is:retweet lang:en"
            else:
                twitter_q = f"({search_queries[0][:50]}) -is:retweet"

            start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)
            related = scanner._search_tweets(twitter_q, start_time, 10)

            for t in related:
                if t.id != tweet_id and len(t.text) > 50:
                    result.related_tweets.append({
                        "text": t.text,
                        "author": t.author_username,
                        "likes": t.like_count,
                        "url": t.url,
                    })

            result.related_tweets.sort(key=lambda x: x["likes"], reverse=True)
            result.related_tweets = result.related_tweets[:5]
        except Exception as e:
            print(f"Twitter search error: {e}")

    # Step 4: Compile
    if progress_callback:
        progress_callback("Araştırma derleniyor...")

    result.summary = compile_research_summary(result)
    return result


def compile_research_summary(research: ResearchResult) -> str:
    """Compile all research into a structured summary for the AI"""
    parts = []

    parts.append(f"## Konu: {research.topic}")
    parts.append(f"## Orijinal Tweet (@{research.original_tweet_author}): \"{research.original_tweet_text}\"")

    if research.web_results:
        parts.append("\n## Araştırma Bulguları (Web)")
        for i, wr in enumerate(research.web_results[:8], 1):
            source = wr.get("source", "")
            source_str = f" ({source})" if source else ""
            parts.append(f"{i}. {wr['title']}{source_str}: {wr['body'][:200]}")

    if research.related_tweets:
        parts.append("\n## X'te Diğer Kullanıcıların Yorumları")
        for i, rt in enumerate(research.related_tweets[:5], 1):
            parts.append(f"{i}. @{rt['author']} ({rt['likes']} beğeni): \"{rt['text'][:150]}\"")

    return "\n".join(parts)
