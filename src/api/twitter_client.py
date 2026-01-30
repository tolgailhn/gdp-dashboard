"""
Twitter/X API Client
====================

Twitter API v2 ile etkileşim için istemci sınıfı.
Trend analizi, tweet gönderme ve etkileşim takibi.

Kaynak: https://developer.x.com/en/docs/x-api
"""

import tweepy
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import time

import sys
sys.path.append(str(__file__).rsplit('/', 3)[0])
from config.settings import config

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Tweet veri sınıfı"""
    id: str
    text: str
    author_id: str
    author_username: str
    created_at: datetime
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    impression_count: int = 0
    url: str = ""

    @property
    def engagement_score(self) -> float:
        """Twitter algoritmasına göre etkileşim skoru hesapla"""
        weights = config.algorithm.engagement_weights
        return (
            self.like_count * weights["like"] +
            self.retweet_count * weights["retweet"] +
            self.reply_count * weights["reply"]
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "author_id": self.author_id,
            "author_username": self.author_username,
            "created_at": self.created_at.isoformat(),
            "like_count": self.like_count,
            "retweet_count": self.retweet_count,
            "reply_count": self.reply_count,
            "quote_count": self.quote_count,
            "impression_count": self.impression_count,
            "engagement_score": self.engagement_score,
            "url": self.url,
        }


@dataclass
class Trend:
    """Trend veri sınıfı"""
    name: str
    url: str
    tweet_volume: Optional[int]
    query: str

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "url": self.url,
            "tweet_volume": self.tweet_volume,
            "query": self.query,
        }


class TwitterClient:
    """
    Twitter/X API istemcisi

    Bu sınıf Twitter API v2 ile etkileşim sağlar:
    - Trend analizi
    - Tweet arama ve analiz
    - Tweet gönderme
    - Etkileşim takibi
    """

    def __init__(self):
        """Twitter API istemcisini başlat"""
        self.api_v1 = None
        self.client_v2 = None
        self._authenticated = False

        if config.twitter.is_configured():
            self._setup_clients()

    def _setup_clients(self):
        """API istemcilerini kur"""
        try:
            # OAuth 1.0a Authentication (v1.1 API için)
            auth = tweepy.OAuthHandler(
                config.twitter.api_key,
                config.twitter.api_secret
            )
            auth.set_access_token(
                config.twitter.access_token,
                config.twitter.access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

            # Twitter API v2 Client
            self.client_v2 = tweepy.Client(
                bearer_token=config.twitter.bearer_token,
                consumer_key=config.twitter.api_key,
                consumer_secret=config.twitter.api_secret,
                access_token=config.twitter.access_token,
                access_token_secret=config.twitter.access_token_secret,
                wait_on_rate_limit=True
            )

            self._authenticated = True
            logger.info("Twitter API bağlantısı başarılı")

        except Exception as e:
            logger.error(f"Twitter API bağlantı hatası: {e}")
            self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """API bağlantısının aktif olup olmadığını kontrol et"""
        return self._authenticated

    # ========================================================================
    # TREND ANALİZİ
    # ========================================================================

    def get_trends(self, woeid: int = None) -> List[Trend]:
        """
        Belirtilen konum için trendleri getir

        Args:
            woeid: Where On Earth ID (varsayılan: Türkiye)

        Returns:
            Trend listesi
        """
        if not self._authenticated:
            logger.warning("API bağlantısı yok, demo trend verisi döndürülüyor")
            return self._get_demo_trends()

        woeid = woeid or config.trend.default_woeid

        try:
            trends_response = self.api_v1.get_place_trends(woeid)

            trends = []
            for trend_data in trends_response[0]["trends"]:
                # Sponsorlu trendleri filtrele
                if config.trend.exclude_promoted and trend_data.get("promoted_content"):
                    continue

                # Minimum tweet hacmi kontrolü
                volume = trend_data.get("tweet_volume")
                if volume and volume < config.trend.min_tweet_volume:
                    continue

                trend = Trend(
                    name=trend_data["name"],
                    url=trend_data["url"],
                    tweet_volume=volume,
                    query=trend_data["query"]
                )
                trends.append(trend)

            # Hacme göre sırala (yüksekten düşüğe)
            trends.sort(key=lambda t: t.tweet_volume or 0, reverse=True)

            logger.info(f"{len(trends)} trend bulundu")
            return trends[:config.trend.trends_to_analyze]

        except Exception as e:
            logger.error(f"Trend getirme hatası: {e}")
            return self._get_demo_trends()

    def _get_demo_trends(self) -> List[Trend]:
        """Demo trend verisi (API yokken test için)"""
        return [
            Trend(name="#Teknoloji", url="", tweet_volume=50000, query="Teknoloji"),
            Trend(name="#Yapay Zeka", url="", tweet_volume=35000, query="Yapay Zeka"),
            Trend(name="#Ekonomi", url="", tweet_volume=28000, query="Ekonomi"),
            Trend(name="#Spor", url="", tweet_volume=45000, query="Spor"),
            Trend(name="#Gündem", url="", tweet_volume=60000, query="Gündem"),
        ]

    # ========================================================================
    # TWEET ARAMA VE ANALİZ
    # ========================================================================

    def search_tweets(
        self,
        query: str,
        max_results: int = 100,
        sort_by_engagement: bool = True
    ) -> List[Tweet]:
        """
        Tweet ara ve analiz et

        Args:
            query: Arama sorgusu
            max_results: Maksimum sonuç sayısı
            sort_by_engagement: Etkileşime göre sırala

        Returns:
            Tweet listesi
        """
        if not self._authenticated:
            logger.warning("API bağlantısı yok")
            return []

        try:
            # API v2 ile arama
            response = self.client_v2.search_recent_tweets(
                query=f"{query} -is:retweet lang:tr",
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics", "author_id"],
                user_fields=["username"],
                expansions=["author_id"]
            )

            if not response.data:
                return []

            # Kullanıcı bilgilerini eşleştir
            users = {u.id: u for u in response.includes.get("users", [])}

            tweets = []
            for tweet_data in response.data:
                metrics = tweet_data.public_metrics or {}
                author = users.get(tweet_data.author_id)

                tweet = Tweet(
                    id=str(tweet_data.id),
                    text=tweet_data.text,
                    author_id=str(tweet_data.author_id),
                    author_username=author.username if author else "unknown",
                    created_at=tweet_data.created_at,
                    like_count=metrics.get("like_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    reply_count=metrics.get("reply_count", 0),
                    quote_count=metrics.get("quote_count", 0),
                    impression_count=metrics.get("impression_count", 0),
                    url=f"https://twitter.com/{author.username if author else 'i'}/status/{tweet_data.id}"
                )
                tweets.append(tweet)

            if sort_by_engagement:
                tweets.sort(key=lambda t: t.engagement_score, reverse=True)

            logger.info(f"'{query}' için {len(tweets)} tweet bulundu")
            return tweets

        except Exception as e:
            logger.error(f"Tweet arama hatası: {e}")
            return []

    def get_top_engaging_tweets(
        self,
        topic: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Tweet]:
        """
        Bir konu hakkında en çok etkileşim alan tweetleri getir

        Args:
            topic: Konu
            hours: Kaç saatlik tweetler
            limit: Maksimum tweet sayısı

        Returns:
            En çok etkileşim alan tweetler
        """
        tweets = self.search_tweets(topic, max_results=100, sort_by_engagement=True)
        return tweets[:limit]

    def analyze_trend_content(self, trend: Trend) -> Dict[str, Any]:
        """
        Bir trend hakkında içerik analizi yap

        Args:
            trend: Analiz edilecek trend

        Returns:
            Analiz sonuçları
        """
        tweets = self.search_tweets(trend.query, max_results=100)

        if not tweets:
            return {
                "trend": trend.to_dict(),
                "analysis": {
                    "total_tweets": 0,
                    "avg_engagement": 0,
                    "top_tweets": [],
                    "common_keywords": [],
                    "sentiment": "neutral"
                }
            }

        # Temel analiz
        total_engagement = sum(t.engagement_score for t in tweets)
        avg_engagement = total_engagement / len(tweets) if tweets else 0

        # En iyi 5 tweet
        top_tweets = [t.to_dict() for t in tweets[:5]]

        return {
            "trend": trend.to_dict(),
            "analysis": {
                "total_tweets": len(tweets),
                "avg_engagement": round(avg_engagement, 2),
                "top_tweets": top_tweets,
                "total_likes": sum(t.like_count for t in tweets),
                "total_retweets": sum(t.retweet_count for t in tweets),
                "total_replies": sum(t.reply_count for t in tweets),
            }
        }

    # ========================================================================
    # TWEET GÖNDERME
    # ========================================================================

    def post_tweet(
        self,
        text: str,
        media_ids: List[str] = None,
        reply_to: str = None
    ) -> Optional[str]:
        """
        Tweet gönder

        Args:
            text: Tweet metni
            media_ids: Medya ID'leri (görseller)
            reply_to: Yanıtlanacak tweet ID'si

        Returns:
            Gönderilen tweet ID'si veya None
        """
        if not self._authenticated:
            logger.error("API bağlantısı yok, tweet gönderilemedi")
            return None

        try:
            # Tweet gönder
            response = self.client_v2.create_tweet(
                text=text,
                media_ids=media_ids,
                in_reply_to_tweet_id=reply_to
            )

            tweet_id = str(response.data["id"])
            logger.info(f"Tweet gönderildi: {tweet_id}")
            return tweet_id

        except Exception as e:
            logger.error(f"Tweet gönderme hatası: {e}")
            return None

    def post_thread(self, tweets: List[str], media_ids_list: List[List[str]] = None) -> List[str]:
        """
        Thread (tweet zinciri) gönder

        Args:
            tweets: Tweet metinleri listesi
            media_ids_list: Her tweet için medya ID'leri

        Returns:
            Gönderilen tweet ID'leri
        """
        if not tweets:
            return []

        posted_ids = []
        reply_to = None

        for i, text in enumerate(tweets):
            media_ids = media_ids_list[i] if media_ids_list and i < len(media_ids_list) else None

            tweet_id = self.post_tweet(text, media_ids, reply_to)

            if tweet_id:
                posted_ids.append(tweet_id)
                reply_to = tweet_id
                time.sleep(1)  # Rate limiting için kısa bekleme
            else:
                logger.error(f"Thread tweet {i+1} gönderilemedi")
                break

        return posted_ids

    # ========================================================================
    # MEDYA YÜKLEME
    # ========================================================================

    def upload_media(self, file_path: str) -> Optional[str]:
        """
        Medya dosyası yükle

        Args:
            file_path: Dosya yolu

        Returns:
            Medya ID'si veya None
        """
        if not self._authenticated:
            logger.error("API bağlantısı yok")
            return None

        try:
            media = self.api_v1.media_upload(file_path)
            logger.info(f"Medya yüklendi: {media.media_id_string}")
            return media.media_id_string

        except Exception as e:
            logger.error(f"Medya yükleme hatası: {e}")
            return None

    # ========================================================================
    # KULLANICI BİLGİLERİ
    # ========================================================================

    def get_me(self) -> Optional[Dict]:
        """Bağlı hesap bilgilerini getir"""
        if not self._authenticated:
            return None

        try:
            user = self.client_v2.get_me(
                user_fields=["public_metrics", "description", "created_at"]
            )

            if user.data:
                metrics = user.data.public_metrics or {}
                return {
                    "id": str(user.data.id),
                    "username": user.data.username,
                    "name": user.data.name,
                    "followers_count": metrics.get("followers_count", 0),
                    "following_count": metrics.get("following_count", 0),
                    "tweet_count": metrics.get("tweet_count", 0),
                }
            return None

        except Exception as e:
            logger.error(f"Kullanıcı bilgisi hatası: {e}")
            return None

    def get_my_recent_tweets(self, limit: int = 10) -> List[Tweet]:
        """Son gönderilen tweetleri getir"""
        if not self._authenticated:
            return []

        try:
            me = self.get_me()
            if not me:
                return []

            response = self.client_v2.get_users_tweets(
                id=me["id"],
                max_results=min(limit, 100),
                tweet_fields=["created_at", "public_metrics"]
            )

            if not response.data:
                return []

            tweets = []
            for tweet_data in response.data:
                metrics = tweet_data.public_metrics or {}
                tweet = Tweet(
                    id=str(tweet_data.id),
                    text=tweet_data.text,
                    author_id=me["id"],
                    author_username=me["username"],
                    created_at=tweet_data.created_at,
                    like_count=metrics.get("like_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    reply_count=metrics.get("reply_count", 0),
                    quote_count=metrics.get("quote_count", 0),
                    impression_count=metrics.get("impression_count", 0),
                    url=f"https://twitter.com/{me['username']}/status/{tweet_data.id}"
                )
                tweets.append(tweet)

            return tweets

        except Exception as e:
            logger.error(f"Tweet getirme hatası: {e}")
            return []


# Singleton instance
twitter_client = TwitterClient()
