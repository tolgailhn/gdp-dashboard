"""
Deep Research Module
Full research pipeline: Tweet URL → Fetch thread → AI-powered topic extraction
→ Multi-platform search → Fetch full article content → Compile → Generate

Key principles:
1. Use AI to UNDERSTAND the tweet first, then generate targeted search queries
2. Don't just match brand names — understand what the tweet is actually about
3. Visit and READ the top articles, not just snippets
4. Search across platforms: web, Reddit, tech blogs, news
"""
import re
import json
import datetime
import requests
from dataclasses import dataclass, field
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup


# --- Constants ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
FETCH_TIMEOUT = 10
MAX_ARTICLE_CHARS = 3000
SKIP_DOMAINS = {
    "twitter.com", "x.com", "t.co", "youtube.com", "youtu.be",
    "facebook.com", "instagram.com", "tiktok.com",
}


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
    deep_articles: list = field(default_factory=list)
    reddit_results: list = field(default_factory=list)
    related_tweets: list = field(default_factory=list)
    summary: str = ""


def extract_tweet_id(url_or_id: str) -> str | None:
    """Extract tweet ID from a URL or raw ID string"""
    url_or_id = url_or_id.strip()
    if url_or_id.isdigit():
        return url_or_id
    match = re.search(r'(?:twitter\.com|x\.com)/\w+/status/(\d+)', url_or_id)
    return match.group(1) if match else None


# ========================================================================
# SEARCH FUNCTIONS
# ========================================================================

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


def web_search_news(query: str, max_results: int = 6) -> list[dict]:
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


# ========================================================================
# AI-POWERED TOPIC EXTRACTION — understands what the tweet is ACTUALLY about
# ========================================================================

