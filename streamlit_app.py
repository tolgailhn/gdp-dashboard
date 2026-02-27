"""
Twitter/X Growth Dashboard - Kişiselleştirilmiş Versiyon
=========================================================

Kullanıcının tarzını öğrenen, viral optimizasyonlu tweet oluşturucu.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import random
from pathlib import Path

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import config
from src.scraper.trend_scraper import trend_scraper
from src.content.ai_writer import ai_writer, TweetType
from src.content.image_finder import image_finder
from src.content.voice_profile import VoiceProfile, TweetOptimizer, load_or_create_default
from src.content.viral_strategies import (
    viral_time_optimizer, viral_formulas, viral_checklist, xpatla_tips,
    ViralTimeOptimizer, ViralContentFormulas, XPatlaInspiredTips
)
from src.content.viral_discovery import (
    viral_discovery, CONTENT_CATEGORIES, ViralTweet
)
from src.content.trending_discovery import (
    trending_discovery, TRENDING_CATEGORIES,
    TrendingTopic, ThreadContent, InformativeThreadGenerator
)

# AI client'ı thread generator için kullanacağız
def get_ai_client():
    """AI client'ı döndür (Gemini veya fallback)"""
    if ai_writer.is_available:
        return ai_writer
    return None

# Sayfa yapılandırması - MOBİL UYUMLU
st.set_page_config(
    page_title="Tweet Oluşturucu",
    page_icon="🐦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# MODERN VE ŞIK CSS - Light Theme
st.markdown("""
<style>
    /* Genel sayfa stili - AÇIK TEMA */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%);
    }

    /* Ana başlık */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }

    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* Tweet kutusu */
    .tweet-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 24px;
        margin: 20px 0;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #1e293b;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .tweet-box:hover {
        border-color: #a855f7;
        box-shadow: 0 8px 30px rgba(168, 85, 247, 0.15);
    }

    /* Kopyalama ipucu */
    .copy-hint {
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
        border: 1px solid #a855f7;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin: 12px 0;
        color: #6b21a8;
    }

    /* Haber kartı */
    .news-card {
        background: white;
        border-left: 4px solid #8b5cf6;
        padding: 16px;
        margin: 10px 0;
        border-radius: 0 16px 16px 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        color: #334155;
    }

    .news-card:hover {
        background: #faf5ff;
        border-left-color: #a855f7;
        transform: translateX(5px);
    }

    /* Butonlar */
    .stButton > button {
        width: 100%;
        padding: 14px 24px;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 14px;
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
        border: none;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
    }

    /* Karakter sayacı */
    .char-counter {
        text-align: right;
        font-size: 0.85rem;
        color: #64748b;
        font-family: monospace;
    }
    .char-ok { color: #22c55e; }
    .char-warn { color: #f59e0b; }
    .char-over { color: #ef4444; }

    /* Adım göstergesi */
    .step-indicator {
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 15px;
        font-size: 0.9rem;
    }

    /* Viral skor */
    .viral-score {
        background: linear-gradient(135deg, #f97316 0%, #eab308 50%, #22c55e 100%);
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        color: white;
        font-weight: 700;
        margin: 15px 0;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.3);
    }

    /* İpucu kutusu */
    .tip-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 16px;
        padding: 16px;
        margin: 15px 0;
        color: #92400e;
    }

    /* Başarı kutusu */
    .success-box {
        background: #dcfce7;
        border: 1px solid #22c55e;
        border-radius: 16px;
        padding: 16px;
        margin: 15px 0;
        color: #166534;
    }

    /* Profil kartı */
    .profile-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        color: #334155;
    }

    /* Trend kartı */
    .trend-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px;
        margin: 12px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #334155;
    }

    .trend-card:hover {
        background: #faf5ff;
        border-color: #a855f7;
        transform: scale(1.02);
    }

    /* Stats badge */
    .stats-badge {
        background: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }

    /* Kategori seçici */
    .category-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 25px;
        padding: 8px 16px;
        color: #64748b;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        cursor: pointer;
        display: inline-block;
        margin: 4px;
    }

    .category-btn:hover, .category-btn.active {
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
        color: white;
        border-color: transparent;
    }

    /* Input alanları */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        color: #1e293b !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 12px;
        color: #64748b;
        border: 1px solid #e2e8f0;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
        color: white;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 12px;
        color: #334155 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        border-right: 1px solid #e2e8f0;
    }

    /* Text colors for readability */
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
    }

    p, span, div {
        color: #334155;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    /* Big emoji */
    .big-emoji {
        font-size: 2.5rem;
        display: block;
        text-align: center;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


def init_session():
    """Session state başlat"""
    defaults = {
        "current_tweet": "",
        "current_image": None,
        "selected_trend": None,
        "trend_analysis": None,
        "trends_cache": None,
        "voice_profile": load_or_create_default(),  # @ilhntolga profili otomatik yüklenir
        "page": "main",  # main, profile, tips, xpatla, discover, trending
        "viral_analysis": None,
        "daily_tip": xpatla_tips.get_daily_tip(),
        # Keşfet sayfası için (yeni AI content engine)
        "discover_category": "ai",  # ai veya football
        "discover_tweets": [],
        "pending_viral": None,  # Onay bekleyen viral tweet
        "pending_tweet_idx": None,
        # Eski keşfet (geriye uyumluluk)
        "discovered_tweets": [],
        "selected_category": None,
        "search_topic": "",
        "selected_viral_tweet": None,
        # Trending sayfası için
        "trending_topics": [],
        "trending_category": "all",
        "selected_trending_topic": None,
        "generated_thread": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_trends():
    """Trendleri getir"""
    if st.session_state.trends_cache is None:
        with st.spinner("Trendler yükleniyor..."):
            st.session_state.trends_cache = trend_scraper.get_turkey_trends()
    return st.session_state.trends_cache


def generate_personalized_tweet(topic: str, analysis: dict = None, tweet_style: str = "auto") -> dict:
    """
    Kişiselleştirilmiş tweet oluştur - Kullanıcının ses profiline göre
    """
    profile = st.session_state.voice_profile

    # AI varsa profili kullanarak tweet oluştur
    if ai_writer.is_available:
        try:
            # Profil prompt'unu oluştur
            profile_prompt = profile.to_prompt()

            # Ek bağlam
            context_parts = []
            if analysis:
                if analysis.get("key_points"):
                    context_parts.append(f"Ana noktalar: {', '.join(analysis['key_points'][:3])}")
                if analysis.get("news"):
                    titles = [n.get("title", "")[:50] for n in analysis["news"][:2]]
                    context_parts.append(f"Güncel haberler: {'; '.join(titles)}")

            context = "\n".join(context_parts) if context_parts else ""

            # Tweet oluştur
            full_prompt = f"""{profile_prompt}

KONU: {topic}
{f'BAĞLAM: {context}' if context else ''}

Bu konu hakkında kullanıcının tarzında bir tweet yaz. Maximum 250 karakter (hashtag için yer bırak).
Sadece tweet metnini yaz, başka bir şey yazma."""

            result = ai_writer._call_ai(full_prompt)

            if result and len(result) > 10:
                # Tweet'i temizle
                tweet_text = result.strip().strip('"').strip("'")

                # Hashtag oluştur
                clean_topic = topic.replace("#", "").replace(" ", "")
                hashtags = [clean_topic]
                if analysis and analysis.get("hashtags"):
                    hashtags.extend(analysis["hashtags"][:1])

                return {
                    "text": tweet_text,
                    "hashtags": hashtags[:2],
                    "image_query": topic,
                    "source": "ai"
                }
        except Exception as e:
            pass  # AI başarısız olursa şablonlara geç

    # Şablon bazlı üretim (fallback)
    return generate_template_tweet(topic, analysis, tweet_style, profile)


def generate_template_tweet(topic: str, analysis: dict, tweet_style: str, profile: VoiceProfile) -> dict:
    """Şablon bazlı tweet üret"""

    # Profil bazlı şablonlar
    templates = {
        "samimi": [
            f"Arkadaşlar {topic} hakkında ne düşünüyorsunuz? Ben şunu fark ettim:\n\n{{insight}}\n\nYorumlara beklerim! 👇",
            f"Bugün {topic} ile ilgili güzel bir şey paylaşmak istedim:\n\n{{insight}}",
            f"{topic} konusunda bence çoğu kişi yanılıyor. Neden mi?\n\n{{insight}}\n\nKatılıyor musunuz?",
        ],
        "profesyonel": [
            f"{topic} hakkında önemli bir değerlendirme:\n\n{{insight}}\n\nBu konuda görüşlerinizi merak ediyorum.",
            f"Son gelişmeler ışığında {topic} konusunu ele alalım:\n\n{{insight}}",
            f"{topic} ile ilgili dikkat edilmesi gereken kritik nokta:\n\n{{insight}}",
        ],
        "mizahi": [
            f"{topic} deyince herkes ciddi ciddi konuşuyor ama:\n\n{{insight}} 😅",
            f"Bi dk {topic} hakkında bir şey söyleyeceğim:\n\n{{insight}}\n\n😂 Yanlış mıyım?",
            f"{topic} hakkında unpopular opinion:\n\n{{insight}}\n\nHadi tartışalım 🍿",
        ],
        "provokatif": [
            f"Kimse {topic} hakkında gerçeği söylemiyor:\n\n{{insight}}\n\nDeğişir misiniz?",
            f"{topic} konusunda herkes aynı şeyi söylüyor. Ama gerçek şu ki:\n\n{{insight}}",
            f"Hot take: {topic} hakkında...\n\n{{insight}}\n\nTartışmaya açığım 🔥",
        ],
    }

    tone = profile.tone if profile.tone in templates else "samimi"
    template_list = templates[tone]
    template = random.choice(template_list)

    # Insight oluştur
    insights = [
        "Farklı bir bakış açısı gerekiyor.",
        "Detaylara baktığımızda ilginç şeyler çıkıyor.",
        "Herkesin gözden kaçırdığı bir nokta var.",
        "Bu konuyu ciddiye almak lazım.",
        "Burada önemli bir fırsat/risk var.",
    ]

    insight = random.choice(insights)
    if analysis and analysis.get("key_points"):
        points = analysis["key_points"]
        if points and len(points[0]) < 100:
            insight = points[0]

    text = template.format(insight=insight)

    # Emoji ekle (profile'a göre)
    if profile.emoji_usage == "çok" and profile.favorite_emojis:
        text += f" {random.choice(profile.favorite_emojis)}"

    # Hashtag
    clean_topic = topic.replace("#", "").replace(" ", "")
    hashtags = [clean_topic]

    return {
        "text": text,
        "hashtags": hashtags,
        "image_query": topic,
        "source": "template"
    }


def render_header():
    """Başlık"""
    st.markdown('<p class="main-header">🐦 Tweet Oluşturucu</p>', unsafe_allow_html=True)

    profile = st.session_state.voice_profile
    if profile.twitter_username:
        st.markdown(f'<p class="sub-header">@{profile.twitter_username} için kişiselleştirilmiş</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="sub-header">Gündem analizi • Kişisel içerik • Viral optimizasyon</p>', unsafe_allow_html=True)


def render_navigation():
    """Üst navigasyon - tabs kullan"""
    # Streamlit tabs ile daha görünür navigasyon
    pages = {
        "🏠 Tweet": "main",
        "📡 Gündem": "trending",
        "🔍 Keşfet": "discover",
        "🔥 XPatla": "xpatla",
        "⚙️ Ayarlar": "profile",
    }

    # Mevcut sayfa indeksi
    current_page = st.session_state.page
    page_keys = list(pages.keys())
    page_values = list(pages.values())

    try:
        current_idx = page_values.index(current_page)
    except ValueError:
        current_idx = 0

    # Selectbox ile sayfa seçimi (mobil uyumlu)
    selected = st.selectbox(
        "Sayfa Seç:",
        options=page_keys,
        index=current_idx,
        label_visibility="collapsed"
    )

    # Sayfa değiştiyse güncelle
    new_page = pages[selected]
    if new_page != current_page:
        st.session_state.page = new_page
        st.rerun()

    st.markdown("---")


def render_profile_page():
    """Profil ayarları sayfası"""
    st.markdown("## 👤 Ses Profilini Ayarla")
    st.markdown("AI'ın senin gibi yazması için bu bilgileri doldur.")

    profile = st.session_state.voice_profile

    # Temel bilgiler
    st.markdown("### 📝 Temel Bilgiler")

    col1, col2 = st.columns(2)
    with col1:
        profile.twitter_username = st.text_input(
            "Twitter Kullanıcı Adı",
            value=profile.twitter_username,
            placeholder="ilhntolga"
        )
    with col2:
        profile.display_name = st.text_input(
            "Görünen İsim",
            value=profile.display_name,
            placeholder="Tolga İlhan"
        )

    profile.bio = st.text_area(
        "Kısa Bio (Hakkında)",
        value=profile.bio,
        placeholder="Örn: Yazılımcı, girişimci, teknoloji meraklısı...",
        height=80
    )

    profile.profession = st.text_input(
        "Meslek/Alan",
        value=profile.profession,
        placeholder="Örn: Yazılım Mühendisi, Girişimci, Öğrenci..."
    )

    # Yazım tarzı
    st.markdown("### ✍️ Yazım Tarzı")

    col1, col2 = st.columns(2)
    with col1:
        profile.tone = st.selectbox(
            "Genel Ton",
            ["samimi", "profesyonel", "mizahi", "ciddi", "provokatif"],
            index=["samimi", "profesyonel", "mizahi", "ciddi", "provokatif"].index(profile.tone)
        )

    with col2:
        profile.language_style = st.selectbox(
            "Dil Tarzı",
            ["günlük", "resmi", "argo", "karma"],
            index=["günlük", "resmi", "argo", "karma"].index(profile.language_style) if profile.language_style in ["günlük", "resmi", "argo", "karma"] else 0
        )

    col1, col2 = st.columns(2)
    with col1:
        profile.emoji_usage = st.selectbox(
            "Emoji Kullanımı",
            ["yok", "az", "orta", "çok"],
            index=["yok", "az", "orta", "çok"].index(profile.emoji_usage)
        )

    with col2:
        profile.sentence_style = st.selectbox(
            "Cümle Uzunluğu",
            ["kısa", "orta", "uzun"],
            index=["kısa", "orta", "uzun"].index(profile.sentence_style)
        )

    # Favori emojiler
    profile.favorite_emojis = st.text_input(
        "Favori Emojiler (boşlukla ayır)",
        value=" ".join(profile.favorite_emojis),
        placeholder="🚀 💪 🔥 😊"
    ).split()

    # Konular
    st.markdown("### 📌 Konular")

    profile.main_topics = st.text_input(
        "Ana Konuların (virgülle ayır)",
        value=", ".join(profile.main_topics),
        placeholder="teknoloji, girişimcilik, yapay zeka, kripto"
    ).split(", ") if st.session_state.get("topics_input") else profile.main_topics

    main_topics_input = st.text_input(
        "Ana Konuların (virgülle ayır)",
        value=", ".join(profile.main_topics) if profile.main_topics else "",
        placeholder="teknoloji, girişimcilik, yapay zeka, kripto",
        key="main_topics_input"
    )
    profile.main_topics = [t.strip() for t in main_topics_input.split(",") if t.strip()]

    avoid_topics_input = st.text_input(
        "Kaçınılacak Konular (virgülle ayır)",
        value=", ".join(profile.avoid_topics) if profile.avoid_topics else "",
        placeholder="siyaset, din, kavga...",
        key="avoid_topics_input"
    )
    profile.avoid_topics = [t.strip() for t in avoid_topics_input.split(",") if t.strip()]

    # İlgi alanları
    interests_input = st.text_input(
        "İlgi Alanların (virgülle ayır)",
        value=", ".join(profile.interests) if profile.interests else "",
        placeholder="kitap, spor, müzik, seyahat",
        key="interests_input"
    )
    profile.interests = [t.strip() for t in interests_input.split(",") if t.strip()]

    # Viral taktikler
    st.markdown("### 🚀 Viral Taktikler")

    col1, col2 = st.columns(2)
    with col1:
        profile.use_questions = st.checkbox("❓ Soru sor", value=profile.use_questions)
        profile.use_humor = st.checkbox("😄 Mizah kullan", value=profile.use_humor)
        profile.use_personal_stories = st.checkbox("📖 Kişisel hikayeler", value=profile.use_personal_stories)

    with col2:
        profile.use_hot_takes = st.checkbox("🔥 Cesur görüşler", value=profile.use_hot_takes)
        profile.use_controversy = st.checkbox("⚡ Tartışmalı konular", value=profile.use_controversy)
        profile.use_hashtags = st.checkbox("#️⃣ Hashtag kullan", value=profile.use_hashtags)

    # Örnek tweetler
    st.markdown("### 📝 Örnek Tweetlerin (AI eğitimi için)")
    st.caption("En beğendiğin 3-5 tweet'ini yapıştır. AI senin tarzını öğrensin.")

    sample_tweets_text = st.text_area(
        "Her tweet'i yeni satıra yaz",
        value="\n".join(profile.sample_tweets) if profile.sample_tweets else "",
        height=200,
        placeholder="Tweet 1...\nTweet 2...\nTweet 3..."
    )
    profile.sample_tweets = [t.strip() for t in sample_tweets_text.split("\n") if t.strip()]

    # Kaydet butonu
    st.markdown("---")

    if st.button("💾 Profili Kaydet", type="primary", use_container_width=True):
        profile.save()
        st.session_state.voice_profile = profile
        st.success("✅ Profil kaydedildi! Artık AI senin gibi yazacak.")
        st.balloons()

    # Profil önizleme
    if profile.twitter_username:
        st.markdown("---")
        st.markdown("### 👀 Profil Önizleme")
        st.markdown(f"""
        <div class="profile-card">
            <h4>@{profile.twitter_username}</h4>
            <p>{profile.bio or 'Bio eklenmemiş'}</p>
            <p><b>Ton:</b> {profile.tone} | <b>Emoji:</b> {profile.emoji_usage}</p>
            <p><b>Konular:</b> {', '.join(profile.main_topics[:5]) if profile.main_topics else 'Belirlenmemiş'}</p>
            <p><b>Örnek tweet sayısı:</b> {len(profile.sample_tweets)}</p>
        </div>
        """, unsafe_allow_html=True)

    # Twitter/X API Ayarları
    st.markdown("---")
    st.markdown("### 🔑 X/Twitter Bağlantısı")
    st.caption("X'ten trend çekmek için auth token'larını gir")

    with st.expander("🔧 X Auth Token Ayarları", expanded=False):
        st.markdown("""
        **Token'ları nasıl bulursun:**
        1. twitter.com'a giriş yap
        2. F12 ile DevTools aç
        3. Application > Cookies > twitter.com
        4. `auth_token` ve `ct0` değerlerini kopyala
        """)

        auth_token = st.text_input(
            "Auth Token",
            type="password",
            placeholder="auth_token cookie değeri",
            help="twitter.com cookies'den auth_token"
        )

        ct0_token = st.text_input(
            "CT0 Token",
            type="password",
            placeholder="ct0 cookie değeri",
            help="twitter.com cookies'den ct0 (CSRF token)"
        )

        if st.button("💾 Token'ları Kaydet", use_container_width=True):
            if auth_token and ct0_token:
                # Environment variable olarak kaydet (session için)
                import os
                os.environ["TWITTER_AUTH_TOKEN"] = auth_token
                os.environ["TWITTER_CT0"] = ct0_token

                # trending_discovery'yi güncelle
                trending_discovery.twitter_auth_token = auth_token
                trending_discovery.twitter_ct0 = ct0_token

                st.success("✅ Token'lar kaydedildi! Gündem sayfasında X trendleri görünecek.")
            else:
                st.warning("Her iki token'ı da gir")

        # Test butonu
        if st.button("🧪 Bağlantıyı Test Et"):
            if trending_discovery.twitter_auth_token and trending_discovery.twitter_ct0:
                with st.spinner("X'e bağlanılıyor..."):
                    topics = trending_discovery._get_x_trends_graphql()
                    if topics:
                        st.success(f"✅ Bağlantı başarılı! {len(topics)} trend bulundu")
                        for t in topics[:3]:
                            st.markdown(f"• {t.title}")
                    else:
                        st.warning("Trend bulunamadı, token'ları kontrol et")
            else:
                st.warning("Önce token'ları kaydet")


def render_trending_page():
    """Gündem - X, Reddit, HackerNews'ten trending konular"""
    st.markdown("## 📡 Şu An Ne Konuşuluyor?")

    # X bağlantı durumu
    if trending_discovery.twitter_auth_token and trending_discovery.twitter_ct0:
        st.markdown("🐦 **X/Twitter** • 🔴 Reddit • 🟠 HackerNews'ten anlık gündem")
    else:
        st.markdown("🔴 Reddit • 🟠 HackerNews'ten anlık gündem")
        st.caption("💡 X trendlerini görmek için Profil > X Auth Token Ayarları'nı kullan")

    st.caption("🔵 X Premium desteği - Uzun, detaylı içerikler oluştur!")

    # Kategori seçimi
    st.markdown("### 📂 Kategori")
    cat_cols = st.columns(5)

    for i, (cat_key, cat_data) in enumerate(TRENDING_CATEGORIES.items()):
        with cat_cols[i % 5]:
            is_selected = st.session_state.trending_category == cat_key
            btn_type = "primary" if is_selected else "secondary"

            if st.button(cat_data["name"], key=f"trend_cat_{cat_key}", type=btn_type, use_container_width=True):
                st.session_state.trending_category = cat_key
                with st.spinner(f"🔄 {cat_data['name']} yükleniyor..."):
                    st.session_state.trending_topics = trending_discovery.get_all_trending(cat_key)
                st.rerun()

    # Yükle butonu
    if not st.session_state.trending_topics:
        st.markdown("---")
        if st.button("🔄 Gündem Yükle", type="primary", use_container_width=True):
            with st.spinner("Reddit, HackerNews, Tech haberler taranıyor..."):
                st.session_state.trending_topics = trending_discovery.get_all_trending(
                    st.session_state.trending_category
                )
            st.rerun()

        st.info("👆 Butona tıkla ve şu an internette en çok konuşulan konuları gör!")

    # Trending konular listesi
    if st.session_state.trending_topics:
        st.markdown("---")
        st.markdown(f"### 🔥 Trending Konular ({len(st.session_state.trending_topics)})")

        # Yenile butonu
        if st.button("🔄 Yenile"):
            with st.spinner("Güncelleniyor..."):
                st.session_state.trending_topics = trending_discovery.get_all_trending(
                    st.session_state.trending_category
                )
            st.rerun()

        for i, topic in enumerate(st.session_state.trending_topics):
            with st.container():
                # Kaynak ikonu
                source_icons = {
                    "twitter": "🐦",
                    "reddit": "🔴",
                    "hackernews": "🟠",
                    "techcrunch": "💚",
                    "wired": "🔵",
                    "arstechnica": "🟣",
                }
                source_icon = source_icons.get(topic.source, "📰")

                # Kategori rengi
                cat_colors = {
                    "ai": "#10B981",
                    "tech": "#3B82F6",
                    "crypto": "#F59E0B",
                    "world": "#EF4444",
                }
                cat_color = cat_colors.get(topic.category, "#6B7280")

                # Engagement göstergesi
                engagement = f"⬆️ {topic.upvotes:,}" if topic.upvotes else ""
                comments = f"💬 {topic.comments:,}" if topic.comments else ""
                time_display = f"⏰ {topic.time_ago}" if topic.time_ago else ""

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border-left: 4px solid {cat_color};
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 12px 12px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <span style="font-size: 0.75rem; color: #6B7280;">
                            {source_icon} {topic.source.upper()} • {topic.category.upper()}
                        </span>
                        <span style="font-size: 0.75rem; color: #9CA3AF;">{time_display}</span>
                    </div>
                    <p style="font-size: 1rem; font-weight: 600; margin: 8px 0; color: #1F2937;">
                        {topic.title[:150]}{'...' if len(topic.title) > 150 else ''}
                    </p>
                    <p style="font-size: 0.85rem; color: #6B7280; margin: 5px 0;">
                        {topic.description[:120]}{'...' if len(topic.description) > 120 else ''}
                    </p>
                    <div style="font-size: 0.8rem; color: #10B981; margin-top: 8px;">
                        {engagement} {comments}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📝 İçerik Yaz", key=f"thread_{i}", use_container_width=True):
                        with st.spinner("🔍 Araştırma yapılıyor..."):
                            # 1. GERÇEK ARAŞTIRMA YAP
                            researched_topic = trending_discovery.research_topic(topic)

                        with st.spinner("✍️ İçerik oluşturuluyor..."):
                            # 2. AI ile bilgilendirici içerik oluştur
                            ai_client = get_ai_client()
                            user_tone = st.session_state.voice_profile.tone

                            thread = InformativeThreadGenerator.generate_informative_content(
                                topic=researched_topic,
                                ai_client=ai_client,
                                user_voice=user_tone,
                                max_length=2000  # X Premium için uzun içerik
                            )
                            st.session_state.generated_thread = thread
                            st.session_state.selected_trending_topic = researched_topic

                        st.rerun()

                with col2:
                    if st.button("⚡ Hızlı Tweet", key=f"single_{i}", use_container_width=True):
                        # Kısa tweet oluştur (araştırma olmadan)
                        quick_content = InformativeThreadGenerator.generate_informative_content(
                            topic=topic,
                            ai_client=get_ai_client(),
                            user_voice=st.session_state.voice_profile.tone,
                            max_length=280
                        )
                        st.session_state.current_tweet = quick_content.full_text[:280]
                        st.session_state.page = "main"
                        st.rerun()

                with col3:
                    if topic.url:
                        st.markdown(f"[🔗 Kaynak]({topic.url})")

                st.markdown("---")

    # Oluşturulan içerik - X PREMIUM UZUN TWEET GÖSTERİMİ
    if st.session_state.generated_thread:
        thread = st.session_state.generated_thread
        topic = st.session_state.selected_trending_topic

        st.markdown("### 📝 Oluşturulan İçerik")

        # Araştırma bilgisi göster
        if topic and topic.key_points:
            with st.expander("🔍 Araştırma Sonuçları", expanded=False):
                st.markdown("**Bulunan önemli noktalar:**")
                for point in topic.key_points[:5]:
                    st.markdown(f"• {point[:200]}")
                if topic.url:
                    st.markdown(f"**Kaynak:** [{topic.url[:50]}...]({topic.url})")

        # Karakter sayısı
        char_count = thread.char_count
        if char_count <= 280:
            char_info = f"📊 {char_count} karakter (Standart tweet)"
        elif char_count <= 4000:
            char_info = f"📊 {char_count} karakter (X Premium uzun tweet ✓)"
        else:
            char_info = f"📊 {char_count} karakter (Çok uzun, kısaltılabilir)"

        st.caption(char_info)

        # ANA İÇERİK - Düzenlenebilir text area
        edited_content = st.text_area(
            "İçerik (düzenleyebilirsin):",
            value=thread.full_text,
            height=400,
            label_visibility="collapsed",
            key="thread_editor"
        )

        # Hashtag'ler
        if thread.hashtags:
            st.markdown(f"**Önerilen Hashtagler:** {' '.join(thread.hashtags)}")

        # GÖRSEL OLUŞTURMA BÖLÜMÜ
        st.markdown("---")
        st.markdown("### 🖼️ Görsel")

        # Session state için görsel değişkenleri
        if "generated_image" not in st.session_state:
            st.session_state.generated_image = None
        if "image_prompt" not in st.session_state:
            st.session_state.image_prompt = ""

        col_img1, col_img2 = st.columns(2)

        with col_img1:
            if st.button("🎨 Görsel Prompt Oluştur", use_container_width=True):
                with st.spinner("Görsel prompt'u oluşturuluyor..."):
                    # AI ile görsel prompt'u oluştur
                    image_prompt = ai_writer.generate_image_prompt(
                        content=edited_content,
                        topic=topic.title if topic else ""
                    )
                    st.session_state.image_prompt = image_prompt
                st.rerun()

        with col_img2:
            if st.button("🔍 Hazır Görsel Bul", use_container_width=True):
                with st.spinner("İlgili görsel aranıyor..."):
                    # Pexels'tan görsel ara
                    search_term = topic.title.split()[0] if topic else "technology"
                    image_result = ai_writer.find_relevant_image(search_term)
                    if image_result:
                        st.session_state.generated_image = image_result
                    else:
                        st.warning("Görsel bulunamadı, farklı bir terim deneyin.")
                st.rerun()

        # Görsel prompt'u göster ve düzenle
        if st.session_state.image_prompt:
            st.markdown("**Görsel Prompt'u (düzenleyebilirsin):**")
            edited_prompt = st.text_area(
                "Prompt:",
                value=st.session_state.image_prompt,
                height=100,
                label_visibility="collapsed",
                key="image_prompt_editor"
            )

            if st.button("🖼️ Görsel Oluştur (Gemini Imagen)", use_container_width=True):
                with st.spinner("Görsel oluşturuluyor... (bu biraz sürebilir)"):
                    try:
                        image = ai_writer.generate_image(edited_prompt)
                        if image:
                            st.session_state.generated_image = {"pil_image": image, "source": "gemini"}
                        else:
                            st.warning("Görsel oluşturulamadı. Hazır görsel aramayı deneyin.")
                    except Exception as e:
                        st.error(f"Hata: {e}")
                        st.info("💡 İpucu: Hazır görsel bul butonunu kullanabilirsiniz.")
                st.rerun()

        # Oluşturulan/bulunan görseli göster
        if st.session_state.generated_image:
            st.markdown("**Önerilen Görsel:**")
            img = st.session_state.generated_image

            if img.get("source") == "gemini" and img.get("pil_image"):
                st.image(img["pil_image"], use_container_width=True)
                st.caption("Gemini Imagen ile oluşturuldu")
            elif img.get("url"):
                st.image(img["url"], use_container_width=True)
                st.markdown(f"[📥 Görseli İndir]({img.get('download_url', img['url'])})")
                st.caption(f"Fotoğraf: {img.get('photographer', 'Pexels')}")

            if st.button("❌ Görseli Kaldır"):
                st.session_state.generated_image = None
                st.rerun()

        st.markdown("---")

        # Kopyalama ipucu
        st.markdown("""
        <div class="copy-hint">
            💡 <b>X Premium ile uzun tweet paylaşabilirsin!</b><br>
            Metni seç → Kopyala → X uygulamasına yapıştır
        </div>
        """, unsafe_allow_html=True)

        # Aksiyonlar
        col1, col2, col3 = st.columns(3)

        with col1:
            # X'te paylaş butonu
            import urllib.parse
            tweet_encoded = urllib.parse.quote(edited_content[:280])  # Intent için ilk 280 karakter
            twitter_url = f"https://twitter.com/intent/tweet?text={tweet_encoded}"

            st.markdown(f"""
            <a href="{twitter_url}" target="_blank" style="
                display: block;
                background: #1DA1F2;
                color: white;
                text-align: center;
                padding: 12px;
                border-radius: 20px;
                text-decoration: none;
                font-weight: bold;
            ">
                🐦 X'te Paylaş
            </a>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("🔄 Yeniden Yaz", use_container_width=True):
                topic = st.session_state.selected_trending_topic
                if topic:
                    with st.spinner("Yeniden yazılıyor..."):
                        thread = InformativeThreadGenerator.generate_informative_content(
                            topic=topic,
                            ai_client=get_ai_client(),
                            user_voice=st.session_state.voice_profile.tone,
                            max_length=2000
                        )
                        st.session_state.generated_thread = thread
                        st.session_state.generated_image = None
                        st.session_state.image_prompt = ""
                    st.rerun()

        with col3:
            if st.button("📋 Ana Sayfaya Al", use_container_width=True):
                # Hashtag'leri ekle
                final_text = edited_content
                if thread.hashtags and not any(h in edited_content for h in thread.hashtags):
                    final_text += f"\n\n{' '.join(thread.hashtags)}"

                st.session_state.current_tweet = final_text
                # Görseli de taşı
                if st.session_state.generated_image and st.session_state.generated_image.get("url"):
                    st.session_state.current_image = type('obj', (object,), {
                        'url': st.session_state.generated_image['url'],
                        'download_url': st.session_state.generated_image.get('download_url', ''),
                        'photographer': st.session_state.generated_image.get('photographer', '')
                    })()
                st.session_state.page = "main"
                st.rerun()

        # Temizle
        if st.button("❌ Kapat"):
            st.session_state.generated_thread = None
            st.session_state.selected_trending_topic = None
            st.session_state.generated_image = None
            st.session_state.image_prompt = ""
            st.rerun()


def render_discover_page():
    """AI/Futbol içerik keşfet - Ton seçimi + Araştırma + Model bilgisi"""
    st.markdown("## 🔍 AI Haber Keşfet")

    # AI Content Engine'i yükle
    try:
        from src.content.ai_content_engine import (
            AIContentEngine, AI_ACCOUNTS, FOOTBALL_ACCOUNTS,
            WRITING_STYLES, AVAILABLE_MODELS
        )
        engine = AIContentEngine()
        engine_available = True
    except Exception as e:
        st.error(f"Content engine yüklenemedi: {e}")
        engine_available = False
        return

    # Üst bilgi - Model bilgisi
    model_info = AVAILABLE_MODELS.get(engine.current_model, {})
    st.caption(f"🤖 Model: **{model_info.get('name', 'Claude Sonnet')}** ({model_info.get('provider', 'Anthropic')})")

    # Kategori seçimi
    st.markdown("### 📂 Kategori")
    col1, col2 = st.columns(2)

    with col1:
        ai_selected = st.session_state.get("discover_category", "ai") == "ai"
        if st.button("🤖 AI Haberleri", type="primary" if ai_selected else "secondary", use_container_width=True):
            st.session_state.discover_category = "ai"
            st.session_state.discover_tweets = []
            st.rerun()

    with col2:
        football_selected = st.session_state.get("discover_category", "ai") == "football"
        if st.button("⚽ Futbol", type="primary" if football_selected else "secondary", use_container_width=True):
            st.session_state.discover_category = "football"
            st.session_state.discover_tweets = []
            st.rerun()

    # Zaman aralığı
    hours = st.select_slider(
        "⏰ Zaman Aralığı",
        options=[6, 12, 24, 48],
        value=12,
        format_func=lambda x: f"Son {x} saat"
    )

    # Yazım stili seçimi
    st.markdown("### ✍️ Yazım Stili")
    style_options = list(WRITING_STYLES.keys())
    style_names = [WRITING_STYLES[s]["name"] for s in style_options]

    selected_style_idx = st.selectbox(
        "Ton seç:",
        range(len(style_options)),
        format_func=lambda i: style_names[i],
        index=0,
        label_visibility="collapsed"
    )
    selected_style = style_options[selected_style_idx]
    style_info = WRITING_STYLES[selected_style]

    # Stil açıklaması
    st.caption(f"_{style_info['description']}_")

    with st.expander("📝 Stil Örneği"):
        st.code(style_info["example"], language=None)

    st.markdown("---")

    # İçerik yükle butonu
    category = st.session_state.get("discover_category", "ai")

    if st.button("🔄 AI Haberlerini Tara", type="primary", use_container_width=True):
        with st.spinner(f"🔍 {category.upper()} haberleri aranıyor (son {hours} saat)..."):
            try:
                if category == "ai":
                    tweets, error = engine.get_ai_news(hours=hours, limit=15)
                else:
                    tweets, error = engine.get_football_content(hours=hours, limit=15)

                st.session_state.discover_tweets = tweets
                st.session_state.selected_style = selected_style
                st.session_state.discover_error = error
            except Exception as e:
                tweets = []
                st.session_state.discover_tweets = []
                st.session_state.discover_error = str(e)

        if tweets:
            st.success(f"✅ {len(tweets)} AI haberi bulundu!")
        else:
            error_msg = st.session_state.get("discover_error", "")
            if error_msg:
                st.error(f"❌ Hata: {error_msg}")
            st.warning("Haber bulunamadı. Token'ları kontrol et veya zaman aralığını artır.")
        st.rerun()

    # Sonuçları göster
    tweets = st.session_state.get("discover_tweets", [])
    current_style = st.session_state.get("selected_style", "samimi")

    if tweets:
        st.markdown(f"### 📰 AI Haberleri ({len(tweets)})")

        for i, tweet in enumerate(tweets):
            with st.container():
                # Tweet kartı
                engagement = f"❤️ {tweet.likes:,} | 🔄 {tweet.retweets:,}"

                # AI haberi badge
                ai_badge = "🔥 AI Haberi" if getattr(tweet, 'is_ai_news', False) else ""

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border-left: 4px solid {'#10B981' if ai_badge else '#1DA1F2'};
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 12px 12px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                ">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #657786; margin-bottom: 8px;">
                        <span><strong>@{tweet.author}</strong></span>
                        <span style="color: #10B981;">{ai_badge}</span>
                    </div>
                    <p style="font-size: 1rem; margin-bottom: 10px; line-height: 1.5;">{tweet.text[:400]}{'...' if len(tweet.text) > 400 else ''}</p>
                    <div style="color: #17bf63; font-size: 0.85rem;">{engagement}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("✨ Araştır & Yaz", key=f"viral_{i}", use_container_width=True):
                        with st.spinner("🔍 Konu araştırılıyor..."):
                            # Araştırma + Yazma
                            viral = engine.rewrite_viral(
                                tweet,
                                style=current_style,
                                do_research=True
                            )
                            st.session_state.pending_viral = viral
                            st.session_state.pending_tweet_idx = i
                        st.rerun()

                with col2:
                    if st.button("⚡ Hızlı Yaz", key=f"quick_{i}", use_container_width=True):
                        with st.spinner("✍️ Yazılıyor..."):
                            # Araştırma olmadan hızlı yaz
                            viral = engine.rewrite_viral(
                                tweet,
                                style=current_style,
                                do_research=False
                            )
                            st.session_state.pending_viral = viral
                            st.session_state.pending_tweet_idx = i
                        st.rerun()

                with col3:
                    st.markdown(f"[🔗 Kaynak]({tweet.url})")

                # Viral preview göster
                if st.session_state.get("pending_tweet_idx") == i and st.session_state.get("pending_viral"):
                    viral = st.session_state.pending_viral

                    st.markdown("---")
                    st.markdown("#### ✅ Yeniden Yazıldı")

                    # Model ve stil bilgisi
                    st.caption(f"🤖 Model: **{viral.model_used}** | ✍️ Stil: **{WRITING_STYLES.get(viral.style_used, {}).get('name', viral.style_used)}**")

                    # Araştırma sonucu göster
                    if viral.research:
                        with st.expander("🔍 Araştırma Özeti", expanded=False):
                            st.markdown(viral.research.summary)
                            if viral.research.key_points:
                                st.markdown("**Önemli Noktalar:**")
                                for point in viral.research.key_points[:3]:
                                    st.markdown(f"• {point}")

                    # Düzenlenebilir alan
                    edited_text = st.text_area(
                        "Tweet metni (düzenleyebilirsin):",
                        value=viral.rewritten_text,
                        height=250,
                        key=f"edit_viral_{i}"
                    )

                    # Karakter sayısı
                    char_count = len(edited_text)
                    char_color = "green" if char_count <= 2000 else "red"
                    st.caption(f"Karakter: :{char_color}[{char_count}] / 2000")

                    # Viral skor
                    col_score, col_info = st.columns([1, 2])
                    with col_score:
                        st.progress(viral.viral_score / 100)
                    with col_info:
                        st.caption(f"Viral Potansiyel: **{viral.viral_score:.0f}/100**")

                    # Butonlar
                    approve_col, regen_col, reject_col = st.columns(3)

                    with approve_col:
                        if st.button("✅ Onayla", key=f"approve_{i}", type="primary", use_container_width=True):
                            st.session_state.current_tweet = edited_text
                            st.session_state.pending_viral = None
                            st.session_state.pending_tweet_idx = None
                            st.session_state.page = "main"
                            st.rerun()

                    with regen_col:
                        if st.button("🔄 Yeniden Yaz", key=f"regen_{i}", use_container_width=True):
                            with st.spinner("Yeniden yazılıyor..."):
                                viral = engine.rewrite_viral(
                                    tweet,
                                    style=current_style,
                                    do_research=True
                                )
                                st.session_state.pending_viral = viral
                            st.rerun()

                    with reject_col:
                        if st.button("❌ İptal", key=f"reject_{i}", use_container_width=True):
                            st.session_state.pending_viral = None
                            st.session_state.pending_tweet_idx = None
                            st.rerun()

                st.markdown("---")

    else:
        st.info("👆 'AI Haberlerini Tara' butonuna tıkla!")
        st.markdown("""
        **Ne aranacak:**
        - 🚀 Yeni model duyuruları (GPT-5, Claude 4, Gemini 2...)
        - 📊 Benchmark sonuçları
        - 🔧 Özellik güncellemeleri
        - 📰 AI şirketlerinden haberler
        """)


def render_xpatla_page():
    """XPatla tarzı viral strateji sayfası"""
    st.markdown("## 🔥 XPatla - Viral Stratejiler")
    st.markdown("X'te patlamak artık şans işi değil!")

    # Günün ipucu
    st.markdown("### 💡 Günün İpucu")
    st.info(st.session_state.daily_tip)

    if st.button("🔄 Yeni İpucu"):
        st.session_state.daily_tip = xpatla_tips.get_daily_tip()
        st.rerun()

    st.markdown("---")

    # En iyi paylaşım saatleri
    st.markdown("### ⏰ Bugün İçin En İyi Saatler")
    best_times = ViralTimeOptimizer.get_best_times_today()

    for time_slot in best_times:
        if time_slot["is_current"]:
            st.success(f"🟢 **{time_slot['time']}** - {time_slot['description']} - **ŞİMDİ!**")
        elif time_slot["is_upcoming"]:
            st.info(f"🔵 {time_slot['time']} - {time_slot['description']}")
        else:
            st.markdown(f"⚪ ~~{time_slot['time']}~~ - {time_slot['description']}")

    # Gün stratejisi
    st.markdown("---")
    st.markdown("### 📅 Bugünün Stratejisi")
    st.markdown(ViralTimeOptimizer.get_day_strategy())

    st.markdown("---")

    # İçerik fikirleri
    st.markdown("### 💭 İçerik Fikirleri")
    ideas = xpatla_tips.get_content_ideas(5)
    for i, idea in enumerate(ideas, 1):
        st.markdown(f"{i}. {idea}")

    if st.button("🎲 Yeni Fikirler Getir"):
        st.rerun()

    st.markdown("---")

    # Hook örnekleri
    st.markdown("### 🪝 Dikkat Çekici Başlangıçlar (Hook)")
    st.caption("Bu başlangıçları kullanarak tweet'lerine dikkat çek:")

    for hook in ViralContentFormulas.HOOKS[:5]:
        example = hook.format(topic="[KONU]", count=5)
        st.code(example, language=None)

    st.markdown("---")

    # Engagement triggers
    st.markdown("### 💬 Etkileşim Tetikleyicileri")
    st.caption("Tweet'inin sonuna bunlardan birini ekle:")

    for trigger in ViralContentFormulas.ENGAGEMENT_TRIGGERS[:5]:
        st.markdown(f"• {trigger.strip()}")

    st.markdown("---")

    # Algoritma ağırlıkları özeti
    st.markdown("### 📊 X Algoritması Özeti")
    st.markdown("""
    | Aksiyon | Ağırlık | Strateji |
    |---------|---------|----------|
    | Reply alan reply | **75x** | Kendi tweetine reply at! |
    | Reply | **13.5x** | Soru sor, tartışma başlat |
    | Profil tıklama | **12x** | Merak uyandır |
    | 2+ dk kalma | **10x** | Thread yap |
    | Retweet | **1x** | Paylaşılabilir yaz |
    | Like | **0.5x** | En kolay ama en az değerli |
    """)

    # Cezalar
    st.markdown("### ⚠️ Bunlardan Kaçın!")
    st.error("""
    - ❌ Harici link → %50 reach düşüşü
    - ❌ 3+ hashtag → Spam algılanır
    - ❌ Offensive içerik → %80 reach düşüşü
    - ❌ Çok fazla mention → Spam riski
    """)


def render_tips_page():
    """Viral ipuçları sayfası"""
    st.markdown("## 💡 Viral Tweet İpuçları")
    st.markdown("Twitter algoritmasına göre optimize edilmiş stratejiler")

    # Algoritma bilgileri
    st.markdown("### 📊 Twitter Algoritması Ağırlıkları")
    st.markdown("""
    | Etkileşim | Ağırlık | Açıklama |
    |-----------|---------|----------|
    | 💬 Reply | **13.5x** | En değerli! |
    | 👤 Profil Tıklama | **12x** | Merak uyandır |
    | 🔗 Link Tıklama | **1.5x** | Linksiz daha iyi |
    | 🔄 Retweet | **1x** | Paylaşılabilir yaz |
    | ❤️ Like | **0.5x** | En kolay ama en az değerli |
    """)

    st.markdown("---")
    st.markdown("### ⏰ En İyi Paylaşım Saatleri (Türkiye)")
    st.markdown("""
    - 🌅 **08:00-09:00** - Sabah rutini
    - 🍽️ **12:00-13:00** - Öğle arası
    - 🏠 **17:00-18:00** - İşten çıkış
    - 🌙 **21:00-22:00** - Prime time!
    """)

    st.markdown("---")
    st.markdown("### 🔥 Viral Tweet Formülleri")

    tips = TweetOptimizer.get_improvement_tips()
    for tip in tips:
        st.markdown(f"- {tip}")

    st.markdown("---")
    st.markdown("### ✅ Tweet Kontrol Listesi")
    st.markdown("""
    - [ ] 280 karakterin altında mı?
    - [ ] Soru içeriyor mu? (Reply için)
    - [ ] 1-2 hashtag var mı?
    - [ ] Emoji var mı?
    - [ ] İlk 30 dakika etkileşime hazır mısın?
    - [ ] Görsel ekledin mi? (1.5x etkileşim)
    - [ ] Link YOK değil mi? (algoritma cezalandırır)
    """)

    st.markdown("---")
    st.markdown("### 🧵 Thread Stratejisi")
    st.markdown("""
    Thread = Daha fazla süre = Daha yüksek skor

    **İdeal Thread Yapısı:**
    1. **İlk tweet**: Hook - merak uyandır
    2. **2-7. tweetler**: Değerli içerik
    3. **Son tweet**: CTA (takip et, paylaş)

    **Thread başlangıçları:**
    - "🧵 Thread:"
    - "1/ Bugün ... hakkında konuşacağız"
    - "Herkesin bilmesi gereken X şey:"
    """)


def render_step1_trends():
    """Adım 1: Trend seçimi"""
    st.markdown('<span class="step-indicator">1️⃣ Konu Seç</span>', unsafe_allow_html=True)

    mode = st.radio(
        "Nasıl seçmek istersin?",
        ["🔥 Gündem'den Seç", "✍️ Kendi Konumu Yaz"],
        horizontal=True,
        label_visibility="collapsed"
    )

    topic = None

    if mode == "🔥 Gündem'den Seç":
        trends = get_trends()

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄", help="Trendleri yenile"):
                st.session_state.trends_cache = None
                st.session_state.trend_analysis = None
                st.rerun()

        if trends:
            trend_options = [f"{t.name}" + (f" ({t.tweet_count})" if t.tweet_count else "") for t in trends]

            selected = st.selectbox(
                "Gündemdeki konular:",
                options=trend_options,
                index=0,
                label_visibility="collapsed"
            )

            if selected:
                idx = trend_options.index(selected)
                topic = trends[idx].name
                st.session_state.selected_trend = topic
        else:
            st.warning("Trend yüklenemedi. Manuel konu girin.")

    else:
        topic = st.text_input(
            "Konu:",
            placeholder="Örn: Yapay Zeka, Kripto, Ekonomi...",
            label_visibility="collapsed"
        )
        st.session_state.selected_trend = topic

    return topic


def render_trend_analysis(topic: str):
    """Adım 1.5: Trend analizi göster"""

    # Analiz yap (cache'le)
    if st.session_state.trend_analysis is None or st.session_state.trend_analysis.get("topic") != topic:
        with st.spinner("Konu analiz ediliyor..."):
            st.session_state.trend_analysis = trend_scraper.analyze_trend(topic)

    analysis = st.session_state.trend_analysis

    # Analiz sonuçlarını göster
    with st.expander("📊 Konu Analizi", expanded=True):

        # Haberler
        if analysis.get("news"):
            st.markdown("**📰 Güncel Haberler:**")
            for news in analysis["news"][:3]:
                st.markdown(f"""
                <div class="news-card">
                    <b>{news.get('title', '')[:80]}...</b><br>
                    <small>{news.get('source', '')} • {news.get('date', '')[:20]}</small>
                </div>
                """, unsafe_allow_html=True)

        # Önerilen açılar
        if analysis.get("suggested_angles"):
            st.markdown("**💡 Tweet Açıları:**")
            for angle in analysis["suggested_angles"][:3]:
                st.markdown(f"• {angle}")

        # Hashtag önerileri
        if analysis.get("hashtags"):
            hashtags = " ".join([f"#{h}" for h in analysis["hashtags"]])
            st.markdown(f"**#️⃣ Önerilen:** {hashtags}")

    return analysis


def render_step2_generate(topic: str, analysis: dict = None):
    """Adım 2: Tweet oluştur"""
    st.markdown("---")
    st.markdown('<span class="step-indicator">2️⃣ Tweet Oluştur</span>', unsafe_allow_html=True)

    # Eğer viral tweet seçiliyse göster
    if st.session_state.selected_viral_tweet:
        vt = st.session_state.selected_viral_tweet
        st.info(f"📌 **İlham:** {vt.text[:100]}... (❤️{vt.likes:,})")
        if st.button("❌ İlhamı Kaldır"):
            st.session_state.selected_viral_tweet = None
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        tweet_style = st.selectbox(
            "Tweet Türü",
            ["Otomatik", "Bilgilendirici", "Soru", "Görüş/Yorum", "Gündem Yorumu"],
            label_visibility="collapsed"
        )

    with col2:
        include_image = st.checkbox("📷 Görsel ekle", value=True)

    # AI ve profil durumu göster
    profile = st.session_state.voice_profile
    if ai_writer.is_available:
        if profile.twitter_username:
            st.caption(f"✨ AI aktif • @{profile.twitter_username} tarzında yazılacak")
        else:
            st.caption(f"✨ AI aktif ({ai_writer.provider}) - Profil ayarla daha iyi sonuç al!")
    else:
        st.caption("📝 Akıllı şablonlar kullanılıyor")

    if st.button("✨ Tweet Oluştur", type="primary", use_container_width=True):
        with st.spinner("Senin tarzında tweet hazırlanıyor..."):

            # Kişiselleştirilmiş tweet oluştur
            result = generate_personalized_tweet(topic, analysis, tweet_style)

            # Hashtag'leri ekle
            text = result["text"]
            if result["hashtags"] and profile.use_hashtags:
                hashtags = " ".join([f"#{h}" for h in result["hashtags"][:2]])
                if len(text) + len(hashtags) + 2 <= 280:
                    text = f"{text}\n\n{hashtags}"

            st.session_state.current_tweet = text

            # Viral analiz yap
            st.session_state.viral_analysis = TweetOptimizer.analyze_viral_potential(text)

            # Görsel bul
            if include_image:
                try:
                    image = image_finder.find_best_image(result["image_query"])
                    st.session_state.current_image = image
                except:
                    st.session_state.current_image = None
            else:
                st.session_state.current_image = None

        st.rerun()


def render_viral_analysis():
    """Viral analiz sonuçlarını göster"""
    if not st.session_state.viral_analysis:
        return

    analysis = st.session_state.viral_analysis

    with st.expander("🔥 Viral Analiz", expanded=True):
        # Skor
        score = analysis["score"]
        st.markdown(f"""
        <div class="viral-score">
            Viral Skor: {score}/10 {analysis['viral_potential']}
        </div>
        """, unsafe_allow_html=True)

        # Bulunan faktörler
        if analysis["factors_found"]:
            st.markdown("**✅ İyi yaptıkların:**")
            for factor in analysis["factors_found"]:
                st.markdown(f"- {factor}")

        # Öneriler
        if analysis["suggestions"]:
            st.markdown("**💡 İyileştirme önerileri:**")
            for suggestion in analysis["suggestions"]:
                st.markdown(f"- {suggestion}")

        # İstatistikler
        st.markdown(f"""
        **📊 İstatistikler:**
        - Karakter: {analysis['character_count']}/280
        - Hashtag: {analysis['hashtag_count']}
        - Tahmin: {analysis['engagement_estimate']}
        """)


def render_step3_copypost():
    """Adım 3: İncele, Düzenle ve Paylaş"""

    if not st.session_state.current_tweet:
        return

    st.markdown("---")
    st.markdown('<span class="step-indicator">3️⃣ İncele & Paylaş</span>', unsafe_allow_html=True)

    # Viral analiz
    render_viral_analysis()

    tweet_text = st.session_state.current_tweet

    # Karakter sayısı
    char_count = len(tweet_text)
    if char_count <= 280:
        char_class = "char-ok"
        char_status = "✓"
    elif char_count <= 300:
        char_class = "char-warn"
        char_status = "⚠️ Biraz uzun"
    else:
        char_class = "char-over"
        char_status = "❌ Çok uzun"

    st.markdown(f'<p class="char-counter {char_class}">{char_count}/280 {char_status}</p>', unsafe_allow_html=True)

    # Tweet düzenleme
    edited_tweet = st.text_area(
        "Tweet metni (düzenleyebilirsin):",
        value=tweet_text,
        height=180,
        label_visibility="collapsed",
        key="tweet_editor"
    )

    # Değişiklik yapıldıysa yeniden analiz et
    if edited_tweet != tweet_text:
        st.session_state.current_tweet = edited_tweet
        if st.button("🔄 Yeniden Analiz Et", use_container_width=True):
            st.session_state.viral_analysis = TweetOptimizer.analyze_viral_potential(edited_tweet)
            st.rerun()

    # Kopyalama ipucu
    st.markdown("""
    <div class="copy-hint">
        💡 <b>Metni seç</b> → <b>Kopyala</b> → <b>X uygulamasına yapıştır</b>
    </div>
    """, unsafe_allow_html=True)

    # Görsel
    if st.session_state.current_image:
        st.markdown("---")
        st.markdown("**📷 Önerilen Görsel:**")
        image = st.session_state.current_image
        st.image(image.url, use_container_width=True)
        st.markdown(f"[📥 Görseli İndir]({image.download_url})")
        st.caption(f"Fotoğraf: {image.photographer}")

    # X'te paylaş butonu
    st.markdown("---")

    import urllib.parse
    tweet_encoded = urllib.parse.quote(edited_tweet[:280])
    twitter_url = f"https://twitter.com/intent/tweet?text={tweet_encoded}"

    st.markdown(f"""
    <a href="{twitter_url}" target="_blank" style="
        display: block;
        background: #1DA1F2;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 25px;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.1rem;
    ">
        🐦 X'te Paylaş
    </a>
    """, unsafe_allow_html=True)

    st.caption("Butona tıkla → X açılacak → Tweet hazır olacak!")

    # Yeni tweet butonu
    if st.button("🔄 Yeni Tweet Oluştur", use_container_width=True):
        st.session_state.current_tweet = ""
        st.session_state.current_image = None
        st.session_state.viral_analysis = None
        st.rerun()


def render_settings():
    """Ayarlar (sidebar)"""
    with st.sidebar:
        st.markdown("## ⚙️ Durum")

        profile = st.session_state.voice_profile

        # Profil durumu
        if profile.twitter_username:
            st.success(f"✓ @{profile.twitter_username}")
        else:
            st.warning("⚠️ Profil yok")

        # AI durumu
        if ai_writer.is_available:
            st.success(f"✓ AI: {ai_writer.provider}")
        else:
            st.info("📝 Şablon modu")

        st.markdown("---")

        # Şu anki saat analizi
        st.markdown("### ⏰ Viral Saat")
        best_times = ViralTimeOptimizer.get_best_times_today()
        current_slot = next((t for t in best_times if t["is_current"]), None)

        if current_slot:
            st.success(f"🟢 Şimdi paylaş!\n{current_slot['description']}")
        else:
            next_slot = next((t for t in best_times if t["is_upcoming"]), None)
            if next_slot:
                st.info(f"⏳ Sonraki: {next_slot['time']}")

        st.markdown("---")

        # XPatla günlük ipucu
        st.markdown("### 💡 XPatla İpucu")
        st.caption(st.session_state.daily_tip[:100] + "..." if len(st.session_state.daily_tip) > 100 else st.session_state.daily_tip)


def render_main_page():
    """Ana sayfa - Tweet oluşturma"""
    # Adım 1: Konu seç
    topic = render_step1_trends()

    # Adım 1.5: Konu analizi (seçiliyse)
    analysis = None
    if topic:
        analysis = render_trend_analysis(topic)

    # Adım 2: Tweet oluştur
    if topic:
        render_step2_generate(topic, analysis)

    # Adım 3: İncele ve paylaş
    render_step3_copypost()


def main():
    """Ana uygulama"""
    init_session()

    render_header()
    render_navigation()
    render_settings()

    # Sayfa yönlendirme
    if st.session_state.page == "profile":
        render_profile_page()
    elif st.session_state.page == "tips":
        render_tips_page()
    elif st.session_state.page == "xpatla":
        render_xpatla_page()
    elif st.session_state.page == "discover":
        render_discover_page()
    elif st.session_state.page == "trending":
        render_trending_page()
    else:
        render_main_page()

    # Footer
    st.markdown("---")
    profile = st.session_state.voice_profile
    if profile.twitter_username:
        st.caption(f"🐦 @{profile.twitter_username} için kişiselleştirilmiş | Powered by Gemini AI")
    else:
        st.caption("🐦 Twitter/X Growth Tool | Ücretsiz")


if __name__ == "__main__":
    main()
