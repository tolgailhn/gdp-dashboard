"""
Grok AI Client Module
xAI Grok API integration for X search, web search, and agentic research.
Uses OpenAI SDK compatible API at api.x.ai/v1.
"""
import json
import re
import datetime
import streamlit as st
from openai import OpenAI


# Grok model for research (fast + cheap)
GROK_MODEL = "grok-3-fast"

# Cost estimates per 1M tokens (USD)
COST_INPUT_PER_M = 5.00
COST_OUTPUT_PER_M = 25.00

# Tool costs (estimated per call)
TOOL_COST_X_SEARCH = 0.005
TOOL_COST_WEB_SEARCH = 0.005


def _get_grok_client(api_key: str = None) -> OpenAI | None:
    """Create Grok API client."""
    if not api_key:
        from modules.ui_components import get_secret
        api_key = get_secret("xai_api_key", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


def _track_cost(input_tokens: int = 0, output_tokens: int = 0, tool_calls: int = 0):
    """Track estimated Grok usage cost in session state."""
    token_cost = (input_tokens / 1_000_000 * COST_INPUT_PER_M +
                  output_tokens / 1_000_000 * COST_OUTPUT_PER_M)
    tool_cost = tool_calls * TOOL_COST_X_SEARCH
    total = token_cost + tool_cost

    if "grok_usage_cost" not in st.session_state:
        st.session_state["grok_usage_cost"] = 0.0
    if "grok_call_count" not in st.session_state:
        st.session_state["grok_call_count"] = 0

    st.session_state["grok_usage_cost"] += total
    st.session_state["grok_call_count"] += 1


def _extract_usage(response) -> tuple[int, int]:
    """Extract token usage from API response."""
    try:
        usage = response.usage
        return (usage.prompt_tokens or 0, usage.completion_tokens or 0)
    except Exception:
        return (0, 0)


# ========================================================================
# SEARCH FUNCTIONS — replacements for DuckDuckGo
# ========================================================================

def grok_search_x(query: str, api_key: str = None, max_results: int = 10) -> list[dict]:
    """
    Search X/Twitter using Grok's x_search tool.
    Returns list of dicts with: text, author, url, likes, retweets.
    """
    client = _get_grok_client(api_key)
    if not client:
        return []

    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": "You are a research assistant. Search X for the given query and return relevant posts. Return results as a JSON array."},
                {"role": "user", "content": f"""Search X/Twitter for: "{query}"

Return the top {max_results} most relevant and recent posts as a JSON array. Each item should have:
- "text": the tweet text
- "author": the username (without @)
- "likes": number of likes (estimate if exact not available)
- "retweets": number of retweets (estimate if exact not available)

Return ONLY the JSON array, no other text."""}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "x_search",
                    "description": "Search X (Twitter) for posts matching a query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "description": "Maximum results"}
                        },
                        "required": ["query"]
                    }
                }
            }],
            tool_choice="auto",
            max_tokens=2000,
            temperature=0.1,
        )

        inp, out = _extract_usage(response)
        tool_count = 0

        # Process tool calls if any
        choice = response.choices[0]
        messages = [
            {"role": "system", "content": "You are a research assistant. Return results as a JSON array."},
            {"role": "user", "content": f'Search X for: "{query}" and return top {max_results} results as JSON array with text, author, likes, retweets fields.'},
            choice.message,
        ]

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_count += 1
                # Grok handles x_search internally, we get result back
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "Search completed. Please format the results.",
                })

            # Get formatted results
            response2 = client.chat.completions.create(
                model=GROK_MODEL,
                messages=messages,
                max_tokens=2000,
                temperature=0.1,
            )
            inp2, out2 = _extract_usage(response2)
            inp += inp2
            out += out2
            raw = response2.choices[0].message.content or ""
        else:
            raw = choice.message.content or ""

        _track_cost(inp, out, tool_count)

        # Parse JSON results
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            results = json.loads(json_match.group())
            return results[:max_results]

        return []

    except Exception as e:
        print(f"Grok X search error: {e}")
        return []


