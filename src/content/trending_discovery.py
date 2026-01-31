"""
Trending Topic Discovery - Gündem Keşif Sistemi
=================================================

Reddit, Hacker News, Tech haberleri ve sosyal medyadan
şu an en çok konuşulan konuları bulur.

Thread formatında bilgilendirici içerik oluşturur.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import re
import logging
import random
from datetime import datetime
import urllib.parse
import json

logger = logging.getLogger(__name__)


@dataclass
class TrendingTopic:
    """Trending konu verisi"""
    title: str
    source: str  # reddit, hackernews, technews, twitter
    category: str  # ai, tech, crypto, world, turkey
    url: str = ""
    description: str = ""
    upvotes: int = 0
    comments: int = 0
    time_ago: str = ""
    key_points: List[str] = field(default_factory=list)
    related_links: List[str] = field(default_factory=list)


@dataclass
class ThreadContent:
    """Thread içeriği"""
    topic: str
    hook: str  # İlk tweet (dikkat çekici)
    body_tweets: List[str]  # Ana içerik tweet'leri
    conclusion: str  # Son tweet (CTA)
    hashtags: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)


class TrendingDiscovery:
    """
    Trending konu keşif ve içerik oluşturma sistemi.
    Reddit, HackerNews, Tech haberleri tarar.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        })

    def get_all_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Tüm kaynaklardan trending konuları getir"""
        all_topics = []

        # Reddit
        reddit_topics = self.get_reddit_trending(category)
        all_topics.extend(reddit_topics)

        # Hacker News
        hn_topics = self.get_hackernews_trending()
        all_topics.extend(hn_topics)

        # Tech News
        tech_topics = self.get_tech_news()
        all_topics.extend(tech_topics)

        # Sırala (upvotes + comments)
        all_topics.sort(key=lambda x: x.upvotes + x.comments * 2, reverse=True)

        return all_topics[:20]

    def get_reddit_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Reddit'ten trending konuları getir"""
        topics = []

        # Kategori bazlı subreddit'ler
        subreddits = {
            "ai": ["artificial", "MachineLearning", "ChatGPT", "OpenAI", "LocalLLaMA"],
            "tech": ["technology", "programming", "webdev", "gadgets"],
            "crypto": ["cryptocurrency", "Bitcoin", "ethereum"],
            "world": ["worldnews", "news"],
            "turkey": ["Turkey", "KGBTR"],
            "all": ["artificial", "technology", "worldnews", "ChatGPT", "cryptocurrency"],
        }

        subs = subreddits.get(category, subreddits["all"])

        for sub in subs[:3]:
            try:
                # Reddit JSON API (resmi değil ama çalışıyor)
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        post_data = post.get("data", {})

                        # Pinned ve reklam postlarını atla
                        if post_data.get("stickied") or post_data.get("promoted"):
                            continue

                        topic = TrendingTopic(
                            title=post_data.get("title", "")[:200],
                            source="reddit",
                            category=category if category != "all" else self._detect_category(post_data.get("title", "")),
                            url=f"https://reddit.com{post_data.get('permalink', '')}",
                            description=post_data.get("selftext", "")[:300],
                            upvotes=post_data.get("ups", 0),
                            comments=post_data.get("num_comments", 0),
                            time_ago=self._format_time(post_data.get("created_utc", 0)),
                        )

                        if topic.upvotes > 100:  # Sadece popüler olanları al
                            topics.append(topic)

            except Exception as e:
                logger.debug(f"Reddit hatası ({sub}): {e}")
                continue

        return topics

    def get_hackernews_trending(self) -> List[TrendingTopic]:
        """Hacker News'ten trending konuları getir"""
        topics = []

        try:
            # HN Top Stories API
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                story_ids = response.json()[:10]

                for story_id in story_ids[:7]:
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = self.session.get(story_url, timeout=5)

                        if story_response.status_code == 200:
                            story = story_response.json()

                            topic = TrendingTopic(
                                title=story.get("title", ""),
                                source="hackernews",
                                category=self._detect_category(story.get("title", "")),
                                url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                upvotes=story.get("score", 0),
                                comments=story.get("descendants", 0),
                                time_ago=self._format_time(story.get("time", 0)),
                            )

                            topics.append(topic)

                    except Exception as e:
                        continue

        except Exception as e:
            logger.debug(f"HackerNews hatası: {e}")

        return topics

    def get_tech_news(self) -> List[TrendingTopic]:
        """Teknoloji haberlerini getir"""
        topics = []

        # TechCrunch, Wired vb. RSS'lerden
        rss_feeds = [
            ("https://techcrunch.com/feed/", "TechCrunch"),
            ("https://www.wired.com/feed/rss", "Wired"),
            ("https://feeds.arstechnica.com/arstechnica/technology-lab", "ArsTechnica"),
        ]

        for feed_url, source in rss_feeds:
            try:
                response = self.session.get(feed_url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')[:3]

                    for item in items:
                        title = item.find('title')
                        link = item.find('link')
                        description = item.find('description')

                        if title:
                            topic = TrendingTopic(
                                title=title.get_text(strip=True)[:200],
                                source=source.lower(),
                                category=self._detect_category(title.get_text()),
                                url=link.get_text(strip=True) if link else "",
                                description=self._clean_html(description.get_text()[:300]) if description else "",
                            )
                            topics.append(topic)

            except Exception as e:
                logger.debug(f"RSS hatası ({source}): {e}")
                continue

        return topics

    def get_topic_details(self, topic: TrendingTopic) -> TrendingTopic:
        """Konu hakkında detaylı bilgi topla"""

        # URL'den içerik çek
        if topic.url:
            try:
                response = self.session.get(topic.url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')

                    # Paragrafları bul
                    paragraphs = soup.find_all('p')[:10]
                    text_content = " ".join([p.get_text(strip=True) for p in paragraphs])

                    # Key points çıkar
                    sentences = text_content.split('.')[:5]
                    topic.key_points = [s.strip() + '.' for s in sentences if len(s.strip()) > 30]

            except Exception as e:
                logger.debug(f"Detay çekme hatası: {e}")

        return topic

    def search_topic_info(self, query: str) -> Dict:
        """Konu hakkında bilgi ara"""
        info = {
            "query": query,
            "reddit_discussions": [],
            "news_articles": [],
            "key_facts": [],
            "related_topics": [],
        }

        # Reddit'te ara
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.reddit.com/search.json?q={encoded_query}&sort=hot&limit=5"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts[:3]:
                    post_data = post.get("data", {})
                    info["reddit_discussions"].append({
                        "title": post_data.get("title", ""),
                        "subreddit": post_data.get("subreddit", ""),
                        "upvotes": post_data.get("ups", 0),
                        "comments": post_data.get("num_comments", 0),
                    })

        except Exception as e:
            logger.debug(f"Reddit arama hatası: {e}")

        return info

    def _detect_category(self, text: str) -> str:
        """Metinden kategori tespit et"""
        text_lower = text.lower()

        categories = {
            "ai": ["ai", "artificial intelligence", "machine learning", "chatgpt", "openai", "llm", "gpt", "claude", "gemini", "neural", "deep learning"],
            "crypto": ["bitcoin", "crypto", "ethereum", "blockchain", "btc", "eth", "token", "defi", "nft"],
            "tech": ["apple", "google", "microsoft", "startup", "app", "software", "programming", "code", "developer"],
            "world": ["war", "election", "president", "government", "politics", "climate", "economy"],
        }

        for cat, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return cat

        return "tech"

    def _format_time(self, timestamp: float) -> str:
        """Unix timestamp'i okunabilir formata çevir"""
        if not timestamp:
            return ""

        try:
            dt = datetime.fromtimestamp(timestamp)
            now = datetime.now()
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days} gün önce"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600} saat önce"
            else:
                return f"{diff.seconds // 60} dakika önce"
        except:
            return ""

    def _clean_html(self, text: str) -> str:
        """HTML taglerini temizle"""
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()


class ThreadGenerator:
    """
    Bilgilendirici thread içeriği oluşturucu.
    Çağla Üren tarzı detaylı, eğitici thread'ler.
    """

    # Thread şablonları
    THREAD_TEMPLATES = {
        "ai": {
            "hooks": [
                "🧵 {topic} hakkında bilmeniz gereken her şey.\n\nBu gelişme çok önemli. Açıklıyorum 👇",
                "Herkes {topic} konuşuyor ama çoğu kişi detayları bilmiyor.\n\nThread: Neler oluyor? 🧵",
                "🚨 {topic} - Bu gelişmeyi kaçırmayın.\n\nNeden önemli? Anlatıyorum 👇",
            ],
            "body_templates": [
                "1/ Önce temel bilgi:\n\n{point}",
                "2/ Peki bu neden önemli?\n\n{point}",
                "3/ Teknik detaylar:\n\n{point}",
                "4/ Pratik etkileri:\n\n{point}",
                "5/ Gelecekte ne olacak?\n\n{point}",
            ],
            "conclusions": [
                "Son olarak:\n\nBu gelişmeyi takip etmeye devam edeceğim.\n\nTakip et, kaçırma! 🔔\n\nFaydalı bulduysan RT 🙏",
                "Özetle:\n\n{topic} dünyayı değiştirecek.\n\nHazır mısınız?\n\nKaydet 📌 Paylaş 🔄",
            ],
        },
        "tech": {
            "hooks": [
                "🔥 {topic} - Teknoloji dünyasından önemli gelişme.\n\nDetaylar thread'de 👇",
                "Bugün herkes {topic} konuşuyor.\n\nNeden? Anlatıyorum 🧵",
            ],
            "body_templates": [
                "1/ Ne oldu?\n\n{point}",
                "2/ Neden önemli?\n\n{point}",
                "3/ Kullanıcıları nasıl etkileyecek?\n\n{point}",
                "4/ Rakipler ne yapıyor?\n\n{point}",
            ],
            "conclusions": [
                "Son söz:\n\nTeknoloji hızla değişiyor.\n\nGüncel kalmak için takipte kal! 🚀",
            ],
        },
        "crypto": {
            "hooks": [
                "💰 {topic} - Kripto dünyasında neler oluyor?\n\nThread 🧵",
                "🚨 {topic} haberi piyasaları salladı.\n\nNe bilmeniz gerekiyor? 👇",
            ],
            "body_templates": [
                "1/ Gelişme ne?\n\n{point}",
                "2/ Piyasa tepkisi:\n\n{point}",
                "3/ Uzman görüşleri:\n\n{point}",
                "4/ Ne yapmalı?\n\n{point}",
            ],
            "conclusions": [
                "Dikkat:\n\nBu finansal tavsiye değil.\n\nKendi araştırmanızı yapın. DYOR! 🔍",
            ],
        },
        "default": {
            "hooks": [
                "🧵 {topic} hakkında thread.\n\nÖnemli detaylar aşağıda 👇",
                "Bugün {topic} gündemde.\n\nNeler oluyor? Anlatıyorum 🧵",
            ],
            "body_templates": [
                "1/ Konu ne?\n\n{point}",
                "2/ Neden önemli?\n\n{point}",
                "3/ Detaylar:\n\n{point}",
                "4/ Sonuç:\n\n{point}",
            ],
            "conclusions": [
                "Faydalı bulduysan:\n\n❤️ Beğen\n🔄 Paylaş\n💾 Kaydet\n\nTakipte kal!",
            ],
        },
    }

    @classmethod
    def generate_thread(cls, topic: TrendingTopic, user_style: str = "samimi",
                        additional_info: str = "") -> ThreadContent:
        """
        Trending konudan thread oluştur.
        """
        category = topic.category if topic.category in cls.THREAD_TEMPLATES else "default"
        templates = cls.THREAD_TEMPLATES[category]

        # Hook oluştur
        hook = random.choice(templates["hooks"]).format(topic=topic.title[:50])

        # Body tweets
        body_tweets = []
        points = topic.key_points if topic.key_points else [
            topic.description or "Bu konu hakkında önemli gelişmeler var.",
            "Detaylar henüz netleşiyor.",
            "Takipte kalın.",
        ]

        for i, template in enumerate(templates["body_templates"][:len(points)]):
            point = points[i] if i < len(points) else "..."
            tweet = template.format(point=point[:200])
            body_tweets.append(tweet)

        # Conclusion
        conclusion = random.choice(templates["conclusions"]).format(topic=topic.title[:30])

        # Hashtags
        category_hashtags = {
            "ai": ["#YapayZeka", "#AI", "#Teknoloji"],
            "tech": ["#Teknoloji", "#Tech"],
            "crypto": ["#Bitcoin", "#Kripto"],
            "default": ["#Gündem"],
        }
        hashtags = category_hashtags.get(category, category_hashtags["default"])

        return ThreadContent(
            topic=topic.title,
            hook=hook,
            body_tweets=body_tweets,
            conclusion=conclusion,
            hashtags=hashtags,
            sources=[topic.url] if topic.url else [],
        )

    @classmethod
    def format_as_single_tweet(cls, thread: ThreadContent) -> str:
        """Thread'i tek tweet olarak formatla (kısa versiyon)"""
        return f"{thread.hook}\n\n{' '.join(thread.hashtags[:2])}"

    @classmethod
    def format_as_full_thread(cls, thread: ThreadContent) -> List[str]:
        """Thread'i tweet listesi olarak formatla"""
        tweets = [thread.hook]
        tweets.extend(thread.body_tweets)
        tweets.append(thread.conclusion)
        return tweets


# Kategoriler için Türkçe isimler
TRENDING_CATEGORIES = {
    "ai": {"name": "🤖 Yapay Zeka", "desc": "AI, ChatGPT, LLM haberleri"},
    "tech": {"name": "💻 Teknoloji", "desc": "Genel teknoloji haberleri"},
    "crypto": {"name": "₿ Kripto", "desc": "Bitcoin, Ethereum, DeFi"},
    "world": {"name": "🌍 Dünya", "desc": "Dünya gündemi"},
    "all": {"name": "🔥 Tümü", "desc": "Tüm kategoriler"},
}


# Global instance
trending_discovery = TrendingDiscovery()
thread_generator = ThreadGenerator()
