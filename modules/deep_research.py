"""
Deep Research Module
Full research pipeline: Tweet URL → Fetch thread → Extract topic → Web search → Compile → Generate

The goal: When user gives a tweet URL, understand the FULL context (thread, topic, details)
then research it from web sources, and provide all this to the AI so it writes an informed tweet.
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
    thread_texts: list = field(default_factory=list)
    full_thread_text: str = ""
    topic: str = ""
    web_results: list = field(default_factory=list)
    related_tweets: list = field(default_factory=list)
    summary: str = ""


def extract_tweet_id(url_or_id: str) -> str | None:
    """Extract tweet ID from a URL or raw ID string"""
    url_or_id = url_or_id.strip()
    if url_or_id.isdigit():
        return url_or_id
    match = re.search(r'(?:twitter\.com|x\.com)/\w+/status/(\d+)', url_or_id)
    return match.group(1) if match else None


def web_search(query: str, max_results: int = 8) -> list[dict]:
    """Search the web using DuckDuckGo"""
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
    """Search recent news"""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "body": r.get("body", ""),
                    "source": r.get("source", ""),
                })
    except Exception as e:
        print(f"News search error: {e}")
    return results


def extract_topic_from_text(full_text: str) -> dict:
    """
    Smart topic extraction from tweet/thread text.
    Finds actual product names, companies, and what happened.
    Returns targeted search queries.
    """
    current_year = str(datetime.datetime.now().year)
    text = re.sub(r'https?://\S+', '', full_text).strip()
    text_clean = re.sub(r'@\w+', '', text)
    text_clean = re.sub(r'#(\w+)', r'\1', text_clean)

    # --- Product/model detection ---
    product_patterns = {
        r'\bGPT[-\s]?4[o.]?\w*\b': 'GPT-4o',
        r'\bGPT[-\s]?5\b': 'GPT-5',
        r'\bGPT[-\s]?4\.?1\b': 'GPT-4.1',
        r'\bo[13][-\s]?(pro|mini|preview)?\b': 'o1',
        r'\bClaude\s*[\d.]*\s*(Opus|Sonnet|Haiku)?\b': 'Claude',
        r'\bGemini\s*[\d.]*\s*(Pro|Ultra|Flash|Nano)?\b': 'Gemini',
        r'\bLlama\s*[\d.]*\b': 'Llama',
        r'\bQwen\s*[\d.]*\b': 'Qwen',
        r'\bMistral\s*\w*\b': 'Mistral',
        r'\bDeepSeek[-\s]?\w*\b': 'DeepSeek',
        r'\bGrok\s*[\d.]*\b': 'Grok',
        r'\bPhi[-\s]?[\d.]+\b': 'Phi',
        r'\bCopilot\b': 'Copilot',
        r'\bCursor\b': 'Cursor',
        r'\bSora\b': 'Sora',
        r'\bDALL[-\s]?E\s*[\d]*\b': 'DALL-E',
        r'\bMidjourney\b': 'Midjourney',
        r'\bStable\s*Diffusion\b': 'Stable Diffusion',
        r'\bChatGPT\b': 'ChatGPT',
        r'\bPerplexity\b': 'Perplexity',
        r'\bNotebookLM\b': 'NotebookLM',
        r'\bWindsurf\b': 'Windsurf',
        r'\bDevin\b': 'Devin',
    }

    company_patterns = {
        r'\bOpenAI\b': 'OpenAI', r'\bAnthropic\b': 'Anthropic',
        r'\bGoogle\b': 'Google', r'\bMeta\b': 'Meta',
        r'\bMicrosoft\b': 'Microsoft', r'\bApple\b': 'Apple',
        r'\bNVIDIA\b': 'NVIDIA', r'\bAmazon\b': 'Amazon',
        r'\bxAI\b': 'xAI', r'\bCohere\b': 'Cohere',
        r'\bStability\s*AI\b': 'Stability AI',
        r'\bRunway\b': 'Runway', r'\bMistral\s*AI\b': 'Mistral AI',
        r'\bMiniMax\b': 'MiniMax', r'\bSamsung\b': 'Samsung',
        r'\bSoftBank\b': 'SoftBank',
    }

    found_products = list({name for pat, name in product_patterns.items()
                          if re.search(pat, text, re.IGNORECASE)})
    found_companies = list({name for pat, name in company_patterns.items()
                           if re.search(pat, text, re.IGNORECASE)})

    # --- Action detection ---
    action_map = {
        r'(?i)(releas|launch|announc|introduc|unveil|drop)': 'release',
        r'(?i)(updat|upgrad|improv|new version)': 'update',
        r'(?i)(benchmark|outperform|beats?|surpass|SOTA)': 'benchmark',
        r'(?i)(open.?sourc|weights?|github)': 'open-source',
        r'(?i)(pric|cost|\$\d|free tier|API.?pric)': 'pricing',
        r'(?i)(acqui|fund|rais|\$\d+[BMb]|valuation|invest)': 'investment',
        r'(?i)(paper|research|arxiv|study)': 'research',
        r'(?i)(agent|autono|tool.?use)': 'agents',
        r'(?i)(ban|regulat|safety|alignment)': 'regulation',
        r'(?i)(partner|deal|collaborat|agreement)': 'partnership',
    }

    action = None
    for pat, act in action_map.items():
        if re.search(pat, text):
            action = act
            break

    # --- Also find dollar amounts, percentages, numbers ---
    amounts = re.findall(r'\$[\d,.]+\s*[BMKbmk](?:illion)?', text)
    percentages = re.findall(r'\d+(?:\.\d+)?%', text)

    # --- Build search queries ---
    queries = []

    # Strategy: specific queries about what actually happened
    entities = found_products + found_companies

    if entities and action:
        main = entities[0]
        if action == 'investment' and amounts:
            queries.append(f"{main} {amounts[0]} investment funding {current_year}")
        elif action == 'release':
            queries.append(f"{main} release announcement features {current_year}")
        elif action == 'benchmark' and percentages:
            queries.append(f"{main} benchmark results {percentages[0]} {current_year}")
        else:
            queries.append(f"{main} {action} {current_year}")

        # Second query: combine companies + products
        if len(entities) > 1:
            queries.append(f"{entities[0]} {entities[1]} {action or 'AI'} {current_year}")
    elif entities:
        queries.append(f"{entities[0]} AI news {current_year}")
    else:
        # Fallback: get proper nouns from text
        proper = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\b', text_clean)
        if proper:
            queries.append(" ".join(proper[:3]) + f" AI {current_year}")
        else:
            queries.append(text_clean[:60])

    # Add a news-specific query
    if entities:
        queries.append(f"{' '.join(entities[:2])} latest news")

    topic_str = " ".join(filter(None, [
        " ".join(found_companies[:2]),
        " ".join(found_products[:2]),
        action or "",
        amounts[0] if amounts else "",
    ])).strip() or text_clean[:80]

    return {
        "topic": topic_str,
        "products": found_products,
        "companies": found_companies,
        "action": action,
        "amounts": amounts,
        "percentages": percentages,
        "search_queries": queries[:3],
    }


def research_topic(tweet_text: str, tweet_author: str = "",
                   tweet_id: str = "", scanner=None,
                   progress_callback=None) -> ResearchResult:
    """
    Full research pipeline.

    1. Fetch thread (if scanner available)
    2. Extract topic from full thread text
    3. Web search with targeted queries
    4. News search
    5. Twitter search for other opinions
    6. Compile everything
    """
    result = ResearchResult(
        original_tweet_text=tweet_text,
        original_tweet_author=tweet_author,
        original_tweet_id=tweet_id,
    )

    # === STEP 1: Fetch full thread ===
    if scanner and tweet_id:
        if progress_callback:
            progress_callback("Thread kontrol ediliyor...")
        try:
            thread_texts = scanner.get_thread(tweet_id)
            if thread_texts and len(thread_texts) > 1:
                result.thread_texts = thread_texts
                result.full_thread_text = "\n\n".join(thread_texts)
                if progress_callback:
                    progress_callback(f"Thread bulundu: {len(thread_texts)} tweet")
            else:
                result.thread_texts = [tweet_text]
                result.full_thread_text = tweet_text
        except Exception as e:
            print(f"Thread fetch error: {e}")
            result.thread_texts = [tweet_text]
            result.full_thread_text = tweet_text
    else:
        result.thread_texts = [tweet_text]
        result.full_thread_text = tweet_text

    # === STEP 2: Extract topic from FULL thread text ===
    topic_info = extract_topic_from_text(result.full_thread_text)
    result.topic = topic_info["topic"]
    search_queries = topic_info["search_queries"]

    if not search_queries:
        search_queries = [tweet_text[:60]]

    # === STEP 3: Web search ===
    if progress_callback:
        progress_callback(f"Web araştırması: {search_queries[0][:50]}...")

    for query in search_queries[:3]:
        results = web_search(query, max_results=8)
        result.web_results.extend(results)

    # === STEP 4: News search ===
    if progress_callback:
        progress_callback("Son haberler aranıyor...")

    news = web_search_news(search_queries[0], max_results=6)
    for n in news:
        result.web_results.append({
            "title": f"[HABER] {n['title']}",
            "url": n["url"],
            "body": n["body"],
            "source": n.get("source", ""),
        })

    # Deduplicate
    seen = set()
    unique = []
    for wr in result.web_results:
        if wr["url"] not in seen:
            seen.add(wr["url"])
            unique.append(wr)
    result.web_results = unique

    # === STEP 5: Twitter search ===
    if scanner:
        if progress_callback:
            progress_callback("X'te ilgili yorumlar aranıyor...")
        try:
            parts = topic_info["products"][:2] + topic_info["companies"][:1]
            if parts:
                twitter_q = f"({' OR '.join(parts)}) -is:retweet lang:en"
            else:
                twitter_q = f"({search_queries[0][:50]}) -is:retweet"

            start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)
            related = scanner._search_tweets(twitter_q, start, 10)

            for t in related:
                if t.id != tweet_id and len(t.text) > 50:
                    result.related_tweets.append({
                        "text": t.text,
                        "author": t.author_username,
                        "likes": t.like_count,
                    })

            result.related_tweets.sort(key=lambda x: x["likes"], reverse=True)
            result.related_tweets = result.related_tweets[:5]
        except Exception as e:
            print(f"Twitter search error: {e}")

    # === STEP 6: Compile ===
    if progress_callback:
        progress_callback("Araştırma derleniyor...")

    result.summary = compile_research_summary(result)
    return result


def compile_research_summary(r: ResearchResult) -> str:
    """
    Build the research context that will be sent to the AI.
    This is the most important part - it determines what the AI knows.
    """
    parts = []

    # Section 1: What was the original tweet/thread about
    parts.append(f"# KONU: {r.topic}")

    if len(r.thread_texts) > 1:
        parts.append(f"\n## Orijinal Thread (@{r.original_tweet_author}) - {len(r.thread_texts)} tweet:")
        for i, t in enumerate(r.thread_texts, 1):
            parts.append(f"  {i}/ {t}")
    else:
        parts.append(f"\n## Orijinal Tweet (@{r.original_tweet_author}):")
        parts.append(f"  {r.original_tweet_text}")

    # Section 2: What the web says about this topic
    if r.web_results:
        parts.append(f"\n## Web Araştırma Bulguları ({len(r.web_results)} kaynak):")
        for i, wr in enumerate(r.web_results[:10], 1):
            src = f" ({wr['source']})" if wr.get("source") else ""
            parts.append(f"  {i}. {wr['title']}{src}")
            parts.append(f"     {wr['body'][:400]}")

    # Section 3: What others on X are saying
    if r.related_tweets:
        parts.append(f"\n## X'te Diğer Yorumlar:")
        for i, rt in enumerate(r.related_tweets[:5], 1):
            parts.append(f"  {i}. @{rt['author']} ({rt['likes']} beğeni): {rt['text'][:180]}")

    return "\n".join(parts)
