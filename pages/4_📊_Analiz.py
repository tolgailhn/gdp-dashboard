"""
Tweet Analiz Sayfasi
Herhangi bir hesabin son tweet'lerini cekip engagement analizi yapar.
Analiz sonuclari tweet yaziminda AI egitim verisi olarak kullanilir.

Streamlit Cloud uyumlulugu:
- Veriler hem dosya sistemine hem session_state'e kaydedilir
- Export/Import ile analiz verileri indirilebilir ve geri yuklenebilir
"""
import json
import streamlit as st
import openai as _openai
import anthropic as _anthropic
from modules.ui_components import inject_custom_css, check_password, get_secret, render_sidebar_nav
from modules.twikit_client import TwikitSearchClient
from modules.tweet_analyzer import (
    pull_user_tweets, analyze_tweets, generate_ai_analysis,
    save_tweet_analysis, load_all_analyses,
    delete_tweet_analysis, build_training_context,
    export_all_analyses, import_analyses_from_json
)

# Page config
st.set_page_config(
    page_title="Tweet Analiz | X AI Otomasyon",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_custom_css()

if not check_password():
    st.stop()

render_sidebar_nav(current_page="analiz")

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>📊 Tweet Analizi</h1>
    <p style="color:#8899a6;">Hesaplarin tweet'lerini cek, engagement analizi yap, AI'i egit</p>
</div>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🔍 Yeni Analiz", "📁 Kayitli Analizler", "💾 Disa/Iceri Aktar"])

# ===================
# TAB 1: New Analysis
# ===================
with tab1:
    st.markdown("""
    <div style="background:#16213e; border:1px solid #1DA1F2; border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">Nasil Calisiyor?</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            1. Hesap adi gir (birden fazla olabilir)<br>
            2. Twikit ile son tweet'leri ceker<br>
            3. Engagement analizi yapar (hangi tweet'ler ne kadar etkilesim almis)<br>
            4. AI analiz raporu uretir<br>
            5. Sonuclari kaydeder → Tweet yazarken AI bu verileri kullanir<br>
            <br>
            <strong>💡 Streamlit Cloud:</strong> Analiz sonuclarini "Disa Aktar" sekmesinden indirin.
            Bir sonraki oturumda "Iceri Aktar" ile geri yukleyin.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Check Twikit availability
    twikit_user = get_secret("twikit_username", "")
    twikit_pass = get_secret("twikit_password", "")
    twikit_email = get_secret("twikit_email", "")

    if not twikit_user or not twikit_pass:
        st.error("Twikit yapilandirilmamis! Ayarlar sayfasindan Twikit kullanici adi ve sifre ekleyin.")
        st.stop()

    # Username input
    st.markdown("### Analiz Edilecek Hesaplar")

    usernames_input = st.text_input(
        "Twitter kullanici adi(lari)",
        placeholder="ornek: elonmusk, sama, AnthropicAI (virgul ile ayirin)",
        key="analysis_usernames"
    )

    col1, col2 = st.columns(2)
    with col1:
        tweet_count = st.slider("Cekilecek tweet sayisi", 50, 500, 200, step=50, key="tweet_count")
    with col2:
        generate_ai_report = st.checkbox("AI analiz raporu uret", value=True, key="ai_report")

    # Analyze button
    analyze_clicked = st.button(
        "📊 Analiz Baslat",
        type="primary",
        use_container_width=True,
        disabled=not usernames_input.strip()
    )

    if analyze_clicked:
        usernames = [u.strip().lstrip("@") for u in usernames_input.split(",") if u.strip()]

        if not usernames:
            st.warning("En az bir kullanici adi girin!")
            st.stop()

        # Initialize Twikit
        with st.spinner("Twikit ile giris yapiliyor..."):
            twikit = TwikitSearchClient(twikit_user, twikit_pass, twikit_email)
            if not twikit.authenticate():
                st.error("Twikit giris basarisiz! Ayarlar sayfasindan kontrol edin.")
                st.stop()

        # Build AI client for report generation
        _ai_client = None
        _ai_model = None
        _ai_provider = "minimax"

        if generate_ai_report:
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

        # Process each username
        for username in usernames:
            st.markdown("---")
            st.markdown(f"## @{username}")

            progress = st.empty()
            status = st.empty()

            try:
                # Pull tweets
                tweets = pull_user_tweets(
                    twikit, username, count=tweet_count,
                    progress_callback=lambda msg: progress.caption(msg)
                )

                if not tweets:
                    status.warning(f"@{username} icin tweet bulunamadi. Hesap adi dogru mu?")
                    continue

                progress.caption(f"@{username}: {len(tweets)} tweet cekildi. Analiz yapiliyor...")

                # Analyze
                analysis = analyze_tweets(tweets)

                # Generate AI report
                ai_report = ""
                if generate_ai_report and _ai_client:
                    progress.caption(f"@{username}: AI analiz raporu uretiliyor...")
                    ai_report = generate_ai_analysis(
                        analysis, _ai_client, _ai_model, _ai_provider, username
                    )

                # Save to BOTH file and session_state
                save_tweet_analysis(username, analysis, ai_report,
                                    session_state=st.session_state)
                progress.empty()
                status.success(f"@{username} analizi tamamlandi ve kaydedildi!")

                # Display results
                _display_analysis(username, analysis, ai_report)

            except Exception as e:
                progress.empty()
                status.error(f"@{username} analiz hatasi: {e}")


# ===================
# TAB 2: Saved Analyses
# ===================
with tab2:
    st.markdown("### Kayitli Analizler")
    st.markdown("Bu analizler tweet yazarken AI egitim verisi olarak otomatik kullanilir.")

    analyses = load_all_analyses(session_state=st.session_state)

    if not analyses:
        st.info("Henuz kayitli analiz yok. 'Yeni Analiz' sekmesinden analiz yapin "
                "veya 'Disa/Iceri Aktar' sekmesinden onceki analiz dosyanizi yukleyin.")
    else:
        # Training data preview
        training_context = build_training_context(analyses)
        if training_context:
            with st.expander("🧠 AI Egitim Verisi Onizleme (Tweet yazarken kullanilan)"):
                st.markdown(f"""
                <div style="background:#1a1a2e; border:1px solid #2a2a4a;
                            border-radius:8px; padding:14px; font-size:12px;
                            color:#8899a6; max-height:400px; overflow-y:auto;">
                    <pre style="white-space:pre-wrap;">{training_context[:3000]}...</pre>
                </div>
                """, unsafe_allow_html=True)

        for saved in analyses:
            username = saved.get("username", "?")
            analyzed_at = saved.get("analyzed_at", "?")[:16]
            analysis = saved.get("analysis", {})
            ai_report = saved.get("ai_report", "")
            total = analysis.get("total_tweets", 0)

            with st.expander(f"@{username} — {total} tweet — {analyzed_at}"):
                _display_analysis(username, analysis, ai_report)

                if st.button(f"🗑️ @{username} Analizini Sil", key=f"del_analysis_{username}"):
                    delete_tweet_analysis(username, session_state=st.session_state)
                    st.success(f"@{username} analizi silindi!")
                    st.rerun()


# ===================
# TAB 3: Export / Import
# ===================
with tab3:
    st.markdown("### Disa / Iceri Aktar")

    st.markdown("""
    <div style="background:#16213e; border:1px solid #1DA1F2; border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">Neden Gerekli?</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            Streamlit Cloud'da dosya sistemi gecicidir — uygulama yeniden basladiginda
            analiz verileri kaybolur.<br><br>
            <strong>Cozum:</strong><br>
            1. Analiz yaptiktan sonra "Tumunu Indir" ile JSON dosyasini bilgisayariniza kaydedin<br>
            2. Bir sonraki oturumda "Dosya Yukle" ile geri yukleyin<br>
            3. Veya JSON dosyasini repo'nuzdaki <code>data/tweet_analyses/</code> klasorune commit edin<br>
            &nbsp;&nbsp;&nbsp;(Bu sekilde her deploy'da otomatik yuklenir)
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_exp, col_imp = st.columns(2)

    with col_exp:
        st.markdown("#### 📤 Disa Aktar (Indir)")

        current_analyses = load_all_analyses(session_state=st.session_state)
        if current_analyses:
            usernames = [a.get("username", "?") for a in current_analyses]
            st.info(f"{len(current_analyses)} analiz mevcut: {', '.join(['@' + u for u in usernames])}")

            export_json = export_all_analyses(session_state=st.session_state)

            st.download_button(
                label="📥 Tumunu Indir (JSON)",
                data=export_json,
                file_name="tweet_analyses_export.json",
                mime="application/json",
                use_container_width=True,
                type="primary"
            )
        else:
            st.warning("Indirilecek analiz yok. Once 'Yeni Analiz' yapin.")

    with col_imp:
        st.markdown("#### 📥 Iceri Aktar (Yukle)")

        uploaded_file = st.file_uploader(
            "Onceki analiz dosyasini yukleyin",
            type=["json"],
            key="import_analyses_file"
        )

        if uploaded_file:
            try:
                json_str = uploaded_file.read().decode("utf-8")

                # Preview
                preview_data = json.loads(json_str)
                preview_analyses = preview_data.get("analyses", {})
                if preview_analyses:
                    st.info(f"Dosyada {len(preview_analyses)} analiz var: "
                            f"{', '.join(['@' + k for k in preview_analyses.keys()])}")

                    if st.button("✅ Iceri Aktar", type="primary", use_container_width=True):
                        count = import_analyses_from_json(json_str,
                                                          session_state=st.session_state)
                        st.success(f"{count} analiz basariyla yuklendi! "
                                   f"Artik tweet yazarken otomatik kullanilacak.")
                        st.rerun()
                else:
                    st.error("Gecersiz dosya formati. 'Tumunu Indir' ile alinan dosyayi kullanin.")
            except Exception as e:
                st.error(f"Dosya okuma hatasi: {e}")


def _display_analysis(username: str, analysis: dict, ai_report: str = ""):
    """Display analysis results in a structured format."""

    # Overall stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam Tweet", analysis.get("total_tweets", 0))
    with col2:
        st.metric("Toplam Like", f"{analysis.get('total_likes', 0):,}")
    with col3:
        st.metric("Toplam RT", f"{analysis.get('total_retweets', 0):,}")
    with col4:
        st.metric("Ort. Skor", f"{analysis.get('avg_engagement_score', 0):,.0f}")

    # Top performing tweets
    top_tweets = analysis.get("top_tweets", [])
    if top_tweets:
        st.markdown("#### En Iyi Performans Gosteren Tweet'ler")
        for i, t in enumerate(top_tweets[:10], 1):
            score = t.get("engagement_score", 0)
            likes = t.get("like_count", 0)
            rts = t.get("retweet_count", 0)
            replies = t.get("reply_count", 0)
            text = t.get("text", "")[:300]

            if i <= 3:
                border_color = "#1DA1F2"
            elif i <= 7:
                border_color = "#2a2a4a"
            else:
                border_color = "#1a1a2e"

            st.markdown(f"""
            <div style="background:#1a1a2e; border-left:3px solid {border_color};
                        padding:10px 14px; margin:6px 0; border-radius:4px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#1DA1F2; font-weight:bold; font-size:13px;">#{i}</span>
                    <span style="color:#8899a6; font-size:12px;">
                        Skor: {score:,.0f} | ❤️ {likes:,} | 🔁 {rts:,} | 💬 {replies:,}
                    </span>
                </div>
                <div style="color:#f0f0f0; font-size:13px; line-height:1.5;">{text}</div>
            </div>
            """, unsafe_allow_html=True)

    # Length analysis
    length_data = analysis.get("length_analysis", {})
    if length_data:
        st.markdown("#### Uzunluk Analizi")
        len_col1, len_col2, len_col3 = st.columns(3)
        with len_col1:
            short = length_data.get("short", {})
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f0f0f0; font-weight:bold;">Kisa (≤280)</div>
                <div style="color:#1DA1F2; font-size:20px; font-weight:bold;">{short.get('count', 0)} tweet</div>
                <div style="color:#8899a6; font-size:12px;">Ort. Skor: {short.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with len_col2:
            medium = length_data.get("medium", {})
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f0f0f0; font-weight:bold;">Orta (281-500)</div>
                <div style="color:#1DA1F2; font-size:20px; font-weight:bold;">{medium.get('count', 0)} tweet</div>
                <div style="color:#8899a6; font-size:12px;">Ort. Skor: {medium.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with len_col3:
            long_d = length_data.get("long", {})
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f0f0f0; font-weight:bold;">Uzun (>500)</div>
                <div style="color:#1DA1F2; font-size:20px; font-weight:bold;">{long_d.get('count', 0)} tweet</div>
                <div style="color:#8899a6; font-size:12px;">Ort. Skor: {long_d.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # Question analysis
    q_data = analysis.get("question_analysis", {})
    if q_data:
        st.markdown("#### Soru vs Beyan")
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            q = q_data.get("question_tweets", {})
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f0f0f0; font-weight:bold;">❓ Soru Iceren</div>
                <div style="color:#1DA1F2; font-size:20px; font-weight:bold;">{q.get('count', 0)} tweet</div>
                <div style="color:#8899a6; font-size:12px;">Ort. Skor: {q.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with q_col2:
            s = q_data.get("statement_tweets", {})
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f0f0f0; font-weight:bold;">📝 Beyan</div>
                <div style="color:#1DA1F2; font-size:20px; font-weight:bold;">{s.get('count', 0)} tweet</div>
                <div style="color:#8899a6; font-size:12px;">Ort. Skor: {s.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # Top keywords
    top_kw = analysis.get("top_keywords", [])
    if top_kw:
        st.markdown("#### Etkilesim Ceken Kelimeler")
        kw_text = ""
        for kw in top_kw[:20]:
            kw_text += f"""<span style="display:inline-block; background:#16213e; border:1px solid #1DA1F2;
                            border-radius:16px; padding:4px 12px; margin:3px; font-size:12px; color:#f0f0f0;">
                            {kw['keyword']} <span style="color:#1DA1F2;">{kw['avg_score']:,.0f}</span>
                          </span>"""
        st.markdown(f'<div style="margin:8px 0;">{kw_text}</div>', unsafe_allow_html=True)

    # Top hashtags
    top_tags = analysis.get("top_hashtags", [])
    if top_tags:
        st.markdown("#### En Iyi Hashtag'ler")
        tag_text = ""
        for tag in top_tags[:10]:
            tag_text += f"""<span style="display:inline-block; background:#16213e; border:1px solid #2a2a4a;
                            border-radius:16px; padding:4px 12px; margin:3px; font-size:12px; color:#1DA1F2;">
                            {tag['tag']} ({tag['count']}x, skor:{tag['avg_score']:,.0f})
                          </span>"""
        st.markdown(f'<div style="margin:8px 0;">{tag_text}</div>', unsafe_allow_html=True)

    # Best hours
    best_hours = analysis.get("best_hours", [])
    if best_hours:
        st.markdown("#### En Iyi Saat Dilimleri")
        hours_text = " | ".join([f"🕐 {h['hour']:02d}:00 (skor: {h['avg_score']:,.0f}, {h['tweet_count']} tweet)"
                                  for h in best_hours[:5]])
        st.markdown(f"<div style='color:#8899a6; font-size:13px;'>{hours_text}</div>", unsafe_allow_html=True)

    # AI Report
    if ai_report:
        st.markdown("#### 🧠 AI Analiz Raporu")
        st.markdown(f"""
        <div style="background:#1a1a2e; border:1px solid #2a2a4a;
                    border-radius:8px; padding:14px; margin:8px 0;
                    font-size:13px; color:#f0f0f0; line-height:1.6;
                    max-height:500px; overflow-y:auto;">
            {ai_report}
        </div>
        """, unsafe_allow_html=True)
