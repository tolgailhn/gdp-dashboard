"""
AI Gündem Tarayıcı Sayfası
X/Twitter'da AI gelişmelerini tarar ve listeler
"""
import streamlit as st
import datetime
from collections import defaultdict
from modules.ui_components import (inject_custom_css, check_password, render_tweet_card,
                                   get_secret, render_sidebar_nav, render_research_engine_toggle)
from modules.twitter_scanner import (
    TwitterScanner, DEFAULT_AI_ACCOUNTS, is_turkish_account,
    generate_content_summary, MIN_FOLLOWER_COUNT_DISCOVER, is_ai_relevant
)
from modules.style_manager import load_monitored_accounts

# Page config
st.set_page_config(
    page_title="AI Tara | X AI Otomasyon",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_custom_css()

if not check_password():
    st.stop()

render_sidebar_nav(current_page="tara")

# --- Header ---
st.markdown("""
<div class="page-header">
    <span class="page-icon">🔍</span>
    <h1>AI Gündem Tarayıcı</h1>
    <p>X/Twitter'da son saatlerin AI gelişmelerini tara</p>
</div>
""", unsafe_allow_html=True)

# --- Main Tabs ---
main_tab1, main_tab2 = st.tabs(["🔍 Tara", "🌐 Keşfet"])

with main_tab1:

    # --- Controls ---
    col1, col2, col3 = st.columns(3)

    with col1:
        time_range = st.selectbox(
            "⏱️ Zaman",
            options=[6, 12, 24],
            format_func=lambda x: f"Son {x} saat",
            index=2,
            key="scan_time_range"
        )

    with col2:
        category_filter = st.selectbox(
            "📁 Kategori",
            options=["Tümü", "Yeni Model", "Model Güncelleme", "Araştırma",
                     "Benchmark", "Açık Kaynak", "API/Platform", "AI Ajanlar",
                     "Görüntü/Video", "Endüstri"],
            key="scan_category"
        )

    with col3:
        max_results = st.number_input(
            "📊 Maks. Sonuç",
            min_value=5, max_value=50, value=20,
            key="scan_max_results"
        )

    # Custom search query + filters
    with st.expander("⚙️ Gelişmiş Arama", expanded=False):
        custom_query = st.text_input(
            "Özel arama sorgusu",
            placeholder="Örn: 'Qwen release' veya 'GPT-5 leak'",
            key="custom_query"
        )
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            min_likes = st.number_input("Min. beğeni", min_value=0, value=10, key="min_likes")
        with fc2:
            min_retweets = st.number_input("Min. RT", min_value=0, value=5, key="min_retweets")
        with fc3:
            min_followers = st.number_input("Min. takipçi", min_value=0, value=500, key="min_followers")

        scan_engine = render_research_engine_toggle(key_suffix="scan")

    # --- Scan Button ---
    scan_clicked = st.button("🔍 Tara", type="primary", use_container_width=True, key="scan_button")

    # --- Results ---
    if scan_clicked:
        # Check API keys
        bearer_token = get_secret("twitter_bearer_token", "")
        api_key = get_secret("twitter_api_key", "")
        api_secret = get_secret("twitter_api_secret", "")
        access_token = get_secret("twitter_access_token", "")
        access_secret = get_secret("twitter_access_secret", "")

        # Twikit credentials (free alternative)
        twikit_username = get_secret("twikit_username", "")
        twikit_password = get_secret("twikit_password", "")
        twikit_email = get_secret("twikit_email", "")

        if not bearer_token and not twikit_username:
            st.error("Twitter API veya Twikit bilgileri yapılandırılmamış! Ayarlar sayfasından ekleyin.")
            st.stop()

        with st.spinner("X'te AI gelişmeleri taranıyor..."):
            try:
                scanner = TwitterScanner(
                    bearer_token=bearer_token,
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token,
                    access_secret=access_secret,
                    twikit_username=twikit_username,
                    twikit_password=twikit_password,
                    twikit_email=twikit_email,
                )

                if scanner.use_twikit:
                    st.success("Twikit ile taranıyor (ücretsiz)")
                elif scanner.client:
                    st.info("Twitter API ile taranıyor")
                else:
                    twikit_err = getattr(scanner, 'twikit_error', '')
                    if twikit_err:
                        st.error(f"Twikit bağlantı hatası: {twikit_err}")
                    else:
                        st.error("Ne Twikit ne de Twitter API bağlanamadı. Ayarlar sayfasından kontrol edin.")
                    st.stop()

                # Get custom accounts
                custom_accounts = load_monitored_accounts()

                # Build custom queries
                custom_queries = []
                if custom_query:
                    custom_queries.append(f"{custom_query} -is:retweet")

                # Scan (standard scanner for account-based search)
                topics = scanner.scan_ai_topics(
                    time_range_hours=time_range,
                    max_results_per_query=max_results,
                    custom_accounts=custom_accounts,
                    custom_queries=custom_queries if scan_engine != "grok" else [],
                )

                # Grok custom query search (if engine is grok and query exists)
                if scan_engine == "grok" and custom_query:
                    try:
                        from modules.grok_client import grok_scan_topics
                        from modules.twitter_scanner import AITopic
                        st.caption("🧠 Grok ile özel arama yapılıyor...")
                        grok_results = grok_scan_topics(custom_query)
                        for gr in grok_results:
                            # Convert to AITopic for consistency
                            grok_topic = AITopic(
                                id=f"grok_{hash(gr.get('text', '')[:50])}",
                                text=gr.get("text", ""),
                                author_name=gr.get("author_name", ""),
                                author_username=gr.get("author_username", ""),
                                like_count=gr.get("like_count", 0),
                                retweet_count=gr.get("retweet_count", 0),
                                reply_count=gr.get("reply_count", 0),
                                url=gr.get("url", ""),
                                category=gr.get("category", "Grok Arama"),
                            )
                            topics.append(grok_topic)
                    except Exception as e:
                        st.warning(f"Grok arama hatası: {e}")

                # Show search errors if any
                errors = getattr(scanner, 'search_errors', [])
                if errors:
                    unique_errors = list(dict.fromkeys(errors))[:5]
                    with st.expander(f"⚠️ {len(errors)} arama hatası oluştu", expanded=not topics):
                        for err in unique_errors:
                            st.warning(err)
                        if len(errors) > 5:
                            st.caption(f"...ve {len(errors) - 5} hata daha")

                # Store raw results before filtering (for account view)
                st.session_state.scan_results_raw = list(topics)

                # Apply filters
                if category_filter != "Tümü":
                    topics = [t for t in topics if t.category == category_filter]

                if min_likes > 0:
                    topics = [t for t in topics if t.like_count >= min_likes]

                if min_retweets > 0:
                    topics = [t for t in topics if t.retweet_count >= min_retweets]

                if min_followers > 0:
                    topics = [t for t in topics if t.author_followers_count == 0 or t.author_followers_count >= min_followers]

                # Store in session state
                st.session_state.scan_results = topics

            except Exception as e:
                st.error(f"Tarama hatası: {e}")
                st.session_state.scan_results = []

    # Display results
    if "scan_results" in st.session_state and st.session_state.scan_results:
        topics = st.session_state.scan_results

        st.markdown(f"### 📊 {len(topics)} sonuç bulundu")

        # Category summary
        categories = {}
        for t in topics:
            categories[t.category] = categories.get(t.category, 0) + 1

        if categories:
            cols = st.columns(min(len(categories), 5))
            for i, (cat, count) in enumerate(sorted(categories.items(), key=lambda x: -x[1])):
                with cols[i % len(cols)]:
                    st.metric(cat, count)

        # --- View Toggle ---
        view_mode = st.radio(
            "Görünüm",
            options=["relevans", "hesap"],
            format_func=lambda x: "🏆 Relevans Sırası" if x == "relevans" else "👤 Hesap Bazlı",
            horizontal=True,
            key="view_mode"
        )

        if view_mode == "hesap":
            # --- Account-Based View ---
            # Group topics by author
            account_topics = defaultdict(list)
            for t in topics:
                account_topics[t.author_username].append(t)

            # Also show accounts with NO results
            custom_accounts = load_monitored_accounts()
            all_tracked = DEFAULT_AI_ACCOUNTS + custom_accounts
            for acc in all_tracked:
                if acc.lower() not in [k.lower() for k in account_topics]:
                    account_topics[acc] = []

            # Sort: accounts with tweets first (by tweet count desc), then empty ones
            sorted_accounts = sorted(
                account_topics.items(),
                key=lambda x: (-len(x[1]), x[0].lower())
            )

            st.markdown(f"**{len([a for a, t in sorted_accounts if t])}** / **{len(sorted_accounts)}** hesapta tweet bulundu")

            for account_name, account_tweets in sorted_accounts:
                tweet_count = len(account_tweets)
                if tweet_count > 0:
                    top_tweet = max(account_tweets, key=lambda t: t.engagement_score)
                    total_likes = sum(t.like_count for t in account_tweets)
                    total_rts = sum(t.retweet_count for t in account_tweets)

                    with st.expander(
                        f"@{account_name} — {tweet_count} tweet | ❤️ {total_likes:,} | 🔁 {total_rts:,}",
                        expanded=False,
                    ):
                        for j, t in enumerate(account_tweets):
                            render_tweet_card(t, key_prefix=f"acc_{account_name}_{j}")

                            bcol1, bcol2, bcol3 = st.columns([1, 1, 1])
                            with bcol1:
                                if st.button("✍️ Bu konuda yaz", key=f"acc_write_{account_name}_{j}", use_container_width=True):
                                    st.session_state.selected_topic = {
                                        "text": t.text, "author": t.author_username,
                                        "url": t.url, "id": t.id, "category": t.category,
                                    }
                                    st.switch_page("pages/2_✍️_Yaz.py")
                            with bcol2:
                                if st.button("💬 Quote", key=f"acc_quote_{account_name}_{j}", use_container_width=True):
                                    st.session_state.quote_topic = {
                                        "text": t.text, "author": t.author_username,
                                        "url": t.url, "id": t.id,
                                    }
                                    st.session_state.write_mode = "quote"
                                    st.switch_page("pages/2_✍️_Yaz.py")
                            with bcol3:
                                st.link_button("🔗 X'te Aç", t.url, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px;
                                padding:10px 14px; margin:4px 0;">
                        <span style="color:#a5b4fc; font-weight:bold;">@{account_name}</span>
                        <span style="color:#94a3b8; font-size:12px; margin-left:8px;">— Bu zaman aralığında tweet bulunamadı</span>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            # --- Relevance View (original) ---
            for i, topic in enumerate(topics):
                render_tweet_card(topic, key_prefix=f"scan_{i}")

                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    if st.button("✍️ Bu konuda yaz", key=f"write_{i}", use_container_width=True):
                        st.session_state.selected_topic = {
                            "text": topic.text,
                            "author": topic.author_username,
                            "url": topic.url,
                            "id": topic.id,
                            "category": topic.category,
                        }
                        st.switch_page("pages/2_✍️_Yaz.py")

                with col2:
                    if st.button("💬 Quote Tweet", key=f"quote_{i}", use_container_width=True):
                        st.session_state.quote_topic = {
                            "text": topic.text,
                            "author": topic.author_username,
                            "url": topic.url,
                            "id": topic.id,
                        }
                        st.session_state.write_mode = "quote"
                        st.switch_page("pages/2_✍️_Yaz.py")

                with col3:
                    st.link_button("🔗 X'te Aç", topic.url, use_container_width=True)

                st.markdown("")

    elif "scan_results" in st.session_state:
        st.info("Arama kriterlerine uygun sonuç bulunamadı. Filtreleri değiştirmeyi deneyin.")

    else:
        # Show monitored accounts — ALL of them
        st.markdown("### 👀 İzlenen AI Hesapları")
        st.markdown("Tarama başlatıldığında bu hesaplar kontrol edilecek:")

        custom_accounts = load_monitored_accounts()
        all_accounts = DEFAULT_AI_ACCOUNTS + custom_accounts

        # Display ALL accounts (no limit)
        cols = st.columns(4)
        for i, account in enumerate(all_accounts):
            with cols[i % 4]:
                is_custom = account in custom_accounts
                border_color = "#6366f1" if is_custom else "rgba(255,255,255,0.06)"
                badge = " <span style='color:#a5b4fc; font-size:10px;'>✦ özel</span>" if is_custom else ""
                st.markdown(f"""
                <div style="background:rgba(15,20,35,0.7); border:1px solid {border_color}; border-radius:8px;
                            padding:8px 12px; margin:4px 0; font-size:13px;">
                    <span style="color:#a5b4fc;">@{account}</span>{badge}
                </div>
                """, unsafe_allow_html=True)

        st.caption(f"Toplam {len(all_accounts)} hesap izleniyor ({len(DEFAULT_AI_ACCOUNTS)} varsayılan + {len(custom_accounts)} özel)")

        st.info("💡 **İpucu:** Tarama butonuna basarak son saatlerin AI gelişmelerini bulun. "
                "Sonra bir konu seçip tweet yazabilirsiniz.")

# ============================================================
# TAB 2: KEŞFET — Trending AI topics from accounts you don't follow
# ============================================================
with main_tab2:
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">🌐 AI Keşfet</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
            Takip etmediğin hesaplardan ve trending konulardan yeni AI gelişmelerini bul
        </div>
    </div>
    """, unsafe_allow_html=True)

    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        discover_time = st.selectbox(
            "⏱️ Zaman",
            options=[6, 12, 24],
            format_func=lambda x: f"Son {x} saat",
            index=1,
            key="discover_time"
        )
    with dc2:
        discover_max = st.number_input(
            "📊 Maks. Sonuç",
            min_value=10, max_value=100, value=30,
            key="discover_max"
        )
    with dc3:
        st.write("")  # spacer

    # === AI DEVELOPMENT DISCOVERY QUERIES ===
    # Specific AI model names + action verbs (avoids zodiac/gaming false positives)
    DISCOVER_QUERIES = [
        # Model releases & launches
        '("new AI model" OR "new LLM" OR "just released" OR "just launched") (AI OR model OR LLM) -is:retweet lang:en min_faves:50',
        # Specific model names with AI context (NOT generic "Gemini" etc.)
        '(ChatGPT OR "GPT-4" OR "GPT-5" OR "Claude 4" OR "Claude Opus" OR "Claude Sonnet" OR "Gemini Pro" OR "Gemini Ultra" OR "Gemini 2") -is:retweet lang:en min_faves:30',
        '(DeepSeek OR Qwen OR "Llama 4" OR "Llama 3" OR Mixtral OR Mistral OR Grok) (model OR release OR update OR benchmark) -is:retweet lang:en min_faves:30',
        # AI tools & coding
        '(Cursor OR Windsurf OR "GitHub Copilot" OR Devin OR "v0.dev" OR "bolt.new" OR Replit) (AI OR update OR release OR new) -is:retweet lang:en min_faves:20',
        # AI agents & frameworks
        '("AI agent" OR "AI agents" OR agentic OR "function calling" OR MCP OR "tool use") -is:retweet lang:en min_faves:30',
        # Open source & benchmarks
        '("open source" OR "open-source") (model OR AI OR LLM) (release OR new OR weights) -is:retweet lang:en min_faves:30',
        '(benchmark OR MMLU OR HumanEval OR leaderboard OR SOTA) (AI OR model OR LLM) -is:retweet lang:en min_faves:30',
        # AI companies & industry
        '(OpenAI OR Anthropic OR "Google DeepMind" OR "Meta AI" OR xAI) (announce OR release OR launch OR update) -is:retweet lang:en min_faves:50',
        # Generative AI (image/video)
        '("Stable Diffusion" OR Midjourney OR "DALL-E" OR Sora OR Runway OR Flux) (new OR update OR release) -is:retweet lang:en min_faves:30',
        # AI infrastructure
        '(NVIDIA OR H100 OR H200 OR B200 OR "AI chip" OR TPU) (AI OR training OR inference) -is:retweet lang:en min_faves:40',
    ]

    # === GITHUB REPO DISCOVERY QUERIES ===
    GITHUB_QUERIES = [
        '(github.com) (AI OR LLM OR "machine learning" OR "deep learning" OR GPT OR agent) -is:retweet lang:en min_faves:20',
        '("open source" OR "open-source") (github.com OR huggingface.co) (AI OR model OR tool) -is:retweet lang:en min_faves:15',
        '(github.com) ("star" OR "stars" OR "just released" OR "check out" OR "built" OR repo) (AI OR LLM OR ML) -is:retweet lang:en min_faves:10',
        '(huggingface.co OR "Hugging Face") (model OR dataset OR space) (new OR release OR open) -is:retweet lang:en min_faves:15',
        '(arxiv.org) (AI OR LLM OR "machine learning" OR transformer OR diffusion) -is:retweet lang:en min_faves:20',
    ]

    with st.expander("⚙️ Gelişmiş Ayarlar", expanded=False):
        discover_engine = render_research_engine_toggle(key_suffix="discover")

    discover_clicked = st.button("🌐 Keşfet", type="primary", use_container_width=True, key="discover_button")

    if discover_clicked:
        # Grok shortcut: use Grok's native X search for AI trend discovery
        if discover_engine == "grok":
            try:
                from modules.grok_client import grok_discover_ai_trends, has_grok_key
                if has_grok_key():
                    with st.spinner("🧠 Grok ile AI trendleri keşfediliyor..."):
                        grok_topics = grok_discover_ai_trends()

                    if grok_topics:
                        st.success(f"🧠 Grok {len(grok_topics)} trend konu buldu!")
                        st.session_state.grok_discover_results = grok_topics

                        for i, topic_item in enumerate(grok_topics):
                            title = topic_item.get("title", f"Konu {i+1}")
                            desc = topic_item.get("description", "")
                            angle = topic_item.get("angle", "")
                            potential = topic_item.get("potential", "")

                            with st.expander(f"**{i+1}. {title}**", expanded=(i < 5)):
                                st.write(desc)
                                if angle:
                                    st.markdown(f"**Açı:** {angle}")
                                if potential:
                                    st.markdown(f"**Potansiyel:** {potential}")

                                if st.button(f"✍️ Bu konuda yaz", key=f"grok_discover_write_{i}",
                                             use_container_width=True):
                                    st.session_state.selected_topic = {
                                        "text": f"{title}: {desc}",
                                        "author": "Grok Keşif",
                                        "url": "",
                                        "id": "",
                                        "category": "Grok Keşif",
                                    }
                                    st.switch_page("pages/2_✍️_Yaz.py")
                    else:
                        st.warning("Grok trend bulamadı. Standart keşif deneyin.")
                    st.stop()
            except Exception as e:
                st.warning(f"Grok keşif hatası: {e}. Standart modla devam ediliyor...")

        bearer_token = get_secret("twitter_bearer_token", "")
        twikit_username = get_secret("twikit_username", "")
        twikit_password = get_secret("twikit_password", "")
        twikit_email = get_secret("twikit_email", "")

        if not bearer_token and not twikit_username:
            st.error("Twitter API veya Twikit bilgileri yapılandırılmamış!")
            st.stop()

        with st.spinner("AI dünyasında yeni gelişmeler keşfediliyor..."):
            try:
                scanner = TwitterScanner(
                    bearer_token=bearer_token,
                    api_key=get_secret("twitter_api_key", ""),
                    api_secret=get_secret("twitter_api_secret", ""),
                    access_token=get_secret("twitter_access_token", ""),
                    access_secret=get_secret("twitter_access_secret", ""),
                    twikit_username=twikit_username,
                    twikit_password=twikit_password,
                    twikit_email=twikit_email,
                )

                from modules.twitter_scanner import is_spam, categorize_topic, calculate_relevance

                all_discover = []
                github_discover = []
                seen_ids = set()
                start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=discover_time)

                progress_bar = st.progress(0)
                total_queries = len(DISCOVER_QUERIES) + len(GITHUB_QUERIES)
                query_idx = 0

                def _process_tweet(t, target_list):
                    """Filter and process a single tweet result."""
                    if t.id in seen_ids or is_spam(t.text):
                        return
                    # Filter Turkish accounts
                    if is_turkish_account(t.text, t.author_name):
                        return
                    # Filter low-follower accounts
                    if t.author_followers_count > 0 and t.author_followers_count < MIN_FOLLOWER_COUNT_DISCOVER:
                        return
                    # AI relevance check — reject zodiac, gaming, fashion etc.
                    if not is_ai_relevant(t.text):
                        return
                    seen_ids.add(t.id)
                    t.category = categorize_topic(t.text)
                    t.relevance_score = calculate_relevance(t, discover_time)
                    t.content_summary = generate_content_summary(t.text, t.category)
                    target_list.append(t)

                # Search with AI discovery queries
                for query in DISCOVER_QUERIES:
                    try:
                        results = scanner._search_tweets(query, start_time, discover_max)
                        for t in results:
                            _process_tweet(t, all_discover)
                    except Exception:
                        pass
                    query_idx += 1
                    progress_bar.progress(query_idx / total_queries)

                # Search with GitHub repo queries
                for query in GITHUB_QUERIES:
                    try:
                        results = scanner._search_tweets(query, start_time, discover_max)
                        for t in results:
                            _process_tweet(t, github_discover)
                    except Exception:
                        pass
                    query_idx += 1
                    progress_bar.progress(query_idx / total_queries)

                progress_bar.empty()

                # Filter out tweets from accounts we already track
                custom_accs = load_monitored_accounts()
                tracked_lower = {a.lower() for a in DEFAULT_AI_ACCOUNTS + custom_accs}
                new_discoveries = [t for t in all_discover if t.author_username.lower() not in tracked_lower]
                tracked_discoveries = [t for t in all_discover if t.author_username.lower() in tracked_lower]

                # GitHub results (separate, don't filter tracked accounts — repos are always useful)
                github_results = sorted(github_discover, key=lambda t: t.relevance_score, reverse=True)

                new_discoveries.sort(key=lambda t: t.relevance_score, reverse=True)
                tracked_discoveries.sort(key=lambda t: t.relevance_score, reverse=True)

                st.session_state.discover_new = new_discoveries
                st.session_state.discover_tracked = tracked_discoveries
                st.session_state.discover_github = github_results

            except Exception as e:
                st.error(f"Keşfet hatası: {e}")

    # === DISPLAY DISCOVER RESULTS ===
    if "discover_new" in st.session_state:
        new_items = st.session_state.discover_new
        tracked_items = st.session_state.get("discover_tracked", [])
        github_items = st.session_state.get("discover_github", [])

        # --- GitHub Repos Section ---
        if github_items:
            st.markdown(f"### 📦 GitHub / Açık Kaynak ({len(github_items)} paylaşım)")
            st.caption("AI ile ilgili GitHub repo ve açık kaynak proje paylaşımları")

            for i, t in enumerate(github_items[:15]):
                render_tweet_card(t, key_prefix=f"gh_{i}")

                gh_col1, gh_col2, gh_col3 = st.columns([1, 1, 1])
                with gh_col1:
                    if st.button("✍️ Yaz", key=f"gh_write_{i}", use_container_width=True):
                        st.session_state.selected_topic = {
                            "text": t.text, "author": t.author_username,
                            "url": t.url, "id": t.id, "category": t.category,
                        }
                        st.switch_page("pages/2_✍️_Yaz.py")
                with gh_col2:
                    if st.button("💬 Quote", key=f"gh_quote_{i}", use_container_width=True):
                        st.session_state.quote_topic = {
                            "text": t.text, "author": t.author_username,
                            "url": t.url, "id": t.id,
                        }
                        st.session_state.write_mode = "quote"
                        st.switch_page("pages/2_✍️_Yaz.py")
                with gh_col3:
                    st.link_button("🔗 X'te Aç", t.url, use_container_width=True)

        # --- AI Developments Section ---
        if new_items:
            new_accounts = defaultdict(list)
            for t in new_items:
                new_accounts[t.author_username].append(t)

            sorted_new = sorted(new_accounts.items(), key=lambda x: -max(t.engagement_score for t in x[1]))

            st.markdown(f"### 🆕 AI Gelişmeleri — {len(new_items)} tweet ({len(sorted_new)} farklı hesap)")
            st.caption("AI hakkında paylaşım yapan yeni hesaplar")

            for acc_name, acc_tweets in sorted_new[:20]:
                total_eng = sum(t.like_count + t.retweet_count for t in acc_tweets)

                with st.expander(f"@{acc_name} — {len(acc_tweets)} tweet | Etkileşim: {total_eng:,}"):
                    if st.button(f"➕ @{acc_name} hesabını izleme listesine ekle", key=f"add_{acc_name}"):
                        from modules.style_manager import save_monitored_accounts
                        current = load_monitored_accounts()
                        if acc_name not in current:
                            current.append(acc_name)
                            save_monitored_accounts(current)
                            st.success(f"@{acc_name} izleme listesine eklendi!")
                        else:
                            st.info(f"@{acc_name} zaten izleme listesinde.")

                    for j, t in enumerate(acc_tweets[:5]):
                        render_tweet_card(t, key_prefix=f"disc_{acc_name}_{j}")

                        dcol1, dcol2, dcol3 = st.columns([1, 1, 1])
                        with dcol1:
                            if st.button("✍️ Yaz", key=f"disc_write_{acc_name}_{j}", use_container_width=True):
                                st.session_state.selected_topic = {
                                    "text": t.text, "author": t.author_username,
                                    "url": t.url, "id": t.id, "category": t.category,
                                }
                                st.switch_page("pages/2_✍️_Yaz.py")
                        with dcol2:
                            if st.button("💬 Quote", key=f"disc_quote_{acc_name}_{j}", use_container_width=True):
                                st.session_state.quote_topic = {
                                    "text": t.text, "author": t.author_username,
                                    "url": t.url, "id": t.id,
                                }
                                st.session_state.write_mode = "quote"
                                st.switch_page("pages/2_✍️_Yaz.py")
                        with dcol3:
                            st.link_button("🔗 X'te Aç", t.url, use_container_width=True)
        elif not github_items:
            st.info("AI içerik bulunamadı. Zaman aralığını artırmayı deneyin.")

        if tracked_items:
            with st.expander(f"📌 İzlenen hesaplardan da {len(tracked_items)} trend tweet bulundu"):
                for i, t in enumerate(tracked_items[:10]):
                    render_tweet_card(t, key_prefix=f"disc_tracked_{i}")
    elif not discover_clicked:
        st.info("💡 Keşfet butonuna basarak takip etmediğin hesaplardan AI gelişmelerini bul. "
                "GitHub repo paylaşımları ayrı gösterilir.")
