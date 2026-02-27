"""
Ücretsiz Twitter/X Trend Scraper
================================

Twitter API olmadan trend ve popüler içerik çekme.
Web scraping ve ücretsiz API'ler kullanır.

Kaynaklar:
- Google Trends
- Nitter (Twitter mirror)
- trends24.in
- getdaytrends.com
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import re
import logging
import random

logger = logging.getLogger(__name__)

# User-Agent listesi (engellenmemek için)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


@dataclass
class TrendTopic:
    """Trend konu veri sınıfı"""
    name: str
    tweet_count: Optional[str] = None
    category: str = "trending"
    url: str = ""
    rank: int = 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "tweet_count": self.tweet_count,
            "category": self.category,
            "url": self.url,
            "rank": self.rank,
        }


@dataclass
class PopularTweet:
    """Popüler tweet veri sınıfı"""
    text: str
    author: str
    likes: str = "0"
    retweets: str = "0"
    replies: str = "0"
    url: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "author": self.author,
            "likes": self.likes,
            "retweets": self.retweets,
            "replies": self.replies,
            "url": self.url,
            "timestamp": self.timestamp,
        }


class FreeTrendScraper:
    """
    Ücretsiz Twitter trend scraper

    Twitter API'ye ihtiyaç duymadan:
    - Türkiye trendlerini çeker
    - Popüler tweetleri analiz eder
    - Hashtag araştırması yapar
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def _get_page(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Sayfa içeriğini çek"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Sayfa çekme hatası ({url}): {e}")
            return None

    # ========================================================================
    # TREND KAYNAKLARI
    # ========================================================================

    def get_trends_from_trends24(self, country: str = "turkey") -> List[TrendTopic]:
        """
        trends24.in'den Türkiye trendlerini çek
        """
        url = f"https://trends24.in/{country}/"
        soup = self._get_page(url)

        if not soup:
            return []

        trends = []
        try:
            # Trend listelerini bul
            trend_cards = soup.select(".trend-card__list li a")

            for i, item in enumerate(trend_cards[:20], 1):
                name = item.get_text(strip=True)
                if name:
                    trends.append(TrendTopic(
                        name=name,
                        rank=i,
                        category="trending",
                        url=f"https://twitter.com/search?q={name}"
                    ))

            logger.info(f"trends24.in'den {len(trends)} trend çekildi")

        except Exception as e:
            logger.error(f"trends24 parse hatası: {e}")

        return trends

    def get_trends_from_getdaytrends(self, country: str = "turkey") -> List[TrendTopic]:
        """
        getdaytrends.com'dan trendleri çek
        """
        url = f"https://getdaytrends.com/{country}/"
        soup = self._get_page(url)

        if not soup:
            return []

        trends = []
        try:
            # Trend tablolarını bul
            trend_rows = soup.select("table.ranking-table tbody tr")

            for i, row in enumerate(trend_rows[:20], 1):
                cells = row.select("td")
                if len(cells) >= 2:
                    name = cells[1].get_text(strip=True)
                    tweet_count = cells[2].get_text(strip=True) if len(cells) > 2 else None

                    if name:
                        trends.append(TrendTopic(
                            name=name,
                            tweet_count=tweet_count,
                            rank=i,
                            category="trending",
                            url=f"https://twitter.com/search?q={name}"
                        ))

            logger.info(f"getdaytrends.com'dan {len(trends)} trend çekildi")

        except Exception as e:
            logger.error(f"getdaytrends parse hatası: {e}")

        return trends

    def get_trends_from_google(self, country: str = "TR") -> List[TrendTopic]:
        """
        Google Trends'den güncel aramaları çek
        """
        url = f"https://trends.google.com/trending/rss?geo={country}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # RSS parse
            soup = BeautifulSoup(response.text, 'xml')
            items = soup.find_all('item')

            trends = []
            for i, item in enumerate(items[:15], 1):
                title = item.find('title')
                traffic = item.find('ht:approx_traffic')

                if title:
                    trends.append(TrendTopic(
                        name=title.get_text(strip=True),
                        tweet_count=traffic.get_text(strip=True) if traffic else None,
                        rank=i,
                        category="google_trends",
                    ))

            logger.info(f"Google Trends'den {len(trends)} trend çekildi")
            return trends

        except Exception as e:
            logger.error(f"Google Trends hatası: {e}")
            return []

    # ========================================================================
    # BİRLEŞİK FONKSİYONLAR
    # ========================================================================

    def get_turkey_trends(self) -> List[TrendTopic]:
        """
        Tüm kaynaklardan Türkiye trendlerini çek ve birleştir
        """
        all_trends = []

        # trends24.in dene
        trends = self.get_trends_from_trends24("turkey")
        if trends:
            all_trends.extend(trends)

        # getdaytrends.com dene (yedek)
        if not all_trends:
            trends = self.get_trends_from_getdaytrends("turkey")
            all_trends.extend(trends)

        # Google Trends ekle
        google_trends = self.get_trends_from_google("TR")
        for gt in google_trends:
            # Tekrar kontrolü
            if not any(t.name.lower() == gt.name.lower() for t in all_trends):
                all_trends.append(gt)

        # Demo verisi (hiçbir kaynak çalışmazsa)
        if not all_trends:
            all_trends = self._get_demo_trends()

        return all_trends[:20]

    def search_topic_tweets(self, topic: str) -> List[PopularTweet]:
        """
        Bir konu hakkında örnek tweet metinleri getir
        (Nitter veya alternatif kaynaklardan)
        """
        # Nitter instance'ları (Twitter mirror)
        nitter_instances = [
            "nitter.net",
            "nitter.privacydev.net",
            "nitter.poast.org",
        ]

        for instance in nitter_instances:
            try:
                url = f"https://{instance}/search?f=tweets&q={topic}&since=&until=&near="
                soup = self._get_page(url)

                if not soup:
                    continue

                tweets = []
                tweet_divs = soup.select(".timeline-item")

                for div in tweet_divs[:10]:
                    try:
                        text_elem = div.select_one(".tweet-content")
                        author_elem = div.select_one(".username")
                        stats = div.select(".tweet-stat")

                        if text_elem:
                            tweet = PopularTweet(
                                text=text_elem.get_text(strip=True),
                                author=author_elem.get_text(strip=True) if author_elem else "unknown",
                                likes=stats[2].get_text(strip=True) if len(stats) > 2 else "0",
                                retweets=stats[1].get_text(strip=True) if len(stats) > 1 else "0",
                                replies=stats[0].get_text(strip=True) if len(stats) > 0 else "0",
                            )
                            tweets.append(tweet)
                    except:
                        continue

                if tweets:
                    logger.info(f"'{topic}' için {len(tweets)} tweet bulundu")
                    return tweets

            except Exception as e:
                logger.debug(f"Nitter instance {instance} başarısız: {e}")
                continue

        # Hiçbir kaynak çalışmazsa boş liste
        return []

    def get_topic_context(self, topic: str) -> Dict:
        """
        Bir konu hakkında bağlam bilgisi topla
        """
        context = {
            "topic": topic,
            "sample_tweets": [],
            "news": [],
            "summary": "",
            "key_points": [],
            "sentiment": "neutral",
        }

        # Tweet örnekleri
        tweets = self.search_topic_tweets(topic)
        context["sample_tweets"] = [t.to_dict() for t in tweets[:5]]

        # Haber ara
        news = self.search_news(topic)
        context["news"] = news[:5]

        # Özet oluştur
        if news:
            context["summary"] = f"{topic} hakkında güncel haberler mevcut."
            context["key_points"] = [n.get("title", "")[:100] for n in news[:3]]

        return context

    def search_news(self, topic: str) -> List[Dict]:
        """
        Konu hakkında güncel haberleri çek
        """
        news_list = []

        # Google News RSS dene
        try:
            import urllib.parse
            encoded_topic = urllib.parse.quote(topic)
            url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=tr&gl=TR&ceid=TR:tr"

            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')

                for item in items[:10]:
                    title = item.find('title')
                    link = item.find('link')
                    pub_date = item.find('pubDate')
                    source = item.find('source')

                    if title:
                        news_list.append({
                            "title": title.get_text(strip=True),
                            "url": link.get_text(strip=True) if link else "",
                            "date": pub_date.get_text(strip=True) if pub_date else "",
                            "source": source.get_text(strip=True) if source else "",
                        })

                logger.info(f"'{topic}' için {len(news_list)} haber bulundu")

        except Exception as e:
            logger.error(f"Haber arama hatası: {e}")

        return news_list

    def analyze_trend(self, topic: str) -> Dict:
        """
        Bir trend hakkında kapsamlı analiz yap

        Returns:
            - Konu özeti
            - Güncel haberler
            - Örnek tweetler
            - Anahtar noktalar
            - Önerilen açılar (tweet için)
        """
        analysis = {
            "topic": topic,
            "news": [],
            "sample_tweets": [],
            "key_points": [],
            "suggested_angles": [],
            "hashtags": [],
            "best_time_to_post": "Şimdi gündemde!",
        }

        # Haberleri çek
        news = self.search_news(topic)
        analysis["news"] = news[:5]

        # Anahtar noktaları çıkar
        if news:
            analysis["key_points"] = [
                n.get("title", "")[:80] + "..." if len(n.get("title", "")) > 80 else n.get("title", "")
                for n in news[:3]
            ]

        # Tweet örnekleri
        tweets = self.search_topic_tweets(topic)
        analysis["sample_tweets"] = [t.to_dict() for t in tweets[:5]]

        # Önerilen tweet açıları
        analysis["suggested_angles"] = [
            f"📊 {topic} hakkında bilgilendirici bir paylaşım",
            f"💭 {topic} konusunda kişisel görüş",
            f"❓ {topic} hakkında takipçilere soru",
            f"📰 {topic} ile ilgili güncel gelişme yorumu",
        ]

        # Hashtag önerileri
        clean_topic = topic.replace("#", "").replace(" ", "")
        analysis["hashtags"] = [
            clean_topic,
            "Gündem",
            "Türkiye",
        ]

        return analysis

    def _get_demo_trends(self) -> List[TrendTopic]:
        """Demo trend verisi"""
        demo_trends = [
            ("Türkiye", "125K"),
            ("Ekonomi", "89K"),
            ("Dolar", "67K"),
            ("Teknoloji", "45K"),
            ("Yapay Zeka", "38K"),
            ("İstanbul", "92K"),
            ("Spor", "78K"),
            ("Gündem", "156K"),
            ("Siyaset", "84K"),
            ("Eğitim", "32K"),
        ]

        return [
            TrendTopic(
                name=name,
                tweet_count=count,
                rank=i,
                category="demo"
            )
            for i, (name, count) in enumerate(demo_trends, 1)
        ]


# Singleton instance
trend_scraper = FreeTrendScraper()