def ai_extract_topic(tweet_text: str, ai_client=None, ai_model: str = None,
                     provider: str = "minimax") -> dict | None:
    """
    Use AI to understand the tweet and generate targeted search queries.
    This is the KEY fix: instead of regex matching brand names,
    AI actually reads the tweet and understands the topic.

    Returns:
        {
            "topic": "Blackbox CLI AI terminal tool major update",
            "search_queries": {
                "general": [...],
                "technical": [...],
                "reddit": [...],
                "news": [...]
            }
        }
    """
    if not ai_client:
        return None

    current_year = str(datetime.datetime.now().year)

    prompt = f"""Aşağıdaki tweet'i oku ve konusunu analiz et. Tweet'in ASIL konusu nedir?

TWEET:
{tweet_text[:1500]}

Görevin: Bu tweet'in gerçek konusunu anla ve araştırma yapmak için arama sorguları üret.

DİKKAT: Tweet'te birçok marka/ürün adı geçebilir ama asıl konu farklı olabilir.
Örnek: "Claude ve Codex built-in" diyen bir tweet Claude hakkında değil, o ürünleri entegre eden ARAÇ hakkındadır.

Yanıtını SADECE şu JSON formatında ver, başka hiçbir şey yazma:
{{
    "topic": "tweet'in asıl konusunun 5-10 kelimelik özeti (İngilizce)",
    "main_subject": "tweet'in ana konusu olan ürün/şirket/olay (tek isim)",
    "general_queries": ["genel web araması 1", "genel web araması 2", "genel web araması 3"],
    "technical_queries": ["teknik detay araması 1", "teknik detay araması 2"],
    "reddit_queries": ["site:reddit.com ile reddit araması 1", "site:reddit.com ile reddit araması 2"]
}}

KURALLAR:
- Arama sorgularını İngilizce yaz
- Her sorguya "{current_year}" ekle
- "general_queries" konunun ne olduğunu araştırsın
- "technical_queries" teknik detayları bulsun
- "reddit_queries" Reddit'te tartışmaları bulsun
- Sorgular SPESİFİK olsun, genel "AI news" gibi değil"""

    try:
        if provider == "anthropic":
            import anthropic
            response = ai_client.messages.create(
                model=ai_model or "claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw = response.content[0].text.strip()
        else:
            response = ai_client.chat.completions.create(
                model=ai_model or "MiniMax-M2.5",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1,
            )
            raw = response.choices[0].message.content.strip()

        # Strip <think> tags from reasoning models
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            return None

        data = json.loads(json_match.group())

        return {
            "topic": data.get("topic", ""),
            "main_subject": data.get("main_subject", ""),
            "search_queries": {
                "general": data.get("general_queries", [])[:3],
                "technical": data.get("technical_queries", [])[:2],
                "reddit": data.get("reddit_queries", [])[:2],
                "news": [
                    f"{data.get('main_subject', '')} news {current_year}",
                    f"{data.get('topic', '')[:40]} {current_year}",
                ],
            }
        }

    except Exception as e:
        print(f"AI topic extraction error: {e}")
        return None


# ========================================================================
# ARTICLE CONTENT FETCHER — the key missing piece
# ========================================================================

def fetch_article_content(url: str) -> dict | None:
    """
    Fetch and extract the main text content from a web page.
    Returns clean article text that the AI can use for analysis.
    """
    # Skip social media / video sites
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in SKIP_DOMAINS:
            return None
    except Exception:
        return None

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=FETCH_TIMEOUT,
            allow_redirects=True,
        )
        resp.raise_for_status()

        # Only parse HTML
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer",
                                   "aside", "iframe", "form", "noscript",
                                   "button", "svg", "img"]):
            tag.decompose()

        # Try to find the main article content
        article_text = ""

        # Strategy 1: Look for <article> tag
        article_tag = soup.find("article")
        if article_tag:
            article_text = article_tag.get_text(separator="\n", strip=True)

        # Strategy 2: Look for main content div
        if not article_text or len(article_text) < 200:
            for selector in ["main", "[role='main']", ".post-content",
                             ".article-content", ".entry-content",
                             ".post-body", "#content", ".content"]:
                main = soup.select_one(selector)
                if main:
                    candidate = main.get_text(separator="\n", strip=True)
                    if len(candidate) > len(article_text):
                        article_text = candidate

        # Strategy 3: Reddit-specific
        if "reddit.com" in url:
            comments = []
            # Post body
            post_body = soup.select_one("[data-test-id='post-content']")
            if post_body:
                comments.append(post_body.get_text(separator="\n", strip=True))
            # Also get top comments
            for comment_div in soup.select(".comment, [data-testid='comment']")[:10]:
                text = comment_div.get_text(separator=" ", strip=True)
                if len(text) > 30:
                    comments.append(text[:500])
            if comments:
                article_text = "\n\n".join(comments)

        # Strategy 4: Fallback to all paragraphs
        if not article_text or len(article_text) < 200:
            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 40:
                    paragraphs.append(text)
            article_text = "\n\n".join(paragraphs)

        if not article_text or len(article_text) < 100:
            return None

        # Clean up
        article_text = re.sub(r'\n{3,}', '\n\n', article_text)
        article_text = re.sub(r' {2,}', ' ', article_text)
        article_text = article_text[:MAX_ARTICLE_CHARS]

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)[:150]

        return {
            "url": url,
            "title": title,
            "content": article_text,
            "length": len(article_text),
        }

    except Exception as e:
        print(f"Article fetch error ({url[:60]}): {e}")
        return None


# ========================================================================
# TOPIC EXTRACTION
# ========================================================================

