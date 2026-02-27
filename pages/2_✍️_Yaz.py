"""
Tweet Yazıcı Sayfası
AI ile doğal tweet üretir, düzenler ve paylaşır
"""
import streamlit as st
import datetime
from modules.ui_components import (inject_custom_css, check_password,
                                   render_generated_tweet, render_thread_preview,
                                   get_secret)
from modules.content_generator import ContentGenerator, get_available_styles, get_style_info
from modules.tweet_publisher import TweetPublisher
from modules.deep_research import extract_tweet_id, research_topic
from modules.style_manager import (
    load_user_samples, load_custom_persona,
    add_to_post_history, add_draft, load_draft_tweets
)

# Page config
st.set_page_config(
    page_title="Tweet Yaz | X AI Otomasyon",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_css()

if not check_password():
    st.stop()

# --- Determine mode ---
write_mode = st.session_state.get("write_mode", "normal")
selected_topic = st.session_state.get("selected_topic", None)
quote_topic = st.session_state.get("quote_topic", None)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>✍️ Tweet Yazıcı</h1>
    <p style="color:#8899a6;">AI ile doğal, insan gibi tweet üret</p>
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
    <div style="background:#16213e; border:1px solid #1DA1F2; border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">🔬 Araştırmalı Quote Tweet</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            Tweet URL → Thread'i oku → Web'de araştır → X'te ara → Bilgili quote yaz
        </div>
    </div>
    """, unsafe_allow_html=True)

    quote_url = st.text_input(
        "Tweet URL'si",
        placeholder="https://x.com/kullanici/status/123456789...",
        key="research_quote_url"
    )

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
                <div class="tweet-card" style="border-color:#1DA1F2;">
                    <div>
                        <span class="tweet-author">{original_tweet.author_name}</span>
                        <span class="tweet-username">@{original_author}</span>
                    </div>
                    <div class="tweet-text">{original_tweet_text}</div>
                    <div style="color:#8899a6; font-size:12px; margin-top:8px;">
                        ❤️ {original_tweet.like_count:,} · 🔁 {original_tweet.retweet_count:,} · 💬 {original_tweet.reply_count:,}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # === FULL RESEARCH PIPELINE ===
            progress_text = st.empty()
            with st.spinner("Derin araştırma yapılıyor..."):
                research = research_topic(
                    tweet_text=original_tweet_text,
                    tweet_author=original_author,
                    tweet_id=tweet_id,
                    scanner=scanner,
                    progress_callback=lambda msg: progress_text.caption(msg),
                )
                progress_text.empty()

            st.session_state.research_data = research
            research_summary = research.summary

            # --- Show thread if found ---
            if len(research.thread_texts) > 1:
                with st.expander(f"🧵 Thread ({len(research.thread_texts)} tweet)", expanded=True):
                    for i, t in enumerate(research.thread_texts, 1):
                        st.markdown(f"""
                        <div style="background:#1a1a2e; border-left:3px solid #1DA1F2;
                                    padding:8px 12px; margin:4px 0; border-radius:4px;">
                            <span style="color:#1DA1F2; font-weight:bold;">{i}/</span>
                            <span style="color:#f0f0f0; font-size:13px;">{t}</span>
                        </div>
                        """, unsafe_allow_html=True)

            # --- Show research results ---
            with st.expander("📊 Araştırma Sonuçları", expanded=True):
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
                        st.markdown(f"- @{rt['author']} ({rt['likes']} ❤️): _{rt['text'][:140]}_")

                if not research.web_results and not research.deep_articles and not research.related_tweets:
                    st.warning("Bu konu için web'de yeterli bilgi bulunamadı.")

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
    if write_mode == "quote" and quote_topic:
        st.markdown(f"""
        <div class="tweet-card" style="border-color:#1DA1F2;">
            <div>
                <span class="tweet-author">Orijinal Tweet</span>
                <span class="tweet-username">@{quote_topic.get('author', '')}</span>
            </div>
            <div class="tweet-text">{quote_topic.get('text', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        topic_text = quote_topic.get("text", "")
        topic_source = quote_topic.get("author", "")

        if st.button("Quote modu kapat", key="clear_quote"):
            st.session_state.write_mode = "normal"
            st.session_state.quote_topic = None
            st.rerun()
    else:
        st.info("Tara sayfasından bir tweet seçip 'Quote Tweet' butonuna tıklayın, veya '🔬 Araştırmalı Quote Tweet' sekmesini kullanın.")
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
            placeholder="Tweet yazmak istediğiniz konuyu veya AI gelişmesini buraya yazın...\n\nÖrnek: Qwen 3 modeli çıktı, coding benchmark'larında GPT-4o'yu geçti",
            height=120,
            key="manual_topic"
        )
        topic_source = st.text_input(
            "Kaynak (opsiyonel)",
            placeholder="Tweet URL'si veya kaynak",
            key="topic_source"
        )

# Get research summary if available (from research tab)
if "research_summary" in st.session_state:
    research_summary = st.session_state.research_summary

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# --- Writing Style ---
st.markdown("### 🎨 Yazım Tarzı")

styles = get_available_styles()

# Don't show quote_tweet in normal mode
if write_mode != "quote":
    display_styles = {k: v for k, v in styles.items() if k != "quote_tweet"}
else:
    display_styles = {"quote_tweet": styles["quote_tweet"]}

style_options = list(display_styles.keys())
style_labels = [display_styles[k]["name"] for k in style_options]

cols = st.columns(len(style_options))
selected_style = st.session_state.get("selected_style", style_options[0])

for i, (key, label) in enumerate(zip(style_options, style_labels)):
    with cols[i]:
        desc = display_styles[key]["description"]
        is_selected = selected_style == key
        border = "2px solid #1DA1F2" if is_selected else "1px solid #2a2a4a"
        bg = "#16213e" if is_selected else "#1a1a2e"

        st.markdown(f"""
        <div style="background:{bg}; border:{border}; border-radius:12px;
                    padding:12px; text-align:center; min-height:80px;">
            <div style="color:#f0f0f0; font-weight:bold; font-size:14px;">{label}</div>
            <div style="color:#8899a6; font-size:11px; margin-top:4px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Seç" if not is_selected else "✓ Seçili",
                     key=f"style_{key}", use_container_width=True,
                     type="primary" if is_selected else "secondary"):
            st.session_state.selected_style = key
            st.rerun()

# --- Tweet Length ---
st.markdown("### 📏 Uzunluk")

length_options = {
    "kisa": {"label": "Kısa", "range": "100-280", "desc": "Tek tweet, vurucu", "icon": "📝"},
    "orta": {"label": "Orta", "range": "281-500", "desc": "Detaylı tek tweet", "icon": "📄"},
    "uzun": {"label": "Uzun", "range": "501-1000", "desc": "Derinlemesine analiz", "icon": "📑"},
}

selected_length = st.session_state.get("selected_length", "orta")

len_cols = st.columns(len(length_options))
for i, (lkey, linfo) in enumerate(length_options.items()):
    with len_cols[i]:
        is_sel = selected_length == lkey
        border = "2px solid #1DA1F2" if is_sel else "1px solid #2a2a4a"
        bg = "#16213e" if is_sel else "#1a1a2e"

        st.markdown(f"""
        <div style="background:{bg}; border:{border}; border-radius:12px;
                    padding:12px; text-align:center; min-height:70px;">
            <div style="color:#f0f0f0; font-weight:bold; font-size:14px;">{linfo['icon']} {linfo['label']}</div>
            <div style="color:#1DA1F2; font-size:13px;">{linfo['range']} karakter</div>
            <div style="color:#8899a6; font-size:11px; margin-top:2px;">{linfo['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Seç" if not is_sel else "✓ Seçili",
                     key=f"length_{lkey}", use_container_width=True,
                     type="primary" if is_sel else "secondary"):
            st.session_state.selected_length = lkey
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

    # Get user samples and persona
    user_samples = load_user_samples()
    custom_persona = load_custom_persona()

    with st.spinner("Tweet üretiliyor... 🤖"):
        try:
            generator = ContentGenerator(
                provider=ai_provider,
                api_key=api_key,
                model=model,
                custom_persona=custom_persona if custom_persona else None,
            )

            thread_mode = st.session_state.get("thread_mode", False)
            additional = st.session_state.get("additional_instructions", "")
            max_length = 0 if st.session_state.get("use_premium", True) else 280

            # Add length preference to additional context
            sel_len = st.session_state.get("selected_length", "orta")
            length_map = {
                "kisa": "UZUNLUK: 100-280 karakter arası yaz. Kısa, vurucu, tek tweet.",
                "orta": "UZUNLUK: 281-500 karakter arası yaz. Detaylı ama öz.",
                "uzun": "UZUNLUK: 501-1000 karakter arası yaz. Derinlemesine analiz, birden fazla paragraf.",
            }
            length_instruction = length_map.get(sel_len, length_map["orta"])
            if additional:
                additional = f"{length_instruction}\n{additional}"
            else:
                additional = length_instruction

            if write_mode == "quote" and quote_topic:
                # Quote tweet mode (with or without research)
                result = generator.generate_quote_tweet(
                    original_tweet=topic_text,
                    original_author=topic_source,
                    style=selected_style,
                    additional_context=additional,
                    user_samples=user_samples if user_samples else None,
                    research_summary=research_summary,
                    length_preference=sel_len,
                )
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
                # Normal tweet
                result = generator.generate_tweet(
                    topic_text=topic_text,
                    topic_source=topic_source,
                    style=selected_style,
                    additional_context=additional,
                    max_length=max_length,
                    user_samples=user_samples if user_samples else None,
                )
                st.session_state.generated_tweet = result
                st.session_state.generated_thread = None

        except Exception as e:
            st.error(f"Üretim hatası: {e}")

# --- Display Generated Content ---
if "generated_tweet" in st.session_state and st.session_state.generated_tweet:
    st.markdown("### 📝 Oluşturulan Tweet")

    tweet_text = st.session_state.generated_tweet

    render_generated_tweet(tweet_text)

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
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🚀 Paylaş", type="primary", use_container_width=True, key="publish_btn"):
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

                    if write_mode == "quote" and quote_topic:
                        result = publisher.post_quote_tweet(
                            text=tweet_text,
                            quoted_tweet_id=quote_topic["id"]
                        )
                    else:
                        result = publisher.post_tweet(text=tweet_text)

                    if result["success"]:
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
                    else:
                        st.error(f"Paylaşım hatası: {result['error']}")

                except Exception as e:
                    st.error(f"Hata: {e}")

    with col2:
        if st.button("💾 Taslak Kaydet", use_container_width=True, key="save_draft_btn"):
            add_draft(
                text=tweet_text,
                topic=topic_text[:100] if topic_text else "",
                style=selected_style
            )
            st.success("Taslak kaydedildi!")

    with col3:
        if st.button("📋 Kopyala", use_container_width=True, key="copy_btn"):
            st.code(tweet_text, language=None)
            st.info("Yukarıdaki metni kopyalayabilirsiniz")

    with col4:
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

                generator = ContentGenerator(
                    provider=ai_provider, api_key=api_key, model=model
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
                <div style="background:#1a1a2e; border:1px solid #2a2a4a;
                            border-radius:8px; padding:10px 14px; margin:4px 0;">
                    <div style="color:#f0f0f0; font-size:13px;">{preview}</div>
                    <div style="color:#8899a6; font-size:11px; margin-top:4px;">
                        {draft.get('style', '')} | {draft.get('created_at', '')[:10]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("Kullan", key=f"use_draft_{i}", use_container_width=True):
                    st.session_state.generated_tweet = draft["text"]
                    st.rerun()
