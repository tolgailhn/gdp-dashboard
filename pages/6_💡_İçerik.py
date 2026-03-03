"""
İçerik Üretici Sayfası
AI ile konu keşfet, uzun içerik üret, thread oluştur
"""
import streamlit as st
import datetime
from modules.ui_components import (inject_custom_css, check_password,
                                   get_secret, render_sidebar_nav)
from modules.content_generator import ContentGenerator
from modules.deep_research import discover_topics, research_topic_from_text
from modules.style_manager import load_user_samples, add_draft
from modules.tweet_publisher import TweetPublisher

# Page config
st.set_page_config(
    page_title="İçerik Üret | X AI Otomasyon",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_custom_css()

if not check_password():
    st.stop()

render_sidebar_nav(current_page="icerik")

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>💡 İçerik Üretici</h1>
    <p style="color:#8899a6;">Konu keşfet, araştır, uzun içerik üret</p>
</div>
""", unsafe_allow_html=True)

# --- Init AI (same logic as Yaz page) ---
def get_ai_client():
    """Build AI client using the same key lookup as Yaz page."""
    import openai as _openai
    import anthropic as _anthropic

    minimax_key = get_secret("minimax_api_key", "")
    anthropic_key = get_secret("anthropic_api_key", "")
    openai_key = get_secret("openai_api_key", "")

    if minimax_key:
        client = _openai.OpenAI(api_key=minimax_key, base_url="https://api.minimax.io/v1")
        return client, "MiniMax-M2.5", "minimax", minimax_key
    elif anthropic_key:
        client = _anthropic.Anthropic(api_key=anthropic_key)
        return client, "claude-haiku-4-5-20251001", "anthropic", anthropic_key
    elif openai_key:
        client = _openai.OpenAI(api_key=openai_key)
        return client, "gpt-4o-mini", "openai", openai_key
    else:
        return None, None, None, None


def get_scanner():
    """Try to initialize X scanner for topic discovery."""
    try:
        from modules.x_scanner import XScanner
        cookies = get_secret("x_cookies", get_secret("X_COOKIES", ""))
        if not cookies:
            return None
        scanner = XScanner(cookies)
        return scanner
    except Exception:
        return None


ai_client, ai_model, ai_provider, ai_api_key = get_ai_client()

if not ai_client:
    st.error("AI API anahtarı bulunamadı. Ayarlar sayfasından yapılandırın.")
    st.stop()

# --- Tabs ---
tab1, tab2 = st.tabs(["🔍 Konu Keşfet", "✍️ İçerik Üret"])

# ============================================================
# TAB 1: Topic Discovery
# ============================================================
with tab1:
    st.markdown("""
    <div style="background:#16213e; border:1px solid #1DA1F2; border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">🔍 Konu Keşfet</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            AI, X'te trend konuları ve güncel haberleri tarayıp sana içerik önerileri sunar
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        focus_area = st.text_input(
            "Odak Alanı",
            value="AI ve teknoloji",
            placeholder="Örn: yapay zeka, SaaS, girişimcilik...",
            key="topic_focus"
        )
    with col2:
        st.write("")
        st.write("")
        discover_btn = st.button("🔍 Konuları Keşfet", type="primary", use_container_width=True)

    if discover_btn:
        scanner = get_scanner()
        progress = st.empty()
        with st.spinner("Konular araştırılıyor..."):
            topics = discover_topics(
                ai_client=ai_client,
                ai_model=ai_model,
                ai_provider=ai_provider,
                scanner=scanner,
                focus_area=focus_area,
                progress_callback=lambda msg: progress.info(msg),
            )
        progress.empty()

        if topics:
            st.session_state["discovered_topics"] = topics
            st.success(f"{len(topics)} konu önerisi bulundu!")
        else:
            st.warning("Konu önerisi bulunamadı. Farklı bir odak alanı deneyin.")

    # Display discovered topics
    if "discovered_topics" in st.session_state and st.session_state["discovered_topics"]:
        st.markdown("### 📋 Önerilen Konular")

        for i, topic in enumerate(st.session_state["discovered_topics"]):
            title = topic.get("title", f"Konu {i+1}")
            desc = topic.get("description", "")
            angle = topic.get("angle", "")
            potential = topic.get("potential", "")

            with st.expander(f"**{i+1}. {title}**", expanded=(i < 3)):
                st.write(desc)
                if angle:
                    st.markdown(f"**Açı:** {angle}")
                if potential:
                    st.markdown(f"**Potansiyel:** {potential}")

                if st.button(f"Bu konuyu yaz →", key=f"pick_topic_{i}"):
                    st.session_state["content_topic"] = title
                    st.session_state["content_desc"] = desc
                    st.session_state["content_angle"] = angle
                    st.rerun()


# ============================================================
# TAB 2: Content Generation
# ============================================================
with tab2:
    st.markdown("""
    <div style="background:#16213e; border:1px solid #1e3a5f; border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">✍️ Uzun İçerik Üret</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            Konu gir → AI araştırsın → Detaylı, uzun-form X içeriği üretsin
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pre-fill from topic discovery
    default_topic = st.session_state.get("content_topic", "")
    default_desc = st.session_state.get("content_desc", "")
    default_angle = st.session_state.get("content_angle", "")

    # --- Input Form ---
    topic = st.text_input(
        "Konu",
        value=default_topic,
        placeholder="Ne hakkında yazmak istiyorsun?",
        key="content_topic_input",
    )

    col_style, col_len = st.columns(2)
    with col_style:
        style_options = {
            "deneyim": "🗣️ Kişisel Deneyim",
            "egitici": "📚 Eğitici / Tutorial",
            "karsilastirma": "⚖️ Karşılaştırma",
            "analiz": "📊 Analiz",
            "hikaye": "📖 Hikaye Anlatımı",
        }

        # Auto-select style from angle
        default_style_idx = 0
        if default_angle:
            angle_lower = default_angle.lower()
            if "deneyim" in angle_lower or "kişisel" in angle_lower:
                default_style_idx = 0
            elif "eğitici" in angle_lower or "tutorial" in angle_lower or "nasıl" in angle_lower:
                default_style_idx = 1
            elif "karşılaştır" in angle_lower:
                default_style_idx = 2
            elif "analiz" in angle_lower:
                default_style_idx = 3
            elif "hikaye" in angle_lower:
                default_style_idx = 4

        style = st.selectbox(
            "İçerik Tarzı",
            options=list(style_options.keys()),
            format_func=lambda x: style_options[x],
            index=default_style_idx,
            key="content_style",
        )

    with col_len:
        length_options = {
            "kisa": "📏 Kısa (300-500 karakter)",
            "orta": "📐 Orta (500-1000 karakter)",
            "uzun": "📏 Uzun (1000-2000 karakter)",
        }
        length = st.selectbox(
            "Uzunluk",
            options=list(length_options.keys()),
            format_func=lambda x: length_options[x],
            index=1,
            key="content_length",
        )

    extra_instructions = st.text_area(
        "Ek Talimatlar (opsiyonel)",
        value=default_desc,
        placeholder="Ek detay, ton, hedef kitle vs. varsa yaz...",
        height=80,
        key="content_extra",
    )

    # --- Research settings ---
    do_research = st.checkbox("🔬 Önce konuyu araştır", value=True, key="content_research")

    if do_research:
        research_mode_options = {
            "x_and_web": "🌐 X + Web (Önerilen)",
            "x_only": "🐦 Sadece X",
            "x_deep": "🔬 Derin X (50-100 tweet)",
        }
        col_rm, col_ag = st.columns(2)
        with col_rm:
            research_mode = st.selectbox(
                "Araştırma Modu",
                options=list(research_mode_options.keys()),
                format_func=lambda x: research_mode_options[x],
                index=0,
                key="research_mode",
            )
        with col_ag:
            st.write("")
            st.write("")
            use_agentic = st.checkbox(
                "🤖 AI Otonom Araştırma",
                value=False,
                key="use_agentic",
                help="AI internette kendi başına gezinip bilgi toplar (daha yavaş ama daha kapsamlı)",
            )

    generate_btn = st.button("✨ İçerik Üret", type="primary", use_container_width=True, key="gen_content_btn")

    if generate_btn and topic:
        research_context = ""

        # Step 1: Research if requested
        if do_research:
            progress = st.empty()
            with st.spinner("Konu araştırılıyor..."):
                try:
                    scanner = get_scanner()
                    research_result = research_topic_from_text(
                        topic_input=topic,
                        scanner=scanner,
                        time_hours=24,
                        search_mode=research_mode,
                        progress_callback=lambda msg: progress.info(msg),
                        ai_client=ai_client,
                        ai_model=ai_model,
                        ai_provider=ai_provider,
                        use_agentic=use_agentic,
                    )
                    progress.empty()
                    if research_result and research_result.summary:
                        research_context = research_result.summary

                        # Show research stats
                        stats_parts = []
                        if research_result.x_tweets:
                            stats_parts.append(f"🐦 {len(research_result.x_tweets)} tweet")
                        if research_result.web_results:
                            stats_parts.append(f"🌐 {len(research_result.web_results)} web sonucu")
                        if research_result.news_results:
                            stats_parts.append(f"📰 {len(research_result.news_results)} haber")
                        if research_result.deep_articles:
                            stats_parts.append(f"📄 {len(research_result.deep_articles)} makale")
                        if getattr(research_result, 'agentic_summary', None):
                            stats_parts.append("🤖 AI araştırma")

                        st.success(f"Araştırma tamamlandı! ({' | '.join(stats_parts)})")
                        with st.expander("📄 Araştırma Verileri", expanded=False):
                            st.text(research_context[:5000])
                    else:
                        progress.empty()
                        st.info("Araştırma sonucu bulunamadı, direkt içerik üretiliyor.")
                except Exception as e:
                    progress.empty()
                    st.warning(f"Araştırma hatası (devam ediliyor): {e}")

        # Step 2: Generate content
        with st.spinner("İçerik üretiliyor..."):
            try:
                user_samples = load_user_samples()
                generator = ContentGenerator(
                    provider=ai_provider,
                    api_key=ai_api_key,
                    model=ai_model,
                )
                content = generator.generate_long_content(
                    topic=topic,
                    research_context=research_context,
                    style=style,
                    length=length,
                    additional_instructions=extra_instructions,
                    user_samples=user_samples if user_samples else None,
                )
                st.session_state["generated_content"] = content
                st.session_state["generated_content_topic"] = topic
            except Exception as e:
                st.error(f"İçerik üretim hatası: {e}")

    # --- Display generated content ---
    if "generated_content" in st.session_state and st.session_state["generated_content"]:
        content = st.session_state["generated_content"]

        st.markdown("---")
        st.markdown("### 📝 Üretilen İçerik")

        # Preview box
        st.markdown(f"""
        <div style="background:#192734; border:1px solid #38444d; border-radius:16px;
                    padding:20px; margin:12px 0; font-size:15px; line-height:1.7;
                    color:#e1e8ed; white-space:pre-wrap;">{content}</div>
        """, unsafe_allow_html=True)

        char_count = len(content)
        st.caption(f"📊 {char_count} karakter")
        if char_count > 280:
            st.info(f"Bu içerik {char_count} karakter — X'te uzun post olarak paylaşılabilir (X Premium).")

        # Actions
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📋 Kopyala", key="copy_content"):
                st.code(content, language=None)
                st.success("Yukarıdan kopyalayabilirsiniz!")

        with col_b:
            if st.button("💾 Taslağa Kaydet", key="save_draft"):
                try:
                    add_draft(content, label=st.session_state.get("generated_content_topic", "İçerik"))
                    st.success("Taslak kaydedildi!")
                except Exception as e:
                    st.error(f"Taslak kaydetme hatası: {e}")

        with col_c:
            if st.button("🔄 Yeniden Üret", key="regen_content"):
                # Clear and re-trigger
                st.session_state.pop("generated_content", None)
                st.rerun()

        # Direct publish option
        st.markdown("---")
        with st.expander("📤 Direkt Paylaş"):
            st.warning("Paylaşmadan önce içeriği gözden geçirdiğinizden emin olun!")
            if st.button("🐦 X'te Paylaş", key="publish_content"):
                try:
                    cookies = get_secret("x_cookies", get_secret("X_COOKIES", ""))
                    if not cookies:
                        st.error("X çerezleri ayarlanmamış. Ayarlar sayfasından yapılandırın.")
                    else:
                        publisher = TweetPublisher(cookies)
                        result = publisher.publish_tweet(content)
                        if result:
                            st.success("İçerik başarıyla paylaşıldı!")
                        else:
                            st.error("Paylaşım başarısız oldu.")
                except Exception as e:
                    st.error(f"Paylaşım hatası: {e}")
