"""
Tweet Zamanlama ve Otomasyon Motoru
===================================

Otomatik tweet zamanlama ve gönderme sistemi.
Twitter algoritmasına göre optimize edilmiş zamanlama.

Özellikler:
- Optimal saat hesaplama
- Kuyruk yönetimi
- Günlük limit takibi
- Gece modu
"""

import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import sqlite3
import threading
import time
from pathlib import Path
import pytz

import sys
sys.path.append(str(__file__).rsplit('/', 3)[0])
from config.settings import config

logger = logging.getLogger(__name__)


class TweetStatus(Enum):
    """Tweet durumu"""
    PENDING = "pending"          # Beklemede
    SCHEDULED = "scheduled"      # Zamanlandı
    POSTED = "posted"            # Gönderildi
    FAILED = "failed"            # Başarısız
    CANCELLED = "cancelled"      # İptal edildi


@dataclass
class ScheduledTweet:
    """Zamanlanmış tweet veri sınıfı"""
    id: int = None
    text: str = ""
    scheduled_time: datetime = None
    status: TweetStatus = TweetStatus.PENDING
    media_path: Optional[str] = None
    thread_parts: List[str] = None
    tweet_id: Optional[str] = None  # Gönderildikten sonra
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    topic: str = ""
    hashtags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "status": self.status.value,
            "media_path": self.media_path,
            "thread_parts": self.thread_parts,
            "tweet_id": self.tweet_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "topic": self.topic,
            "hashtags": self.hashtags,
        }


