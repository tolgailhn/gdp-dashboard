"""
Analiz & Takipci Sayfasi
- Tweet analizi: hesaplarin tweet'lerini cekip engagement analizi yapar
- Takipci kesfi: benzer hesaplarin onayli takipcilerini bul
- Tweet havuzu: coklu hesaptan tweet biriktir

Streamlit Cloud uyumlulugu:
- Veriler hem dosya sistemine hem session_state'e kaydedilir
- Export/Import ile veriler indirilebilir ve geri yuklenebilir
"""
import json
import datetime
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
from modules.tweet_pool import (
    load_pool, load_pool_accounts, save_pool_accounts,
    get_pool_stats, bulk_fetch_accounts, import_from_analyses,
    regenerate_pool_dna, get_pool_dna,
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
<div class="page-header">
    <span class="page-icon">📊</span>
    <h1>Analiz & Keşif</h1>
    <p>Tweet analizi, takipçi keşfi, tweet havuzu — hepsi tek yerde</p>
</div>
""", unsafe_allow_html=True)


# --- Follower helper functions ---
def _save_followers(username: str, followers: list[dict]):
    """Save to both session_state and file."""
    data = {
        "username": username,
        "fetched_at": datetime.datetime.now().isoformat(),
        "followers": followers,
    }
    if "follower_suggestions" not in st.session_state:
        st.session_state["follower_suggestions"] = {}
    st.session_state["follower_suggestions"][username.lower()] = data
    try:
        from modules.style_manager import save_follower_suggestions
        save_follower_suggestions(username, followers)
    except Exception:
        pass


def _load_all_followers() -> dict:
    """Load from session_state first, then files."""
    result = {}
    try:
        from modules.style_manager import load_all_follower_suggestions
        result = load_all_follower_suggestions()
    except Exception:
        pass
    ss = st.session_state.get("follower_suggestions", {})
    result.update(ss)
    if result:
        st.session_state["follower_suggestions"] = result
    return result


def _delete_followers(username: str):
    """Delete from both session_state and file."""
    ss = st.session_state.get("follower_suggestions", {})
    if username.lower() in ss:
        del ss[username.lower()]
    try:
        from modules.style_manager import delete_follower_suggestions
        delete_follower_suggestions(username)
    except Exception:
        pass


def _export_followers_json() -> str:
    """Export all follower data as JSON."""
    data = _load_all_followers()
    return json.dumps({
        "type": "follower_suggestions_export",
        "exported_at": datetime.datetime.now().isoformat(),
        "suggestions": data,
    }, ensure_ascii=False, indent=2)


def _import_followers_json(json_str: str) -> int:
    """Import follower data from JSON. Returns count."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return 0
    suggestions = data.get("suggestions", {})
    if not suggestions:
        return 0
    if "follower_suggestions" not in st.session_state:
        st.session_state["follower_suggestions"] = {}
    count = 0
    for key, value in suggestions.items():
        st.session_state["follower_suggestions"][key] = value
        try:
            from modules.style_manager import save_follower_suggestions
            save_follower_suggestions(value.get("username", key), value.get("followers", []))
        except Exception:
            pass
        count += 1
    return count


def _display_followers(followers: list[dict], source_username: str):
    """Display follower list with profile links."""
    verified_count = sum(1 for f in followers if f.get("is_blue_verified"))
    total_followers_of_followers = sum(f.get("followers_count", 0) for f in followers)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Toplam", len(followers))
    with col2:
        st.metric("Onayli", verified_count)
    with col3:
        avg_followers = total_followers_of_followers // max(len(followers), 1)
        st.metric("Ort. Takipci", f"{avg_followers:,}")

    sort_by = st.selectbox(
        "Sirala",
        options=["followers_count", "name"],
        format_func=lambda x: {"followers_count": "Takipci sayisina gore", "name": "Isme gore"}[x],
        key=f"sort_{source_username}"
    )

    sorted_followers = sorted(followers, key=lambda f: f.get(sort_by, 0),
                              reverse=(sort_by == "followers_count"))

    for i, f in enumerate(sorted_followers):
        name = f.get("name", "?")
        uname = f.get("username", "?")
        bio = f.get("bio", "")[:120]
        f_count = f.get("followers_count", 0)
        is_verified = f.get("is_blue_verified", False)
        profile_url = f"https://x.com/{uname}"
        verified_badge = ' <span style="color:#a5b4fc;">✓</span>' if is_verified else ""

        st.markdown(f"""
        <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px;
                    padding:10px 14px; margin:4px 0; display:flex; justify-content:space-between; align-items:center;">
            <div style="flex:1;">
                <div>
                    <span style="color:#f1f5f9; font-weight:bold; font-size:14px;">{name}</span>{verified_badge}
                    <span style="color:#94a3b8; font-size:13px;"> @{uname}</span>
                </div>
                <div style="color:#94a3b8; font-size:12px; margin-top:2px;">{bio}</div>
                <div style="color:#94a3b8; font-size:11px; margin-top:2px;">👥 {f_count:,} takipci</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            f"@{uname} Profilini Ac",
            profile_url,
            use_container_width=False,
            key=f"follow_{source_username}_{i}_{uname}"
        )

def _display_analysis(username: str, analysis: dict, ai_report: str = ""):
    """Display analysis results in a structured format."""

    # Overall stats
    orig_count = analysis.get("original_count", 0)
    rt_count = analysis.get("retweet_count", 0)
    has_breakdown = orig_count > 0 or rt_count > 0

    if has_breakdown:
        col1, col2, col3, col4, col5 = st.columns(5)
    else:
        col1, col2, col3, col4 = st.columns(4)
        col5 = None

    with col1:
        st.metric("Toplam Tweet", analysis.get("total_tweets", 0))
    with col2:
        st.metric("Toplam Like", f"{analysis.get('total_likes', 0):,}")
    with col3:
        st.metric("Toplam RT", f"{analysis.get('total_retweets', 0):,}")
    with col4:
        st.metric("Ort. Skor", f"{analysis.get('avg_engagement_score', 0):,.0f}")
    if col5:
        with col5:
            st.metric("Orijinal / RT", f"{orig_count} / {rt_count}")

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
                border_color = "#6366f1"
            elif i <= 7:
                border_color = "rgba(255,255,255,0.06)"
            else:
                border_color = "rgba(15,20,35,0.7)"

            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.7); border-left:3px solid {border_color};
                        padding:10px 14px; margin:6px 0; border-radius:4px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#a5b4fc; font-weight:bold; font-size:13px;">#{i}</span>
                    <span style="color:#94a3b8; font-size:12px;">
                        Skor: {score:,.0f} | ❤️ {likes:,} | 🔁 {rts:,} | 💬 {replies:,}
                    </span>
                </div>
                <div style="color:#f1f5f9; font-size:13px; line-height:1.5;">{text}</div>
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
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f1f5f9; font-weight:bold;">Kisa (≤280)</div>
                <div style="color:#a5b4fc; font-size:20px; font-weight:bold;">{short.get('count', 0)} tweet</div>
                <div style="color:#94a3b8; font-size:12px;">Ort. Skor: {short.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with len_col2:
            medium = length_data.get("medium", {})
            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f1f5f9; font-weight:bold;">Orta (281-500)</div>
                <div style="color:#a5b4fc; font-size:20px; font-weight:bold;">{medium.get('count', 0)} tweet</div>
                <div style="color:#94a3b8; font-size:12px;">Ort. Skor: {medium.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with len_col3:
            long_d = length_data.get("long", {})
            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f1f5f9; font-weight:bold;">Uzun (>500)</div>
                <div style="color:#a5b4fc; font-size:20px; font-weight:bold;">{long_d.get('count', 0)} tweet</div>
                <div style="color:#94a3b8; font-size:12px;">Ort. Skor: {long_d.get('avg_score', 0):,.0f}</div>
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
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f1f5f9; font-weight:bold;">❓ Soru Iceren</div>
                <div style="color:#a5b4fc; font-size:20px; font-weight:bold;">{q.get('count', 0)} tweet</div>
                <div style="color:#94a3b8; font-size:12px;">Ort. Skor: {q.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with q_col2:
            s = q_data.get("statement_tweets", {})
            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#f1f5f9; font-weight:bold;">📝 Beyan</div>
                <div style="color:#a5b4fc; font-size:20px; font-weight:bold;">{s.get('count', 0)} tweet</div>
                <div style="color:#94a3b8; font-size:12px;">Ort. Skor: {s.get('avg_score', 0):,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # Top keywords
    top_kw = analysis.get("top_keywords", [])
    if top_kw:
        st.markdown("#### Etkilesim Ceken Kelimeler")
        kw_text = ""
        for kw in top_kw[:20]:
            kw_text += f"""<span style="display:inline-block; background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2);
                            border-radius:16px; padding:4px 12px; margin:3px; font-size:12px; color:#f1f5f9;">
                            {kw['keyword']} <span style="color:#a5b4fc;">{kw['avg_score']:,.0f}</span>
                          </span>"""
        st.markdown(f'<div style="margin:8px 0;">{kw_text}</div>', unsafe_allow_html=True)

    # Top hashtags
    top_tags = analysis.get("top_hashtags", [])
    if top_tags:
        st.markdown("#### En Iyi Hashtag'ler")
        tag_text = ""
        for tag in top_tags[:10]:
            tag_text += f"""<span style="display:inline-block; background:rgba(99,102,241,0.08); border:1px solid rgba(255,255,255,0.06);
                            border-radius:16px; padding:4px 12px; margin:3px; font-size:12px; color:#a5b4fc;">
                            {tag['tag']} ({tag['count']}x, skor:{tag['avg_score']:,.0f})
                          </span>"""
        st.markdown(f'<div style="margin:8px 0;">{tag_text}</div>', unsafe_allow_html=True)

    # Best hours
    best_hours = analysis.get("best_hours", [])
    if best_hours:
        st.markdown("#### En Iyi Saat Dilimleri")
        hours_text = " | ".join([f"🕐 {h['hour']:02d}:00 (skor: {h['avg_score']:,.0f}, {h['tweet_count']} tweet)"
                                  for h in best_hours[:5]])
        st.markdown(f"<div style='color:#94a3b8; font-size:13px;'>{hours_text}</div>", unsafe_allow_html=True)

    # AI Report
    if ai_report:
        st.markdown("#### 🧠 AI Analiz Raporu")
        st.markdown(f"""
        <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                    border-radius:8px; padding:14px; margin:8px 0;
                    font-size:13px; color:#f1f5f9; line-height:1.6;
                    max-height:500px; overflow-y:auto;">
            {ai_report}
        </div>
        """, unsafe_allow_html=True)


# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Yeni Analiz",
    "📁 Kayitli Analizler",
    "👥 Takipci Kesfi",
    "🏊 Tweet Havuzu",
    "💾 Disa/Iceri Aktar",
])

# ===================
# TAB 1: New Analysis
# ===================
with tab1:
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">Nasil Calisiyor?</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
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

    _has_tw_cookies = bool(get_secret("twikit_auth_token", "")) and bool(get_secret("twikit_ct0", ""))
    if not twikit_user and not _has_tw_cookies:
        st.error("Twikit yapilandirilmamis! Ayarlar sayfasindan Twikit kullanici adi/sifre ekleyin veya cookie yapisturin.")
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
                err = twikit.last_error or "Bilinmeyen hata"
                st.error(f"Twikit giris basarisiz! {err}")
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
                    err_detail = twikit.last_error
                    if err_detail:
                        status.warning(f"@{username} icin tweet bulunamadi: {err_detail}")
                    else:
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
                <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                            border-radius:8px; padding:14px; font-size:12px;
                            color:#94a3b8; max-height:400px; overflow-y:auto;">
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
# TAB 3: Takipci Kesfi
# ===================
with tab3:
    st.markdown("### Onayli Takipci Kesfet")
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">Nasil Calisiyor?</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
            1. Senin nisindeki bir hesabin kullanici adini gir<br>
            2. O hesabin onayli (mavi tikli) takipcilerini cekeriz<br>
            3. Listeden profillerine tikla ve manuel takip et<br>
            4. Geri takip ederlerse onayli takipci sayin artar<br>
            <br>
            <strong>⚠️ Otomatik takip YOK</strong> — ban riski yuzunden. Sen tikla, sen takip et.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _tw_user = get_secret("twikit_username", "")
    _tw_pass = get_secret("twikit_password", "")
    _tw_email = get_secret("twikit_email", "")

    _has_tw_cookies2 = bool(get_secret("twikit_auth_token", "")) and bool(get_secret("twikit_ct0", ""))
    if not _tw_user and not _has_tw_cookies2:
        st.error("Twikit yapilandirilmamis! Ayarlar sayfasindan Twikit bilgileri ekleyin veya cookie yapisturin.")
    else:
        st.markdown("#### Hedef Hesap")

        target_username = st.text_input(
            "Twitter kullanici adi",
            placeholder="ornek: AnthropicAI veya sama (@ olmadan)",
            key="target_follower_username"
        )

        fcol1, fcol2 = st.columns(2)
        with fcol1:
            follower_limit = st.slider("Maks takipci sayisi", 50, 500, 200, step=50, key="follower_limit")
        with fcol2:
            verified_only = st.checkbox("Sadece onayli (mavi tikli)", value=True, key="verified_only")

        fetch_clicked = st.button(
            "👥 Takipci Cek",
            type="primary",
            use_container_width=True,
            disabled=not target_username.strip(),
            key="fetch_followers_btn"
        )

        if fetch_clicked:
            username = target_username.strip().lstrip("@")

            with st.spinner("Twikit ile giris yapiliyor..."):
                _twikit = TwikitSearchClient(_tw_user, _tw_pass, _tw_email)
                if not _twikit.authenticate():
                    err = _twikit.last_error or "Bilinmeyen hata"
                    st.error(f"Twikit giris basarisiz! {err}")
                    st.stop()

            progress = st.empty()
            progress.caption(f"@{username} bilgileri aliniyor...")

            user_info = _twikit.get_user_info(username)
            if not user_info:
                st.error(f"@{username} bulunamadi. Kullanici adi dogru mu?")
                st.stop()

            st.markdown(f"""
            <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                        padding:16px; margin:12px 0;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div>
                        <span style="color:#f1f5f9; font-weight:bold; font-size:16px;">{user_info['name']}</span>
                        <span style="color:#a5b4fc; font-size:14px;"> @{user_info['username']}</span>
                        {"<span style='color:#a5b4fc;'> ✓</span>" if user_info.get('is_blue_verified') else ""}
                    </div>
                </div>
                <div style="color:#94a3b8; font-size:13px; margin-top:6px;">{user_info.get('bio', '')[:200]}</div>
                <div style="color:#94a3b8; font-size:12px; margin-top:8px;">
                    👥 {user_info.get('followers_count', 0):,} takipci |
                    👤 {user_info.get('following_count', 0):,} takip |
                    📝 {user_info.get('tweet_count', 0):,} tweet
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner(f"@{username} takipcileri cekiliyor... Bu biraz zaman alabilir."):
                followers = _twikit.get_user_followers(
                    username, limit=follower_limit,
                    verified_only=verified_only,
                    progress_callback=lambda msg: progress.caption(msg)
                )

            progress.empty()

            if not followers:
                if verified_only:
                    st.warning(f"@{username} hesabinda onayli takipci bulunamadi. "
                              f"'Sadece onayli' secenegini kapatip tekrar deneyin.")
                else:
                    st.warning(f"@{username} takipcileri cekilemedi.")
            else:
                _save_followers(username, followers)
                st.success(f"{len(followers)} {'onayli ' if verified_only else ''}takipci bulundu ve kaydedildi!")
                _display_followers(followers, username)

    # --- Kayitli Takipci Listeleri ---
    st.markdown("---")
    st.markdown("#### Kayitli Takipci Listeleri")

    all_suggestions = _load_all_followers()

    if not all_suggestions:
        st.info("Henuz kayitli takipci listesi yok. Yukaridan bir hesap girerek baslayin.")
    else:
        for key, data in all_suggestions.items():
            f_username = data.get("username", key)
            fetched_at = data.get("fetched_at", "?")[:16]
            followers_list = data.get("followers", [])

            with st.expander(f"@{f_username} — {len(followers_list)} takipci ({fetched_at})"):
                _display_followers(followers_list, f_username)

                if st.button(f"🗑️ @{f_username} Listesini Sil", key=f"del_followers_{f_username}"):
                    _delete_followers(f_username)
                    st.success(f"@{f_username} listesi silindi!")
                    st.rerun()


# ===================
# TAB 4: Tweet Havuzu
# ===================
with tab4:
    st.markdown("### Tweet Havuzu Yönetimi")
    st.markdown("""
    Birden fazla hesaptan yüksek etkileşimli tweet'leri otomatik çekip biriktir.
    Bu havuz, tweet yazarken AI'a çeşitli örnekler sunar. Tweet'ler hiçbir zaman silinmez, sadece birikir.
    """)

    # --- Hesap Listesi ---
    st.markdown("#### Kaynak Hesaplar")
    st.markdown("Tweet'leri çekilecek hesapları virgülle ayırarak girin.")

    pool_accounts = load_pool_accounts()

    accounts_input = st.text_area(
        "Hesap listesi",
        value=", ".join(pool_accounts) if pool_accounts else "",
        placeholder="hrrcnes, elonmusk, hesap3, hesap4",
        height=80,
        key="pool_accounts_input",
        help="@ işareti olmadan, virgülle ayırarak yazın"
    )

    col_save, col_clear = st.columns(2)
    with col_save:
        if st.button("💾 Hesap Listesini Kaydet", use_container_width=True, type="primary",
                      key="pool_save_accounts"):
            if accounts_input.strip():
                new_accounts = [a.strip().lstrip("@").lower()
                               for a in accounts_input.split(",") if a.strip()]
                save_pool_accounts(new_accounts)
                st.success(f"{len(new_accounts)} hesap kaydedildi!")
                st.rerun()
            else:
                st.warning("En az bir hesap girin!")

    with col_clear:
        if st.button("🗑️ Listeyi Temizle", use_container_width=True, key="pool_clear_accounts"):
            save_pool_accounts([])
            st.success("Hesap listesi temizlendi!")
            st.rerun()

    st.markdown("---")

    # --- Engagement Eşiği ---
    st.markdown("#### Çekme Ayarları")
    col_eng, col_count = st.columns(2)
    with col_eng:
        pool_min_engagement = st.slider(
            "Min Engagement Skoru",
            min_value=0, max_value=1000, value=100, step=10,
            help="Bu skorun altındaki tweet'ler havuza eklenmez. RT=20x, Reply=13.5x, Like=1x",
            key="pool_min_engagement"
        )
    with col_count:
        pool_tweet_count = st.slider(
            "Hesap başına çekilecek tweet",
            min_value=50, max_value=1000, value=500, step=50,
            help="Her hesaptan kaç tweet çekilsin",
            key="pool_tweet_count"
        )

    # --- Çekme Butonu ---
    pool_accounts_current = load_pool_accounts()
    if pool_accounts_current:
        st.markdown(f"**{len(pool_accounts_current)} hesaptan tweet çekilecek:** "
                    f"{', '.join(f'@{a}' for a in pool_accounts_current)}")

        if st.button("🚀 Tweet'leri Çek ve Havuza Ekle", type="primary", use_container_width=True,
                      key="fetch_pool_tweets"):
            _pw_user = get_secret("twikit_username", "")
            _pw_pass = get_secret("twikit_password", "")
            _pw_email = get_secret("twikit_email", "")
            _pw_totp = get_secret("twikit_totp_secret", "")

            _has_pw_cookies = bool(get_secret("twikit_auth_token", "")) and bool(get_secret("twikit_ct0", ""))
            if not _pw_user and not _has_pw_cookies:
                st.error("Twikit kullanıcı bilgileri eksik! Ayarlar sayfasından Twikit bilgilerini girin veya cookie yapıştırın.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                def pool_progress_callback(msg):
                    status_text.markdown(f"⏳ {msg}")

                with st.spinner("Tweet'ler çekiliyor..."):
                    try:
                        tc = TwikitSearchClient(
                            _pw_user, _pw_pass, _pw_email,
                            totp_secret=_pw_totp
                        )

                        if not tc.authenticate():
                            err = tc.last_error or "Bilinmeyen hata"
                            st.error(f"Twikit giriş başarısız! {err}")
                        else:
                            results = bulk_fetch_accounts(
                                twikit_client=tc,
                                accounts=pool_accounts_current,
                                min_engagement=pool_min_engagement,
                                tweet_count=pool_tweet_count,
                                progress_callback=pool_progress_callback,
                            )

                            total_added = 0
                            for i, r in enumerate(results):
                                progress_bar.progress((i + 1) / len(results))
                                if r.get("error"):
                                    st.warning(f"@{r['username']}: Hata — {r['error']}")
                                else:
                                    total_added += r["added"]
                                    st.success(
                                        f"@{r['username']}: {r['fetched']} tweet çekildi, "
                                        f"**{r['added']} eklendi**, {r['skipped']} atlandı"
                                    )

                            status_text.empty()
                            st.markdown(f"### Toplam **{total_added}** yeni tweet havuza eklendi!")

                    except Exception as e:
                        st.error(f"Beklenmeyen hata: {e}")
    else:
        st.info("Önce yukarıdan hesap listesi ekleyin, sonra tweet'leri çekebilirsiniz.")

    st.markdown("---")

    # --- Analizlerden Havuza Aktar (tekrar çekmeden) ---
    st.markdown("#### Mevcut Analizlerden Havuza Aktar")

    all_analyses = load_all_analyses(st.session_state)
    if all_analyses:
        analysis_usernames = [a.get("username", "?") for a in all_analyses]
        analysis_tweet_counts = []
        for a in all_analyses:
            ana = a.get("analysis", {})
            orig_count = len(ana.get("all_original_tweets", []))
            if not orig_count:
                orig_count = len(ana.get("top_tweets", []))
            analysis_tweet_counts.append(orig_count)

        total_analysis_tweets = sum(analysis_tweet_counts)
        st.markdown(
            f"**{len(all_analyses)} analiz dosyasi mevcut** "
            f"({', '.join(f'@{u}({c})' for u, c in zip(analysis_usernames, analysis_tweet_counts))}) "
            f"— Toplam **{total_analysis_tweets:,}** tweet"
        )

        pool_import_min_eng = st.slider(
            "Min Engagement (aktarma icin)",
            min_value=0, max_value=1000, value=100, step=10,
            key="pool_import_min_engagement",
            help="Bu skorun altindaki tweet'ler havuza eklenmez"
        )

        if st.button("Analizlerden Havuza Aktar (tekrar cekmeden)", type="secondary",
                      use_container_width=True, key="import_analyses_to_pool"):
            with st.spinner("Analiz dosyalarindan havuza aktariliyor..."):
                import_status = st.empty()

                def import_progress(msg):
                    import_status.markdown(f"... {msg}")

                import_results = import_from_analyses(
                    min_engagement=pool_import_min_eng,
                    progress_callback=import_progress,
                )

                import_status.empty()
                total_imported = 0
                for r in import_results:
                    if r.get("error"):
                        st.warning(f"@{r['username']}: {r['error']}")
                    else:
                        total_imported += r["added"]
                        st.success(
                            f"@{r['username']}: {r['fetched']} tweet'ten "
                            f"**{r['added']} eklendi**, {r['skipped']} atlandi"
                        )

                st.markdown(f"### Toplam **{total_imported}** tweet havuza eklendi!")
                st.rerun()
    else:
        st.info("Henuz analiz dosyasi yok. Once 'Analiz' sekmesinden hesap analizi yapin.")

    st.markdown("---")

    # --- Havuz İstatistikleri ---
    st.markdown("#### Havuz Istatistikleri")
    pool_data = load_pool()
    stats = get_pool_stats(pool_data)

    if stats["total_tweets"] > 0:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("Toplam Tweet", f"{stats['total_tweets']:,}")
        with col_s2:
            st.metric("Hesap Sayısı", stats["accounts_count"])
        with col_s3:
            st.metric("Ort. Engagement", f"{stats['avg_engagement']:,.0f}")
        with col_s4:
            st.metric("Max Engagement", f"{stats['max_engagement']:,.0f}")

        if stats.get("authors"):
            st.markdown("**Hesap bazlı dağılım:**")
            for author, count in sorted(stats["authors"].items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"- @{author}: **{count}** tweet")

        if pool_data.get("last_updated"):
            st.caption(f"Son güncelleme: {pool_data['last_updated'][:19]}")

        # --- DNA Yenileme ---
        st.markdown("---")
        st.markdown("#### Havuz DNA'si")

        pool_dna = get_pool_dna()
        if pool_dna:
            dna_updated = pool_data.get("pool_dna_updated", "")
            st.caption(f"DNA son guncelleme: {dna_updated[:19] if dna_updated else 'Bilinmiyor'}")

            dna_col1, dna_col2, dna_col3 = st.columns(3)
            with dna_col1:
                st.metric("Tweet Sayisi (DNA)", pool_dna.get("tweet_sayisi", 0))
            with dna_col2:
                st.metric("Kucuk Harf %", f"{pool_dna.get('kucuk_harf_yuzde', 0)}%")
            with dna_col3:
                st.metric("Emoji %", f"{pool_dna.get('emoji_yuzde', 0)}%")

            with st.expander("DNA Detaylari"):
                sig_words = pool_dna.get("imza_kelimeleri", {})
                if sig_words:
                    top_words = list(sig_words.items())[:15]
                    st.markdown("**Imza Kelimeleri:** " + ", ".join(f'`{w}` ({c}x)' for w, c in top_words))

                sig_phrases = pool_dna.get("imza_kaliplari", {})
                if sig_phrases:
                    top_phrases = list(sig_phrases.items())[:10]
                    st.markdown("**Imza Kaliplari:** " + ", ".join(f'`{p}` ({c}x)' for p, c in top_phrases))

                hooks = pool_dna.get("hook_ornekleri", [])
                if hooks:
                    st.markdown("**En Etkili Hook'lar:**")
                    for h in hooks[:8]:
                        st.markdown(f'- "{h[:120]}"')

        if st.button("DNA'yi Yeniden Hesapla", type="secondary", use_container_width=True,
                      key="regenerate_pool_dna"):
            with st.spinner("Havuzdaki tum tweet'lerden DNA cikariliyor..."):
                result = regenerate_pool_dna()
                if result["dna"]:
                    st.success(
                        f"DNA yenilendi! {result['tweet_count']} tweet, "
                        f"{result['account_count']} hesaptan"
                    )
                    st.rerun()
                else:
                    st.warning("Havuz bos — DNA olusturulamadi.")

        with st.expander("Havuz Onizleme (ilk 10 tweet)"):
            for t in pool_data["pool"][:10]:
                st.markdown(f"""
                <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                            border-radius:8px; padding:8px 12px; margin:4px 0; font-size:13px; color:#f1f5f9;">
                    <b>@{t['author']}</b> — Skor: {t['engagement_score']:,.0f}<br>
                    {t['text'][:200]}{'...' if len(t['text']) > 200 else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Havuz henuz bos. Yukaridan hesap ekleyip tweet'leri cekin!")


# ===================
# TAB 5: Export / Import
# ===================
with tab5:
    st.markdown("### Disa / Iceri Aktar")

    st.markdown("""
    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2); border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:16px;">Neden Gerekli?</div>
        <div style="color:#94a3b8; font-size:13px; margin-top:4px;">
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

    # --- Takipci Verileri ---
    st.markdown("---")
    st.markdown("### Takipci Verileri")

    col_fexp, col_fimp = st.columns(2)

    with col_fexp:
        st.markdown("#### 📤 Takipci Listesi Indir")

        current_followers = _load_all_followers()
        if current_followers:
            total_f = sum(len(d.get("followers", [])) for d in current_followers.values())
            st.info(f"{len(current_followers)} liste, toplam {total_f} takipci")

            fexport_json = _export_followers_json()
            st.download_button(
                label="📥 Takipci Listesini Indir (JSON)",
                data=fexport_json,
                file_name="follower_suggestions_export.json",
                mime="application/json",
                use_container_width=True,
                type="primary",
                key="export_followers_btn"
            )
        else:
            st.warning("Indirilecek takipci listesi yok.")

    with col_fimp:
        st.markdown("#### 📥 Takipci Listesi Yukle")

        uploaded_f_file = st.file_uploader(
            "Onceki takipci dosyasini yukleyin",
            type=["json"],
            key="import_followers_file"
        )

        if uploaded_f_file:
            try:
                f_json_str = uploaded_f_file.read().decode("utf-8")
                preview = json.loads(f_json_str)
                suggestions = preview.get("suggestions", {})

                if suggestions:
                    total_f = sum(len(d.get("followers", [])) for d in suggestions.values())
                    st.info(f"Dosyada {len(suggestions)} liste, toplam {total_f} takipci")

                    if st.button("✅ Takipci Listesini Iceri Aktar", type="primary",
                                 use_container_width=True, key="import_followers_btn"):
                        fcount = _import_followers_json(f_json_str)
                        st.success(f"{fcount} liste yuklendi!")
                        st.rerun()
                else:
                    st.error("Gecersiz dosya formati.")
            except Exception as e:
                st.error(f"Dosya okuma hatasi: {e}")