def extract_topic_from_text(full_text: str) -> dict:
    """
    Smart topic extraction from tweet/thread text.
    Finds actual product names, companies, and what happened.
    Returns targeted search queries for multiple platforms.
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
        r'\bNIM\b': 'NIM',
        r'\bNeMo\b': 'NeMo',
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
        r'\bSoftBank\b': 'SoftBank', r'\bAlibaba\b': 'Alibaba',
        r'\bBaidu\b': 'Baidu', r'\bHuawei\b': 'Huawei',
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
        r'(?i)(deploy|production|inference|endpoint|API)': 'deployment',
    }

    action = None
    for pat, act in action_map.items():
        if re.search(pat, text):
            action = act
            break

    # --- Dollar amounts, percentages, big numbers ---
    amounts = re.findall(r'\$[\d,.]+\s*[BMKbmk](?:illion)?', text)
    percentages = re.findall(r'\d+(?:\.\d+)?%', text)
    big_numbers = re.findall(r'\b\d+[BMK]\b|\b\d{3,}B\b', text)

    # --- Build DIVERSE search queries ---
    queries = {
        "general": [],
        "technical": [],
        "reddit": [],
        "news": [],
    }

    entities = found_products + found_companies

    if entities and action:
        main = entities[0]
        # General search
        if action == 'investment' and amounts:
            queries["general"].append(f"{main} {amounts[0]} investment funding {current_year}")
        elif action == 'release':
            queries["general"].append(f"{main} release announcement features {current_year}")
        elif action == 'benchmark' and percentages:
            queries["general"].append(f"{main} benchmark results {percentages[0]} {current_year}")
        elif action == 'deployment':
            queries["general"].append(f"{main} deployment API production {current_year}")
        else:
            queries["general"].append(f"{main} {action} {current_year}")

        if len(entities) > 1:
            queries["general"].append(f"{entities[0]} {entities[1]} {action or 'AI'} {current_year}")

        # Technical deep search
        queries["technical"].append(f"{main} technical details specs parameters architecture {current_year}")
        if found_products:
            queries["technical"].append(f"{found_products[0]} benchmark comparison performance {current_year}")

        # Reddit search
        queries["reddit"].append(f"site:reddit.com {' '.join(entities[:2])} {action or 'AI'} {current_year}")
        queries["reddit"].append(f"site:reddit.com {main} {current_year}")

        # News search
        queries["news"].append(f"{main} {action or ''} {current_year}")
        if len(entities) > 1:
            queries["news"].append(f"{' '.join(entities[:3])} news")

    elif entities:
        queries["general"].append(f"{entities[0]} AI news {current_year}")
        queries["technical"].append(f"{entities[0]} technical details {current_year}")
        queries["reddit"].append(f"site:reddit.com {entities[0]} {current_year}")
        queries["news"].append(f"{entities[0]} latest {current_year}")
    else:
        proper = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\b', text_clean)
        if proper:
            base = " ".join(proper[:3])
            queries["general"].append(f"{base} AI {current_year}")
            queries["reddit"].append(f"site:reddit.com {base} AI")
            queries["news"].append(f"{base} news {current_year}")
        else:
            queries["general"].append(text_clean[:60])

    # Always add a latest-news query
    if entities:
        queries["general"].append(f"{' '.join(entities[:2])} latest news {current_year}")

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
        "big_numbers": big_numbers,
        "search_queries": queries,
    }


# ========================================================================
# MAIN RESEARCH PIPELINE
# ========================================================================

def research_topic(tweet_text: str, tweet_author: str = "",
                   tweet_id: str = "", scanner=None,
                   progress_callback=None,
                   ai_client=None, ai_model: str = None,
                   ai_provider: str = "minimax") -> ResearchResult:
    """
    Full deep research pipeline:

    1. Fetch thread (if scanner available)
    2. AI-powered topic extraction (understands what the tweet is ACTUALLY about)
    3. Fallback to regex if AI not available
    4. Web search with diverse queries (general + technical + reddit)
    5. News search
    6. DEEP FETCH: Read full article content from top URLs
    7. Twitter search for other opinions
    8. Compile everything into rich context
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

    # === STEP 2: AI-powered topic extraction ===
    # Try AI first — it actually UNDERSTANDS the tweet
    ai_topic = None
    if ai_client:
        if progress_callback:
            progress_callback("AI ile konu analiz ediliyor...")
        ai_topic = ai_extract_topic(
            result.full_thread_text,
            ai_client=ai_client,
            ai_model=ai_model,
            provider=ai_provider,
        )

    if ai_topic and ai_topic.get("search_queries"):
        # AI understood the tweet — use its queries
        result.topic = ai_topic["topic"]
        search_queries = ai_topic["search_queries"]
        if progress_callback:
            progress_callback(f"Konu: {result.topic}")
    else:
        # Fallback to regex extraction
        topic_info = extract_topic_from_text(result.full_thread_text)
        result.topic = topic_info["topic"]
        search_queries = topic_info["search_queries"]

    # === STEP 3: General + Technical web search ===
    if progress_callback:
        progress_callback("Web'de araştırma yapılıyor...")

    all_urls = set()

    # General search
    for query in search_queries.get("general", [])[:3]:
        results = web_search(query, max_results=6)
        for r in results:
            if r["url"] not in all_urls:
                all_urls.add(r["url"])
                result.web_results.append(r)

    # Technical deep search
    if progress_callback:
        progress_callback("Teknik detaylar araştırılıyor...")
    for query in search_queries.get("technical", [])[:2]:
        results = web_search(query, max_results=5)
        for r in results:
            if r["url"] not in all_urls:
                all_urls.add(r["url"])
                r["title"] = f"[TEKNİK] {r['title']}"
                result.web_results.append(r)

    # Reddit search
    if progress_callback:
        progress_callback("Reddit araştırılıyor...")
    for query in search_queries.get("reddit", [])[:2]:
        results = web_search(query, max_results=4)
        for r in results:
            if r["url"] not in all_urls:
                all_urls.add(r["url"])
                result.reddit_results.append(r)

    # === STEP 4: News search ===
    if progress_callback:
        progress_callback("Son haberler aranıyor...")

    for query in search_queries.get("news", [])[:2]:
        news = web_search_news(query, max_results=5)
        for n in news:
            if n["url"] not in all_urls:
                all_urls.add(n["url"])
                result.web_results.append({
                    "title": f"[HABER] {n['title']}",
                    "url": n["url"],
                    "body": n["body"],
                    "source": n.get("source", ""),
                })

    # === STEP 5: DEEP FETCH — Read full article content ===
    if progress_callback:
        progress_callback("Makaleler okunuyor (derin araştırma)...")

    # Pick the most promising URLs to fetch
    urls_to_fetch = _pick_best_urls(result.web_results + result.reddit_results)

    fetched_count = 0
    for url in urls_to_fetch:
        if fetched_count >= 5:
            break
        if progress_callback:
            progress_callback(f"Makale okunuyor ({fetched_count + 1}/5)...")
        article = fetch_article_content(url)
        if article and article["content"] and len(article["content"]) > 200:
            result.deep_articles.append(article)
            fetched_count += 1

    # === STEP 6: Twitter search ===
    if scanner:
        if progress_callback:
            progress_callback("X'te ilgili yorumlar aranıyor...")
        try:
            parts = topic_info["products"][:2] + topic_info["companies"][:1]
            if parts:
                twitter_q = f"({' OR '.join(parts)}) -is:retweet lang:en"
            else:
                general_q = search_queries.get("general", ["AI"])[0][:50]
                twitter_q = f"({general_q}) -is:retweet"

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

    # === STEP 7: Compile ===
    if progress_callback:
        progress_callback("Araştırma derleniyor...")

    result.summary = compile_research_summary(result)
    return result


