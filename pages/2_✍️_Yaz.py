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
if write_mode == "quote" and quote_topic:
    st.markdown("""
    <div class="main-header">
        <h1>💬 Quote Tweet Yaz</h1>
        <p style="color:#8899a6;">Seçilen tweet'e doğal bir yorum yaz</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>✍️ Tweet Yazıcı</h1>
        <p style="color:#8899a6;">AI ile doğal, insan gibi tweet üret</p>
    </div>
    """, unsafe_allow_html=True)

# --- Topic Input ---
st.markdown("### 📌 Konu")

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

elif selected_topic:
    st.info(f"📌 Seçilen konu: {selected_topic.get('text', '')[:100]}...")
    topic_text = selected_topic.get("text", "")
    topic_source = selected_topic.get("url", "")

    if st.button("Konuyu temizle", key="clear_topic"):
        st.session_state.selected_topic = None
        st.rerun()
else:
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
    with col1:
        ai_provider = st.selectbox(
            "AI Sağlayıcı",
            options=["anthropic", "openai"],
            format_func=lambda x: "Anthropic Claude" if x == "anthropic" else "OpenAI GPT",
            key="ai_provider"
        )
    with col2:
        if ai_provider == "anthropic":
            ai_model = st.selectbox(
                "Model",
                options=["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
                format_func=lambda x: x.split("-")[1].capitalize() + " " + x.split("-")[2].replace("20250514", "4").replace("20251001", "4.5"),
                key="ai_model_anthropic"
            )
        else:
            ai_model = st.selectbox(
                "Model",
                options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
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
    ai_provider = st.session_state.get("ai_provider", "anthropic")
    if ai_provider == "anthropic":
        api_key = get_secret("anthropic_api_key", "")
        model = st.session_state.get("ai_model_anthropic", "claude-sonnet-4-20250514")
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

            if write_mode == "quote" and quote_topic:
                # Quote tweet mode
                result = generator.generate_quote_tweet(
                    original_tweet=topic_text,
                    original_author=topic_source,
                    style=selected_style,
                    additional_context=additional,
                    user_samples=user_samples if user_samples else None,
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
                ai_provider = st.session_state.get("ai_provider", "anthropic")
                if ai_provider == "anthropic":
                    api_key = get_secret("anthropic_api_key", "")
                    model = st.session_state.get("ai_model_anthropic", "claude-sonnet-4-20250514")
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
