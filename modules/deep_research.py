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
    synthesized_brief: str = ""  # AI-synthesized structured research brief


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

def web_search(query: str, max_results: int = 8, timelimit: str = "w") -> list[dict]:
    """Search the web using DuckDuckGo with time filter.

    Args:
        query: Search query
        max_results: Maximum results to return
        timelimit: Time filter - "d" (day), "w" (week), "m" (month), None (all time)
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, timelimit=timelimit):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "body": r.get("body", ""),
                })
    except Exception as e:
        print(f"Web search error: {e}")
    # If time-limited search returned nothing, retry without time filter
    if not results and timelimit:
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "body": r.get("body", ""),
                    })
        except Exception as e:
            print(f"Web search fallback error: {e}")
    return results


def web_search_news(query: str, max_results: int = 6, timelimit: str = "w") -> list[dict]:
    """Search recent news with time filter.

    Args:
        query: Search query
        max_results: Maximum results to return
        timelimit: Time filter - "d" (day), "w" (week), "m" (month), None (all time)
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results, timelimit=timelimit):
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

    # Detect if tweet is short (needs deeper query expansion)
    is_short_tweet = len(tweet_text.strip()) < 300

    short_tweet_extra = """
ÖNEMLİ: Bu tweet KISA. Konu hakkında derinlemesine araştırma yapabilmek için
sorguları çeşitlendir. Sadece "X nedir" değil, şu açılardan da sorgula:
- Bu konuda son gelişmeler neler?
- Rakamlar/istatistikler neler?
- Uzman görüşleri ve karşıt fikirler neler?
- Bu konunun piyasa/sektör etkisi nedir?
""" if is_short_tweet else ""

    prompt = f"""Aşağıdaki tweet'i oku ve konusunu analiz et. Tweet'in ASIL konusu nedir?

TWEET:
{tweet_text[:1500]}

Görevin: Bu tweet'in gerçek konusunu anla ve araştırma yapmak için HEDEFLI arama sorguları üret.

DİKKAT: Tweet'te birçok marka/ürün adı geçebilir ama asıl konu farklı olabilir.
Örnek: "Claude ve Codex built-in" diyen bir tweet Claude hakkında değil, o ürünleri entegre eden ARAÇ hakkındadır.
{short_tweet_extra}
Yanıtını SADECE şu JSON formatında ver, başka hiçbir şey yazma:
{{
    "topic": "tweet'in asıl konusunun 5-10 kelimelik özeti (İngilizce)",
    "main_subject": "tweet'in ana konusu olan ürün/şirket/olay (tek isim)",
    "general_queries": ["ne oldu/ne çıktı araması", "detay/özellik araması", "etki/analiz araması"],
    "technical_queries": ["teknik detay/benchmark araması", "karşılaştırma/rakip araması"],
    "reddit_queries": ["site:reddit.com spesifik tartışma 1", "site:reddit.com spesifik tartışma 2"],
    "news_queries": ["haber araması 1", "haber araması 2"]
}}

KURALLAR:
- Arama sorgularını İngilizce yaz
- Her sorguya "{current_year}" ekle
- general_queries: 3 farklı AÇI ile ara (ne oldu + detaylar + etki/analiz)
- technical_queries: teknik detay + benchmark/karşılaştırma
- reddit_queries: Reddit'te kullanıcı deneyimleri ve tartışmaları bul
- news_queries: son haberler ve duyurular
- Sorgular KISA olsun (3-7 kelime ideal), spesifik olsun
- "AI news" gibi genel sorgular YASAK, her sorgu konuya özel olmalı"""

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

        # Use AI-generated news queries if available, fallback to auto-generated
        news_queries = data.get("news_queries", [])[:2]
        if not news_queries:
            news_queries = [
                f"{data.get('main_subject', '')} news {current_year}",
                f"{data.get('topic', '')[:40]} {current_year}",
            ]

        return {
            "topic": data.get("topic", ""),
            "main_subject": data.get("main_subject", ""),
            "search_queries": {
                "general": data.get("general_queries", [])[:3],
                "technical": data.get("technical_queries", [])[:2],
                "reddit": data.get("reddit_queries", [])[:2],
                "news": news_queries,
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
                   ai_provider: str = "minimax",
                   research_sources: list = None) -> ResearchResult:
    """
    Full deep research pipeline with selectable sources:

    research_sources: list of sources to search. Options:
        - "web" : General + technical web search
        - "reddit" : Reddit discussions
        - "news" : News articles
        - "x" : X/Twitter search for related tweets
        - None/empty : defaults to all sources

    1. Fetch thread (if scanner available)
    2. AI-powered topic extraction (understands what the tweet is ACTUALLY about)
    3. Fallback to regex if AI not available
    4. Search selected sources
    5. Compile everything into rich context
    """
    # Default: all sources
    if not research_sources:
        research_sources = ["web", "reddit", "news", "x"]

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

    # Always run regex extraction for entity info
    topic_info = extract_topic_from_text(result.full_thread_text)

    if ai_topic and ai_topic.get("search_queries"):
        result.topic = ai_topic["topic"]
        search_queries = ai_topic["search_queries"]
        if progress_callback:
            progress_callback(f"Konu: {result.topic}")
    else:
        result.topic = topic_info["topic"]
        search_queries = topic_info["search_queries"]

    all_urls = set()

    # === STEP 3: Web search (only if "web" in sources) ===
    if "web" in research_sources:
        if progress_callback:
            progress_callback("Web'de araştırma yapılıyor...")

        for query in search_queries.get("general", [])[:3]:
            results = web_search(query, max_results=6, timelimit="w")
            for r in results:
                if r["url"] not in all_urls:
                    all_urls.add(r["url"])
                    result.web_results.append(r)

        if progress_callback:
            progress_callback("Teknik detaylar araştırılıyor...")
        for query in search_queries.get("technical", [])[:2]:
            results = web_search(query, max_results=5, timelimit="m")
            for r in results:
                if r["url"] not in all_urls:
                    all_urls.add(r["url"])
                    r["title"] = f"[TEKNİK] {r['title']}"
                    result.web_results.append(r)

    # === STEP 4: Reddit search (only if "reddit" in sources) ===
    if "reddit" in research_sources:
        if progress_callback:
            progress_callback("Reddit araştırılıyor...")
        for query in search_queries.get("reddit", [])[:2]:
            results = web_search(query, max_results=4, timelimit="w")
            for r in results:
                if r["url"] not in all_urls:
                    all_urls.add(r["url"])
                    result.reddit_results.append(r)

    # === STEP 5: News search (only if "news" in sources) ===
    if "news" in research_sources:
        if progress_callback:
            progress_callback("Son haberler aranıyor...")

        for query in search_queries.get("news", [])[:2]:
            news = web_search_news(query, max_results=5, timelimit="d")
            if not news:
                news = web_search_news(query, max_results=5, timelimit="w")
            for n in news:
                if n["url"] not in all_urls:
                    all_urls.add(n["url"])
                    result.web_results.append({
                        "title": f"[HABER] {n['title']}",
                        "url": n["url"],
                        "body": n["body"],
                        "source": n.get("source", ""),
                    })

    # === STEP 6: DEEP FETCH (only if web or reddit or news selected) ===
    if any(s in research_sources for s in ["web", "reddit", "news"]):
        if progress_callback:
            progress_callback("Makaleler okunuyor (derin araştırma)...")

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

    # === STEP 7: X/Twitter search (only if "x" in sources) ===
    # When X is selected, do a DEEP search (40-50 tweets, not just 10)
    if "x" in research_sources and scanner:
        x_only_mode = research_sources == ["x"]
        max_tweets = 50 if x_only_mode else 15
        if progress_callback:
            progress_callback(f"X'te {'detaylı' if x_only_mode else ''} arama yapılıyor...")
        try:
            parts = topic_info["products"][:2] + topic_info["companies"][:1]

            # Build multiple search queries for thorough X coverage
            x_queries = []
            if parts:
                x_queries.append(f"({' OR '.join(parts)}) -is:retweet lang:en")
                if len(parts) > 1:
                    x_queries.append(f"({parts[0]}) -is:retweet lang:en min_faves:10")
                    x_queries.append(f"({parts[1]}) -is:retweet lang:en")
                # Add action-based query
                action = topic_info.get("action", "")
                if action:
                    x_queries.append(f"({parts[0]}) ({action}) -is:retweet lang:en")
            else:
                general_q = search_queries.get("general", ["AI"])[0][:50]
                x_queries.append(f"({general_q}) -is:retweet")

            # In X-only mode, add more query variations
            if x_only_mode:
                # Use AI-generated queries if available
                if ai_topic and ai_topic.get("search_queries"):
                    for gq in ai_topic["search_queries"].get("general", [])[:2]:
                        x_queries.append(f"({gq[:50]}) -is:retweet lang:en")
                # Add topic-based variations
                if topic_info["products"]:
                    for prod in topic_info["products"][:3]:
                        x_queries.append(f"{prod} -is:retweet lang:en min_faves:5")
                if topic_info["companies"]:
                    for comp in topic_info["companies"][:2]:
                        x_queries.append(f"{comp} {topic_info.get('action', 'AI')} -is:retweet lang:en")

            start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=72)
            seen_ids = set()
            per_query_count = max(max_tweets // len(x_queries), 10) if x_queries else 20

            for idx, q in enumerate(x_queries):
                if len(result.related_tweets) >= max_tweets:
                    break
                if progress_callback and idx > 0:
                    progress_callback(f"X araması {idx + 1}/{len(x_queries)}... ({len(result.related_tweets)} tweet bulundu)")
                try:
                    related = scanner._search_tweets(q, start, per_query_count)
                    for t in related:
                        if t.id != tweet_id and t.id not in seen_ids and len(t.text) > 50:
                            seen_ids.add(t.id)
                            result.related_tweets.append({
                                "text": t.text,
                                "author": t.author_username,
                                "likes": t.like_count,
                                "retweets": getattr(t, 'retweet_count', 0),
                                "followers": getattr(t, 'author_followers_count', 0),
                            })
                except Exception as e:
                    print(f"X search error ({q[:40]}): {e}")

            result.related_tweets.sort(key=lambda x: x.get("likes", 0) + x.get("retweets", 0) * 2, reverse=True)
            result.related_tweets = result.related_tweets[:max_tweets]

            if progress_callback:
                progress_callback(f"X'te {len(result.related_tweets)} tweet bulundu")
        except Exception as e:
            print(f"Twitter search error: {e}")

    # === STEP 8: Compile raw summary ===
    if progress_callback:
        progress_callback("Araştırma derleniyor...")

    result.summary = compile_research_summary(result)

    # === STEP 9: AI Synthesis — structured research brief ===
    # This transforms raw research into prioritized, tweet-friendly format
    if ai_client and (result.deep_articles or result.web_results or result.reddit_results):
        if progress_callback:
            progress_callback("AI ile araştırma sentezleniyor...")
        brief = ai_synthesize_research(
            raw_summary=result.summary,
            original_tweet=result.full_thread_text or result.original_tweet_text,
            ai_client=ai_client,
            ai_model=ai_model,
            provider=ai_provider,
        )
        if brief:
            result.synthesized_brief = brief
            if progress_callback:
                progress_callback("Araştırma sentezi tamamlandı")

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
# AI-POWERED RESEARCH SYNTHESIS — structured Research Brief
# ========================================================================

def ai_synthesize_research(raw_summary: str, original_tweet: str,
                           ai_client=None, ai_model: str = None,
                           provider: str = "minimax") -> str | None:
    """
    Use AI to transform raw research into a structured Research Brief.
    This is the KEY step: instead of dumping raw articles into the tweet prompt,
    we first extract the most useful facts, data, and angles.

    Returns a structured brief optimized for tweet writing, or None if AI unavailable.
    """
    if not ai_client:
        return None

    prompt = f"""Aşağıda bir tweet ve o tweet hakkında yapılmış araştırma sonuçları var.

ORİJİNAL TWEET:
"{original_tweet[:800]}"

ARAŞTIRMA SONUÇLARI:
{raw_summary[:6000]}

---

GÖREV: Bu araştırmadan tweet yazarken kullanılabilecek en değerli bilgileri çıkar.
Sadece TWEET KONUSUYLA İLGİLİ bilgileri dahil et, alakasız olanları AT.

Yanıtını şu formatta yaz:

## TEMEL BULGULAR
(Tweet'in konusuyla doğrudan ilgili en önemli 3-5 bilgi. Her biri tek cümle.)

## RAKAMLAR VE VERİLER
(Spesifik rakamlar, yüzdeler, dolar tutarları, tarihler — tweet'e güç katacak veriler.)

## UZMAN GÖRÜŞLERİ / ALITILAR
(Varsa, kaynaklardan alıntılanabilecek görüşler veya ifadeler.)

## KARŞIT GÖRÜŞ / ÇELİŞKİ
(Konuyla ilgili karşıt bir bakış açısı veya ilginç bir çelişki varsa yaz.)

## BAĞLAM
(Bu olay neden önemli? Piyasa etkisi, sektörel anlam, trend bağlamı.)

KURALLAR:
- Her madde TEK CÜMLE olsun, kısa ve net
- Sadece GERÇEK bilgi yaz, yorum ekleme
- Tweet konusuyla ALAKASIZ bilgileri dahil etme
- "Bulunamadı" yazmak yerine o bölümü boş bırak
- Araştırmada bilgi yoksa bölümü atla"""

    try:
        if provider == "anthropic":
            import anthropic
            response = ai_client.messages.create(
                model=ai_model or "claude-haiku-4-5-20251001",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return response.content[0].text.strip()
        else:
            response = ai_client.chat.completions.create(
                model=ai_model or "MiniMax-M2.5",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1,
            )
            result = response.choices[0].message.content.strip()
            # Strip <think> tags from reasoning models
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            return result

    except Exception as e:
        print(f"AI research synthesis error: {e}")
        return None


# ========================================================================
# RESEARCH SUMMARY COMPILER
# ========================================================================

def compile_research_summary(r: ResearchResult) -> str:
    """
    Build structured research context optimized for tweet writing.

    Priority order (most important first):
    1. Original tweet/thread (the ANCHOR)
    2. Deep articles (highest info density)
    3. Web snippets (supporting context)
    4. Reddit discussions (community perspective)
    5. X opinions (limited — only high-engagement ones)

    Keeps total under ~5000 chars to avoid token bloat.
    """
    parts = []
    total_chars = 0
    MAX_TOTAL = 5500  # Target max for research context

    # Section 1: Original tweet/thread — MOST IMPORTANT (always included)
    parts.append(f"# ANA KONU: {r.topic}")

    if len(r.thread_texts) > 1:
        parts.append(f"\n## ORİJİNAL THREAD (@{r.original_tweet_author}) - {len(r.thread_texts)} tweet:")
        for i, t in enumerate(r.thread_texts, 1):
            parts.append(f"  {i}/ {t}")
    else:
        parts.append(f"\n## ORİJİNAL TWEET (@{r.original_tweet_author}):")
        parts.append(f"  {r.original_tweet_text}")

    total_chars = sum(len(p) for p in parts)

    # Section 2: DEEP ARTICLES — Key content from fetched pages
    # Limit each article to 2000 chars, max 3 articles
    if r.deep_articles:
        parts.append(f"\n## ARAŞTIRMA KAYNAKLARI ({len(r.deep_articles)} makale okundu):")
        for i, article in enumerate(r.deep_articles[:3], 1):
            content = article['content'][:2000]
            article_text = f"\n### Kaynak {i}: {article['title']}\n{content}"
            if total_chars + len(article_text) > MAX_TOTAL:
                # Truncate this article to fit budget
                remaining = max(500, MAX_TOTAL - total_chars - 200)
                article_text = f"\n### Kaynak {i}: {article['title']}\n{article['content'][:remaining]}..."
            parts.append(article_text)
            total_chars += len(article_text)

    # Section 3: Web search snippets (compact — title + snippet)
    if r.web_results and total_chars < MAX_TOTAL - 300:
        deep_urls = {a["url"] for a in r.deep_articles}
        remaining = [wr for wr in r.web_results if wr["url"] not in deep_urls]

        if remaining:
            parts.append(f"\n## Ek Web Bulguları ({len(remaining)} kaynak):")
            for i, wr in enumerate(remaining[:5], 1):
                snippet = f"  {i}. {wr['title']}: {wr['body'][:250]}"
                if total_chars + len(snippet) > MAX_TOTAL:
                    break
                parts.append(snippet)
                total_chars += len(snippet)

    # Section 4: Reddit (compact)
    if r.reddit_results and total_chars < MAX_TOTAL - 200:
        deep_urls = {a["url"] for a in r.deep_articles}
        remaining_reddit = [rr for rr in r.reddit_results if rr["url"] not in deep_urls]
        if remaining_reddit:
            parts.append(f"\n## Reddit Tartışmaları:")
            for i, rr in enumerate(remaining_reddit[:3], 1):
                snippet = f"  {i}. {rr['title']}: {rr['body'][:200]}"
                if total_chars + len(snippet) > MAX_TOTAL:
                    break
                parts.append(snippet)
                total_chars += len(snippet)

    # Section 5: X opinions — ONLY high-engagement, max 3
    # (This is where irrelevant tangents come from — be very selective)
    if r.related_tweets and total_chars < MAX_TOTAL - 200:
        # Only include tweets with significant engagement
        quality_tweets = [rt for rt in r.related_tweets
                          if rt.get("likes", 0) >= 5 or rt.get("retweets", 0) >= 2]
        if quality_tweets:
            parts.append(f"\n## X'te Öne Çıkan Yorumlar ({len(quality_tweets)} kaliteli):")
            for i, rt in enumerate(quality_tweets[:3], 1):
                snippet = f"  {i}. @{rt['author']} ({rt['likes']}❤️): {rt['text'][:150]}"
                if total_chars + len(snippet) > MAX_TOTAL:
                    break
                parts.append(snippet)
                total_chars += len(snippet)

    return "\n".join(parts)


# ========================================================================
# TOPIC-BASED RESEARCH (for normal tweet writing — no quote tweet needed)
# ========================================================================

@dataclass
class TopicResearchResult:
    """Research result for a user-provided topic (not a quote tweet)."""
    topic_input: str = ""
    topic: str = ""
    search_mode: str = "x_only"  # "x_only" or "x_and_web"
    x_tweets: list = field(default_factory=list)
    web_results: list = field(default_factory=list)
    deep_articles: list = field(default_factory=list)
    news_results: list = field(default_factory=list)
    summary: str = ""


def research_topic_from_text(
    topic_input: str,
    scanner=None,
    time_hours: int = 12,
    search_mode: str = "x_only",
    progress_callback=None,
    ai_client=None,
    ai_model: str = None,
    ai_provider: str = "minimax",
) -> TopicResearchResult:
    """
    Research a topic by searching X and optionally the web.

    Args:
        topic_input: User's topic text
        scanner: TwitterScanner instance for X search
        time_hours: How far back to search
        search_mode: "x_only" | "x_and_web" | "x_deep" (50-100 tweets for personal mode)
        progress_callback: Progress update function
        ai_client: AI client for topic extraction
        ai_model: AI model name
        ai_provider: AI provider name

    Steps:
    1. AI extracts keywords & generates diverse search queries
    2. Deep search X with multiple query variations (TR + EN)
    3. (Optional) Search web + news if search_mode == "x_and_web"
    4. Compile into context for tweet generation
    """
    result = TopicResearchResult(topic_input=topic_input, search_mode=search_mode)

    # === STEP 1: Understand the topic & generate search queries ===
    if progress_callback:
        progress_callback("Konu analiz ediliyor ve arama sorguları üretiliyor...")

    ai_topic = None
    if ai_client:
        ai_topic = _ai_extract_topic_for_research(
            topic_input, ai_client, ai_model, ai_provider
        )

    # Fallback: regex-based extraction
    topic_info = extract_topic_from_text(topic_input)

    if ai_topic and ai_topic.get("x_queries_en"):
        result.topic = ai_topic["topic"]
        search_queries = ai_topic.get("search_queries", {})
        x_queries_tr = ai_topic.get("x_queries_tr", [])
        x_queries_en = ai_topic.get("x_queries_en", [])
    else:
        result.topic = topic_info["topic"]
        search_queries = topic_info["search_queries"]
        # Build X queries from entities
        entities = topic_info["products"][:2] + topic_info["companies"][:2]
        action = topic_info.get("action", "")
        if entities:
            x_queries_en = [
                f"({' OR '.join(entities)}) {action or ''} -is:retweet lang:en".strip(),
                f"({' OR '.join(entities)}) -is:retweet",
            ]
            x_queries_tr = [f"({' OR '.join(entities)}) -is:retweet lang:tr"]
        else:
            words = topic_input.split()[:5]
            q = " ".join(words)
            x_queries_en = [f"({q}) -is:retweet lang:en", f"({q}) -is:retweet"]
            x_queries_tr = [f"({q}) -is:retweet lang:tr"]

    if progress_callback:
        progress_callback(f"Konu: {result.topic}")

    # === STEP 2: Deep X search with multiple query variations ===
    is_deep_mode = search_mode == "x_deep"
    if scanner:
        if progress_callback:
            label = "X'te derin arama yapılıyor (50-100 tweet)..." if is_deep_mode else "X'te detaylı arama yapılıyor..."
            progress_callback(label)

        # In deep mode, search wider time range and more tweets per query
        search_hours = max(time_hours, 48) if is_deep_mode else time_hours
        start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=search_hours)
        per_query = 15 if is_deep_mode else 20

        seen_ids = set()

        # Combine all X queries — run ALL of them
        all_x_queries = x_queries_en + x_queries_tr

        # Also build extra variations for thorough coverage
        extra_queries = _build_x_query_variations(topic_input, result.topic, ai_topic)
        all_x_queries.extend(extra_queries)

        # In deep mode, add even more query variations
        if is_deep_mode:
            # Add min engagement queries for quality tweets
            for q in x_queries_en[:3]:
                base = q.replace("min_faves:5", "").replace("min_faves:10", "").strip()
                all_x_queries.append(f"{base} min_faves:20")
                all_x_queries.append(f"{base} min_faves:50")

        # Deduplicate queries (case-insensitive)
        seen_queries = set()
        unique_queries = []
        for q in all_x_queries:
            q_key = q.lower().strip()
            if q_key not in seen_queries:
                seen_queries.add(q_key)
                unique_queries.append(q)

        total_queries = len(unique_queries)
        if progress_callback:
            progress_callback(f"X'te {total_queries} farklı arama yapılıyor...")

        for idx, q in enumerate(unique_queries):
            if progress_callback and idx > 0 and idx % 3 == 0:
                progress_callback(f"X araması {idx}/{total_queries}... ({len(result.x_tweets)} tweet bulundu)")
            try:
                tweets = scanner._search_tweets(q, start, per_query)
                for t in tweets:
                    if t.id not in seen_ids and len(t.text) > 40:
                        seen_ids.add(t.id)
                        result.x_tweets.append({
                            "text": t.text,
                            "author": t.author_username,
                            "likes": t.like_count,
                            "retweets": t.retweet_count,
                            "url": t.url,
                            "created_at": t.created_at.isoformat() if t.created_at else "",
                        })
            except Exception as e:
                print(f"X topic search error ({q[:50]}): {e}")

        # Sort by engagement
        result.x_tweets.sort(key=lambda x: x.get("likes", 0) + x.get("retweets", 0) * 2, reverse=True)

        # Keep top tweets sorted by engagement
        max_keep = 35 if is_deep_mode else 25
        result.x_tweets = result.x_tweets[:max_keep]

        if progress_callback:
            progress_callback(f"X'te {len(result.x_tweets)} tweet bulundu")

    # === STEP 3: Web + News search (ONLY if search_mode == "x_and_web") ===
    if search_mode == "x_and_web":
        if progress_callback:
            progress_callback("Web'de güncel bilgiler aranıyor...")

        all_urls = set()

        # General web search — last day first, then week
        for query in search_queries.get("general", [])[:3]:
            results = web_search(query, max_results=6, timelimit="d")
            if not results:
                results = web_search(query, max_results=6, timelimit="w")
            for r in results:
                if r["url"] not in all_urls:
                    all_urls.add(r["url"])
                    result.web_results.append(r)

        # News search — last day
        if progress_callback:
            progress_callback("Son haberler aranıyor...")
        for query in search_queries.get("news", [])[:2]:
            news = web_search_news(query, max_results=5, timelimit="d")
            if not news:
                news = web_search_news(query, max_results=5, timelimit="w")
            for n in news:
                if n["url"] not in all_urls:
                    all_urls.add(n["url"])
                    result.news_results.append({
                        "title": n["title"],
                        "url": n["url"],
                        "body": n["body"],
                        "source": n.get("source", ""),
                    })

        # Deep fetch top articles
        if progress_callback:
            progress_callback("Makaleler okunuyor...")

        all_search_results = result.web_results + result.news_results
        urls_to_fetch = _pick_best_urls(all_search_results)

        fetched = 0
        for url in urls_to_fetch:
            if fetched >= 3:
                break
            article = fetch_article_content(url)
            if article and article["content"] and len(article["content"]) > 200:
                result.deep_articles.append(article)
                fetched += 1

    # === STEP 4: Compile summary ===
    if progress_callback:
        progress_callback("Araştırma derleniyor...")
    result.summary = _compile_topic_research_summary(result)
    return result


def _build_x_query_variations(topic_input: str, topic_en: str, ai_topic: dict | None) -> list[str]:
    """
    Build extra X search query variations for thorough coverage.
    Extracts keywords and creates different combinations.
    """
    extra = []

    # Extract key words from topic_input (Turkish)
    # Remove common Turkish stop words
    tr_stop = {"bir", "ve", "de", "da", "bu", "şu", "o", "ile", "için", "gibi",
               "ama", "ya", "diye", "ki", "mi", "mu", "mü", "mı", "ne", "var",
               "yok", "olan", "ben", "sen", "biz", "siz", "onlar", "kadar"}
    tr_words = [w for w in topic_input.split() if w.lower() not in tr_stop and len(w) > 2]

    # Extract key words from English topic
    en_stop = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
               "to", "for", "of", "and", "or", "but", "has", "had", "by", "its"}
    en_words = [w for w in topic_en.split() if w.lower() not in en_stop and len(w) > 2] if topic_en else []

    # Build variations from Turkish keywords
    if len(tr_words) >= 2:
        # Pairs of keywords
        for i in range(min(len(tr_words), 4)):
            for j in range(i + 1, min(len(tr_words), 4)):
                q = f"{tr_words[i]} {tr_words[j]} -is:retweet"
                extra.append(q)

    # Build variations from English keywords
    if len(en_words) >= 2:
        for i in range(min(len(en_words), 4)):
            for j in range(i + 1, min(len(en_words), 4)):
                q = f"{en_words[i]} {en_words[j]} -is:retweet lang:en"
                extra.append(q)

    # Use AI-provided keywords if available
    if ai_topic:
        kw_tr = ai_topic.get("keywords_tr", [])
        kw_en = ai_topic.get("keywords_en", [])

        # Build OR queries from keyword groups
        if len(kw_en) >= 2:
            # Top keywords combined
            extra.append(f"({' '.join(kw_en[:3])}) -is:retweet lang:en")
            # Individual important keywords with min engagement
            for kw in kw_en[:3]:
                if len(kw) > 3:
                    extra.append(f"{kw} -is:retweet lang:en min_faves:5")

        if len(kw_tr) >= 2:
            extra.append(f"({' '.join(kw_tr[:3])}) -is:retweet lang:tr")

    # Limit total extra queries to prevent rate limiting
    return extra[:8]