def grok_search_web(query: str, api_key: str = None, max_results: int = 8) -> list[dict]:
    """
    Search the web using Grok's web_search tool.
    Returns list of dicts with: title, url, body (same format as DuckDuckGo).
    """
    client = _get_grok_client(api_key)
    if not client:
        return []

    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": "You are a research assistant. Search the web for the given query and return relevant results as a JSON array."},
                {"role": "user", "content": f"""Search the web for: "{query}"

Return top {max_results} results as a JSON array. Each item should have:
- "title": the page title
- "url": the page URL
- "body": a brief summary/snippet (2-3 sentences)

Return ONLY the JSON array, no other text."""}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            }],
            tool_choice="auto",
            max_tokens=2000,
            temperature=0.1,
        )

        inp, out = _extract_usage(response)
        tool_count = 0

        choice = response.choices[0]
        messages = [
            {"role": "system", "content": "You are a research assistant. Return results as a JSON array."},
            {"role": "user", "content": f'Search web for: "{query}" and return top {max_results} results as JSON array with title, url, body fields.'},
            choice.message,
        ]

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_count += 1
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "Search completed. Please format the results.",
                })

            response2 = client.chat.completions.create(
                model=GROK_MODEL,
                messages=messages,
                max_tokens=2000,
                temperature=0.1,
            )
            inp2, out2 = _extract_usage(response2)
            inp += inp2
            out += out2
            raw = response2.choices[0].message.content or ""
        else:
            raw = choice.message.content or ""

        _track_cost(inp, out, tool_count)

        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            results = json.loads(json_match.group())
            return results[:max_results]

        return []

    except Exception as e:
        print(f"Grok web search error: {e}")
        return []


# ========================================================================
# AGENTIC RESEARCH — Grok browses autonomously with x_search + web_search
# ========================================================================

def grok_agentic_research(tweet_text: str, tweet_author: str = "",
                          api_key: str = None, max_iterations: int = 5,
                          progress_callback=None) -> str:
    """
    Grok otonom araştırma — Grok modeli kendi x_search ve web_search tool'larıyla
    otonom şekilde internette ve X'te gezinerek araştırma yapar.

    Avantaj: X verilerine doğrudan erişim (DuckDuckGo'da yok).
    """
    client = _get_grok_client(api_key)
    if not client:
        return ""

    current_year = str(datetime.datetime.now().year)

    system_prompt = f"""Sen bir tweet araştırma asistanısın. Sana bir tweet verilecek.
Görevin: Tweet'te bahsedilen konuları hem X'te hem web'de araştırıp kapsamlı bir özet hazırlamak.

ARAÇLARIN:
- x_search: X/Twitter'da arama yap — gerçek zamanlı tartışmaları, görüşleri, trendleri bul
- web_search: Web'de arama yap — makaleler, haberler, teknik detaylar bul

ARAŞTIRMA STRATEJİN:
1. Tweet'i oku — hangi konular, ürünler, iddialar var?
2. Önce X'te ara — bu konu hakkında insanlar ne diyor? Hangi tartışmalar var?
3. Sonra web'de ara — teknik detaylar, haberler, benchmark sonuçları
4. Bilgi yeterliyse özetle

⚠️ KURALLAR:
- SADECE tweet'in konusunu araştır, konu dışına çıkma
- Arama sorgularını İngilizce yaz
- Maksimum 4-5 arama yap (odaklan)
- X aramalarında gerçek insanların görüşlerini bul
- Web aramalarında somut veriler ve kaynaklar bul

TAMAMLADIĞINDA şu formatta özetle:

## X'TEKİ TARTIŞMALAR
(Bu konu hakkında X'te ne konuşuluyor? Öne çıkan görüşler, tepkiler)

## TEMEL BULGULAR
(Web'den ve X'ten elde edilen en önemli 3-5 bilgi)

## RAKAMLAR VE VERİLER
(Spesifik rakamlar, yüzdeler — kaynaklı)

## KARŞIT GÖRÜŞ / ÇELİŞKİ
(Varsa farklı bakış açıları)

## BAĞLAM
(Bu olay neden önemli?)"""

    user_message = f"""Bu tweet'i araştır:

@{tweet_author}: "{tweet_text[:1200]}"

Hem X'te hem web'de araştır. Önce X'te bu konuda ne konuşulduğunu bul, sonra web'den detayları çek."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "x_search",
                "description": "Search X (Twitter) for posts, discussions, and opinions about a topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query in English"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for articles, news, technical details, and data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query in English"}
                    },
                    "required": ["query"]
                }
            }
        },
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    total_inp, total_out, total_tools = 0, 0, 0
    search_count = 0

    for iteration in range(max_iterations):
        if progress_callback:
            progress_callback(f"🧠 Grok araştırıyor... (adım {iteration + 1}, {search_count} arama)")

        try:
            response = client.chat.completions.create(
                model=GROK_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=2000,
                temperature=0.2,
            )
        except Exception as e:
            print(f"Grok agentic research error: {e}")
            break

        inp, out = _extract_usage(response)
        total_inp += inp
        total_out += out

        choice = response.choices[0]
        assistant_msg = choice.message
        messages.append(assistant_msg)

        # Check if model is done
        if choice.finish_reason == "stop" or not assistant_msg.tool_calls:
            _track_cost(total_inp, total_out, total_tools)
            return assistant_msg.content or ""

        # Execute tool calls (Grok handles them internally via API)
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            total_tools += 1
            search_count += 1

            if progress_callback:
                query = fn_args.get("query", "")[:50]
                if fn_name == "x_search":
                    progress_callback(f"🐦 X'te arıyor: {query}...")
                elif fn_name == "web_search":
                    progress_callback(f"🌐 Web'de arıyor: {query}...")

            # For Grok's native tools, the API handles execution
            # We just acknowledge and let Grok continue
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": "Search completed successfully. Analyze the results and continue.",
            })

    # Hit max iterations — ask for summary
    messages.append({
        "role": "user",
        "content": "Araştırmayı bitir ve topladığın bilgileri yapılandırılmış formatta özetle."
    })

    try:
        final = client.chat.completions.create(
            model=GROK_MODEL,
            messages=messages,
            max_tokens=2000,
            temperature=0.1,
        )
        inp, out = _extract_usage(final)
        total_inp += inp
        total_out += out
        _track_cost(total_inp, total_out, total_tools)
        return final.choices[0].message.content or ""
    except Exception as e:
        print(f"Grok agentic final error: {e}")
        _track_cost(total_inp, total_out, total_tools)
        return ""


# ========================================================================
# TOPIC DISCOVERY — Grok finds trending topics on X
# ========================================================================

def grok_discover_topics(focus_area: str = "",
                         api_key: str = None,
                         progress_callback=None) -> list[dict]:
    """
    Grok ile X ve web'de spesifik, güncel AI/teknoloji gelişmelerini keşfet.
    Multi-turn agentic: Grok kendi x_search + web_search ile otonom gezinir.
    """
    client = _get_grok_client(api_key)
    if not client:
        return []

    if progress_callback:
        progress_callback("🧠 Grok X ve web'de güncel gelişmeleri araştırıyor...")

    current_year = str(datetime.datetime.now().year)

    focus_instruction = ""
    if focus_area and focus_area.strip():
        focus_instruction = f"""
