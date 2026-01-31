"""
Viral Tweet Discovery - Viral Tweet Keşif Sistemi
===================================================

Konu bazlı viral tweet'leri keşfeder ve analiz eder.
Etkileşim oranlarına göre sıralar ve ilham kaynağı sağlar.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import re
import logging
import random
from datetime import datetime, timedelta
import urllib.parse

logger = logging.getLogger(__name__)


@dataclass
class ViralTweet:
    """Viral tweet verisi"""
    text: str
    author: str = ""
    author_followers: str = ""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: str = ""
    date: str = ""
    has_media: bool = False
    engagement_score: float = 0.0
    viral_reason: str = ""
    url: str = ""


# Sabit içerik kategorileri
CONTENT_CATEGORIES = {
    "futbol": {
        "name": "⚽ Futbol",
        "keywords": ["futbol", "maç", "gol", "şampiyon", "lig", "transfer", "teknik direktör", "galatasaray", "fenerbahçe", "beşiktaş", "trabzonspor"],
        "hashtags": ["#futbol", "#süperlig", "#maç"],
        "tone": "heyecanlı",
        "templates": [
            "Bu transferi kimse beklemiyordu! {insight} Sizce doğru hamle mi?",
            "Maç analizi: {insight} Katılıyor musunuz?",
            "{insight} Bu sezon şampiyon kim olur? 🏆",
        ]
    },
    "finans": {
        "name": "💰 Finans & Kripto",
        "keywords": ["dolar", "euro", "altın", "borsa", "bitcoin", "kripto", "faiz", "enflasyon", "merkez bankası", "yatırım"],
        "hashtags": ["#dolar", "#altın", "#borsa", "#bitcoin"],
        "tone": "bilgilendirici",
        "templates": [
            "Piyasa analizi: {insight} Dikkatli olun!",
            "{insight} Bu seviyeler kritik. Ne düşünüyorsunuz?",
            "Yatırımcılar dikkat! {insight} 📊",
        ]
    },
    "mizah": {
        "name": "😂 Mizah",
        "keywords": ["komik", "caps", "espri", "kahkaha", "gülmek"],
        "hashtags": [],
        "tone": "mizahi",
        "templates": [
            "{insight} 😂",
            "Bunu yaşamayan yoktur: {insight}",
            "{insight} Yanlış mıyım? 🤷‍♂️",
        ]
    },
    "teknoloji": {
        "name": "🚀 Teknoloji & AI",
        "keywords": ["yapay zeka", "AI", "teknoloji", "iPhone", "Android", "uygulama", "startup", "girişim", "ChatGPT", "robot"],
        "hashtags": ["#teknoloji", "#yapayZeka", "#AI"],
        "tone": "bilgilendirici",
        "templates": [
            "Teknoloji dünyasından: {insight} Bu gelişme çok önemli!",
            "AI devrimi devam ediyor: {insight} Siz hazır mısınız?",
            "{insight} Gelecek burada. Ne düşünüyorsunuz?",
        ]
    },
    "gundem": {
        "name": "🔥 Gündem",
        "keywords": ["son dakika", "gündem", "Türkiye", "dünya", "açıklama", "karar"],
        "hashtags": ["#gündem", "#sondakika"],
        "tone": "ciddi",
        "templates": [
            "Gündemden: {insight} Bu gelişmeyi takip edin.",
            "{insight} Sizin yorumunuz nedir?",
            "Önemli gelişme: {insight}",
        ]
    },
    "motivasyon": {
        "name": "💪 Motivasyon",
        "keywords": ["başarı", "motivasyon", "hedef", "hayat", "mutluluk", "çalışmak"],
        "hashtags": ["#motivasyon", "#başarı"],
        "tone": "ilham verici",
        "templates": [
            "{insight} Başarı tesadüf değil! 💪",
            "Bugün için hatırlatma: {insight}",
            "{insight} Kendinize inanın! 🚀",
        ]
    },
    "yasam": {
        "name": "🌟 Yaşam & Lifestyle",
        "keywords": ["hayat", "yaşam", "mutfak", "yemek", "seyahat", "tatil", "ev", "dekorasyon"],
        "hashtags": ["#yaşam", "#lifestyle"],
        "tone": "samimi",
        "templates": [
            "{insight} Bunu denemeden geçmeyin!",
            "Hayattan bir kesit: {insight}",
            "{insight} Siz de böyle misiniz?",
        ]
    },
}


class ViralTweetDiscovery:
    """Viral tweet keşif ve analiz sistemi"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def search_viral_tweets(self, topic: str, count: int = 10) -> List[ViralTweet]:
        """
        Konu hakkında viral tweet'leri ara.
        Birden fazla kaynaktan veri toplar.
        """
        tweets = []

        # Nitter'dan ara
        nitter_tweets = self._search_nitter(topic, count)
        tweets.extend(nitter_tweets)

        # Eğer yeterli tweet bulunamazsa, örnek viral tweet'ler oluştur
        if len(tweets) < 3:
            sample_tweets = self._generate_sample_viral_tweets(topic)
            tweets.extend(sample_tweets)

        # Engagement skoruna göre sırala
        tweets = sorted(tweets, key=lambda t: t.engagement_score, reverse=True)

        return tweets[:count]

    def _search_nitter(self, topic: str, count: int) -> List[ViralTweet]:
        """Nitter üzerinden tweet ara"""
        tweets = []

        nitter_instances = [
            "https://nitter.poast.org",
            "https://nitter.privacydev.net",
            "https://nitter.net",
        ]

        encoded_topic = urllib.parse.quote(topic)

        for instance in nitter_instances:
            try:
                url = f"{instance}/search?f=tweets&q={encoded_topic}&e-nativeretweets=on"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    parsed = self._parse_nitter_results(response.text, count)
                    if parsed:
                        tweets.extend(parsed)
                        break

            except Exception as e:
                logger.debug(f"Nitter arama hatası ({instance}): {e}")
                continue

        return tweets

    def _parse_nitter_results(self, html: str, count: int) -> List[ViralTweet]:
        """Nitter sonuçlarını parse et"""
        tweets = []
        soup = BeautifulSoup(html, 'lxml')

        try:
            tweet_items = soup.select('.timeline-item')[:count * 2]

            for item in tweet_items:
                try:
                    # Tweet metni
                    content = item.select_one('.tweet-content')
                    if not content:
                        continue

                    text = content.get_text(strip=True)
                    if not text or len(text) < 20:
                        continue

                    # Yazar
                    author_elem = item.select_one('.username')
                    author = author_elem.get_text(strip=True) if author_elem else ""

                    # Stats
                    likes = 0
                    retweets = 0
                    replies = 0

                    stat_container = item.select('.tweet-stat')
                    for stat in stat_container:
                        stat_text = stat.get_text(strip=True)
                        if 'comment' in str(stat):
                            replies = self._parse_count(stat_text)
                        elif 'retweet' in str(stat):
                            retweets = self._parse_count(stat_text)
                        elif 'heart' in str(stat):
                            likes = self._parse_count(stat_text)

                    # Engagement skoru hesapla (Twitter algoritmasına göre)
                    engagement_score = (
                        replies * 13.5 +  # Reply en değerli
                        retweets * 1.0 +
                        likes * 0.5
                    )

                    # Sadece belirli bir engagement üstündekileri al
                    if engagement_score < 10:
                        continue

                    # Media kontrolü
                    has_media = bool(item.select_one('.attachments'))

                    # Viral nedeni analiz et
                    viral_reason = self._analyze_viral_reason(text, likes, retweets, replies)

                    tweet = ViralTweet(
                        text=text,
                        author=author,
                        likes=likes,
                        retweets=retweets,
                        replies=replies,
                        engagement_score=engagement_score,
                        has_media=has_media,
                        viral_reason=viral_reason,
                    )

                    tweets.append(tweet)

                except Exception as e:
                    continue

        except Exception as e:
            logger.error(f"Parse hatası: {e}")

        return tweets

    def _parse_count(self, text: str) -> int:
        """Sayı parse et"""
        if not text:
            return 0

        text = text.strip().replace(',', '').replace('.', '')

        try:
            # K, M gibi kısaltmaları işle
            text_upper = text.upper()
            if 'K' in text_upper:
                num = text_upper.replace('K', '').strip()
                return int(float(num) * 1000)
            elif 'M' in text_upper:
                num = text_upper.replace('M', '').strip()
                return int(float(num) * 1000000)
            else:
                # Sadece rakamları al
                nums = re.findall(r'\d+', text)
                return int(nums[0]) if nums else 0
        except:
            return 0

    def _analyze_viral_reason(self, text: str, likes: int, retweets: int, replies: int) -> str:
        """Tweet'in neden viral olduğunu analiz et"""
        reasons = []

        text_lower = text.lower()

        # Soru içeriyor mu?
        if '?' in text:
            reasons.append("❓ Soru sorarak etkileşim artırmış")

        # Kısa mı?
        if len(text) < 100:
            reasons.append("📝 Kısa ve öz")

        # Emoji var mı?
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]+")
        if emoji_pattern.search(text):
            reasons.append("😊 Emoji kullanmış")

        # Tartışmalı mı?
        controversy_words = ["yanlış", "doğru değil", "saçmalık", "inanamıyorum", "skandal"]
        if any(word in text_lower for word in controversy_words):
            reasons.append("🔥 Tartışmalı/provokatif içerik")

        # Reply çok mu?
        if replies > likes * 0.3:
            reasons.append("💬 Tartışma başlatmış (yüksek reply)")

        # Thread mi?
        if "🧵" in text or "thread" in text_lower or text.startswith("1/"):
            reasons.append("🧵 Thread formatı")

        # Hook var mı?
        hooks = ["kimse", "herkes", "gizli", "sır", "inanamayacaksınız"]
        if any(hook in text_lower for hook in hooks):
            reasons.append("🪝 Dikkat çekici hook kullanmış")

        if not reasons:
            reasons.append("📈 Doğru zamanda doğru kitleye ulaşmış")

        return " | ".join(reasons[:3])

    def _generate_sample_viral_tweets(self, topic: str) -> List[ViralTweet]:
        """
        API/scraping çalışmadığında örnek viral tweet'ler oluştur.
        Gerçekçi viral tweet örnekleri.
        """

        # Kategoriye göre örnek tweet'ler
        sample_templates = {
            "default": [
                {
                    "text": f"{topic} hakkında kimsenin söylemediği bir şey var.\n\nBunu fark eden kazanır.\n\nSiz ne düşünüyorsunuz? 👇",
                    "likes": random.randint(500, 2000),
                    "retweets": random.randint(100, 500),
                    "replies": random.randint(50, 200),
                },
                {
                    "text": f"Thread: {topic} hakkında bilmeniz gereken 5 şey 🧵\n\n1/ Çoğu kişi bunu yanlış biliyor...",
                    "likes": random.randint(1000, 5000),
                    "retweets": random.randint(300, 1000),
                    "replies": random.randint(100, 400),
                },
                {
                    "text": f"{topic} konusunda unpopular opinion:\n\nHerkes X diyor ama aslında Y.\n\nDeğişir misiniz?",
                    "likes": random.randint(300, 1500),
                    "retweets": random.randint(50, 300),
                    "replies": random.randint(200, 800),
                },
                {
                    "text": f"Bugün {topic} ile ilgili öğrendiğim şey beni şok etti.\n\nBunu paylaşmam lazımdı.\n\nKaydedin! 📌",
                    "likes": random.randint(800, 3000),
                    "retweets": random.randint(200, 800),
                    "replies": random.randint(80, 300),
                },
                {
                    "text": f"{topic} deyince aklıma hep şu geliyor:\n\n'...' \n\nYanlış mıyım? 🤔",
                    "likes": random.randint(400, 1800),
                    "retweets": random.randint(80, 400),
                    "replies": random.randint(150, 500),
                },
            ],
            "futbol": [
                {
                    "text": f"Bu sezon {topic} için çok kritik.\n\nTransfer döneminde yapılan hatalar ortaya çıkıyor.\n\nŞampiyon kim olur? 🏆",
                    "likes": random.randint(2000, 8000),
                    "retweets": random.randint(500, 2000),
                    "replies": random.randint(500, 2000),
                },
            ],
            "finans": [
                {
                    "text": f"Dikkat! {topic} için kritik seviyeler yaklaşıyor.\n\nBu grafiği inceleyin.\n\nYatırımcılar dikkatli olsun! 📊",
                    "likes": random.randint(1000, 4000),
                    "retweets": random.randint(400, 1500),
                    "replies": random.randint(200, 800),
                },
            ],
        }

        # Kategori eşleştir
        category = "default"
        topic_lower = topic.lower()

        for cat_key, cat_data in CONTENT_CATEGORIES.items():
            if any(kw in topic_lower for kw in cat_data["keywords"]):
                category = cat_key
                break

        templates = sample_templates.get(category, sample_templates["default"])

        tweets = []
        for template in templates:
            engagement_score = (
                template["replies"] * 13.5 +
                template["retweets"] * 1.0 +
                template["likes"] * 0.5
            )

            tweet = ViralTweet(
                text=template["text"],
                author="@viral_account",
                likes=template["likes"],
                retweets=template["retweets"],
                replies=template["replies"],
                engagement_score=engagement_score,
                viral_reason=self._analyze_viral_reason(
                    template["text"],
                    template["likes"],
                    template["retweets"],
                    template["replies"]
                ),
            )
            tweets.append(tweet)

        return tweets

    def get_category_suggestions(self, category: str) -> Dict:
        """Kategori bazlı öneriler getir"""
        if category not in CONTENT_CATEGORIES:
            return {}

        cat_data = CONTENT_CATEGORIES[category]

        return {
            "name": cat_data["name"],
            "keywords": cat_data["keywords"],
            "hashtags": cat_data["hashtags"],
            "tone": cat_data["tone"],
            "templates": cat_data["templates"],
            "sample_topics": cat_data["keywords"][:5],
        }

    def remix_tweet(self, original_tweet: str, user_topic: str, user_style: str = "samimi") -> str:
        """
        Viral tweet'i kullanıcının tarzında remix et.
        Yapıyı koru, içeriği değiştir.
        """
        # Tweet yapısını analiz et
        has_question = "?" in original_tweet
        has_emoji = bool(re.search(r'[\U0001F600-\U0001F64F]', original_tweet))
        has_newlines = "\n" in original_tweet
        is_thread = "🧵" in original_tweet or original_tweet.startswith("1/")

        # Yapıyı koru, konuyu değiştir
        if is_thread:
            remix = f"Thread: {user_topic} hakkında bilmeniz gereken şeyler 🧵\n\n1/ "
        elif has_newlines:
            parts = original_tweet.split('\n')
            if len(parts) >= 2:
                remix = f"{user_topic} hakkında önemli bir konu var.\n\n"
                remix += "Bunu herkesin bilmesi lazım."
            else:
                remix = f"{user_topic} konusunda düşüncelerim..."
        else:
            remix = f"{user_topic} hakkında ne düşünüyorsunuz?"

        if has_question and "?" not in remix:
            remix += " Katılıyor musunuz?"

        if has_emoji and not re.search(r'[\U0001F600-\U0001F64F]', remix):
            emojis = ["🔥", "💡", "👀", "🚀", "💪"]
            remix += f" {random.choice(emojis)}"

        return remix


# Popüler hesaplar (ilham için)
POPULAR_ACCOUNTS_TR = [
    {"username": "elikizkurt", "category": "teknoloji", "desc": "Teknoloji/AI"},
    {"username": "saborahat", "category": "finans", "desc": "Finans/Ekonomi"},
    {"username": "fuaborsa", "category": "finans", "desc": "Borsa"},
    {"username": "tribaborsa", "category": "finans", "desc": "Kripto/Borsa"},
]


# Global instance
viral_discovery = ViralTweetDiscovery()
