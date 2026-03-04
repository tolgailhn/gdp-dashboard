"""
Tweet Yazıcı Sayfası
AI ile doğal tweet üretir, düzenler ve paylaşır
"""
import streamlit as st
import datetime
import re
from urllib.parse import quote as url_quote
from modules.ui_components import (inject_custom_css, check_password,
                                   render_generated_tweet, render_thread_preview,
                                   get_secret, render_sidebar_nav,
                                   render_research_engine_toggle, render_agentic_mode_toggle,
                                   render_media_suggestions, render_media_source_selector,
                                   render_image_analysis)
from modules.content_generator import (ContentGenerator, get_available_styles, get_style_info,
                                       get_available_formats, get_format_info, score_tweet,
                                       CONTENT_FORMATS)
from modules.tweet_publisher import TweetPublisher
from modules.deep_research import (
    extract_tweet_id, research_topic, research_topic_from_text,
    ai_identify_knowledge_gaps, fill_knowledge_gaps, compile_gap_findings,
    ai_fact_check_draft, verify_claims, compile_verification_context,
)
from modules.style_manager import (
    load_user_samples, load_custom_persona,
    add_to_post_history, add_draft, load_draft_tweets
)
from modules.tweet_analyzer import load_all_analyses, build_training_context

# Page config
st.set_page_config(
    page_title="Tweet Yaz | X AI Otomasyon",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_custom_css()

if not check_password():
    st.stop()

render_sidebar_nav(current_page="yaz")

# --- Determine mode ---
write_mode = st.session_state.get("write_mode", "normal")
selected_topic = st.session_state.get("selected_topic", None)
quote_topic = st.session_state.get("quote_topic", None)

# --- Header ---
st.markdown("""
<div class="page-header">
    <span class="page-icon">✍️</span>
    <h1>Tweet Yazıcı</h1>
    <p>AI ile doğal, insan gibi tweet üret</p>
</div>
""", unsafe_allow_html=True)

# --- Mode Tabs ---
mode_tab1, mode_tab2, mode_tab3 = st.tabs([
    "📝 Tweet Yaz",
    "🔬 Araştırmalı Quote Tweet",
    "💬 Hızlı Quote Tweet",
])

# Track which tab is active
research_summary = ""

with mode_tab2:
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">🔬 Araştırmalı Quote Tweet</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
            Tweet URL → Thread'i oku → Web'de araştır → X'te ara → Bilgili quote yaz
        </div>
    </div>
    """, unsafe_allow_html=True)

    quote_url = st.text_input(
        "Tweet URL'si",
        placeholder="https://x.com/kullanici/status/123456789...",
        key="research_quote_url"
    )

    # Research source selection
    st.markdown("##### 🔎 Araştırma Kaynakları")
    st.caption("Hangi kaynaklarda araştırma yapılsın? Sadece X seçersen 40-50 tweet bulur, daha odaklı sonuç verir.")
    src_cols = st.columns(4)
    with src_cols[0]:
        src_x = st.checkbox("𝕏 Twitter/X", value=True, key="src_x",
                             help="X'te ilgili tweetleri ara (önerilen)")
    with src_cols[1]:
        src_web = st.checkbox("🌐 Web", value=False, key="src_web",
                               help="Web'de makale ve teknik detay ara")
    with src_cols[2]:
        src_reddit = st.checkbox("🔴 Reddit", value=False, key="src_reddit",
                                  help="Reddit tartışmalarını ara")
    with src_cols[3]:
        src_news = st.checkbox("📰 Haberler", value=False, key="src_news",
                                help="Son haberleri ara")

    # Research engine selection
    st.markdown("##### 🔧 Araştırma Motoru")
    research_engine = render_research_engine_toggle(key_suffix="quote")

    # Research mode selection
    st.markdown("##### 🧠 Araştırma Modu")
    agentic_mode = render_agentic_mode_toggle(key_suffix="quote")
    use_agentic = (agentic_mode == "standard")
    use_grok_agentic = (agentic_mode == "grok")

    deep_verify = st.checkbox(
        "🔍 Doğrulama Modu",
        value=False,
        key="deep_verify",
        help="Tweet yazıldıktan sonra iddiaları internette doğrular ve düzeltir. "
             "Otonom araştırmayla birlikte kullanılabilir."
    )

    if use_agentic:
        st.caption("🤖 AI modeli kendi başına web araması yapacak, makale okuyacak ve bilgi toplayacak.")
    elif use_grok_agentic:
        st.caption("🧠 Grok modeli X'te ve web'de kendi başına gezinerek araştırma yapacak.")

    research_clicked = st.button(
        "🔬 Araştır ve Quote Tweet Yaz",
        type="primary",
        use_container_width=True,
        key="research_btn",
        disabled=not quote_url
    )

    if research_clicked:
        tweet_id = extract_tweet_id(quote_url)
        if not tweet_id:
            st.error("Geçersiz tweet URL'si! Örn: https://x.com/user/status/123456")
        else:
            bearer_token = get_secret("twitter_bearer_token", "")
            scanner = None
            original_tweet = None

            if bearer_token:
                from modules.twitter_scanner import TwitterScanner
                scanner = TwitterScanner(bearer_token=bearer_token)
                with st.spinner("Tweet çekiliyor..."):
                    original_tweet = scanner.get_tweet_by_id(tweet_id)

            if not original_tweet and not bearer_token:
                st.warning("Twitter API yapılandırılmamış. Tweet metnini manuel girin.")
                manual_tweet_text = st.text_area(
                    "Tweet metni (thread varsa tüm tweet'leri yapıştırın)",
                    placeholder="Thread'deki tüm tweet'leri yapıştırın...",
                    height=200,
                    key="manual_quote_text"
                )
                if manual_tweet_text:
                    original_tweet_text = manual_tweet_text
                    original_author = "unknown"
                else:
                    st.stop()
            elif not original_tweet:
                st.error("Tweet bulunamadı. URL'yi kontrol edin.")
                st.stop()
            else:
                original_tweet_text = original_tweet.text
                original_author = original_tweet.author_username

                st.markdown(f"""
                <div class="tweet-card" style="border-color:#a5b4fc;">
                    <div>
                        <span class="tweet-author">{original_tweet.author_name}</span>
                        <span class="tweet-username">@{original_author}</span>
                    </div>
                    <div class="tweet-text">{original_tweet_text}</div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:8px;">
                        ❤️ {original_tweet.like_count:,} · 🔁 {original_tweet.retweet_count:,} · 💬 {original_tweet.reply_count:,}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # === Build AI client for smart topic extraction ===
            import openai as _openai
            import anthropic as _anthropic

            _ai_client = None
            _ai_model = None
            _ai_provider = "minimax"

            # Try MiniMax first (cheapest), then Anthropic, then OpenAI
            minimax_key = get_secret("minimax_api_key", "")
            anthropic_key = get_secret("anthropic_api_key", "")
            openai_key = get_secret("openai_api_key", "")

            if minimax_key:
                _ai_client = _openai.OpenAI(api_key=minimax_key, base_url="https://api.minimax.io/v1")
                _ai_model = "MiniMax-M2.5"
                _ai_provider = "minimax"
            elif anthropic_key:
                _ai_client = _anthropic.Anthropic(api_key=anthropic_key)
                _ai_model = "claude-haiku-4-5-20251001"
                _ai_provider = "anthropic"
            elif openai_key:
                _ai_client = _openai.OpenAI(api_key=openai_key)
                _ai_model = "gpt-4o-mini"
                _ai_provider = "openai"

            # === BUILD RESEARCH SOURCES LIST ===
            research_sources = []
            if src_x:
                research_sources.append("x")
            if src_web:
                research_sources.append("web")
            if src_reddit:
                research_sources.append("reddit")
            if src_news:
                research_sources.append("news")
            if not research_sources:
                research_sources = ["x"]  # Default to X if nothing selected

            source_label = ", ".join(research_sources).upper()

            # === FULL RESEARCH PIPELINE ===
            mode_label = "🧠 Grok Otonom" if use_grok_agentic else "🤖 AI Otonom" if use_agentic else source_label
            engine_label = " + Grok" if research_engine == "grok" else ""
            progress_text = st.empty()
            with st.spinner(f"Araştırma yapılıyor ({mode_label}{engine_label})..."):
                research = research_topic(
                    tweet_text=original_tweet_text,
                    tweet_author=original_author,
                    tweet_id=tweet_id,
                    scanner=scanner,
                    progress_callback=lambda msg: progress_text.caption(msg),
                    ai_client=_ai_client,
                    ai_model=_ai_model,
                    ai_provider=_ai_provider,
                    research_sources=research_sources,
                    use_agentic=use_agentic,
                    engine=research_engine,
                    use_grok_agentic=use_grok_agentic,
                )
                progress_text.empty()

            st.session_state.research_data = research
            # Use AI-synthesized brief if available, fallback to raw summary
            research_summary = research.synthesized_brief or research.summary

            # --- Show thread if found ---
            if len(research.thread_texts) > 1:
                with st.expander(f"🧵 Thread ({len(research.thread_texts)} tweet)", expanded=True):
                    for i, t in enumerate(research.thread_texts, 1):
                        st.markdown(f"""
                        <div style="background:rgba(15,20,35,0.7); border-left:3px solid #6366f1;
                                    padding:8px 12px; margin:4px 0; border-radius:4px;">
                            <span style="color:#a5b4fc; font-weight:bold;">{i}/</span>
                            <span style="color:#f1f5f9; font-size:13px;">{t}</span>
                        </div>
                        """, unsafe_allow_html=True)

            # --- Show research results ---
            # In agentic mode, show the AI's own research summary prominently
            if use_agentic and research.synthesized_brief:
                with st.expander("🤖 AI Otonom Araştırma Sonuçları", expanded=True):
                    st.markdown(research.synthesized_brief)
                    if research.related_tweets:
                        st.markdown(f"\n**𝕏 İlgili Yorumlar ({len(research.related_tweets)}):**")
                        for rt in research.related_tweets[:3]:
                            st.markdown(f"- @{rt['author']} ({rt['likes']} ❤️): _{rt['text'][:300]}_")

            with st.expander("📊 Araştırma Sonuçları" if not use_agentic else "📊 Ek Detaylar", expanded=not use_agentic):
                if research.topic:
                    st.markdown(f"**Tespit edilen konu:** `{research.topic}`")

                # Deep articles (full content fetched)
                if research.deep_articles:
                    st.markdown(f"**📖 Okunan Makaleler ({len(research.deep_articles)}):**")
                    for article in research.deep_articles:
                        st.markdown(f"- **{article['title']}**")
                        st.caption(f"  {article['content'][:300]}...")

                # Reddit
                if research.reddit_results:
                    st.markdown(f"**🔴 Reddit ({len(research.reddit_results)}):**")
                    for rr in research.reddit_results[:3]:
                        st.markdown(f"- **{rr['title']}**\n  _{rr['body'][:150]}_")

                # Web snippets
                if research.web_results:
                    remaining = len(research.web_results)
                    st.markdown(f"**🌐 Web ({remaining} kaynak):**")
                    for wr in research.web_results[:4]:
                        st.markdown(f"- **{wr['title']}**\n  _{wr['body'][:150]}_")

                # X opinions
                if research.related_tweets:
                    st.markdown(f"**𝕏 Yorumlar ({len(research.related_tweets)}):**")
                    for rt in research.related_tweets[:3]:
                        st.markdown(f"- @{rt['author']} ({rt['likes']} ❤️): _{rt['text'][:300]}_")

                if not research.web_results and not research.deep_articles and not research.related_tweets:
                    st.warning("Bu konu için web'de yeterli bilgi bulunamadı.")

            # Show AI-synthesized brief if available
            if research.synthesized_brief:
                with st.expander("🧠 AI Araştırma Sentezi", expanded=False):
                    st.markdown(research.synthesized_brief)

            # === DEEP VERIFICATION: Knowledge Gap Filling ===
            if deep_verify and _ai_client:
                progress_text2 = st.empty()
                with st.spinner("🔍 Bilgi boşlukları tespit ediliyor..."):
                    gap_queries = ai_identify_knowledge_gaps(
                        original_tweet=original_tweet_text,
                        current_research=research_summary,
                        ai_client=_ai_client,
                        ai_model=_ai_model,
                        provider=_ai_provider,
                    )

                if gap_queries:
                    with st.spinner(f"🔍 {len(gap_queries)} ek araştırma yapılıyor..."):
                        gap_findings = fill_knowledge_gaps(
                            gap_queries,
                            progress_callback=lambda msg: progress_text2.caption(msg),
                        )
                        progress_text2.empty()

                    gap_context = compile_gap_findings(gap_findings)
                    if gap_context:
                        # Append gap findings to the research summary
                        research_summary = research_summary + "\n\n" + gap_context
                        with st.expander(f"🔍 Ek Araştırma ({len(gap_queries)} boşluk dolduruldu)", expanded=False):
                            for gf in gap_findings:
                                q = gf.get("query", "")
                                article = gf.get("article")
                                if article:
                                    st.markdown(f"- **{q}** → {article.get('title', 'Makale okundu')}")
                                else:
                                    results = gf.get("results", [])
                                    if results:
                                        st.markdown(f"- **{q}** → {results[0].get('title', '')[:80]}")
                else:
                    st.caption("✅ Araştırma yeterli, ek bilgi boşluğu yok.")

            # Store deep_verify state for tweet generation
            st.session_state.deep_verify_enabled = deep_verify

            # Set state for generation
            st.session_state.write_mode = "quote"
            st.session_state.quote_topic = {
                "id": tweet_id,
                "text": original_tweet_text,
                "author": original_author,
            }
            st.session_state.research_summary = research_summary
            st.info("Aşağıdaki 'Tweet Üret' butonuna tıklayarak araştırma sonuçlarıyla quote tweet yazabilirsiniz.")

    # Show previous research
    if "research_data" in st.session_state and not research_clicked:
        rd = st.session_state.research_data
        if rd.summary:
            with st.expander("📊 Önceki Araştırma"):
                st.caption(f"Konu: {rd.topic}")
                if len(rd.thread_texts) > 1:
                    st.caption(f"Thread: {len(rd.thread_texts)} tweet okundu")
                deep = len(rd.deep_articles) if hasattr(rd, 'deep_articles') else 0
                reddit = len(rd.reddit_results) if hasattr(rd, 'reddit_results') else 0
                st.caption(f"📖 Makale: {deep} | 🌐 Web: {len(rd.web_results)} | 🔴 Reddit: {reddit} | 𝕏: {len(rd.related_tweets)}")

with mode_tab3:
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">💬 Hızlı Quote Tweet</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
            Tweet URL yapıştır → Hızlıca quote tweet yaz ve paylaş
        </div>
    </div>
    """, unsafe_allow_html=True)

    quick_quote_url = st.text_input(
        "Quote yapılacak Tweet URL'si",
        placeholder="https://x.com/kullanici/status/123456789...",
        key="quick_quote_url"
    )

    if quick_quote_url:
        quick_tweet_id = extract_tweet_id(quick_quote_url)
        if not quick_tweet_id:
            st.error("Geçersiz tweet URL'si! Örn: https://x.com/user/status/123456")
            topic_text = ""
            topic_source = ""
        else:
            # Fetch original tweet (cached to avoid re-fetching on every rerun)
            cached_id = st.session_state.get("_quick_quote_cached_id")
            if cached_id != quick_tweet_id:
                original_text = ""
                original_author = ""
                bearer_token = get_secret("twitter_bearer_token", "")
                if bearer_token:
                    try:
                        from modules.twitter_scanner import TwitterScanner
                        _scanner = TwitterScanner(bearer_token=bearer_token)
                        with st.spinner("Tweet çekiliyor..."):
                            fetched = _scanner.get_tweet_by_id(quick_tweet_id)
                            if fetched:
                                original_text = fetched.text
                                original_author = fetched.author_username
                    except Exception:
                        pass
                st.session_state._quick_quote_cached_id = quick_tweet_id
                st.session_state._quick_quote_text = original_text
                st.session_state._quick_quote_author = original_author

            original_text = st.session_state.get("_quick_quote_text", "")
            original_author = st.session_state.get("_quick_quote_author", "")

            if original_text:
                st.markdown(f"""
                <div class="tweet-card" style="border-color:#a5b4fc;">
                    <div>
                        <span class="tweet-author">Orijinal Tweet</span>
                        <span class="tweet-username">@{original_author}</span>
                    </div>
                    <div class="tweet-text">{original_text}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"Tweet ID: {quick_tweet_id} — Tweet metni çekilemedi ama quote yapılabilir.")

            # Set quote state
            st.session_state.write_mode = "quote"
            st.session_state.quote_topic = {
                "id": quick_tweet_id,
                "text": original_text or quick_quote_url,
                "author": original_author or "",
            }
            write_mode = "quote"
            quote_topic = st.session_state.quote_topic

            topic_text = original_text or quick_quote_url
            topic_source = original_author or ""

            if st.button("Quote modu kapat", key="clear_quote"):
                st.session_state.write_mode = "normal"
                st.session_state.quote_topic = None
                for k in ["_quick_quote_cached_id", "_quick_quote_text", "_quick_quote_author"]:
                    st.session_state.pop(k, None)
                st.rerun()

    elif write_mode == "quote" and quote_topic:
        # Previously set from Scanner page
        st.markdown(f"""
        <div class="tweet-card" style="border-color:#a5b4fc;">
            <div>
                <span class="tweet-author">Orijinal Tweet</span>
                <span class="tweet-username">@{quote_topic.get('author', '')}</span>
            </div>
            <div class="tweet-text">{quote_topic.get('text', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        topic_text = quote_topic.get("text", "")
        topic_source = quote_topic.get("author", "")

        if st.button("Quote modu kapat", key="clear_quote_prev"):
            st.session_state.write_mode = "normal"
            st.session_state.quote_topic = None
            st.rerun()
    else:
        st.info("Yukarıya quote yapmak istediğiniz tweet'in URL'sini yapıştırın.")
        topic_text = ""
        topic_source = ""

with mode_tab1:
    if selected_topic and write_mode != "quote":
        st.info(f"📌 Seçilen konu: {selected_topic.get('text', '')[:100]}...")
        topic_text = selected_topic.get("text", "")
        topic_source = selected_topic.get("url", "")

        if st.button("Konuyu temizle", key="clear_topic"):
            st.session_state.selected_topic = None
            st.rerun()
    elif write_mode != "quote":
        topic_text = st.text_area(
            "Konu / AI Gelişmesi",
            placeholder="Tweet yazmak istediğiniz konuyu veya AI gelişmesini buraya yazın...\n\nÖrnek: Qwen 3 modeli çıktı, coding benchmark'larında GPT-4o'yu geçti\nÖrnek: Amazon'un BAE'deki AWS deposu bombalandı",
            height=120,
            key="manual_topic"
        )
        topic_source = st.text_input(
            "Kaynak (opsiyonel)",
            placeholder="Tweet URL'si veya kaynak",
            key="topic_source"
        )

        # --- Topic Research Section ---
        if topic_text:
            st.markdown("""
            <div style="background:rgba(99,102,241,0.06); border:1px solid rgba(255,255,255,0.06); border-radius:8px;
                        padding:12px; margin:8px 0;">
                <div style="color:#e2e8f0; font-size:13px; font-weight:bold;">🔍 Konu Araştır</div>
                <div style="color:#94a3b8; font-size:11px;">Konuyu X'te, web'de araştır ve AI ile doğrula</div>
            </div>
            """, unsafe_allow_html=True)

            # Row 1: Time + Source + Button
            rcol1, rcol2, rcol3 = st.columns([1, 1, 2])
            with rcol1:
                topic_research_time = st.selectbox(
                    "Zaman",
                    options=[6, 12, 24],
                    format_func=lambda x: f"Son {x} saat",
                    index=1,
                    key="topic_research_time"
                )
            with rcol2:
                topic_search_mode = st.selectbox(
                    "Kaynak",
                    options=["x_only", "x_and_web"],
                    format_func=lambda x: "𝕏 Sadece X" if x == "x_only" else "𝕏+🌐 X + Web",
                    index=0,
                    key="topic_search_mode"
                )
            with rcol3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                btn_label = "🔍 X'te Araştır" if topic_search_mode == "x_only" else "🔍 X + Web Araştır"
                topic_research_clicked = st.button(
                    btn_label,
                    type="secondary",
                    use_container_width=True,
                    key="topic_research_btn",
                )

            # Research engine selection
            topic_engine = render_research_engine_toggle(key_suffix="topic")

            # Row 2: AI Research Modes
            topic_agentic_mode = render_agentic_mode_toggle(key_suffix="topic")
            topic_use_agentic = (topic_agentic_mode == "standard")
            topic_use_grok_agentic = (topic_agentic_mode == "grok")

            topic_deep_verify = st.checkbox(
                "🔍 Doğrulama Modu",
                value=False,
                key="topic_deep_verify",
                help="Tweet yazıldıktan sonra içindeki iddiaları internette doğrular "
                     "ve hatalı bilgileri düzeltir."
            )

            if topic_use_agentic:
                st.caption("🤖 AI, yazdığın konudaki spesifik iddiaları/ürünleri/rakamları internette araştıracak.")
            elif topic_use_grok_agentic:
                st.caption("🧠 Grok, X'te ve web'de kendi başına gezinerek konu hakkında araştırma yapacak.")

            if topic_research_clicked:
                # Build AI client for topic extraction
                import openai as _openai
                import anthropic as _anthropic

                _ai_client = None
                _ai_model = None
                _ai_provider = "minimax"

                minimax_key = get_secret("minimax_api_key", "")
                anthropic_key = get_secret("anthropic_api_key", "")
                openai_key = get_secret("openai_api_key", "")

                if minimax_key:
                    _ai_client = _openai.OpenAI(api_key=minimax_key, base_url="https://api.minimax.io/v1")
                    _ai_model = "MiniMax-M2.5"
                    _ai_provider = "minimax"
                elif anthropic_key:
                    _ai_client = _anthropic.Anthropic(api_key=anthropic_key)
                    _ai_model = "claude-haiku-4-5-20251001"
                    _ai_provider = "anthropic"
                elif openai_key:
                    _ai_client = _openai.OpenAI(api_key=openai_key)
                    _ai_model = "gpt-4o-mini"
                    _ai_provider = "openai"

                # Build scanner for X search
                bearer_token = get_secret("twitter_bearer_token", "")
                twikit_username = get_secret("twikit_username", "")
                twikit_password = get_secret("twikit_password", "")
                twikit_email = get_secret("twikit_email", "")

                _scanner = None
                if bearer_token or twikit_username:
                    from modules.twitter_scanner import TwitterScanner
                    _scanner = TwitterScanner(
                        bearer_token=bearer_token,
                        api_key=get_secret("twitter_api_key", ""),
                        api_secret=get_secret("twitter_api_secret", ""),
                        access_token=get_secret("twitter_access_token", ""),
                        access_secret=get_secret("twitter_access_secret", ""),
                        twikit_username=twikit_username,
                        twikit_password=twikit_password,
                        twikit_email=twikit_email,
                    )

                progress_text = st.empty()
                mode_label = "🧠 Grok Otonom" if topic_use_grok_agentic else "🤖 AI Otonom" if topic_use_agentic else ("X'te detaylı" if topic_search_mode == "x_only" else "X + Web")
                engine_label = " + Grok" if topic_engine == "grok" else ""
                with st.spinner(f"{mode_label}{engine_label} araştırılıyor..."):
                    topic_research = research_topic_from_text(
                        topic_input=topic_text,
                        scanner=_scanner,
                        time_hours=topic_research_time,
                        search_mode=topic_search_mode,
                        progress_callback=lambda msg: progress_text.caption(msg),
                        ai_client=_ai_client,
                        ai_model=_ai_model,
                        ai_provider=_ai_provider,
                        use_agentic=topic_use_agentic,
                        engine=topic_engine,
                        use_grok_agentic=topic_use_grok_agentic,
                    )
                    progress_text.empty()

                st.session_state.topic_research_data = topic_research
                st.session_state.topic_research_summary = topic_research.summary

            # Show previous/current research results
            if "topic_research_data" in st.session_state and st.session_state.topic_research_data:
                tr = st.session_state.topic_research_data
                has_agentic = bool(getattr(tr, 'agentic_summary', ''))

                # --- AI Autonomous Research Results (prominent) ---
                if has_agentic:
                    with st.expander(f"🤖 AI Otonom Araştırma — {tr.topic}", expanded=True):
                        st.markdown(tr.agentic_summary)

                # --- X Tweets + Web Results ---
                mode_label = "🤖 AI Otonom + X" if has_agentic else ("Sadece X" if tr.search_mode == "x_only" else "X + Web")
                with st.expander(f"📊 Araştırma Detayları — {tr.topic} [{mode_label}]", expanded=not has_agentic):
                    # X tweets found
                    if tr.x_tweets:
                        st.markdown(f"**𝕏 X'te Bulunan Tweetler ({len(tr.x_tweets)}):**")
                        for i, tw in enumerate(tr.x_tweets[:12]):
                            eng = f"❤️ {tw['likes']:,} 🔁 {tw['retweets']:,}"
                            st.markdown(f"""
                            <div style="background:rgba(15,20,35,0.7); border-left:3px solid #6366f1;
                                        padding:8px 12px; margin:4px 0; border-radius:4px;">
                                <div style="color:#a5b4fc; font-size:12px; font-weight:bold;">
                                    @{tw['author']} <span style="color:#94a3b8; font-weight:normal;">{eng}</span>
                                </div>
                                <div style="color:#f1f5f9; font-size:13px; margin-top:4px;">{tw['text'][:300]}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("X'te bu konuyla ilgili güncel tweet bulunamadı.")

                    # Web results only if search mode was x_and_web (and not agentic — agentic already searched web)
                    if tr.search_mode == "x_and_web" and not has_agentic:
                        if tr.deep_articles:
                            st.markdown(f"**📖 Okunan Makaleler ({len(tr.deep_articles)}):**")
                            for article in tr.deep_articles:
                                st.markdown(f"- **{article['title']}**")
                                st.caption(f"  {article['content'][:200]}...")

                        if tr.news_results:
                            st.markdown(f"**📰 Son Haberler ({len(tr.news_results)}):**")
                            for n in tr.news_results[:3]:
                                src = f" ({n['source']})" if n.get("source") else ""
                                st.markdown(f"- **{n['title']}**{src}")

                        if tr.web_results:
                            deep_urls = {a["url"] for a in tr.deep_articles}
                            remaining_web = [w for w in tr.web_results if w["url"] not in deep_urls]
                            if remaining_web:
                                st.markdown(f"**🌐 Web Bulguları ({len(remaining_web)}):**")
                                for w in remaining_web[:3]:
                                    st.markdown(f"- {w['title']}")

                    if not tr.x_tweets and not has_agentic and not tr.deep_articles and not tr.news_results:
                        st.warning("Bu konu için yeterli bilgi bulunamadı. Konuyu daha spesifik yazmayı deneyin.")

                st.success("Araştırma tamamlandı! Aşağıdaki 'Tweet Üret' butonuna basarak araştırma sonuçlarıyla tweet yazabilirsiniz.")

# Get research summary if available (from research tab)
if "research_summary" in st.session_state:
    research_summary = st.session_state.research_summary

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# --- Writing Style ---
st.markdown("### 🎨 Yazım Tarzı")

styles = get_available_styles()

# Don't show quote_tweet in normal mode (it has its own dedicated tab)
if write_mode != "quote":
    display_styles = {k: v for k, v in styles.items() if k != "quote_tweet"}
else:
    display_styles = {k: v for k, v in styles.items()}

style_options = list(display_styles.keys())
style_labels = [display_styles[k]["name"] for k in style_options]

cols = st.columns(len(style_options))
selected_style = st.session_state.get("selected_style", style_options[0])

for i, (key, label) in enumerate(zip(style_options, style_labels)):
    with cols[i]:
        desc = display_styles[key]["description"]
        is_selected = selected_style == key
        border = "2px solid #6366f1" if is_selected else "1px solid rgba(255,255,255,0.06)"
        bg = "rgba(99,102,241,0.06)" if is_selected else "rgba(15,20,35,0.7)"

        st.markdown(f"""
        <div style="background:{bg}; border:{border}; border-radius:12px;
                    padding:12px; text-align:center; min-height:80px;">
            <div style="color:#f1f5f9; font-weight:bold; font-size:14px;">{label}</div>
            <div style="color:#94a3b8; font-size:11px; margin-top:4px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Seç" if not is_selected else "✓ Seçili",
                     key=f"style_{key}", use_container_width=True,
                     type="primary" if is_selected else "secondary"):
            st.session_state.selected_style = key
            st.rerun()

# --- Tweet Format ---
st.markdown("### 📐 Format")

_format_options = get_available_formats("tweet")
selected_format = st.session_state.get("selected_format", "spark")

# Show formats in 2 rows of 3
_fmt_keys = list(_format_options.keys())
_row1_keys = _fmt_keys[:3]
_row2_keys = _fmt_keys[3:]

for row_keys in [_row1_keys, _row2_keys]:
    fmt_cols = st.columns(len(row_keys))
    for i, fkey in enumerate(row_keys):
        finfo = _format_options[fkey]
        with fmt_cols[i]:
            is_sel = selected_format == fkey
            border = "2px solid #6366f1" if is_sel else "1px solid rgba(255,255,255,0.06)"
            bg = "rgba(99,102,241,0.06)" if is_sel else "rgba(15,20,35,0.7)"

            st.markdown(f"""
            <div style="background:{bg}; border:{border}; border-radius:12px;
                        padding:10px; text-align:center; min-height:78px;">
                <div style="color:#f1f5f9; font-weight:bold; font-size:13px;">{finfo['icon']} {finfo['name']}</div>
                <div style="color:#a5b4fc; font-size:12px;">{finfo['range']}</div>
                <div style="color:#94a3b8; font-size:11px; margin-top:2px;">{finfo['description']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Seç" if not is_sel else "✓ Seçili",
                         key=f"format_{fkey}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.selected_format = fkey
                st.rerun()

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# --- Additional Options ---
with st.expander("Ek Seçenekler"):
    col1, col2 = st.columns(2)

    with col1:
        additional_instructions = st.text_area(
            "Ek talimatlar (opsiyonel)",
            placeholder="Örn: 'Biraz daha teknik yaz', 'Espri ekle', 'Kısa tut'",
            height=80,
            key="additional_instructions"
        )

    with col2:
        thread_mode = st.checkbox("Thread modunda yaz", key="thread_mode")
        if thread_mode:
            thread_count = st.slider("Thread uzunluğu", 3, 10, 5, key="thread_count")

        use_premium = st.checkbox("X Premium (karakter sınırı yok)", value=True, key="use_premium")

    # Training data indicator (session_state first, then files)
    _analyses = load_all_analyses(session_state=st.session_state)
    if _analyses:
        usernames = [a.get("username", "?") for a in _analyses]
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.06); border:1px solid rgba(255,255,255,0.06); border-radius:8px;
                    padding:8px 12px; margin:4px 0; font-size:12px; color:#94a3b8;">
            🧠 Egitim verisi aktif: {', '.join(['@' + u for u in usernames[:5]])}
            ({sum(a.get('analysis', {}).get('total_tweets', 0) for a in _analyses)} tweet analiz edilmis)
        </div>
        """, unsafe_allow_html=True)

    # AI Provider selection
    col1, col2 = st.columns(2)
    provider_labels = {
        "minimax": "MiniMax (Uygun Fiyat)",
        "anthropic": "Anthropic Claude",
        "openai": "OpenAI GPT",
    }
    with col1:
        ai_provider = st.selectbox(
            "AI Sağlayıcı",
            options=list(provider_labels.keys()),
            format_func=lambda x: provider_labels[x],
            key="ai_provider"
        )
    with col2:
        if ai_provider == "anthropic":
            model_labels = {
                "claude-opus-4-6": "Opus 4.6 (En Güçlü)",
                "claude-sonnet-4-6": "Sonnet 4.6 (Dengeli)",
                "claude-haiku-4-5-20251001": "Haiku 4.5 (Hızlı/Ucuz)",
            }
            ai_model = st.selectbox(
                "Model",
                options=list(model_labels.keys()),
                format_func=lambda x: model_labels[x],
                key="ai_model_anthropic"
            )
        elif ai_provider == "minimax":
            minimax_labels = {
                "MiniMax-M2.5": "M2.5 (En Güçlü)",
                "MiniMax-M2.5-highspeed": "M2.5 Highspeed (Hızlı)",
                "MiniMax-M2": "M2 (Agent/Coding)",
            }
            ai_model = st.selectbox(
                "Model",
                options=list(minimax_labels.keys()),
                format_func=lambda x: minimax_labels[x],
                key="ai_model_minimax"
            )
        else:
            openai_labels = {
                "gpt-4.1": "GPT-4.1 (En Güçlü)",
                "gpt-4o": "GPT-4o (Dengeli)",
                "gpt-4o-mini": "GPT-4o Mini (Hızlı/Ucuz)",
            }
            ai_model = st.selectbox(
                "Model",
                options=list(openai_labels.keys()),
                format_func=lambda x: openai_labels[x],
                key="ai_model_openai"
            )

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# --- Generate Button ---
col1, col2 = st.columns(2)

with col1:
    generate_clicked = st.button(
        "✨ Tweet Üret",
        type="primary",
        use_container_width=True,
        key="generate_btn",
        disabled=not topic_text
    )

with col2:
    regenerate_clicked = st.button(
        "🔄 Yeniden Üret",
        use_container_width=True,
        key="regenerate_btn",
        disabled="generated_tweet" not in st.session_state
    )

# --- Generation Logic ---
if generate_clicked or regenerate_clicked:
    if not topic_text:
        st.warning("Lütfen bir konu girin!")
        st.stop()

    # Get API key
    ai_provider = st.session_state.get("ai_provider", "minimax")
    if ai_provider == "anthropic":
        api_key = get_secret("anthropic_api_key", "")
        model = st.session_state.get("ai_model_anthropic", "claude-sonnet-4-6")
    elif ai_provider == "minimax":
        api_key = get_secret("minimax_api_key", "")
        model = st.session_state.get("ai_model_minimax", "MiniMax-M2.5")
    else:
        api_key = get_secret("openai_api_key", "")
        model = st.session_state.get("ai_model_openai", "gpt-4o")

    if not api_key:
        st.error(f"{ai_provider.capitalize()} API anahtarı yapılandırılmamış! Ayarlar sayfasından ekleyin.")
        st.stop()

    # Get user samples, persona, and training data
    user_samples = load_user_samples()
    custom_persona = load_custom_persona()

    # Load training data from tweet analyses (session_state first, then files)
    analyses = load_all_analyses(session_state=st.session_state)
    training_context = build_training_context(analyses) if analyses else ""

    with st.spinner("Tweet üretiliyor... 🤖"):
        try:
            generator = ContentGenerator(
                provider=ai_provider,
                api_key=api_key,
                model=model,
                custom_persona=custom_persona if custom_persona else None,
                training_context=training_context if training_context else None,
            )

            thread_mode = st.session_state.get("thread_mode", False)
            additional = st.session_state.get("additional_instructions", "")
            max_length = 0 if st.session_state.get("use_premium", True) else 280

            # Get selected content format (passed via content_format param, not additional)
            sel_format = st.session_state.get("selected_format", "spark")

            # Clear edit widget state so text_area picks up the new value
            if "edit_tweet" in st.session_state:
                del st.session_state["edit_tweet"]

            # Check if we have topic research for normal tweet
            topic_research_ctx = ""
            if "topic_research_summary" in st.session_state and st.session_state.topic_research_summary:
                topic_research_ctx = st.session_state.topic_research_summary

            if write_mode == "quote" and quote_topic:
                # Quote tweet mode (with or without research)
                result = generator.generate_quote_tweet(
                    original_tweet=topic_text,
                    original_author=topic_source,
                    style=selected_style,
                    additional_context=additional,
                    user_samples=user_samples if user_samples else None,
                    research_summary=research_summary,
                    length_preference=sel_format,
                )

                # === DEEP VERIFY: Fact-check draft and refine ===
                do_verify = st.session_state.get("deep_verify_enabled", False)
                if do_verify and research_summary and result:
                    # Build AI client for verification
                    _v_client = None
                    _v_model = None
                    _v_provider = "minimax"
                    minimax_key = get_secret("minimax_api_key", "")
                    anthropic_key = get_secret("anthropic_api_key", "")
                    openai_key = get_secret("openai_api_key", "")
                    if minimax_key:
                        import openai as _oai
                        _v_client = _oai.OpenAI(api_key=minimax_key, base_url="https://api.minimax.io/v1")
                        _v_model = "MiniMax-M2.5"
                    elif anthropic_key:
                        import anthropic as _ant
                        _v_client = _ant.Anthropic(api_key=anthropic_key)
                        _v_model = "claude-haiku-4-5-20251001"
                        _v_provider = "anthropic"
                    elif openai_key:
                        import openai as _oai
                        _v_client = _oai.OpenAI(api_key=openai_key)
                        _v_model = "gpt-4o-mini"
                        _v_provider = "openai"

                    if _v_client:
                        with st.spinner("🔍 Taslak doğrulanıyor..."):
                            check_result = ai_fact_check_draft(
                                draft_tweet=result,
                                original_tweet=topic_text,
                                research_context=research_summary,
                                ai_client=_v_client,
                                ai_model=_v_model,
                                provider=_v_provider,
                            )

                        if check_result and not check_result.get("is_clean", True):
                            issues = check_result.get("issues", [])
                            if issues:
                                with st.spinner(f"🔍 {len(issues)} iddia doğrulanıyor..."):
                                    verified = verify_claims(issues)

                                verification_ctx = compile_verification_context(verified)

                                if verification_ctx:
                                    # Show what was found
                                    with st.expander(f"🔍 Doğrulama: {len(issues)} sorun düzeltildi", expanded=False):
                                        for v in verified:
                                            st.markdown(f"- ❌ **\"{v.get('claim', '')}\"** → {v.get('problem', '')}")
                                            if v.get("article"):
                                                st.caption(f"  ✅ Doğru bilgi: {v['article'].get('title', '')[:80]}")

                                    with st.spinner("✍️ Doğrulanmış bilgilerle yeniden yazılıyor..."):
                                        refined = generator.refine_tweet_with_verification(
                                            draft_tweet=result,
                                            original_tweet=topic_text,
                                            original_author=topic_source,
                                            research_summary=research_summary,
                                            verification_context=verification_ctx,
                                            style=selected_style,
                                            user_samples=user_samples if user_samples else None,
                                            length_preference=sel_format,
                                        )
                                    if refined:
                                        result = refined
                        else:
                            st.caption("✅ Taslak doğrulandı, sorun bulunamadı.")

                st.session_state.generated_tweet = result
                st.session_state.generated_thread = None

            elif thread_mode:
                # Thread mode
                thread_count = st.session_state.get("thread_count", 5)
                result = generator.generate_thread(
                    topic_text=topic_text,
                    topic_source=topic_source,
                    style=selected_style,
                    num_tweets=thread_count,
                    additional_context=additional,
                    user_samples=user_samples if user_samples else None,
                )
                st.session_state.generated_thread = result
                st.session_state.generated_tweet = None

            else:
                # Normal tweet (with optional topic research context)
                if topic_research_ctx:
                    # Append research context to additional instructions
                    research_note = f"\n\n## ARAŞTIRMA SONUÇLARI (bu bilgileri kullanarak güncel ve bilgili bir tweet yaz):\n{topic_research_ctx}"
                    additional = additional + research_note

                result = generator.generate_tweet(
                    topic_text=topic_text,
                    topic_source=topic_source,
                    style=selected_style,
                    additional_context=additional,
                    max_length=max_length,
                    user_samples=user_samples if user_samples else None,
                    content_format=sel_format,
                )

                # === DEEP VERIFY for normal tweets ===
                do_topic_verify = st.session_state.get("topic_deep_verify", False)
                if do_topic_verify and topic_research_ctx and result:
                    _v_client = None
                    _v_model = None
                    _v_provider = "minimax"
                    minimax_key = get_secret("minimax_api_key", "")
                    anthropic_key = get_secret("anthropic_api_key", "")
                    openai_key = get_secret("openai_api_key", "")
                    if minimax_key:
                        import openai as _oai
                        _v_client = _oai.OpenAI(api_key=minimax_key, base_url="https://api.minimax.io/v1")
                        _v_model = "MiniMax-M2.5"
                    elif anthropic_key:
                        import anthropic as _ant
                        _v_client = _ant.Anthropic(api_key=anthropic_key)
                        _v_model = "claude-haiku-4-5-20251001"
                        _v_provider = "anthropic"
                    elif openai_key:
                        import openai as _oai
                        _v_client = _oai.OpenAI(api_key=openai_key)
                        _v_model = "gpt-4o-mini"
                        _v_provider = "openai"

                    if _v_client:
                        with st.spinner("🔍 Tweet doğrulanıyor..."):
                            check_result = ai_fact_check_draft(
                                draft_tweet=result,
                                original_tweet=topic_text,
                                research_context=topic_research_ctx,
                                ai_client=_v_client,
                                ai_model=_v_model,
                                provider=_v_provider,
                            )

                        if check_result and not check_result.get("is_clean", True):
                            issues = check_result.get("issues", [])
                            if issues:
                                with st.spinner(f"🔍 {len(issues)} iddia doğrulanıyor..."):
                                    verified = verify_claims(issues)

                                verification_ctx = compile_verification_context(verified)

                                if verification_ctx:
                                    with st.expander(f"🔍 Doğrulama: {len(issues)} sorun düzeltildi", expanded=False):
                                        for v in verified:
                                            st.markdown(f"- ❌ **\"{v.get('claim', '')}\"** → {v.get('problem', '')}")
                                            if v.get("article"):
                                                st.caption(f"  ✅ Doğru bilgi: {v['article'].get('title', '')[:80]}")

                                    with st.spinner("✍️ Doğrulanmış bilgilerle yeniden yazılıyor..."):
                                        refined = generator.refine_tweet_with_verification(
                                            draft_tweet=result,
                                            original_tweet=topic_text,
                                            original_author="",
                                            research_summary=topic_research_ctx,
                                            verification_context=verification_ctx,
                                            style=selected_style,
                                            user_samples=user_samples if user_samples else None,
                                            length_preference=sel_format,
                                        )
                                    if refined:
                                        result = refined
                        else:
                            st.caption("✅ Tweet doğrulandı, sorun bulunamadı.")

                st.session_state.generated_tweet = result
                st.session_state.generated_thread = None

        except Exception as e:
            st.error(f"Üretim hatası: {e}")

# --- Display Generated Content ---
if "generated_tweet" in st.session_state and st.session_state.generated_tweet:
    st.markdown("### 📝 Oluşturulan Tweet")

    tweet_text = st.session_state.generated_tweet

    render_generated_tweet(tweet_text)

    # Quality score
    _sel_fmt = st.session_state.get("selected_format", "spark")
    _score = score_tweet(tweet_text, content_format=_sel_fmt)
    _fmt_name = CONTENT_FORMATS.get(_sel_fmt, {}).get("name", _sel_fmt)

    st.markdown(f"""
    <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.08);
                border-radius:10px; padding:12px 16px; margin:8px 0;">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <span style="font-size:20px; font-weight:bold; color:#f1f5f9;">
                    {_score['quality_emoji']} {_score['overall']}/100
                </span>
                <span style="color:#94a3b8; font-size:13px; margin-left:8px;">{_score['quality_label']}</span>
            </div>
            <div style="color:#94a3b8; font-size:12px;">
                📐 {_fmt_name} &nbsp;|&nbsp; {_score['char_count']} karakter
            </div>
        </div>
        <div style="display:flex; gap:16px; margin-top:8px;">
            <span style="color:#a5b4fc; font-size:12px;">🎯 Hook: {_score['hook_score']}/25</span>
            <span style="color:#a5b4fc; font-size:12px;">📊 Veri: {_score['data_score']}/25</span>
            <span style="color:#a5b4fc; font-size:12px;">🗣️ Doğallık: {_score['naturalness_score']}/25</span>
            <span style="color:#a5b4fc; font-size:12px;">📐 Format: {_score['format_score']}/25</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if _score['suggestions']:
        with st.expander("💡 İyileştirme Önerileri"):
            for _sug in _score['suggestions']:
                st.markdown(f"- {_sug}")

    # Edit option
    edited_text = st.text_area(
        "Düzenle (opsiyonel)",
        value=tweet_text,
        height=150,
        key="edit_tweet"
    )

    if edited_text != tweet_text:
        st.session_state.generated_tweet = edited_text
        tweet_text = edited_text

    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("🚀 API Paylaş", type="primary", use_container_width=True, key="publish_btn"):
            # Check Twitter API
            api_key = get_secret("twitter_api_key", "")
            api_secret = get_secret("twitter_api_secret", "")
            access_token = get_secret("twitter_access_token", "")
            access_secret = get_secret("twitter_access_secret", "")

            if not all([api_key, api_secret, access_token, access_secret]):
                st.error("Twitter API anahtarları eksik! Ayarlar sayfasından ekleyin.")
            else:
                try:
                    publisher = TweetPublisher(
                        api_key=api_key,
                        api_secret=api_secret,
                        access_token=access_token,
                        access_secret=access_secret,
                        bearer_token=get_secret("twitter_bearer_token", ""),
                    )

                    if write_mode == "quote" and quote_topic and quote_topic.get("id"):
                        result = publisher.post_quote_tweet(
                            text=tweet_text,
                            quoted_tweet_id=str(quote_topic["id"])
                        )
                    elif write_mode == "quote":
                        st.error("Quote edilecek tweet ID'si bulunamadı! Geçerli bir tweet URL'si girin.")
                        result = None
                    else:
                        result = publisher.post_tweet(text=tweet_text)

                    if result and result["success"]:
                        st.success(f"Tweet paylaşıldı! 🎉")
                        st.link_button("X'te Görüntüle", result["url"])

                        add_to_post_history({
                            "text": tweet_text,
                            "style": selected_style,
                            "url": result["url"],
                            "tweet_id": result["tweet_id"],
                            "posted_at": datetime.datetime.now().isoformat(),
                            "type": "quote" if write_mode == "quote" else "tweet",
                        })
                    elif result:
                        st.error(f"Paylaşım hatası: {result['error']}")

                except Exception as e:
                    st.error(f"Hata: {e}")

    with col2:
        # Build X intent URL — opens X app/website with pre-filled text
        if write_mode == "quote" and quote_topic and quote_topic.get("id"):
            tid = str(quote_topic['id'])
            quote_url = f"https://x.com/i/status/{tid}"
            # Strip the quoted tweet URL from text (AI sometimes appends it)
            clean_text = re.sub(
                r'https?://(?:twitter\.com|x\.com)/\S+/status/' + re.escape(tid) + r'\S*',
                '', tweet_text
            ).strip()
            # attachment_url creates a proper quote tweet in X (not just a link)
            intent_url = (
                f"https://x.com/intent/tweet"
                f"?text={url_quote(clean_text)}"
                f"&attachment_url={url_quote(quote_url)}"
            )
        else:
            intent_url = f"https://x.com/intent/tweet?text={url_quote(tweet_text)}"
        st.link_button("📱 X'te Aç", intent_url, use_container_width=True)
        st.caption("Görsel ekleyebilirsin")

    with col3:
        if st.button("💾 Taslak Kaydet", use_container_width=True, key="save_draft_btn"):
            add_draft(
                text=tweet_text,
                topic=topic_text[:100] if topic_text else "",
                style=selected_style
            )
            st.success("Taslak kaydedildi!")

    with col4:
        if st.button("📋 Kopyala", use_container_width=True, key="copy_btn"):
            st.code(tweet_text, language=None)
            st.info("Yukarıdaki metni kopyalayabilirsiniz")

    with col5:
        if st.button("🔄 Yeniden Yaz", use_container_width=True, key="rewrite_btn"):
            try:
                ai_provider = st.session_state.get("ai_provider", "minimax")
                if ai_provider == "anthropic":
                    api_key = get_secret("anthropic_api_key", "")
                    model = st.session_state.get("ai_model_anthropic", "claude-sonnet-4-6")
                elif ai_provider == "minimax":
                    api_key = get_secret("minimax_api_key", "")
                    model = st.session_state.get("ai_model_minimax", "MiniMax-M2.5")
                else:
                    api_key = get_secret("openai_api_key", "")
                    model = st.session_state.get("ai_model_openai", "gpt-4o")

                _rw_analyses = load_all_analyses(session_state=st.session_state)
                _rw_training = build_training_context(_rw_analyses) if _rw_analyses else ""
                _rw_persona = load_custom_persona()
                generator = ContentGenerator(
                    provider=ai_provider, api_key=api_key, model=model,
                    custom_persona=_rw_persona if _rw_persona else None,
                    training_context=_rw_training if _rw_training else None,
                )
                rewritten = generator.rewrite_tweet(
                    draft=tweet_text,
                    style=selected_style,
                    instructions=st.session_state.get("additional_instructions", "")
                )
                st.session_state.generated_tweet = rewritten
                st.rerun()
            except Exception as e:
                st.error(f"Yeniden yazma hatası: {e}")

    # --- Media Finder Section ---
    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    with st.expander("🖼️ Görsel/Video Bul", expanded=False):
        st.markdown("""
        <div style="color:#94a3b8; font-size:12px; margin-bottom:10px;">
            Tweet'inize eklemek için konuyla ilgili görsel ve video önerileri alın
        </div>
        """, unsafe_allow_html=True)

        media_source = render_media_source_selector(key_suffix="yaz")

        if st.button("🔍 Görsel Ara", type="secondary", use_container_width=True, key="find_media_yaz"):
            from modules.media_finder import find_media
            # Get twikit client for X search
            _twikit = None
            if media_source in ("x", "all"):
                try:
                    from modules.twikit_client import TwikitSearchClient
                    _tw_user = get_secret("twikit_username", "")
                    _tw_pass = get_secret("twikit_password", "")
                    _tw_email = get_secret("twikit_email", "")
                    if _tw_user:
                        _twikit = TwikitSearchClient(
                            username=_tw_user, password=_tw_pass, email=_tw_email
                        )
                        _twikit.authenticate()
                except Exception as e:
                    st.caption(f"Twikit bağlantı hatası: {e}")

            with st.spinner("Görseller aranıyor..."):
                media_result = find_media(
                    topic_text=tweet_text,
                    source=media_source,
                    twikit_client=_twikit,
                )
                st.session_state["yaz_media_result"] = media_result

        if "yaz_media_result" in st.session_state and st.session_state["yaz_media_result"]:
            render_media_suggestions(st.session_state["yaz_media_result"], key_prefix="yaz")

            # Vision analysis for images from research
            if st.session_state["yaz_media_result"].images:
                analyze_col1, analyze_col2 = st.columns([3, 1])
                with analyze_col2:
                    if st.button("👁️ Görseli Analiz Et", key="analyze_media_yaz", use_container_width=True):
                        first_img = st.session_state["yaz_media_result"].images[0]
                        # Use vision-capable AI
                        _prov = st.session_state.get("ai_provider", "minimax")
                        _vision_provider = _prov if _prov != "minimax" else "anthropic"
                        _vision_key = get_secret(f"{_vision_provider}_api_key", "")
                        if _vision_key:
                            try:
                                gen = ContentGenerator(
                                    provider=_vision_provider,
                                    api_key=_vision_key,
                                )
                                analysis = gen.analyze_image(first_img.url, context=tweet_text[:200])
                                if analysis:
                                    st.session_state["yaz_image_analysis"] = analysis
                            except Exception as e:
                                st.error(f"Görsel analiz hatası: {e}")
                        else:
                            st.warning("Görsel analizi için Anthropic veya OpenAI API anahtarı gerekli.")

            if "yaz_image_analysis" in st.session_state:
                render_image_analysis(st.session_state["yaz_image_analysis"])

# Thread display
if "generated_thread" in st.session_state and st.session_state.generated_thread:
    st.markdown("### 🧵 Oluşturulan Thread")

    tweets = st.session_state.generated_thread
    render_thread_preview(tweets)

    # Edit individual tweets
    with st.expander("Thread'i düzenle"):
        edited_tweets = []
        for i, tweet in enumerate(tweets):
            edited = st.text_area(
                f"Tweet {i+1}/{len(tweets)}",
                value=tweet,
                height=80,
                key=f"edit_thread_{i}"
            )
            edited_tweets.append(edited)
            st.caption(f"{len(edited)} karakter")

        if st.button("Değişiklikleri Kaydet", key="save_thread_edits"):
            st.session_state.generated_thread = edited_tweets
            st.rerun()

    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    # Thread actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Thread Paylaş", type="primary", use_container_width=True, key="publish_thread_btn"):
            api_key = get_secret("twitter_api_key", "")
            api_secret = get_secret("twitter_api_secret", "")
            access_token = get_secret("twitter_access_token", "")
            access_secret = get_secret("twitter_access_secret", "")

            if not all([api_key, api_secret, access_token, access_secret]):
                st.error("Twitter API anahtarları eksik!")
            else:
                try:
                    publisher = TweetPublisher(
                        api_key=api_key,
                        api_secret=api_secret,
                        access_token=access_token,
                        access_secret=access_secret,
                    )
                    results = publisher.post_thread(tweets)

                    success_count = sum(1 for r in results if r["success"])
                    if success_count == len(tweets):
                        st.success(f"Thread paylaşıldı! ({success_count} tweet) 🎉")
                        if results[0].get("url"):
                            st.link_button("X'te Görüntüle", results[0]["url"])

                        add_to_post_history({
                            "text": f"[Thread - {len(tweets)} tweet] {tweets[0][:80]}...",
                            "style": selected_style,
                            "url": results[0].get("url", ""),
                            "tweet_id": results[0].get("tweet_id", ""),
                            "posted_at": datetime.datetime.now().isoformat(),
                            "type": "thread",
                        })
                    else:
                        st.warning(f"{success_count}/{len(tweets)} tweet paylaşıldı.")
                        for r in results:
                            if not r["success"]:
                                st.error(r["error"])

                except Exception as e:
                    st.error(f"Thread paylaşım hatası: {e}")

    with col2:
        if st.button("💾 Thread Taslak Kaydet", use_container_width=True, key="save_thread_draft"):
            add_draft(
                text="\n---\n".join(tweets),
                topic=topic_text[:100] if topic_text else "",
                style=selected_style
            )
            st.success("Thread taslağı kaydedildi!")

    with col3:
        if st.button("📋 Thread Kopyala", use_container_width=True, key="copy_thread"):
            full_thread = "\n\n".join([f"{i+1}/{len(tweets)}\n{t}" for i, t in enumerate(tweets)])
            st.code(full_thread, language=None)

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# --- Drafts Section ---
drafts = load_draft_tweets()
if drafts:
    with st.expander(f"📁 Taslaklar ({len(drafts)})"):
        for i, draft in enumerate(drafts[:10]):
            col1, col2 = st.columns([4, 1])
            with col1:
                preview = draft["text"][:100]
                if len(draft["text"]) > 100:
                    preview += "..."
                st.markdown(f"""
                <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                            border-radius:8px; padding:10px 14px; margin:4px 0;">
                    <div style="color:#f1f5f9; font-size:13px;">{preview}</div>
                    <div style="color:#94a3b8; font-size:11px; margin-top:4px;">
                        {draft.get('style', '')} | {draft.get('created_at', '')[:10]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("Kullan", key=f"use_draft_{i}", use_container_width=True):
                    st.session_state.generated_tweet = draft["text"]
                    st.rerun()