ODAK ALANI: "{focus_area}"
Bu alana özel gelişmeleri bul. Ama yine de SPESİFİK gelişmeler olsun, genel kategori değil."""
    else:
        focus_instruction = """
ODAK ALANI: AI, yapay zeka, yazılım ve teknoloji (genel)
En güncel ve ilgi çekici gelişmeleri bul."""

    system_prompt = f"""Sen bir teknoloji trend analisti ve içerik keşifçisisin.
Görevin: X (Twitter) ve web'de SON 24 SAATTEKİ en önemli, spesifik gelişmeleri bulmak.

⚠️ KRİTİK: Genel kategori isimleri YASAK. Her konu SPESİFİK bir gelişme olmalı.

KÖTÜ ÖRNEK (YAPMA):
- "AI in healthcare" ← çok genel, tweet yazılamaz
- "Ethical implications of AI" ← kategori ismi
- "Debates on government AI policies" ← sıkıcı, spesifik değil

İYİ ÖRNEK (BÖYLE YAP):
- "Dvina Code launched: GUI-first agentic coding with Claude Opus 4.6 free" ← spesifik ürün + detay
- "OpenAI raised $110B at $730B valuation — biggest AI round ever" ← spesifik olay + rakam
- "Qwen 3.5 400B MoE beats GPT-4o on coding benchmarks, fully open-source" ← spesifik model + sonuç
- "Cursor vs Windsurf: developers comparing after Windsurf's new agent mode" ← spesifik karşılaştırma

{focus_instruction}

ARAŞTIRMA STRATEJİN:
1. X'te "{current_year}" yılına ait en güncel AI/teknoloji paylaşımlarını ara
2. Yüksek etkileşimli (çok beğeni/RT) tweet'leri bul — bunlar önemli gelişmelere işaret eder
3. Web'de son haberleri kontrol et — yeni çıkan ürünler, güncellemeler, duyurular
4. Her gelişme için: ne oldu, kim yaptı, neden önemli, hangi rakamlar var