class TweetScheduler:
    """
    Tweet zamanlama ve kuyruk yönetimi

    Bu sınıf:
    - Tweetleri optimal saatlere zamanlar
    - Kuyruk yönetimi yapar
    - Günlük limitleri takip eder
    - Otomatik gönderim yapar
    """

    def __init__(self, db_path: Path = None):
        """Scheduler'ı başlat"""
        self.db_path = db_path or config.database.db_path
        self.timezone = pytz.timezone(config.scheduler.timezone)
        self._running = False
        self._thread = None

        # Veritabanını kur
        self._setup_database()

    def _setup_database(self):
        """SQLite veritabanını kur"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                media_path TEXT,
                thread_parts TEXT,
                tweet_id TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                topic TEXT,
                hashtags TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweet_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id TEXT,
                text TEXT,
                posted_at TIMESTAMP,
                likes INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                impressions INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

        logger.info(f"Veritabanı hazır: {self.db_path}")

    # ========================================================================
    # ZAMANLAMA
    # ========================================================================

    def get_next_optimal_time(self) -> datetime:
        """
        Bir sonraki optimal paylaşım zamanını hesapla

        Twitter algoritmasına göre en iyi saat:
        - Türkiye için: 08:00, 12:00, 13:00, 17:00, 19:00, 21:00

        Returns:
            Optimal datetime
        """
        now = datetime.now(self.timezone)
        optimal_hours = config.algorithm.optimal_posting_hours_turkey

        # Bugün için kalan optimal saatleri bul
        for hour in optimal_hours:
            candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)

            # Gece kontrolü
            if not config.scheduler.enable_night_posting:
                if config.scheduler.night_start_hour <= hour or hour < config.scheduler.night_end_hour:
                    continue

            # Geçmişte değilse ve minimum bekleme süresini geçtiyse
            if candidate > now + timedelta(minutes=config.scheduler.min_interval_minutes):
                # Son tweet ile arasında yeterli süre var mı?
                last_tweet = self.get_last_scheduled_tweet()
                if last_tweet and last_tweet.scheduled_time:
                    min_gap = timedelta(minutes=config.scheduler.min_interval_minutes)
                    if candidate - last_tweet.scheduled_time < min_gap:
                        continue

                return candidate

        # Bugün uygun saat yoksa yarın ilk optimal saat
        tomorrow = now + timedelta(days=1)
        first_hour = optimal_hours[0]

        # Gece kontrolü
        if not config.scheduler.enable_night_posting:
            for hour in optimal_hours:
                if config.scheduler.night_end_hour <= hour < config.scheduler.night_start_hour:
                    first_hour = hour
                    break

        return tomorrow.replace(hour=first_hour, minute=0, second=0, microsecond=0)

    def schedule_tweet(
        self,
        text: str,
        scheduled_time: datetime = None,
        media_path: str = None,
        thread_parts: List[str] = None,
        topic: str = "",
        hashtags: List[str] = None
    ) -> ScheduledTweet:
        """
        Tweet zamanla

        Args:
            text: Tweet metni
            scheduled_time: Zamanlanacak saat (None ise optimal saat)
            media_path: Medya dosyası yolu
            thread_parts: Thread parçaları
            topic: Konu
            hashtags: Hashtag'ler

        Returns:
            Zamanlanmış tweet
        """
        # Günlük limit kontrolü
        today_count = self.get_today_tweet_count()
        if today_count >= config.algorithm.max_tweets_per_day:
            logger.warning("Günlük tweet limiti aşıldı")
            # Yarına zamanla
            scheduled_time = self.get_next_optimal_time()

        # Optimal saat hesapla
        if not scheduled_time:
            scheduled_time = self.get_next_optimal_time()

        # Timezone-aware yap
        if scheduled_time.tzinfo is None:
            scheduled_time = self.timezone.localize(scheduled_time)

        tweet = ScheduledTweet(
            text=text,
            scheduled_time=scheduled_time,
            status=TweetStatus.SCHEDULED,
            media_path=media_path,
            thread_parts=thread_parts,
            topic=topic,
            hashtags=hashtags or []
        )

        # Veritabanına kaydet
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scheduled_tweets
            (text, scheduled_time, status, media_path, thread_parts, topic, hashtags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            text,
            scheduled_time.isoformat(),
            TweetStatus.SCHEDULED.value,
            media_path,
            json.dumps(thread_parts) if thread_parts else None,
            topic,
            json.dumps(hashtags) if hashtags else "[]"
        ))

        tweet.id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Tweet zamanlandı: {scheduled_time.strftime('%Y-%m-%d %H:%M')} - {text[:50]}...")
        return tweet

    def schedule_multiple(self, tweets: List[Dict]) -> List[ScheduledTweet]:
        """
        Birden fazla tweet zamanla (otomatik aralıklarla)

        Args:
            tweets: Tweet listesi [{"text": "...", "media_path": "...", ...}]

        Returns:
            Zamanlanmış tweetler listesi
        """
        scheduled = []
        base_time = None

        for tweet_data in tweets:
            # İlk tweet için optimal saat, sonrakiler için minimum aralık
            if base_time is None:
                scheduled_time = self.get_next_optimal_time()
            else:
                scheduled_time = base_time + timedelta(minutes=config.scheduler.min_interval_minutes)

            tweet = self.schedule_tweet(
                text=tweet_data.get("text", ""),
                scheduled_time=scheduled_time,
                media_path=tweet_data.get("media_path"),
                thread_parts=tweet_data.get("thread_parts"),
                topic=tweet_data.get("topic", ""),
                hashtags=tweet_data.get("hashtags", [])
            )

            scheduled.append(tweet)
            base_time = scheduled_time

        return scheduled

    # ========================================================================
    # KUYRUK YÖNETİMİ
    # ========================================================================

    def get_pending_tweets(self) -> List[ScheduledTweet]:
        """Bekleyen tweetleri getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, text, scheduled_time, status, media_path, thread_parts,
                   tweet_id, error_message, created_at, topic, hashtags
            FROM scheduled_tweets
            WHERE status = 'scheduled'
            ORDER BY scheduled_time ASC
        """)

        tweets = []
        for row in cursor.fetchall():
            tweet = self._row_to_tweet(row)
            tweets.append(tweet)

        conn.close()
        return tweets

    def get_due_tweets(self) -> List[ScheduledTweet]:
        """Gönderilmesi gereken tweetleri getir"""
        now = datetime.now(self.timezone).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, text, scheduled_time, status, media_path, thread_parts,
                   tweet_id, error_message, created_at, topic, hashtags
            FROM scheduled_tweets
            WHERE status = 'scheduled' AND scheduled_time <= ?
            ORDER BY scheduled_time ASC
        """, (now,))

        tweets = []
        for row in cursor.fetchall():
            tweet = self._row_to_tweet(row)
            tweets.append(tweet)

        conn.close()
        return tweets

    def get_last_scheduled_tweet(self) -> Optional[ScheduledTweet]:
        """Son zamanlanmış tweeti getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, text, scheduled_time, status, media_path, thread_parts,
                   tweet_id, error_message, created_at, topic, hashtags
            FROM scheduled_tweets
            WHERE status IN ('scheduled', 'posted')
            ORDER BY scheduled_time DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_tweet(row)
        return None

    def get_today_tweet_count(self) -> int:
        """Bugün gönderilen/zamanlanan tweet sayısını getir"""
        today = datetime.now(self.timezone).date().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM scheduled_tweets
            WHERE DATE(scheduled_time) = ? AND status IN ('scheduled', 'posted')
        """, (today,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def update_tweet_status(
        self,
        tweet_id: int,
        status: TweetStatus,
        twitter_id: str = None,
        error: str = None
    ):
        """Tweet durumunu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE scheduled_tweets
            SET status = ?, tweet_id = ?, error_message = ?
            WHERE id = ?
        """, (status.value, twitter_id, error, tweet_id))

        conn.commit()
        conn.close()

        logger.info(f"Tweet #{tweet_id} durumu güncellendi: {status.value}")

    def cancel_tweet(self, tweet_id: int) -> bool:
        """Zamanlanmış tweeti iptal et"""
        self.update_tweet_status(tweet_id, TweetStatus.CANCELLED)
        return True

    # ========================================================================
    # OTOMATİK GÖNDERME
    # ========================================================================

    def start_auto_posting(self, post_callback: Callable[[ScheduledTweet], bool]):
        """
        Otomatik gönderme döngüsünü başlat

        Args:
            post_callback: Tweet gönderme fonksiyonu (True/False döner)
        """
        if self._running:
            logger.warning("Auto posting zaten çalışıyor")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._auto_post_loop,
            args=(post_callback,),
            daemon=True
        )
        self._thread.start()
        logger.info("Otomatik gönderim başlatıldı")

    def stop_auto_posting(self):
        """Otomatik gönderme döngüsünü durdur"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Otomatik gönderim durduruldu")

    def _auto_post_loop(self, post_callback: Callable):
        """Otomatik gönderim döngüsü"""
        while self._running:
            try:
                due_tweets = self.get_due_tweets()

                for tweet in due_tweets:
                    logger.info(f"Tweet gönderiliyor: {tweet.text[:50]}...")

                    success = post_callback(tweet)

                    if success:
                        self.update_tweet_status(
                            tweet.id,
                            TweetStatus.POSTED,
                            twitter_id=tweet.tweet_id
                        )
                    else:
                        self.update_tweet_status(
                            tweet.id,
                            TweetStatus.FAILED,
                            error="Gönderim başarısız"
                        )

                    # Hız sınırlaması
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Auto post hatası: {e}")

            # 1 dakika bekle
            time.sleep(60)

    # ========================================================================
    # İSTATİSTİKLER
    # ========================================================================

    def get_stats(self) -> Dict:
        """Zamanlama istatistiklerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Toplam tweet sayısı
        cursor.execute("SELECT COUNT(*) FROM scheduled_tweets")
        total = cursor.fetchone()[0]

        # Durum bazlı sayılar
        cursor.execute("""
            SELECT status, COUNT(*) FROM scheduled_tweets
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())

        # Bugünkü tweetler
        today = datetime.now(self.timezone).date().isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM scheduled_tweets
            WHERE DATE(scheduled_time) = ?
        """, (today,))
        today_count = cursor.fetchone()[0]

        conn.close()

        return {
            "total_scheduled": total,
            "pending": status_counts.get("pending", 0),
            "scheduled": status_counts.get("scheduled", 0),
            "posted": status_counts.get("posted", 0),
            "failed": status_counts.get("failed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "today_count": today_count,
            "daily_limit": config.algorithm.max_tweets_per_day,
            "remaining_today": max(0, config.algorithm.max_tweets_per_day - today_count),
        }

    # ========================================================================
    # YARDIMCI METODLAR
    # ========================================================================

    def _row_to_tweet(self, row) -> ScheduledTweet:
        """Veritabanı satırını ScheduledTweet'e dönüştür"""
        scheduled_time = None
        if row[2]:
            try:
                scheduled_time = datetime.fromisoformat(row[2])
                if scheduled_time.tzinfo is None:
                    scheduled_time = self.timezone.localize(scheduled_time)
            except:
                pass

        created_at = datetime.now()
        if row[8]:
            try:
                created_at = datetime.fromisoformat(row[8])
            except:
                pass

        thread_parts = None
        if row[5]:
            try:
                thread_parts = json.loads(row[5])
            except:
                pass

        hashtags = []
        if row[10]:
            try:
                hashtags = json.loads(row[10])
            except:
                pass

        return ScheduledTweet(
            id=row[0],
            text=row[1],
            scheduled_time=scheduled_time,
            status=TweetStatus(row[3]) if row[3] else TweetStatus.PENDING,
            media_path=row[4],
            thread_parts=thread_parts,
            tweet_id=row[6],
            error_message=row[7],
            created_at=created_at,
            topic=row[9] or "",
            hashtags=hashtags
        )


# Singleton instance
scheduler = TweetScheduler()
