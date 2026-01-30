"""
Twitter/X Growth Dashboard
==========================

Streamlit ile interaktif kontrol paneli.
Tweet oluşturma, zamanlama ve analiz.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import config
from src.automation_engine import TwitterGrowthEngine, AutomationResult
from src.api.twitter_client import twitter_client
from src.content.ai_writer import ai_writer, TweetType
from src.content.image_finder import image_finder
from src.scheduler.scheduler import scheduler, TweetStatus

# Sayfa yapılandırması
st.set_page_config(
    page_title="Twitter/X Growth Dashboard",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1DA1F2;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .tweet-preview {
        background: #f7f9fa;
        border: 1px solid #e1e8ed;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-msg {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 10px;
        border-radius: 5px;
        color: #155724;
    }
    .warning-msg {
        background: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 10px;
        border-radius: 5px;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Session state'i başlat"""
    if "engine" not in st.session_state:
        st.session_state.engine = TwitterGrowthEngine()

    if "generated_tweet" not in st.session_state:
        st.session_state.generated_tweet = None

    if "preview_image" not in st.session_state:
        st.session_state.preview_image = None


def render_sidebar():
    """Sidebar menüsü"""
    with st.sidebar:
        st.markdown("## 🐦 Twitter Growth")
        st.markdown("---")

        # API Durumu
        st.markdown("### 📡 Bağlantı Durumu")

        col1, col2 = st.columns(2)
        with col1:
            if twitter_client.is_authenticated:
                st.success("Twitter API ✓")
            else:
                st.warning("Twitter API ✗")

        with col2:
            if ai_writer.is_available:
                st.success("AI API ✓")
            else:
                st.warning("AI API ✗")

        # Günlük istatistikler
        st.markdown("---")
        st.markdown("### 📊 Bugünkü Durum")

        stats = scheduler.get_stats()
        st.metric("Zamanlanmış", stats["scheduled"])
        st.metric("Gönderildi", stats["posted"])
        st.metric("Kalan Limit", f"{stats['remaining_today']}/{stats['daily_limit']}")

        # Otomasyon kontrolü
        st.markdown("---")
        st.markdown("### 🤖 Otomasyon")

        if st.button("▶️ Otomasyonu Başlat", use_container_width=True):
            st.session_state.engine.start_automation()
            st.success("Otomasyon başlatıldı!")

        if st.button("⏹️ Otomasyonu Durdur", use_container_width=True):
            st.session_state.engine.stop_automation()
            st.info("Otomasyon durduruldu.")

        # Ayarlar linki
        st.markdown("---")
        st.markdown("### ⚙️ Hızlı Ayarlar")
        st.text_input("Persona/Üslup", value=st.session_state.engine.persona, key="persona_input")


def render_main_content():
    """Ana içerik alanı"""

    # Tab'lar
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚀 Tweet Oluştur",
        "📅 Zamanlanmış",
        "📈 Trendler",
        "📊 Analiz",
        "⚙️ Ayarlar"
    ])

    # TAB 1: Tweet Oluştur
    with tab1:
        render_tweet_generator()

    # TAB 2: Zamanlanmış Tweetler
    with tab2:
        render_scheduled_tweets()

    # TAB 3: Trend Analizi
    with tab3:
        render_trends()

    # TAB 4: Analiz
    with tab4:
        render_analytics()

    # TAB 5: Ayarlar
    with tab5:
        render_settings()


