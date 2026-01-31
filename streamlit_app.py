"""
Twitter/X Growth Dashboard - Ücretsiz Versiyon
===============================================

API gerektirmeyen, telefondan kullanılabilen tweet oluşturucu.
Copy-paste ile manuel paylaşım için optimize edilmiş.
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
</style>
""", unsafe_allow_html=True)


# Tweet şablonları (AI olmadan kullanılır)
TWEET_TEMPLATES = {
    "bilgilendirici": [
        "{topic} hakkında herkesin bilmesi gereken önemli bir nokta var:\n\n{insight}\n\nBu konuda siz ne düşünüyorsunuz?",
        "Son gelişmeler ışığında {topic} konusunu değerlendirmek gerekiyor.\n\n{insight}\n\nFikirlerinizi merak ediyorum.",
        "{topic} ile ilgili dikkat çekici bir detay:\n\n{insight}",
    ],
    "soru": [
        "{topic} denince aklınıza ilk ne geliyor?\n\nYorumlarda buluşalım! 👇",
        "Sizce {topic} konusunda en büyük yanılgı nedir?\n\nMerak ediyorum 🤔",
        "{topic} hakkında bir şeyi değiştirebilseydiniz, ne olurdu?",
    ],
    "görüş": [
        "{topic} konusunda bence çoğu kişinin gözden kaçırdığı bir şey var:\n\n{insight}\n\nKatılıyor musunuz?",
        "Herkes {topic} hakkında konuşuyor ama kimse şunu söylemiyor:\n\n{insight}",
        "{topic} ile ilgili popüler olmayan görüşüm:\n\n{insight}\n\nNe dersiniz?",
    ],
    "gündem": [
        "{topic} gündemde ve herkesin bir fikri var.\n\nBenim bakış açım şu:\n{insight}",
        "Bugün {topic} çok konuşuluyor.\n\n{insight}\n\nSiz ne düşünüyorsunuz?",
        "{topic} hakkında söylenecek çok şey var ama en önemlisi:\n\n{insight}",
    ],
}

INSIGHTS = [
    "Bu konunun farklı perspektiflerden değerlendirilmesi gerekiyor.",
    "Detaylara baktığımızda ilginç şeyler ortaya çıkıyor.",
    "Herkesin gözden kaçırdığı önemli noktalar var.",
    "Bu gelişmenin uzun vadeli etkileri olacak.",
    "Konuya objektif bakmak çok önemli.",
    "Farklı görüşleri dinlemek faydalı olabilir.",
]


def init_session():
    """Session state başlat"""
    defaults = {
        "current_tweet": "",
        "current_image": None,
        "selected_trend": None,
        "trend_analysis": None,
        "persona": "Samimi, bilgili ve profesyonel bir üslup.",
        "trends_cache": None,
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


def generate_smart_tweet(topic: str, analysis: dict = None, tweet_style: str = "auto") -> dict:
    """
    Akıllı tweet oluştur - AI varsa AI kullan, yoksa şablonlardan üret
    """

    # AI varsa kullan
    if ai_writer.is_available:
        try:
            result = ai_writer.generate_tweet(
                topic=topic,
                context=str(analysis.get("key_points", [])) if analysis else "",
                persona=st.session_state.persona
            )
            if result.text and "[İçerik oluşturulamadı" not in result.text:
                return {
                    "text": result.text,
                    "hashtags": result.hashtags or [topic.replace(" ", "").replace("#", "")],
                    "image_query": result.suggested_image_query or topic,
                    "source": "ai"
                }
        except Exception as e:
            pass  # AI başarısız olursa şablonlara geç

    # Şablonlardan üret (AI yoksa veya başarısız olursa)
    style_map = {
        "auto": random.choice(list(TWEET_TEMPLATES.keys())),
        "Bilgilendirici": "bilgilendirici",
        "Soru": "soru",
        "Görüş/Yorum": "görüş",
        "Gündem Yorumu": "gündem",
    }

    style = style_map.get(tweet_style, "gündem")
    templates = TWEET_TEMPLATES.get(style, TWEET_TEMPLATES["gündem"])
    template = random.choice(templates)

    # Analiz varsa, haberlerden insight oluştur
    insight = random.choice(INSIGHTS)
    if analysis and analysis.get("key_points"):
        points = analysis["key_points"]
        if points:
            insight = points[0] if len(points[0]) < 100 else points[0][:97] + "..."

    text = template.format(topic=topic, insight=insight)

    # Hashtag oluştur
    clean_topic = topic.replace("#", "").replace(" ", "")
    hashtags = [clean_topic, "Gündem"]

    return {
        "text": text,
        "hashtags": hashtags,
        "image_query": topic,
        "source": "template"
    }


def render_header():
    """Başlık"""
    st.markdown('<p class="main-header">🐦 Tweet Oluşturucu</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gündem analizi • Akıllı içerik • Kolay paylaşım</p>', unsafe_allow_html=True)


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

    # AI durumu göster
    if ai_writer.is_available:
        st.caption(f"✨ AI aktif ({ai_writer.provider})")
    else:
        st.caption("📝 Akıllı şablonlar kullanılıyor")

    if st.button("✨ Tweet Oluştur", type="primary", use_container_width=True):
        with st.spinner("Tweet hazırlanıyor..."):

            # Tweet oluştur
            result = generate_smart_tweet(topic, analysis, tweet_style)

            # Hashtag'leri ekle
            text = result["text"]
            if result["hashtags"]:
                hashtags = " ".join([f"#{h}" for h in result["hashtags"][:2]])
                if len(text) + len(hashtags) + 2 <= 280:
                    text = f"{text}\n\n{hashtags}"

            st.session_state.current_tweet = text

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


def render_step3_copypost():
    """Adım 3: Kopyala ve Paylaş"""

    if not st.session_state.current_tweet:
        return

    st.markdown("---")
    st.markdown('<span class="step-indicator">3️⃣ Kopyala & Paylaş</span>', unsafe_allow_html=True)

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

    if edited_tweet != tweet_text:
        st.session_state.current_tweet = edited_tweet

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
        st.rerun()


def render_settings():
    """Ayarlar (sidebar)"""
    with st.sidebar:
        st.markdown("## ⚙️ Ayarlar")

        # Durum
        if ai_writer.is_available:
            st.success(f"✓ AI: {ai_writer.provider}")
        else:
            st.info("📝 Şablon modu (AI yok)")
            st.caption("AI için OpenAI key ekleyin")

        if image_finder.is_available:
            st.success("✓ Görsel API aktif")
        else:
            st.info("ℹ️ Demo görseller")

        st.markdown("---")
        st.markdown("### 💡 İpuçları")
        st.markdown("""
        - **Reply** en değerli (13.5x)
        - **İlk 30 dk** kritik
        - **Görsel** 3x etkileşim
        - **1-2 hashtag** yeterli
        """)


def main():
    """Ana uygulama"""
    init_session()

    render_header()
    render_settings()

    # Adım 1: Konu seç
    topic = render_step1_trends()

    # Adım 1.5: Konu analizi (seçiliyse)
    analysis = None
    if topic:
        analysis = render_trend_analysis(topic)

    # Adım 2: Tweet oluştur
    if topic:
        render_step2_generate(topic, analysis)

    # Adım 3: Kopyala ve paylaş
    render_step3_copypost()

    # Footer
    st.markdown("---")
    st.caption("🐦 Twitter/X Growth Tool | Ücretsiz")


if __name__ == "__main__":
    main()
