"""
İçerik Üretici Sayfası
AI ile konu keşfet, uzun içerik üret, thread oluştur
"""
import streamlit as st
import datetime
from urllib.parse import quote as url_quote
from modules.ui_components import (inject_custom_css, check_password,
                                   get_secret, render_sidebar_nav,
                                   render_research_engine_toggle, render_agentic_mode_toggle)
from modules.content_generator import ContentGenerator, get_available_formats, score_tweet, CONTENT_FORMATS
from modules.deep_research import discover_topics, research_topic_from_text
from modules.style_manager import load_user_samples, load_custom_persona, add_draft
from modules.tweet_analyzer import load_all_analyses, build_training_context
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
<div class="page-header">
    <span class="page-icon">💡</span>
    <h1>İçerik Üretici</h1>
    <p>Konu keşfet, araştır, uzun içerik üret</p>
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
        from modules.twitter_scanner import TwitterScanner

        bearer_token = get_secret("twitter_bearer_token", "")
        twikit_username = get_secret("twikit_username", "")
        twikit_password = get_secret("twikit_password", "")
        twikit_email = get_secret("twikit_email", "")

        if not bearer_token and not twikit_username:
            return None

        scanner = TwitterScanner(
            bearer_token=bearer_token,
            twikit_username=twikit_username,
            twikit_password=twikit_password,
            twikit_email=twikit_email,
        )
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
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">🔍 Konu Keşfet</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
            AI, X'te trend konuları ve güncel haberleri tarayıp sana içerik önerileri sunar
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        focus_area = st.text_input(
            "Odak Alanı (opsiyonel)",
            value="",
            placeholder="Boş bırakırsan genel AI/teknoloji gelişmeleri bulunur",
            key="topic_focus"
        )
    with col2:
        st.write("")
        st.write("")
        discover_btn = st.button("🔍 Konuları Keşfet", type="primary", use_container_width=True)

    # Grok engine toggle for topic discovery
    discover_engine = render_research_engine_toggle(key_suffix="icerik_discover")

    if discover_btn:
        scanner = get_scanner()
        progress = st.empty()
        spinner_label = "🧠 Grok ile konular araştırılıyor..." if discover_engine == "grok" else "Konular araştırılıyor..."
        with st.spinner(spinner_label):
            topics = discover_topics(
                ai_client=ai_client,
                ai_model=ai_model,
                ai_provider=ai_provider,
                scanner=scanner,
                focus_area=focus_area,
                progress_callback=lambda msg: progress.info(msg),
                engine=discover_engine,
            )
        progress.empty()

        if topics:
            st.session_state["discovered_topics"] = topics
            st.success(f"{len(topics)} konu önerisi bulundu!")
        else:
            st.warning("Konu önerisi bulunamadı. Tekrar deneyin veya farklı bir odak alanı yazın.")

    # Display discovered topics
    if "discovered_topics" in st.session_state and st.session_state["discovered_topics"]:
        st.markdown("### 📋 Önerilen Konular")

        for i, topic_item in enumerate(st.session_state["discovered_topics"]):
            title = topic_item.get("title", f"Konu {i+1}")
            desc = topic_item.get("description", "")
            angle = topic_item.get("angle", "")
            potential = topic_item.get("potential", "")

            with st.expander(f"**{i+1}. {title}**", expanded=(i < 3)):
                st.write(desc)
                if angle:
                    st.markdown(f"**Açı:** {angle}")
                if potential:
                    st.markdown(f"**Potansiyel:** {potential}")

                if st.button(f"Bu konuyu seç", key=f"pick_topic_{i}"):
                    st.session_state["selected_topic_idx"] = i
                    st.rerun()

    # --- Selected topic: show generation options ---
    if "selected_topic_idx" in st.session_state and "discovered_topics" in st.session_state:
        sel_idx = st.session_state["selected_topic_idx"]
        sel_topic = st.session_state["discovered_topics"][sel_idx]
        sel_title = sel_topic.get("title", "")
        sel_desc = sel_topic.get("description", "")
        sel_angle = sel_topic.get("angle", "")

        st.markdown("---")
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.25); border-radius:12px;
                    padding:16px; margin-bottom:16px;">
            <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">
                ✍️ Seçilen Konu: {sel_title}
            </div>
            <div style="color:#94a3b8; font-size:13px; margin-top:4px;">{sel_desc}</div>
        </div>
        """, unsafe_allow_html=True)

        # Style & length selection
        d_col_style, d_col_len = st.columns(2)
        with d_col_style:
            d_style_options = {
                "deneyim": "🗣️ Kişisel Deneyim",
                "egitici": "📚 Eğitici / Tutorial",
                "karsilastirma": "⚖️ Karşılaştırma",
                "analiz": "📊 Analiz",
                "hikaye": "📖 Hikaye Anlatımı",
            }
            d_default_style_idx = 0
            if sel_angle:
                al = sel_angle.lower()
                if "deneyim" in al or "kişisel" in al:
                    d_default_style_idx = 0
                elif "eğitici" in al or "tutorial" in al or "nasıl" in al:
                    d_default_style_idx = 1
                elif "karşılaştır" in al:
                    d_default_style_idx = 2
                elif "analiz" in al:
                    d_default_style_idx = 3
                elif "hikaye" in al:
                    d_default_style_idx = 4
            d_style = st.selectbox(
                "İçerik Tarzı",
                options=list(d_style_options.keys()),
                format_func=lambda x: d_style_options[x],
                index=d_default_style_idx,
                key="discover_style",
            )
        with d_col_len:
            _d_fmt_options = get_available_formats("long_content")
            _d_fmt_labels = {k: f"{v['icon']} {v['name']}" for k, v in _d_fmt_options.items()}
            d_length = st.selectbox(
                "Format",
                options=list(_d_fmt_labels.keys()),
                format_func=lambda x: _d_fmt_labels[x],
                index=1,
                key="discover_length",
            )

        d_extra = st.text_area(
            "Ek Talimatlar (opsiyonel)",
            value=sel_desc,
            height=60,
            key="discover_extra",
        )

        # Research mode
        d_col_rm, d_col_engine = st.columns(2)
        with d_col_rm:
            d_research_mode_options = {
                "x_and_web": "🌐 X + Web (Önerilen)",
                "x_only": "🐦 Sadece X",
                "x_deep": "🔬 Derin X (50-100 tweet)",
            }
            d_research_mode = st.selectbox(
                "Araştırma Modu",
                options=list(d_research_mode_options.keys()),
                format_func=lambda x: d_research_mode_options[x],
                index=0,
                key="discover_research_mode",
            )
        with d_col_engine:
            st.write("")
            st.write("")
            d_engine = render_research_engine_toggle(key_suffix="discover_gen")

        # Agentic research mode
        d_agentic_mode = render_agentic_mode_toggle(key_suffix="discover_content")
        d_use_agentic = (d_agentic_mode == "standard")
        d_use_grok_agentic = (d_agentic_mode == "grok")

        col_gen, col_cancel = st.columns([3, 1])
        with col_gen:
            d_generate_btn = st.button("✨ Araştır & İçerik Üret", type="primary",
                                       use_container_width=True, key="discover_gen_btn")
        with col_cancel:
            if st.button("✕ İptal", key="cancel_topic", use_container_width=True):
                st.session_state.pop("selected_topic_idx", None)
                st.rerun()

        if d_generate_btn:
            d_research_context = ""
            # Step 1: Research
            d_progress = st.empty()
            with st.spinner("Konu araştırılıyor..."):
                try:
                    scanner = get_scanner()
                    d_research_result = research_topic_from_text(
                        topic_input=sel_title,
                        scanner=scanner,
                        time_hours=24,
                        search_mode=d_research_mode,
                        progress_callback=lambda msg: d_progress.info(msg),
                        ai_client=ai_client,
                        ai_model=ai_model,
                        ai_provider=ai_provider,
                        use_agentic=d_use_agentic,
                        engine=d_engine,
                        use_grok_agentic=d_use_grok_agentic,
                    )
                    d_progress.empty()
                    if d_research_result and d_research_result.summary:
                        d_research_context = d_research_result.summary
                        stats_parts = []
                        if d_research_result.x_tweets:
                            stats_parts.append(f"🐦 {len(d_research_result.x_tweets)} tweet")
                        if d_research_result.web_results:
                            stats_parts.append(f"🌐 {len(d_research_result.web_results)} web sonucu")
                        if d_research_result.news_results:
                            stats_parts.append(f"📰 {len(d_research_result.news_results)} haber")
                        if d_research_result.deep_articles:
                            stats_parts.append(f"📄 {len(d_research_result.deep_articles)} makale")
                        if getattr(d_research_result, 'agentic_summary', None):
                            stats_parts.append("🤖 AI araştırma")
                        st.success(f"Araştırma tamamlandı! ({' | '.join(stats_parts)})")
                        with st.expander("📄 Araştırma Verileri", expanded=False):
                            st.text(d_research_context[:5000])
                    else:
                        d_progress.empty()
                except Exception as e:
                    d_progress.empty()
                    st.warning(f"Araştırma hatası (devam ediliyor): {e}")

            # Step 2: Generate
            with st.spinner("İçerik üretiliyor..."):
                try:
                    user_samples = load_user_samples()
                    custom_persona = load_custom_persona()
                    _analyses = load_all_analyses(session_state=st.session_state)
                    _training_context = build_training_context(_analyses) if _analyses else ""
                    generator = ContentGenerator(
                        provider=ai_provider,
                        api_key=ai_api_key,
                        model=ai_model,
                        custom_persona=custom_persona if custom_persona else None,
                        training_context=_training_context if _training_context else None,
                    )
                    content = generator.generate_long_content(
                        topic=sel_title,
                        research_context=d_research_context,
                        style=d_style,
                        length=d_length,
                        additional_instructions=d_extra,
                        user_samples=user_samples if user_samples else None,
                    )
                    st.session_state["discover_generated_content"] = content
                    st.session_state["discover_generated_topic"] = sel_title
                except Exception as e:
                    st.error(f"İçerik üretim hatası: {e}")

        # Display generated content from discovery flow
        if "discover_generated_content" in st.session_state and st.session_state["discover_generated_content"]:
            d_content = st.session_state["discover_generated_content"]

            st.markdown("---")
            st.markdown("### 📝 Üretilen İçerik")

            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.8); border:1px solid rgba(99,102,241,0.15); border-radius:16px;
                        padding:20px; margin:12px 0; font-size:15px; line-height:1.7;
                        color:#e2e8f0; white-space:pre-wrap;">{d_content}</div>
            """, unsafe_allow_html=True)

            _d_sel_fmt = st.session_state.get("discover_length", "storm")
            _d_score = score_tweet(d_content, content_format=_d_sel_fmt)
            _d_fmt_name = CONTENT_FORMATS.get(_d_sel_fmt, {}).get("name", _d_sel_fmt)
            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.08);
                        border-radius:10px; padding:10px 14px; margin:6px 0;">
                <span style="font-size:18px; font-weight:bold; color:#f1f5f9;">
                    {_d_score['quality_emoji']} {_d_score['overall']}/100
                </span>
                <span style="color:#94a3b8; font-size:12px; margin-left:8px;">
                    {_d_score['quality_label']} &nbsp;|&nbsp; 📐 {_d_fmt_name} &nbsp;|&nbsp; {_d_score['char_count']} karakter
                </span>
            </div>
            """, unsafe_allow_html=True)

            d_col_a, d_col_b, d_col_c, d_col_d = st.columns(4)
            with d_col_a:
                d_intent_url = f"https://x.com/intent/tweet?text={url_quote(d_content)}"
                st.link_button("📱 X'te Aç", d_intent_url, use_container_width=True)
                st.caption("Görsel ekleyebilirsin")
            with d_col_b:
                if st.button("📋 Kopyala", key="d_copy_content", use_container_width=True):
                    st.code(d_content, language=None)
                    st.success("Yukarıdan kopyalayabilirsiniz!")
            with d_col_c:
                if st.button("💾 Taslağa Kaydet", key="d_save_draft", use_container_width=True):
                    try:
                        add_draft(d_content, label=st.session_state.get("discover_generated_topic", "İçerik"))
                        st.success("Taslak kaydedildi!")
                    except Exception as e:
                        st.error(f"Taslak kaydetme hatası: {e}")
            with d_col_d:
                if st.button("🔄 Yeniden Üret", key="d_regen_content", use_container_width=True):
                    st.session_state.pop("discover_generated_content", None)
                    st.rerun()


# ============================================================
# TAB 2: Content Generation
# ============================================================
with tab2:
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.15); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">✍️ Uzun İçerik Üret</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
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
        _fmt_options = get_available_formats("long_content")
        _fmt_labels = {k: f"{v['icon']} {v['name']}" for k, v in _fmt_options.items()}
        length = st.selectbox(
            "Format",
            options=list(_fmt_labels.keys()),
            format_func=lambda x: _fmt_labels[x],
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
        col_rm, col_engine = st.columns(2)
        with col_rm:
            research_mode = st.selectbox(
                "Araştırma Modu",
                options=list(research_mode_options.keys()),
                format_func=lambda x: research_mode_options[x],
                index=0,
                key="research_mode",
            )
        with col_engine:
            st.write("")
            st.write("")
            content_engine = render_research_engine_toggle(key_suffix="content_gen")

        content_agentic_mode = render_agentic_mode_toggle(key_suffix="content_gen")
        use_agentic = (content_agentic_mode == "standard")
        content_use_grok_agentic = (content_agentic_mode == "grok")

    generate_btn = st.button("✨ İçerik Üret", type="primary", use_container_width=True, key="gen_content_btn")

    # Ensure variables exist even when research is disabled
    if not do_research:
        content_engine = "standard"
        content_use_grok_agentic = False

    if generate_btn and topic:
        research_context = ""

        # Step 1: Research if requested
        if do_research:
            progress = st.empty()
            spinner_label = "🧠 Grok ile konu araştırılıyor..." if content_engine == "grok" else "Konu araştırılıyor..."
            with st.spinner(spinner_label):
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
                        engine=content_engine,
                        use_grok_agentic=content_use_grok_agentic,
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
                custom_persona = load_custom_persona()
                _analyses = load_all_analyses(session_state=st.session_state)
                _training_context = build_training_context(_analyses) if _analyses else ""
                generator = ContentGenerator(
                    provider=ai_provider,
                    api_key=ai_api_key,
                    model=ai_model,
                    custom_persona=custom_persona if custom_persona else None,
                    training_context=_training_context if _training_context else None,
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
        <div style="background:rgba(15,20,35,0.8); border:1px solid rgba(99,102,241,0.15); border-radius:16px;
                    padding:20px; margin:12px 0; font-size:15px; line-height:1.7;
                    color:#e2e8f0; white-space:pre-wrap;">{content}</div>
        """, unsafe_allow_html=True)

        _c_sel_fmt = st.session_state.get("content_length", "storm")
        _c_score = score_tweet(content, content_format=_c_sel_fmt)
        _c_fmt_name = CONTENT_FORMATS.get(_c_sel_fmt, {}).get("name", _c_sel_fmt)
        st.markdown(f"""
        <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.08);
                    border-radius:10px; padding:10px 14px; margin:6px 0;">
            <span style="font-size:18px; font-weight:bold; color:#f1f5f9;">
                {_c_score['quality_emoji']} {_c_score['overall']}/100
            </span>
            <span style="color:#94a3b8; font-size:12px; margin-left:8px;">
                {_c_score['quality_label']} &nbsp;|&nbsp; 📐 {_c_fmt_name} &nbsp;|&nbsp; {_c_score['char_count']} karakter
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Actions
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            intent_url = f"https://x.com/intent/tweet?text={url_quote(content)}"
            st.link_button("📱 X'te Aç", intent_url, use_container_width=True)
            st.caption("Görsel ekleyebilirsin")

        with col_b:
            if st.button("📋 Kopyala", key="copy_content", use_container_width=True):
                st.code(content, language=None)
                st.success("Yukarıdan kopyalayabilirsiniz!")

        with col_c:
            if st.button("💾 Taslağa Kaydet", key="save_draft", use_container_width=True):
                try:
                    add_draft(content, label=st.session_state.get("generated_content_topic", "İçerik"))
                    st.success("Taslak kaydedildi!")
                except Exception as e:
                    st.error(f"Taslak kaydetme hatası: {e}")

        with col_d:
            if st.button("🔄 Yeniden Üret", key="regen_content", use_container_width=True):
                # Clear and re-trigger
                st.session_state.pop("generated_content", None)
                st.rerun()
