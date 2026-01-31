"""
Twitter/X Growth Automation - Ayarlar
=====================================

Bu dosya tüm yapılandırma ayarlarını içerir.
Twitter algoritmasına göre optimize edilmiş varsayılan değerler kullanılmıştır.

Kaynak: https://github.com/twitter/the-algorithm
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

# Proje kök dizini
BASE_DIR = Path(__file__).parent.parent


def get_secret(key: str, default: str = "") -> str:
    """
    Hem environment variables hem de Streamlit secrets'dan değer al.
    Streamlit Cloud için secrets.toml desteği.
    """
    # Önce environment variable'dan dene
    value = os.getenv(key, "")
    if value:
        return value

    # Sonra Streamlit secrets'dan dene
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass

    return default

# ============================================================================
# TWITTER/X API AYARLARI
# ============================================================================

@dataclass
class TwitterAPIConfig:
    """Twitter/X API yapılandırması"""

    # API Anahtarları (environment variables veya Streamlit secrets'dan alınır)
    api_key: str = field(default_factory=lambda: get_secret("TWITTER_API_KEY"))
    api_secret: str = field(default_factory=lambda: get_secret("TWITTER_API_SECRET"))
    access_token: str = field(default_factory=lambda: get_secret("TWITTER_ACCESS_TOKEN"))
    access_token_secret: str = field(default_factory=lambda: get_secret("TWITTER_ACCESS_TOKEN_SECRET"))
    bearer_token: str = field(default_factory=lambda: get_secret("TWITTER_BEARER_TOKEN"))

    # API Versiyonu
    api_version: str = "2"  # v2 API kullanıyoruz

    # Rate Limiting
    requests_per_15_min: int = 450  # Premium tier limiti

    def is_configured(self) -> bool:
        """API anahtarlarının ayarlanıp ayarlanmadığını kontrol et"""
        return all([
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret
        ])


# ============================================================================
# AI İÇERİK OLUŞTURMA AYARLARI
# ============================================================================

@dataclass
class AIConfig:
    """AI içerik oluşturma yapılandırması"""

    # Google Gemini API (ÜCRETSİZ - Varsayılan)
    gemini_api_key: str = field(default_factory=lambda: get_secret("GEMINI_API_KEY"))
    gemini_model: str = "gemini-1.5-flash"  # Ücretsiz ve hızlı model

    # OpenAI API (GPT)
    openai_api_key: str = field(default_factory=lambda: get_secret("OPENAI_API_KEY"))
    openai_model: str = "gpt-4-turbo-preview"

    # Anthropic API (Claude)
    anthropic_api_key: str = field(default_factory=lambda: get_secret("ANTHROPIC_API_KEY"))
    anthropic_model: str = "claude-3-opus-20240229"

    # Varsayılan AI sağlayıcı (Gemini ücretsiz olduğu için varsayılan)
    default_provider: str = "gemini"  # "gemini", "openai" veya "anthropic"

    # İçerik oluşturma parametreleri
    max_tokens: int = 500
    temperature: float = 0.7  # Yaratıcılık seviyesi (0-1)

    def get_active_provider(self) -> str:
        """Aktif AI sağlayıcısını döndür"""
        # Önce Gemini'yi dene (ücretsiz)
        if self.gemini_api_key:
            return "gemini"
        # Sonra varsayılan sağlayıcıya bak
        if self.default_provider == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        elif self.default_provider == "openai" and self.openai_api_key:
            return "openai"
        # Herhangi birini dene
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "none"


# ============================================================================
# GÖRSEL ARAMA AYARLARI
# ============================================================================

@dataclass
class ImageConfig:
    """Görsel arama yapılandırması"""

    # Unsplash API
    unsplash_access_key: str = field(default_factory=lambda: get_secret("UNSPLASH_ACCESS_KEY"))

    # Pexels API
    pexels_api_key: str = field(default_factory=lambda: get_secret("PEXELS_API_KEY"))

    # Görsel ayarları
    default_image_width: int = 1200
    default_image_height: int = 675  # Twitter optimal oranı 16:9
    images_per_search: int = 5

    # Görsel kaydetme dizini
    images_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "images")


# ============================================================================
# TWITTER ALGORİTMASI OPTİMİZASYON AYARLARI
# ============================================================================
# Kaynak: https://github.com/twitter/the-algorithm
# https://blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm

@dataclass
class AlgorithmConfig:
    """Twitter algoritması optimizasyon ayarları"""

    # Etkileşim ağırlıkları (Twitter'ın açık kaynak kodundan)
    # Beğeni: 0.5, Retweet: 1.0, Reply: 13.5, Profil tıklama: 12.0
    engagement_weights: Dict[str, float] = field(default_factory=lambda: {
        "like": 0.5,
        "retweet": 1.0,
        "reply": 13.5,
        "profile_click": 12.0,
        "url_click": 1.5,
        "video_playback_50": 0.05,
    })

    # En iyi paylaşım saatleri (UTC)
    # Twitter araştırmalarına göre optimize edilmiş
    optimal_posting_hours_utc: List[int] = field(default_factory=lambda: [
        9, 12, 15, 17, 20  # 09:00, 12:00, 15:00, 17:00, 20:00 UTC
    ])

    # Türkiye için en iyi saatler (UTC+3)
    optimal_posting_hours_turkey: List[int] = field(default_factory=lambda: [
        8, 12, 13, 17, 19, 21  # Sabah, öğle, akşam
    ])

    # Günlük maksimum tweet sayısı
    max_tweets_per_day: int = 5

    # İlk 30 dakika kritik - erken etkileşim önemli
    critical_engagement_window_minutes: int = 30

    # Tweet türü dağılımı (günlük)
    tweet_type_distribution: Dict[str, float] = field(default_factory=lambda: {
        "original": 0.4,      # %40 orijinal içerik
        "trending": 0.3,      # %30 gündem hakkında
        "engagement": 0.2,    # %20 etkileşim odaklı (sorular, anketler)
        "thread": 0.1,        # %10 thread
    })

    # Karakter limitleri
    short_tweet_max_chars: int = 140  # Kısa tweet
    medium_tweet_max_chars: int = 200  # Orta tweet
    long_tweet_max_chars: int = 280   # Uzun tweet

    # Hashtag ayarları
    max_hashtags: int = 3  # Twitter'a göre 1-3 hashtag optimal
    min_hashtags: int = 1


# ============================================================================
# TREND ANALİZİ AYARLARI
# ============================================================================

@dataclass
class TrendConfig:
    """Trend analizi yapılandırması"""

    # Türkiye WOEID (Where On Earth ID)
    turkey_woeid: int = 23424969
    istanbul_woeid: int = 2344116
    ankara_woeid: int = 2323778

    # Varsayılan konum
    default_woeid: int = 23424969  # Türkiye

    # Trend güncelleme sıklığı (dakika)
    update_interval_minutes: int = 15

    # Analiz edilecek trend sayısı
    trends_to_analyze: int = 10

    # Trend filtreleme
    exclude_promoted: bool = True  # Sponsorlu trendleri hariç tut
    min_tweet_volume: int = 1000   # Minimum tweet hacmi


# ============================================================================
# ZAMANLAMA AYARLARI
# ============================================================================

@dataclass
class SchedulerConfig:
    """Tweet zamanlama yapılandırması"""

    # Zaman dilimi
    timezone: str = "Europe/Istanbul"

    # Minimum bekleme süresi (tweet arası, dakika)
    min_interval_minutes: int = 60

    # Maksimum bekleme süresi (dakika)
    max_interval_minutes: int = 240

    # Gece paylaşımı (23:00 - 06:00)
    enable_night_posting: bool = False
    night_start_hour: int = 23
    night_end_hour: int = 6

    # Hafta sonu ayarları
    weekend_posting_enabled: bool = True
    weekend_reduced_frequency: bool = True  # Hafta sonu daha az paylaşım


# ============================================================================
# LOGLAMA VE VERİTABANI AYARLARI
# ============================================================================

@dataclass
class LogConfig:
    """Loglama yapılandırması"""

    log_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_log_size_mb: int = 10
    backup_count: int = 5


@dataclass
class DatabaseConfig:
    """Veritabanı yapılandırması (SQLite)"""

    db_path: Path = field(default_factory=lambda: BASE_DIR / "data" / "twitter_growth.db")


# ============================================================================
# ANA YAPILANDIRMA SINIFI
# ============================================================================

@dataclass
class Config:
    """Tüm yapılandırmaları birleştiren ana sınıf"""

    twitter: TwitterAPIConfig = field(default_factory=TwitterAPIConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    trend: TrendConfig = field(default_factory=TrendConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    log: LogConfig = field(default_factory=LogConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    def validate(self) -> Dict[str, bool]:
        """Tüm yapılandırmaları doğrula"""
        return {
            "twitter_api": self.twitter.is_configured(),
            "ai_provider": self.ai.get_active_provider() != "none",
            "image_api": bool(self.image.unsplash_access_key or self.image.pexels_api_key),
        }


# Varsayılan yapılandırma örneği
config = Config()