def _pick_best_urls(results: list[dict], max_urls: int = 8) -> list[str]:
    """
    Pick the best URLs to deep-fetch based on relevance signals.
    Prioritize: tech blogs, official announcements, Reddit discussions.
    """
    scored = []
    for r in results:
        url = r.get("url", "")
        title = r.get("title", "").lower()
        body = r.get("body", "").lower()

        score = 0

        # Skip social media
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")
            if domain in SKIP_DOMAINS:
                continue
        except Exception:
            continue

        # Boost tech sites
        tech_domains = ["techcrunch.com", "theverge.com", "arstechnica.com",
                        "wired.com", "venturebeat.com", "huggingface.co",
                        "reddit.com", "arxiv.org", "github.com",
                        "nvidia.com", "blog.google", "openai.com",
                        "anthropic.com", "microsoft.com", "meta.com",
                        "towardsdatascience.com", "semianalysis.com"]
        for td in tech_domains:
            if td in url:
                score += 3
                break

        # Boost Reddit
        if "reddit.com" in url:
            score += 2

        # Boost articles with numbers/data
        if re.search(r'\d+[BMK%]|\$\d', body):
            score += 2

        # Boost detailed content
        if len(body) > 150:
            score += 1

        # Boost if title has key signals
        for signal in ["benchmark", "review", "analysis", "comparison",
                        "specs", "details", "announced", "released"]:
            if signal in title:
                score += 1

        scored.append((score, url))

    scored.sort(reverse=True)
    return [url for _, url in scored[:max_urls]]


