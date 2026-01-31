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
from src.content.voice_profile import VoiceProfile, TweetOptimizer

# Sayfa yapılandırması - MOBİL UYUMLU
st.set_page_config(
    page_title="Tweet Oluşturucu",
    page_icon="🐦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# MOBİL UYUMLU CSS
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1DA1F2;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #657786;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .tweet-box {
        background: #ffffff;
        border: 2px solid #1DA1F2;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        font-size: 1.1rem;
        line-height: 1.5;
    }
    .copy-hint {
        background: #e8f5fe;
        border: 1px solid #1DA1F2;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .news-card {
        background: #f8f9fa;
        border-left: 3px solid #1DA1F2;
        padding: 10px;
        margin: 5px 0;
        border-radius: 0 8px 8px 0;
    }
    .stButton > button {
        width: 100%;
        padding: 15px 20px;
        font-size: 1.1rem;
        border-radius: 25px;
    }
    .char-counter {
        text-align: right;
        font-size: 0.85rem;
        color: #657786;
    }
    .char-ok { color: #17bf63; }
    .char-warn { color: #ffad1f; }
    .char-over { color: #e0245e; }
    .step-indicator {
        background: linear-gradient(90deg, #1DA1F2, #17bf63);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }
    .viral-score {
        background: linear-gradient(90deg, #ff6b6b, #feca57, #1dd1a1);
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        color: white;
        font-weight: bold;
        margin: 10px 0;
    }
    .tip-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #28a745;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
    .profile-card {
        background: #f8f9fa;
        border: 2px solid #1DA1F2;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
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
        "voice_profile": VoiceProfile.load(),
        "page": "main",  # main, profile, tips
        "viral_analysis": None,
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
    """Üst navigasyon"""
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Ana Sayfa", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    with col2:
        if st.button("👤 Profilim", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()

    with col3:
        if st.button("💡 İpuçları", use_container_width=True):
            st.session_state.page = "tips"
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
        st.markdown("## ⚙️ Ayarlar")

        profile = st.session_state.voice_profile

        # Profil durumu
        if profile.twitter_username:
            st.success(f"✓ Profil: @{profile.twitter_username}")
        else:
            st.warning("⚠️ Profil ayarlanmamış")
            st.caption("Profilini ayarla, AI seni öğrensin!")

        # AI durumu
        if ai_writer.is_available:
            st.success(f"✓ AI: {ai_writer.provider}")
        else:
            st.info("📝 Şablon modu")
            st.caption("Gemini key ekle (ücretsiz!)")

        if image_finder.is_available:
            st.success("✓ Görsel API aktif")
        else:
            st.info("ℹ️ Demo görseller")

        st.markdown("---")
        st.markdown("### 🔥 Hızlı İpucu")
        tips = [
            "Reply en değerli (13.5x)!",
            "İlk 30 dk kritik.",
            "Link ekleme, algoritma sevmez.",
            "Soru sor, tartışma başlat!",
            "Görsel 3x etkileşim sağlar.",
        ]
        st.info(random.choice(tips))


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