def _ai_extract_topic_for_research(
    topic_input: str, ai_client, ai_model: str, provider: str
) -> dict | None:
    """Use AI to understand user's topic input and generate X + web search queries."""
    current_year = str(datetime.datetime.now().year)

    prompt = f"""Kullanıcı şu konuda tweet yazmak istiyor:
"{topic_input}"

Bu konuyu analiz et ve X/Twitter + web arama sorguları üret.

SADECE şu JSON formatında yanıt ver:
{{
    "topic": "konunun 5-10 kelimelik İngilizce özeti",
    "keywords_tr": ["türkçe", "anahtar", "kelimeler", "max 5"],
    "keywords_en": ["english", "keywords", "max 5"],
    "x_queries_tr": [
        "X'te Türkçe arama sorgusu 1 -is:retweet lang:tr",
        "X'te Türkçe arama sorgusu 2 -is:retweet lang:tr",
        "X'te Türkçe arama sorgusu 3 -is:retweet lang:tr"
    ],
    "x_queries_en": [
        "X English search query 1 -is:retweet lang:en",
        "X English search query 2 -is:retweet lang:en",
        "X English search query 3 -is:retweet lang:en",
        "X English search query 4 -is:retweet lang:en"
    ],
    "general_queries": ["web araması 1 {current_year}", "web araması 2 {current_year}"],
    "news_queries": ["haber araması 1 {current_year}", "haber araması 2"]
}}

ÖNEMLİ KURALLAR:
- x_queries: X/Twitter'da arama yapılacak. KISA ve SPESİFİK sorgular yaz
- X sorgularında FARKLI anahtar kelime kombinasyonları kullan — her sorgu farklı bir açıdan arasın
- Konuyu en az 4-5 farklı İngilizce X sorgusuyla ara (en önemlisi bu!)
- Konuyu en az 2-3 farklı Türkçe X sorgusuyla ara
- keywords_tr ve keywords_en: konunun en önemli 3-5 anahtar kelimesi
- Her web sorguya {current_year} ekle
- Konuyu detaylı analiz et, sadece ana kelimeleri değil bağlam kelimelerini de kullan"""

    try:
        if provider == "anthropic":
            response = ai_client.messages.create(
                model=ai_model or "claude-haiku-4-5-20251001",
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw = response.content[0].text.strip()
        else:
            response = ai_client.chat.completions.create(
                model=ai_model or "MiniMax-M2.5",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.1,
            )
            raw = response.choices[0].message.content.strip()

        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            return None

        data = json.loads(json_match.group())

        return {
            "topic": data.get("topic", ""),
            "keywords_tr": data.get("keywords_tr", [])[:5],
            "keywords_en": data.get("keywords_en", [])[:5],
            "x_queries_tr": data.get("x_queries_tr", [])[:4],
            "x_queries_en": data.get("x_queries_en", [])[:5],
            "search_queries": {
                "general": data.get("general_queries", [])[:3],
                "news": data.get("news_queries", [])[:2],
                "technical": [],
                "reddit": [],
            },
        }
    except Exception as e:
        print(f"AI topic research extraction error: {e}")
        return None


def _compile_topic_research_summary(r: TopicResearchResult) -> str:
    """Compile topic research into context for tweet generation."""
    parts = []

    parts.append(f"# ARAŞTIRMA KONUSU: {r.topic}")
    parts.append(f"Kullanıcının yazmak istediği konu: {r.topic_input}")

    # X tweets — ALWAYS the primary source
    if r.x_tweets:
        show_count = 10 if r.search_mode == "x_deep" else 15
        parts.append(f"\n## X'TE SON PAYLAŞIMLAR ({len(r.x_tweets)} tweet, en iyi {show_count} gösteriliyor):")
        parts.append("(Bu tweetler konuyla ilgili EN GÜNCEL bilgiler — BİRİNCİL KAYNAĞIN BUNLAR!)\n")
        for i, tw in enumerate(r.x_tweets[:show_count], 1):
            parts.append(f"  {i}. @{tw['author']} ({tw['likes']}L {tw['retweets']}RT): {tw['text'][:250]}")

    # Web content only if search_mode was x_and_web
    if r.search_mode == "x_and_web":
        if r.deep_articles:
            parts.append(f"\n## OKUNAN MAKALELER ({len(r.deep_articles)} kaynak):")
            for i, article in enumerate(r.deep_articles, 1):
                parts.append(f"### Kaynak {i}: {article['title']}")
                parts.append(f"URL: {article['url']}")
                parts.append(f"{article['content']}")
                parts.append("")

        if r.news_results:
            parts.append(f"\n## SON HABERLER ({len(r.news_results)} haber):")
            for i, n in enumerate(r.news_results[:5], 1):
                src = f" ({n['source']})" if n.get("source") else ""
                parts.append(f"  {i}. {n['title']}{src}")
                parts.append(f"     {n['body'][:300]}")

        if r.web_results:
            deep_urls = {a["url"] for a in r.deep_articles}
            remaining = [w for w in r.web_results if w["url"] not in deep_urls]
            if remaining:
                parts.append(f"\n## EK WEB BULGULARI ({len(remaining)} kaynak):")
                for i, wr in enumerate(remaining[:5], 1):
                    parts.append(f"  {i}. {wr['title']}")
                    parts.append(f"     {wr['body'][:200]}")

    return "\n".join(parts)