# ========================================================================
# RESEARCH SUMMARY COMPILER
# ========================================================================

def compile_research_summary(r: ResearchResult) -> str:
    """
    Build the research context that will be sent to the AI.
    Now includes FULL ARTICLE CONTENT, not just snippets.
    """
    parts = []

    # Section 1: Original tweet/thread
    parts.append(f"# KONU: {r.topic}")

    if len(r.thread_texts) > 1:
        parts.append(f"\n## Orijinal Thread (@{r.original_tweet_author}) - {len(r.thread_texts)} tweet:")
        for i, t in enumerate(r.thread_texts, 1):
            parts.append(f"  {i}/ {t}")
    else:
        parts.append(f"\n## Orijinal Tweet (@{r.original_tweet_author}):")
        parts.append(f"  {r.original_tweet_text}")

    # Section 2: DEEP ARTICLES — Full content from fetched pages
    if r.deep_articles:
        parts.append(f"\n## DERİN ARAŞTIRMA — Okunan Makaleler ({len(r.deep_articles)} kaynak):")
        parts.append("(Bu makalelerdeki spesifik verileri, rakamları ve detayları kullan!)\n")
        for i, article in enumerate(r.deep_articles, 1):
            parts.append(f"### Kaynak {i}: {article['title']}")
            parts.append(f"URL: {article['url']}")
            parts.append(f"{article['content']}")
            parts.append("")  # blank line

    # Section 3: Web search snippets (for results we couldn't deep-fetch)
    if r.web_results:
        # Only show snippets for results NOT in deep_articles
        deep_urls = {a["url"] for a in r.deep_articles}
        remaining = [wr for wr in r.web_results if wr["url"] not in deep_urls]

        if remaining:
            parts.append(f"\n## Ek Web Bulguları ({len(remaining)} kaynak):")
            for i, wr in enumerate(remaining[:8], 1):
                src = f" ({wr['source']})" if wr.get("source") else ""
                parts.append(f"  {i}. {wr['title']}{src}")
                parts.append(f"     {wr['body'][:400]}")

    # Section 4: Reddit discussions
    if r.reddit_results:
        deep_urls = {a["url"] for a in r.deep_articles}
        remaining_reddit = [rr for rr in r.reddit_results if rr["url"] not in deep_urls]
        if remaining_reddit:
            parts.append(f"\n## Reddit Tartışmaları:")
            for i, rr in enumerate(remaining_reddit[:4], 1):
                parts.append(f"  {i}. {rr['title']}")
                parts.append(f"     {rr['body'][:300]}")

    # Section 5: X/Twitter opinions
    if r.related_tweets:
        parts.append(f"\n## X'te Diğer Yorumlar:")
        for i, rt in enumerate(r.related_tweets[:5], 1):
            parts.append(f"  {i}. @{rt['author']} ({rt['likes']} beğeni): {rt['text'][:200]}")

    return "\n".join(parts)
