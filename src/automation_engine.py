"""
Twitter/X Growth Automation Engine
==================================

Tüm modülleri birleştiren ana otomasyon motoru.
Tek komutla: trend analizi -> içerik oluşturma -> görsel bulma -> tweet gönderme

Özellikler:
- Tam otomatik mod
- Manuel onay modu
- Thread oluşturma
- Günlük rutin
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

import sys
sys.path.append(str(__file__).rsplit('/', 2)[0])

from config.settings import config
from src.api.twitter_client import twitter_client, Tweet, Trend
from src.content.ai_writer import ai_writer, GeneratedTweet, TweetType, TweetLength
from src.content.image_finder import image_finder, ImageResult
from src.scheduler.scheduler import scheduler, ScheduledTweet, TweetStatus

logger = logging.getLogger(__name__)


@dataclass
class AutomationResult:
    """Otomasyon sonucu"""
    success: bool
    tweet: Optional[GeneratedTweet] = None
    image: Optional[ImageResult] = None
    scheduled: Optional[ScheduledTweet] = None
    posted_id: Optional[str] = None
    error: Optional[str] = None
    trend: Optional[Trend] = None

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "tweet": self.tweet.to_dict() if self.tweet else None,
            "image": self.image.to_dict() if self.image else None,
            "scheduled": self.scheduled.to_dict() if self.scheduled else None,
            "posted_id": self.posted_id,
            "error": self.error,
            "trend": self.trend.to_dict() if self.trend else None,
        }


class TwitterGrowthEngine:
    """
    Twitter/X Hesap Büyütme Otomasyon Motoru

    Bu sınıf tüm otomasyon işlemlerini koordine eder:
    1. Trend analizi yapar
    2. En iyi konuları seçer
    3. AI ile içerik oluşturur
    4. Uygun görsel bulur
    5. Tweet'i zamanlar veya hemen gönderir
    """

    def __init__(self, persona: str = None):
        """
        Motoru başlat

        Args:
            persona: Tweet üslubu/kişiliği
        """
        self.persona = persona or "Bilgili, samimi ve profesyonel. Değerli içgörüler paylaşan bir uzman."
        self.twitter = twitter_client
        self.ai = ai_writer
        self.images = image_finder
        self.scheduler = scheduler

        # Durumu logla
        self._log_status()

    def _log_status(self):
        """Modül durumlarını logla"""
        logger.info("=" * 50)
        logger.info("Twitter Growth Engine Başlatıldı")
        logger.info(f"Twitter API: {'Bağlı' if self.twitter.is_authenticated else 'Bağlı Değil (Demo Mod)'}")
        logger.info(f"AI Provider: {self.ai.provider or 'Yok (Demo Mod)'}")
        logger.info(f"Image API: {'Mevcut' if self.images.is_available else 'Yok (Demo Mod)'}")
        logger.info("=" * 50)

    # ========================================================================
    # ANA OTOMASYON FONKSİYONLARI
    # ========================================================================

    def auto_generate_and_schedule(
        self,
        topic: str = None,
        use_trending: bool = True,
        include_image: bool = True,
        auto_post: bool = False
    ) -> AutomationResult:
        """
        Tam otomatik tweet oluştur ve zamanla

        Args:
            topic: Konu (None ise trending'den seç)
            use_trending: Trending konuları kullan
            include_image: Görsel ekle
            auto_post: Hemen gönder (False = zamanla)

        Returns:
            Otomasyon sonucu
        """
        try:
            # 1. Konu seç
            selected_topic = topic
            trend = None

            if not selected_topic and use_trending:
                trend = self._select_best_trend()
                if trend:
                    selected_topic = trend.name
                    logger.info(f"Trend seçildi: {selected_topic}")

            if not selected_topic:
                return AutomationResult(
                    success=False,
                    error="Konu bulunamadı"
                )

            # 2. Trend hakkında bağlam topla
            context = ""
            top_tweets = []
            if trend:
                analysis = self.twitter.analyze_trend_content(trend)
                top_tweets = analysis.get("analysis", {}).get("top_tweets", [])
                context = f"Gündemde {trend.tweet_volume or 'binlerce'} tweet var."

            # 3. AI ile içerik oluştur
            if trend:
                generated = self.ai.generate_trending_tweet(
                    trend_name=selected_topic,
                    trend_context=context,
                    top_tweets=top_tweets,
                    persona=self.persona
                )
            else:
                generated = self.ai.generate_tweet(
                    topic=selected_topic,
                    context=context,
                    persona=self.persona
                )

            logger.info(f"Tweet oluşturuldu: {generated.text[:50]}...")

            # 4. Görsel bul
            image = None
            image_path = None
            if include_image and generated.suggested_image_query:
                image = self.images.find_best_image(generated.suggested_image_query)
                if image:
                    image_path = self.images.download_image(image)
                    logger.info(f"Görsel indirildi: {image_path}")

            # 5. Tweet metnini hashtag'lerle birleştir
            final_text = self._build_final_tweet(generated)

            # 6. Zamanla veya gönder
            if auto_post:
                posted_id = self._post_now(final_text, image_path)
                return AutomationResult(
                    success=posted_id is not None,
                    tweet=generated,
                    image=image,
                    posted_id=posted_id,
                    trend=trend,
                    error=None if posted_id else "Gönderim başarısız"
                )
            else:
                scheduled = self.scheduler.schedule_tweet(
                    text=final_text,
                    media_path=image_path,
                    topic=selected_topic,
                    hashtags=generated.hashtags
                )
                return AutomationResult(
                    success=True,
                    tweet=generated,
                    image=image,
                    scheduled=scheduled,
                    trend=trend
                )

        except Exception as e:
            logger.error(f"Otomasyon hatası: {e}")
            return AutomationResult(success=False, error=str(e))

    def generate_daily_content(
        self,
        num_tweets: int = None,
        topics: List[str] = None
    ) -> List[AutomationResult]:
        """
        Günlük içerik planı oluştur

        Args:
            num_tweets: Oluşturulacak tweet sayısı
            topics: Konu listesi (None ise trending)

        Returns:
            Otomasyon sonuçları listesi
        """
        num_tweets = num_tweets or config.algorithm.max_tweets_per_day
        results = []

        # Kalan günlük limit
        remaining = self.scheduler.get_stats()["remaining_today"]
        num_tweets = min(num_tweets, remaining)

        if num_tweets <= 0:
            logger.warning("Günlük tweet limiti doldu")
            return results

        # Konuları belirle
        if not topics:
            trends = self.twitter.get_trends()
            topics = [t.name for t in trends[:num_tweets]]

        # Her konu için içerik oluştur
        for i, topic in enumerate(topics[:num_tweets]):
            logger.info(f"[{i+1}/{num_tweets}] İçerik oluşturuluyor: {topic}")

            result = self.auto_generate_and_schedule(
                topic=topic,
                use_trending=False,
                include_image=(i == 0),  # Sadece ilk tweet'e görsel
                auto_post=False
            )

            results.append(result)

            if not result.success:
                logger.warning(f"İçerik oluşturulamadı: {result.error}")

        logger.info(f"Günlük plan hazır: {len([r for r in results if r.success])}/{num_tweets} tweet")
        return results

    def create_thread(
        self,
        topic: str,
        num_tweets: int = 4,
        include_image: bool = True,
        auto_post: bool = False
    ) -> AutomationResult:
        """
        Thread oluştur

        Args:
            topic: Konu
            num_tweets: Tweet sayısı
            include_image: İlk tweet'e görsel ekle
            auto_post: Hemen gönder

        Returns:
            Otomasyon sonucu
        """
        try:
            # AI ile thread oluştur
            generated = self.ai.generate_thread(
                topic=topic,
                num_tweets=num_tweets,
                persona=self.persona
            )

            if not generated.thread_parts:
                return AutomationResult(
                    success=False,
                    error="Thread oluşturulamadı"
                )

            logger.info(f"Thread oluşturuldu: {len(generated.thread_parts)} tweet")

            # Görsel bul (ilk tweet için)
            image = None
            image_path = None
            if include_image:
                image = self.images.find_best_image(generated.suggested_image_query or topic)
                if image:
                    image_path = self.images.download_image(image)

            # Gönder veya zamanla
            if auto_post:
                posted_ids = self._post_thread(generated.thread_parts, image_path)
                return AutomationResult(
                    success=len(posted_ids) > 0,
                    tweet=generated,
                    image=image,
                    posted_id=posted_ids[0] if posted_ids else None
                )
            else:
                scheduled = self.scheduler.schedule_tweet(
                    text=generated.thread_parts[0],
                    media_path=image_path,
                    thread_parts=generated.thread_parts,
                    topic=topic,
                    hashtags=generated.hashtags
                )
                return AutomationResult(
                    success=True,
                    tweet=generated,
                    image=image,
                    scheduled=scheduled
                )

        except Exception as e:
            logger.error(f"Thread oluşturma hatası: {e}")
            return AutomationResult(success=False, error=str(e))

    # ========================================================================
    # YARDIMCI FONKSİYONLAR
    # ========================================================================

    def _select_best_trend(self) -> Optional[Trend]:
        """En iyi trendi seç"""
        trends = self.twitter.get_trends()

        if not trends:
            return None

        # Tweet hacmine göre sıralı zaten
        # İlk 5'ten rastgele seç (çeşitlilik için)
        import random
        top_trends = trends[:5]
        return random.choice(top_trends) if top_trends else None

    def _build_final_tweet(self, generated: GeneratedTweet) -> str:
        """
        Final tweet metnini oluştur (hashtag'lerle birlikte)
        """
        text = generated.text

        # Hashtag'leri ekle (metin içinde yoksa)
        hashtags_to_add = []
        for tag in generated.hashtags[:config.algorithm.max_hashtags]:
            if f"#{tag}" not in text.lower():
                hashtags_to_add.append(f"#{tag}")

        if hashtags_to_add:
            hashtag_text = " ".join(hashtags_to_add)

            # Karakter limitini kontrol et
            if len(text) + len(hashtag_text) + 1 <= 280:
                text = f"{text}\n\n{hashtag_text}"
            elif len(text) + len(hashtag_text) + 1 <= 280:
                text = f"{text} {hashtag_text}"

        return text[:280]

    def _post_now(self, text: str, image_path: str = None) -> Optional[str]:
        """Tweet'i hemen gönder"""
        media_ids = None

        if image_path and self.twitter.is_authenticated:
            media_id = self.twitter.upload_media(image_path)
            if media_id:
                media_ids = [media_id]

        return self.twitter.post_tweet(text, media_ids)

    def _post_thread(self, tweets: List[str], first_image_path: str = None) -> List[str]:
        """Thread gönder"""
        media_ids_list = None

        if first_image_path and self.twitter.is_authenticated:
            media_id = self.twitter.upload_media(first_image_path)
            if media_id:
                media_ids_list = [[media_id]] + [None] * (len(tweets) - 1)

        return self.twitter.post_thread(tweets, media_ids_list)

    def post_scheduled_tweet(self, scheduled: ScheduledTweet) -> bool:
        """
        Zamanlanmış tweet'i gönder
        (Scheduler callback'i için)
        """
        try:
            media_ids = None

            if scheduled.media_path and self.twitter.is_authenticated:
                media_id = self.twitter.upload_media(scheduled.media_path)
                if media_id:
                    media_ids = [media_id]

            # Thread mi normal tweet mi?
            if scheduled.thread_parts and len(scheduled.thread_parts) > 1:
                posted_ids = self.twitter.post_thread(scheduled.thread_parts)
                scheduled.tweet_id = posted_ids[0] if posted_ids else None
                return len(posted_ids) > 0
            else:
                tweet_id = self.twitter.post_tweet(scheduled.text, media_ids)
                scheduled.tweet_id = tweet_id
                return tweet_id is not None

        except Exception as e:
            logger.error(f"Scheduled tweet gönderme hatası: {e}")
            return False

    # ========================================================================
    # ANALİZ VE RAPORLAMA
    # ========================================================================

    def analyze_trends(self) -> Dict:
        """Güncel trend analizi yap"""
        trends = self.twitter.get_trends()

        analyses = []
        for trend in trends[:5]:
            analysis = self.twitter.analyze_trend_content(trend)
            analyses.append(analysis)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_trends": len(trends),
            "analyzed": len(analyses),
            "trends": analyses
        }

    def get_account_stats(self) -> Dict:
        """Hesap istatistiklerini getir"""
        me = self.twitter.get_me()
        scheduler_stats = self.scheduler.get_stats()
        recent_tweets = self.twitter.get_my_recent_tweets(10)

        # Son tweetlerin performansı
        total_engagement = sum(t.engagement_score for t in recent_tweets)
        avg_engagement = total_engagement / len(recent_tweets) if recent_tweets else 0

        return {
            "account": me,
            "scheduler": scheduler_stats,
            "recent_performance": {
                "tweets_analyzed": len(recent_tweets),
                "total_engagement": total_engagement,
                "avg_engagement": round(avg_engagement, 2),
                "total_likes": sum(t.like_count for t in recent_tweets),
                "total_retweets": sum(t.retweet_count for t in recent_tweets),
            }
        }

    def preview_content(self, topic: str = None) -> Dict:
        """
        İçerik önizleme (göndermeden)
        """
        result = self.auto_generate_and_schedule(
            topic=topic,
            use_trending=topic is None,
            include_image=True,
            auto_post=False
        )

        # Zamanlanmış tweeti iptal et (sadece önizleme)
        if result.scheduled:
            self.scheduler.cancel_tweet(result.scheduled.id)

        return {
            "preview": True,
            "topic": topic or (result.trend.name if result.trend else "Bilinmeyen"),
            "tweet_text": result.tweet.text if result.tweet else None,
            "hashtags": result.tweet.hashtags if result.tweet else [],
            "image_url": result.image.url if result.image else None,
            "engagement_prediction": result.tweet.engagement_prediction if result.tweet else "unknown",
            "suggested_time": self.scheduler.get_next_optimal_time().strftime("%Y-%m-%d %H:%M"),
        }

    # ========================================================================
    # KONTROL
    # ========================================================================

    def start_automation(self):
        """Otomatik gönderim döngüsünü başlat"""
        self.scheduler.start_auto_posting(self.post_scheduled_tweet)
        logger.info("Otomasyon başlatıldı")

    def stop_automation(self):
        """Otomatik gönderim döngüsünü durdur"""
        self.scheduler.stop_auto_posting()
        logger.info("Otomasyon durduruldu")


# Varsayılan motor örneği
engine = TwitterGrowthEngine()