def render_tweet_generator():
    """Tweet oluşturma arayüzü"""

    st.markdown("## 🚀 Yeni Tweet Oluştur")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Konu seçimi
        topic_mode = st.radio(
            "Konu Seçimi",
            ["📌 Manuel Konu", "🔥 Trending'den Seç", "🎲 Rastgele Trend"],
            horizontal=True
        )

        topic = None
        if topic_mode == "📌 Manuel Konu":
            topic = st.text_input("Konu girin:", placeholder="Örn: Yapay Zeka, Teknoloji, Ekonomi...")
        elif topic_mode == "🔥 Trending'den Seç":
            trends = twitter_client.get_trends()
            if trends:
                trend_options = [f"{t.name} ({t.tweet_volume or '?'} tweet)" for t in trends]
                selected = st.selectbox("Trend seçin:", trend_options)
                if selected:
                    idx = trend_options.index(selected)
                    topic = trends[idx].name

        # Tweet türü
        tweet_type = st.selectbox(
            "Tweet Türü",
            ["Otomatik Seç", "Bilgilendirici", "Görüş/Yorum", "Soru", "Eğitici", "Thread"]
        )

        # Görsel seçeneği
        include_image = st.checkbox("Görsel ekle", value=True)

        # Oluştur butonu
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("✨ Tweet Oluştur", type="primary", use_container_width=True):
                with st.spinner("İçerik oluşturuluyor..."):
                    if tweet_type == "Thread":
                        result = st.session_state.engine.create_thread(
                            topic=topic or "Teknoloji",
                            include_image=include_image,
                            auto_post=False
                        )
                    else:
                        result = st.session_state.engine.auto_generate_and_schedule(
                            topic=topic,
                            use_trending=(topic_mode != "📌 Manuel Konu"),
                            include_image=include_image,
                            auto_post=False
                        )

                    if result.success:
                        st.session_state.generated_tweet = result
                        st.session_state.preview_image = result.image
                        st.success("Tweet oluşturuldu ve zamanlandı!")
                    else:
                        st.error(f"Hata: {result.error}")

        with col_btn2:
            if st.button("👁️ Önizle", use_container_width=True):
                with st.spinner("Önizleme hazırlanıyor..."):
                    preview = st.session_state.engine.preview_content(topic)
                    st.session_state.generated_tweet = preview

    # Önizleme alanı
    with col2:
        st.markdown("### 📱 Önizleme")

        if st.session_state.generated_tweet:
            result = st.session_state.generated_tweet

            # Tweet kartı
            st.markdown('<div class="tweet-preview">', unsafe_allow_html=True)

            if isinstance(result, dict):
                # Preview dict
                st.markdown(f"**{result.get('tweet_text', '')}**")
                if result.get('hashtags'):
                    st.caption(f"Hashtag'ler: {', '.join(['#'+h for h in result['hashtags']])}")
                if result.get('image_url'):
                    st.image(result['image_url'], use_container_width=True)
                st.caption(f"Önerilen zaman: {result.get('suggested_time', '')}")
            else:
                # AutomationResult
                if result.tweet:
                    st.markdown(f"**{result.tweet.text}**")
                    if result.tweet.hashtags:
                        st.caption(f"Hashtag'ler: {', '.join(['#'+h for h in result.tweet.hashtags])}")
                if result.image and result.image.url:
                    st.image(result.image.url, use_container_width=True)
                if result.scheduled:
                    st.caption(f"Zamanlandı: {result.scheduled.scheduled_time}")

            st.markdown('</div>', unsafe_allow_html=True)

            # Düzenleme seçenekleri
            if st.button("🗑️ Zamanlamayı İptal Et"):
                if hasattr(result, 'scheduled') and result.scheduled:
                    scheduler.cancel_tweet(result.scheduled.id)
                    st.session_state.generated_tweet = None
                    st.info("Tweet iptal edildi.")
                    st.rerun()


def render_scheduled_tweets():
    """Zamanlanmış tweetler listesi"""

    st.markdown("## 📅 Zamanlanmış Tweetler")

    pending = scheduler.get_pending_tweets()

    if not pending:
        st.info("Henüz zamanlanmış tweet yok. 'Tweet Oluştur' sekmesinden yeni içerik oluşturabilirsiniz.")
        return

    for tweet in pending:
        with st.expander(f"🕐 {tweet.scheduled_time.strftime('%H:%M')} - {tweet.text[:50]}..."):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Tweet:**\n{tweet.text}")
                if tweet.hashtags:
                    st.caption(f"Hashtag'ler: {', '.join(['#'+h for h in tweet.hashtags])}")
                if tweet.topic:
                    st.caption(f"Konu: {tweet.topic}")

            with col2:
                st.caption(f"Durum: {tweet.status.value}")
                st.caption(f"Oluşturulma: {tweet.created_at.strftime('%d/%m %H:%M')}")

                if st.button("❌ İptal", key=f"cancel_{tweet.id}"):
                    scheduler.cancel_tweet(tweet.id)
                    st.success("Tweet iptal edildi.")
                    st.rerun()