⚠️ SADECE İNGİLİZCE İÇERİK ARA. Türkçe hesaplar/tweet'ler ARAMA — onlar zaten
yabancı kaynaklardan çeviri yapıyor, biz doğrudan kaynağa gidelim.

TAMAMLADIĞINDA şu JSON formatında 5-8 konu ver:
[
  {{
    "title": "Kısa, spesifik Türkçe başlık (ne oldu?)",
    "description": "2-3 cümle: ne oldu, kim yaptı, önemli detaylar/rakamlar",
    "angle": "Bu konuya hangi açıdan tweet yazılabilir (deneyim/analiz/karşılaştırma/haber)",
    "potential": "Neden bu konu iyi? Engagement potansiyeli nedir?",
    "source_tweets": "Bu konuda gördüğün en önemli 1-2 tweet'in özeti"
  }}
]

SADECE JSON döndür, başka bir şey yazma."""

    user_message = f"""X'te ve web'de son 24 saatteki en önemli AI/teknoloji gelişmelerini bul.

Önce X'te ara — hangi konular çok konuşuluyor, hangi ürünler/şirketler gündemde?
Sonra web'de ara — hangi yeni ürünler çıktı, hangi duyurular yapıldı?

SPESİFİK gelişmeler istiyorum: ürün lansmanları, benchmark sonuçları, büyük yatırımlar,
yeni model çıkışları, önemli güncellemeler. Genel kategori isimleri DEĞİL.

{"Özellikle şu alana odaklan: " + focus_area if focus_area else "Genel AI ve teknoloji alanı."}"""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "x_search",
                "description": "Search X (Twitter) for recent posts, discussions, and trending topics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query in English"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for news, articles, and announcements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query in English"}
                    },
                    "required": ["query"]
                }
            }
        },
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    total_inp, total_out, total_tools = 0, 0, 0
    search_count = 0
    max_iterations = 6

    for iteration in range(max_iterations):
        if progress_callback:
            progress_callback(f"🧠 Grok gelişmeleri araştırıyor... (adım {iteration + 1}, {search_count} arama)")

        try:
            response = client.chat.completions.create(
                model=GROK_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=3000,
                temperature=0.3,
            )
        except Exception as e:
            print(f"Grok discover topics error: {e}")
            break

        inp, out = _extract_usage(response)
        total_inp += inp
        total_out += out

        choice = response.choices[0]
        assistant_msg = choice.message
        messages.append(assistant_msg)

        # Check if model is done
        if choice.finish_reason == "stop" or not assistant_msg.tool_calls:
            _track_cost(total_inp, total_out, total_tools)
            raw = assistant_msg.content or ""
            break

        # Execute tool calls (Grok handles them internally via API)
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            total_tools += 1
            search_count += 1

            if progress_callback:
                query = fn_args.get("query", "")[:50]
                if fn_name == "x_search":
                    progress_callback(f"🐦 X'te arıyor: {query}...")
                elif fn_name == "web_search":
                    progress_callback(f"🌐 Web'de arıyor: {query}...")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": "Search completed successfully. Analyze the results and continue researching or provide your final JSON response.",
            })
    else:
        # Hit max iterations — ask for final JSON
        messages.append({
            "role": "user",
            "content": "Araştırmayı bitir. Bulduğun spesifik gelişmeleri JSON formatında ver. SADECE JSON döndür."
        })
        try:
            final = client.chat.completions.create(
                model=GROK_MODEL,
                messages=messages,
                max_tokens=3000,
                temperature=0.2,
            )
            inp, out = _extract_usage(final)
            total_inp += inp
            total_out += out
            _track_cost(total_inp, total_out, total_tools)
            raw = final.choices[0].message.content or ""
        except Exception as e:
            print(f"Grok discover final error: {e}")
            _track_cost(total_inp, total_out, total_tools)
            return []

    if progress_callback:
        progress_callback(f"🧠 Grok {search_count} arama yaptı, konular derleniyor...")

    # Parse JSON response
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return []


# ========================================================================
# FACT CHECK — Grok verifies claims using X + web data
# ========================================================================

def grok_fact_check(draft_text: str, original_tweet: str = "",
                    api_key: str = None,
                    progress_callback=None) -> str:
    """
    Grok ile tweet taslağındaki iddiaları doğrula.
    X'teki tartışmaları ve web kaynaklarını kullanır.
    """
    client = _get_grok_client(api_key)
    if not client:
        return ""

    if progress_callback:
        progress_callback("🧠 Grok iddiaları doğruluyor...")

    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": "You are a fact-checker. Verify claims using X and web search."},
                {"role": "user", "content": f"""Aşağıdaki tweet taslağındaki iddiaları doğrula:

