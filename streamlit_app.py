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
    layout="centered",  # Mobil için centered daha iyi
    initial_sidebar_state="collapsed"  # Mobilde sidebar kapalı başlasın
)

# MOBİL UYUMLU CSS
st.markdown("""
<style>
    /* Mobil uyumlu fontlar */
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

    /* Tweet önizleme kutusu */
    .tweet-box {
        background: #ffffff;
        border: 2px solid #1DA1F2;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        font-size: 1.1rem;
        line-height: 1.5;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    /* Kopyala butonu */
    .copy-hint {
        background: #e8f5fe;
        border: 1px solid #1DA1F2;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin: 10px 0;
        font-size: 0.9rem;
    }

    /* Trend kartları */
    .trend-card {
        background: #f7f9fa;
        border-radius: 10px;
        padding: 10px 15px;
        margin: 5px 0;
        cursor: pointer;
    }

    .trend-card:hover {
        background: #e8f5fe;
    }

    /* Büyük butonlar (mobil için) */
    .stButton > button {
        width: 100%;
        padding: 15px 20px;
        font-size: 1.1rem;
        border-radius: 25px;
    }

    /* Karakter sayacı */
    .char-counter {
        text-align: right;
        font-size: 0.85rem;
        color: #657786;
    }

    .char-ok { color: #17bf63; }
    .char-warn { color: #ffad1f; }
    .char-over { color: #e0245e; }

    /* Adım göstergesi */
    .step-indicator {
        background: linear-gradient(90deg, #1DA1F2, #17bf63);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }

    /* Görsel önizleme */
    .image-preview {
        border-radius: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session():
    """Session state başlat"""
    if "current_tweet" not in st.session_state:
        st.session_state.current_tweet = ""
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    if "selected_trend" not in st.session_state:
        st.session_state.selected_trend = None
    if "persona" not in st.session_state:
        st.session_state.persona = "Samimi, bilgili ve profesyonel bir üslup. Değerli içgörüler paylaşan biri."
    if "trends_cache" not in st.session_state:
        st.session_state.trends_cache = None


def get_trends():
    """Trendleri getir (cache ile)"""
    if st.session_state.trends_cache is None:
        with st.spinner("Trendler yükleniyor..."):
            st.session_state.trends_cache = trend_scraper.get_turkey_trends()
    return st.session_state.trends_cache


def generate_tweet_content(topic: str, tweet_type: str = "auto") -> dict:
    """Tweet içeriği oluştur"""

    # AI ile içerik oluştur
    if ai_writer.is_available:
        if tweet_type == "thread":
            result = ai_writer.generate_thread(
                topic=topic,
                num_tweets=4,
                persona=st.session_state.persona
            )
            return {
                "text": "\n\n---\n\n".join(result.thread_parts) if result.thread_parts else result.text,
                "hashtags": result.hashtags,
                "image_query": result.suggested_image_query,
                "is_thread": True,
                "thread_parts": result.thread_parts
            }
        else:
            result = ai_writer.generate_tweet(
                topic=topic,
                persona=st.session_state.persona
            )
            return {
                "text": result.text,
                "hashtags": result.hashtags,
                "image_query": result.suggested_image_query,
                "is_thread": False
            }
    else:
        # Demo mod (AI yoksa)
        return {
            "text": f"{topic} hakkında düşüncelerim:\n\nBu konu gündemde ve herkesin bir fikri var. Benim görüşüm ise farklı bir perspektiften bakılması gerektiği yönünde.\n\nSiz ne düşünüyorsunuz?",
            "hashtags": [topic.replace(" ", "").replace("#", ""), "Gündem"],
            "image_query": topic,
            "is_thread": False
        }


def render_header():
    """Başlık"""
    st.markdown('<p class="main-header">🐦 Tweet Oluşturucu</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gündem takibi • AI yazım • Copy-paste paylaşım</p>', unsafe_allow_html=True)


def render_step1_trends():
    """Adım 1: Trend seçimi"""
    st.markdown('<span class="step-indicator">1️⃣ Konu Seç</span>', unsafe_allow_html=True)

    # Konu seçim modu
    mode = st.radio(
        "Nasıl seçmek istersin?",
        ["🔥 Gündem'den Seç", "✍️ Kendi Konumu Yaz"],
        horizontal=True,
        label_visibility="collapsed"
    )

    topic = None

    if mode == "🔥 Gündem'den Seç":
        # Trendleri yükle
        trends = get_trends()

        # Yenile butonu
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄", help="Trendleri yenile"):
                st.session_state.trends_cache = None
                st.rerun()

        if trends:
            # Trend listesi
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

    else:  # Manuel konu
        topic = st.text_input(
            "Konu:",
            placeholder="Örn: Yapay Zeka, Kripto, Ekonomi...",
            label_visibility="collapsed"
        )
        st.session_state.selected_trend = topic

    return topic


def render_step2_generate(topic: str):
    """Adım 2: Tweet oluştur"""
    st.markdown("---")
    st.markdown('<span class="step-indicator">2️⃣ Tweet Oluştur</span>', unsafe_allow_html=True)

    # Tweet türü seçimi
    col1, col2 = st.columns(2)
    with col1:
        tweet_type = st.selectbox(
            "Tweet Türü",
            ["Normal Tweet", "Thread (Uzun)"],
            label_visibility="collapsed"
        )

    with col2:
        include_image = st.checkbox("📷 Görsel ekle", value=True)

    # Oluştur butonu
    if st.button("✨ Tweet Oluştur", type="primary", use_container_width=True):
        with st.spinner("AI düşünüyor..."):
            # Tweet oluştur
            result = generate_tweet_content(
                topic,
                "thread" if "Thread" in tweet_type else "auto"
            )

            # Hashtag'leri ekle
            text = result["text"]
            if result["hashtags"]:
                hashtags = " ".join([f"#{h}" for h in result["hashtags"][:3]])
                if len(text) + len(hashtags) + 2 <= 280 or result["is_thread"]:
                    text = f"{text}\n\n{hashtags}"

            st.session_state.current_tweet = text

            # Görsel bul
            if include_image and result.get("image_query"):
                image = image_finder.find_best_image(result["image_query"])
                if image:
                    st.session_state.current_image = image
                else:
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
        char_status = "⚠️"
    else:
        char_class = "char-over"
        char_status = "❌ Thread önerilir"

    st.markdown(f'<p class="char-counter {char_class}">{char_count}/280 {char_status}</p>', unsafe_allow_html=True)

    # Tweet önizleme ve düzenleme
    edited_tweet = st.text_area(
        "Tweet metni (düzenleyebilirsin):",
        value=tweet_text,
        height=200,
        label_visibility="collapsed",
        key="tweet_editor"
    )

    # Güncelleme
    if edited_tweet != tweet_text:
        st.session_state.current_tweet = edited_tweet

    # Kopyalama ipucu
    st.markdown("""
    <div class="copy-hint">
        💡 <b>Metni seç</b> → <b>Kopyala</b> → <b>X'e yapıştır</b>
    </div>
    """, unsafe_allow_html=True)

    # Görsel önizleme
    if st.session_state.current_image:
        st.markdown("---")
        st.markdown("**📷 Önerilen Görsel:**")

        image = st.session_state.current_image
        st.image(image.url, use_container_width=True)

        # Görsel indirme linki
        st.markdown(f"[📥 Görseli İndir]({image.download_url})")
        st.caption(f"Fotoğraf: {image.photographer} ({image.source})")

    # X'te paylaş butonu
    st.markdown("---")

    # Twitter intent URL oluştur
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

    st.caption("(Butona tıkla, X açılacak, tweet hazır olacak)")


def render_settings():
    """Ayarlar (sidebar)"""
    with st.sidebar:
        st.markdown("## ⚙️ Ayarlar")

        # AI Durumu
        if ai_writer.is_available:
            st.success(f"✓ AI: {ai_writer.provider}")
        else:
            st.warning("⚠️ AI API yok (demo mod)")
            st.caption("OpenAI veya Anthropic API key ekleyin")

        # Görsel API
        if image_finder.is_available:
            st.success("✓ Görsel API aktif")
        else:
            st.info("ℹ️ Görsel API yok (demo)")

        st.markdown("---")

        # Persona ayarı
        st.markdown("### 🎭 Üslup")
        new_persona = st.text_area(
            "Tweet'lerin nasıl bir üslupla yazılsın?",
            value=st.session_state.persona,
            height=100,
            label_visibility="collapsed"
        )
        if new_persona != st.session_state.persona:
            st.session_state.persona = new_persona

        st.markdown("---")

        # Yardım
        st.markdown("### 💡 İpuçları")
        st.markdown("""
        - **Reply** en değerli etkileşim (13.5x)
        - **İlk 30 dk** kritik
        - **Görsel** 3x etkileşim
        - **1-3 hashtag** optimal
        - En iyi saatler: 08:00, 12:00, 17:00, 21:00
        """)


def main():
    """Ana uygulama"""
    init_session()

    # Başlık
    render_header()

    # Sidebar (ayarlar)
    render_settings()

    # Adım 1: Konu seç
    topic = render_step1_trends()

    # Adım 2: Tweet oluştur (konu seçiliyse)
    if topic:
        render_step2_generate(topic)

    # Adım 3: Kopyala ve paylaş (tweet varsa)
    render_step3_copypost()

    # Footer
    st.markdown("---")
    st.caption("🐦 Twitter/X Growth Tool | Ücretsiz & API Gerektirmez")


if __name__ == "__main__":
    main()