def render_trends():
    """Trend analizi"""

    st.markdown("## 📈 Güncel Trendler")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("🔄 Trendleri Güncelle", use_container_width=True):
            st.session_state.trends_updated = True

        trends = twitter_client.get_trends()

        if trends:
            # Trend tablosu
            trend_data = []
            for t in trends:
                trend_data.append({
                    "Trend": t.name,
                    "Tweet Sayısı": f"{t.tweet_volume:,}" if t.tweet_volume else "Bilinmiyor",
                })

            df = pd.DataFrame(trend_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Trend verisi alınamadı.")

    with col2:
        st.markdown("### 💡 İpuçları")
        st.info("""
        **Twitter Algoritması:**
        - İlk 30 dakika kritik
        - Reply'lar en değerli etkileşim
        - Görsel içerik 3x daha fazla etkileşim
        - 1-3 hashtag optimal
        """)


def render_analytics():
    """Analiz ve istatistikler"""

    st.markdown("## 📊 Hesap Analizi")

    # Hesap bilgileri
    me = twitter_client.get_me()

    if me:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Takipçi", f"{me.get('followers_count', 0):,}")
        with col2:
            st.metric("Takip", f"{me.get('following_count', 0):,}")
        with col3:
            st.metric("Tweet", f"{me.get('tweet_count', 0):,}")
        with col4:
            ratio = me.get('followers_count', 0) / max(me.get('following_count', 1), 1)
            st.metric("Takipçi/Takip", f"{ratio:.2f}")

    else:
        st.warning("Hesap bilgisi alınamadı. API bağlantısını kontrol edin.")

    st.markdown("---")

    # Scheduler istatistikleri
    st.markdown("### 📅 Zamanlama İstatistikleri")
    stats = scheduler.get_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Toplam Zamanlanmış", stats["total_scheduled"])
    with col2:
        st.metric("Başarılı Gönderim", stats["posted"])
    with col3:
        st.metric("Başarısız", stats["failed"])


def render_settings():
    """Ayarlar sayfası"""

    st.markdown("## ⚙️ Ayarlar")

    # API Ayarları
    st.markdown("### 🔑 API Anahtarları")
    st.info("API anahtarları .env dosyasından okunur. Güvenlik için bu dosyayı düzenleyin.")

    with st.expander("API Durumunu Göster"):
        config_check = config.validate()
        for key, value in config_check.items():
            if value:
                st.success(f"✓ {key}")
            else:
                st.error(f"✗ {key}")

    # Tweet Ayarları
    st.markdown("### 📝 Tweet Ayarları")

    col1, col2 = st.columns(2)

    with col1:
        max_tweets = st.slider(
            "Günlük Maksimum Tweet",
            min_value=1,
            max_value=10,
            value=config.algorithm.max_tweets_per_day
        )

        max_hashtags = st.slider(
            "Maksimum Hashtag",
            min_value=0,
            max_value=5,
            value=config.algorithm.max_hashtags
        )

    with col2:
        night_posting = st.checkbox(
            "Gece Paylaşımı (23:00-06:00)",
            value=config.scheduler.enable_night_posting
        )

        weekend_posting = st.checkbox(
            "Hafta Sonu Paylaşımı",
            value=config.scheduler.weekend_posting_enabled
        )

    # Optimal saatler
    st.markdown("### ⏰ Optimal Paylaşım Saatleri")
    st.caption("Twitter araştırmalarına göre en iyi saatler")

    hours = config.algorithm.optimal_posting_hours_turkey
    st.multiselect(
        "Saatler (Türkiye)",
        options=list(range(0, 24)),
        default=hours,
        format_func=lambda x: f"{x:02d}:00"
    )

    # Persona
    st.markdown("### 🎭 Üslup/Persona")
    persona = st.text_area(
        "Tweet üslubunuzu tanımlayın:",
        value=st.session_state.engine.persona,
        height=100
    )

    if st.button("💾 Ayarları Kaydet"):
        st.session_state.engine.persona = persona
        st.success("Ayarlar kaydedildi!")


def main():
    """Ana uygulama"""

    # Session state'i başlat
    init_session_state()

    # Header
    st.markdown('<p class="main-header">🐦 Twitter/X Growth Dashboard</p>', unsafe_allow_html=True)
    st.caption("Otomatik tweet oluşturma, zamanlama ve hesap büyütme aracı")

    # Sidebar
    render_sidebar()

    # Ana içerik
    render_main_content()

    # Footer
    st.markdown("---")
    st.caption("Twitter/X Growth Automation Tool | Twitter Algoritmasına Göre Optimize Edilmiş")


if __name__ == "__main__":
    main()