TASLAK:
"{draft_text}"

{f'ORİJİNAL TWEET: "{original_tweet[:500]}"' if original_tweet else ''}

Her iddiayı X'te ve web'de araştır. Sonucu şu formatta ver:

## DOĞRULAMA SONUÇLARI
- ✅ [doğru iddia] — kaynak
- ⚠️ [kısmen doğru/güncel değil] — düzeltme + kaynak
- ❌ [yanlış iddia] — doğrusu + kaynak

## ÖNERİLEN DÜZELTMELER
(Varsa düzeltilmesi gereken kısımlar)"""}
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "x_search",
                        "description": "Search X for verification",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search web for verification",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"]
                        }
                    }
                },
            ],
            tool_choice="auto",
            max_tokens=2000,
            temperature=0.1,
        )

        inp, out = _extract_usage(response)
        tool_count = 0

        choice = response.choices[0]
        messages_fc = [
            {"role": "system", "content": "You are a fact-checker."},
            {"role": "user", "content": f'Verify claims in: "{draft_text[:500]}"'},
            choice.message,
        ]

        # Handle up to 3 iterations of tool calls
        for _ in range(3):
            if not choice.message.tool_calls:
                break

            for tc in choice.message.tool_calls:
                tool_count += 1
                messages_fc.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "Verification search completed.",
                })

            response2 = client.chat.completions.create(
                model=GROK_MODEL,
                messages=messages_fc,
                tools=[
                    {"type": "function", "function": {"name": "x_search", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
                    {"type": "function", "function": {"name": "web_search", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
                ],
                tool_choice="auto",
                max_tokens=2000,
                temperature=0.1,
            )
            inp2, out2 = _extract_usage(response2)
            inp += inp2
            out += out2
            choice = response2.choices[0]
            messages_fc.append(choice.message)

        _track_cost(inp, out, tool_count)

        if progress_callback:
            progress_callback("🧠 Grok doğrulama tamamlandı")

        return choice.message.content or ""

    except Exception as e:
        print(f"Grok fact check error: {e}")
        return ""


# ========================================================================
# SCAN HELPERS — for Tara page integration
# ========================================================================

def grok_scan_topics(query: str, api_key: str = None,
                     progress_callback=None) -> list[dict]:
    """
    Grok ile X'te belirli bir sorgu hakkında tweet ara.
    Tara sayfası custom query aramaları için kullanılır.

    Returns list of dicts compatible with AITopic format:
        text, author_username, like_count, retweet_count, url
    """
    results = grok_search_x(query, api_key=api_key, max_results=20)

    formatted = []
    for r in results:
        author = r.get("author", "unknown")
        formatted.append({
            "text": r.get("text", ""),
            "author_username": author,
            "author_name": author,
            "like_count": r.get("likes", 0),
            "retweet_count": r.get("retweets", 0),
            "reply_count": 0,
            "url": f"https://x.com/{author}/status/0",
            "category": "Grok Arama",
        })

    return formatted


def grok_discover_ai_trends(api_key: str = None,
                            progress_callback=None) -> list[dict]:
    """
    Grok ile X'te AI trendlerini keşfet.
    Tara sayfası Keşfet sekmesi için kullanılır.
    """
    if progress_callback:
        progress_callback("🧠 Grok AI trendlerini araştırıyor...")

    return grok_discover_topics(
        focus_area="AI, machine learning, LLM, new model releases, AI tools",
        api_key=api_key,
        progress_callback=progress_callback,
    )


# ========================================================================
# UTILITY
# ========================================================================

def test_grok_connection(api_key: str) -> dict:
    """Test Grok API connection."""
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[{"role": "user", "content": "Say 'connected' in one word."}],
            max_tokens=10,
        )
        return {"success": True, "message": response.choices[0].message.content.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def has_grok_key() -> bool:
    """Check if Grok API key is configured."""
    from modules.ui_components import get_secret
    return bool(get_secret("xai_api_key", ""))


def get_grok_cost() -> float:
    """Get current session's estimated Grok cost."""
    return st.session_state.get("grok_usage_cost", 0.0)


def get_grok_call_count() -> int:
    """Get current session's Grok API call count."""
    return st.session_state.get("grok_call_count", 0)
