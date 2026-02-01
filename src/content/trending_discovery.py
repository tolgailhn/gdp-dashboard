"""
Trending Topic Discovery - Gündem Keşif Sistemi (v2)
======================================================

Reddit, Hacker News, Tech haberleri ve sosyal medyadan
şu an en çok konuşulan konuları bulur.

GERÇEK ARAŞTIRMA yaparak bilgilendirici içerik oluşturur.
X Premium uzun tweet desteği.
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
    full_content: str = ""  # Tam içerik (araştırma sonucu)
    related_links: List[str] = field(default_factory=list)


@dataclass
class ThreadContent:
    """Thread içeriği - X Premium uzun tweet desteği"""
    topic: str
    full_text: str  # Tek uzun tweet (X Premium için)
    hook: str  # İlk kısım
    body: str  # Ana içerik
    conclusion: str  # Son kısım
    hashtags: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    word_count: int = 0
    char_count: int = 0


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

        subreddits = {
            "ai": ["artificial", "MachineLearning", "ChatGPT", "OpenAI", "LocalLLaMA"],
            "tech": ["technology", "programming", "webdev", "gadgets"],
            "crypto": ["cryptocurrency", "Bitcoin", "ethereum"],
            "world": ["worldnews", "news"],
            "turkey": ["Turkey"],
            "all": ["artificial", "technology", "worldnews", "ChatGPT", "cryptocurrency"],
        }

        subs = subreddits.get(category, subreddits["all"])

        for sub in subs[:3]:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        post_data = post.get("data", {})

                        if post_data.get("stickied") or post_data.get("promoted"):
                            continue

                        topic = TrendingTopic(
                            title=post_data.get("title", "")[:200],
                            source="reddit",
                            category=category if category != "all" else self._detect_category(post_data.get("title", "")),
                            url=f"https://reddit.com{post_data.get('permalink', '')}",
                            description=post_data.get("selftext", "")[:500],
                            upvotes=post_data.get("ups", 0),
                            comments=post_data.get("num_comments", 0),
                            time_ago=self._format_time(post_data.get("created_utc", 0)),
                        )

                        if topic.upvotes > 50:
                            topics.append(topic)

            except Exception as e:
                logger.debug(f"Reddit hatası ({sub}): {e}")
                continue

        return topics

    def get_hackernews_trending(self) -> List[TrendingTopic]:
        """Hacker News'ten trending konuları getir"""
        topics = []

        try:
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

        rss_feeds = [
            ("https://techcrunch.com/feed/", "TechCrunch"),
            ("https://www.wired.com/feed/rss", "Wired"),
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
                                description=self._clean_html(description.get_text()[:500]) if description else "",
                            )
                            topics.append(topic)

            except Exception as e:
                logger.debug(f"RSS hatası ({source}): {e}")
                continue

        return topics

    def research_topic(self, topic: TrendingTopic) -> TrendingTopic:
        """
        Konu hakkında GERÇEK araştırma yap.
        Web'den detaylı bilgi topla.
        """
        research_data = []

        # 1. Kaynak URL'den içerik çek
        if topic.url:
            content = self._fetch_article_content(topic.url)
            if content:
                research_data.append(content)
                topic.full_content = content

        # 2. Reddit yorumlarından bilgi topla
        if topic.source == "reddit" and topic.url:
            comments = self._fetch_reddit_comments(topic.url)
            if comments:
                research_data.extend(comments[:5])

        # 3. Key points çıkar
        all_text = " ".join(research_data)
        topic.key_points = self._extract_key_points(all_text)

        return topic

    def _fetch_article_content(self, url: str) -> str:
        """Makale içeriğini çek"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # Script ve style taglerini kaldır
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()

                # Makale içeriğini bul
                article = soup.find('article') or soup.find('main') or soup.find('body')

                if article:
                    paragraphs = article.find_all('p')
                    content = " ".join([p.get_text(strip=True) for p in paragraphs[:15]])
                    return content[:3000]

        except Exception as e:
            logger.debug(f"İçerik çekme hatası: {e}")

        return ""

    def _fetch_reddit_comments(self, url: str) -> List[str]:
        """Reddit yorumlarını çek"""
        comments = []
        try:
            # Reddit JSON API
            json_url = url.rstrip('/') + '.json'
            response = self.session.get(json_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    comment_data = data[1].get("data", {}).get("children", [])

                    for comment in comment_data[:10]:
                        body = comment.get("data", {}).get("body", "")
                        if body and len(body) > 50 and "[deleted]" not in body:
                            comments.append(body[:500])

        except Exception as e:
            logger.debug(f"Reddit yorum hatası: {e}")

        return comments

    def _extract_key_points(self, text: str) -> List[str]:
        """Metinden önemli noktaları çıkar"""
        if not text:
            return []

        # Cümlelere ayır
        sentences = re.split(r'[.!?]', text)

        # Önemli cümleleri filtrele
        key_points = []
        important_words = [
            "önemli", "kritik", "yeni", "ilk", "büyük", "değişti",
            "announced", "launched", "new", "first", "major", "breaking",
            "revolutionary", "significant", "important", "update"
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40 and len(sentence) < 300:
                if any(word in sentence.lower() for word in important_words):
                    key_points.append(sentence)

        # En az 3 nokta olsun
        if len(key_points) < 3:
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 50 and len(sentence) < 250 and sentence not in key_points:
                    key_points.append(sentence)
                    if len(key_points) >= 5:
                        break

        return key_points[:7]

    def _detect_category(self, text: str) -> str:
        """Metinden kategori tespit et"""
        text_lower = text.lower()

        categories = {
            "ai": ["ai", "artificial intelligence", "machine learning", "chatgpt", "openai", "llm", "gpt", "claude", "gemini", "neural", "deep learning", "yapay zeka"],
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


class InformativeThreadGenerator:
    """
    Bilgilendirici, detaylı içerik oluşturucu.
    X Premium uzun tweet desteği (25.000 karakter).

    Çağla Üren tarzı: Araştırma + Bilgi + Analiz
    """

    @classmethod
    def generate_informative_content(
        cls,
        topic: TrendingTopic,
        ai_client=None,
        user_voice: str = "samimi",
        max_length: int = 2000
    ) -> ThreadContent:
        """
        AI kullanarak bilgilendirici içerik oluştur.
        Gerçek araştırma verilerini kullanır.
        """

        # Araştırma verilerini hazırla
        research_context = cls._prepare_research_context(topic)

        # AI varsa kullan
        if ai_client and hasattr(ai_client, '_call_ai'):
            content = cls._generate_with_ai(ai_client, topic, research_context, user_voice, max_length)
            if content:
                return content

        # AI yoksa şablondan oluştur (ama araştırma verilerini kullan)
        return cls._generate_from_template(topic, research_context, user_voice)

    @classmethod
    def _prepare_research_context(cls, topic: TrendingTopic) -> str:
        """Araştırma verilerini context olarak hazırla"""
        context_parts = []

        context_parts.append(f"KONU: {topic.title}")

        if topic.description:
            context_parts.append(f"ÖZET: {topic.description}")

        if topic.full_content:
            context_parts.append(f"DETAYLI İÇERİK: {topic.full_content[:1500]}")

        if topic.key_points:
            points = "\n".join([f"- {p}" for p in topic.key_points])
            context_parts.append(f"ÖNEMLİ NOKTALAR:\n{points}")

        if topic.source:
            context_parts.append(f"KAYNAK: {topic.source}")

        return "\n\n".join(context_parts)

    @classmethod
    def _generate_with_ai(
        cls,
        ai_client,
        topic: TrendingTopic,
        research_context: str,
        user_voice: str,
        max_length: int
    ) -> Optional[ThreadContent]:
        """AI ile içerik oluştur"""

        prompt = f"""Sen bir teknoloji ve gündem yazarısın. Twitter/X için bilgilendirici, detaylı ve etkileşim alan içerikler yazıyorsun.

ARAŞTIRMA VERİLERİ:
{research_context}

GÖREV:
Bu konu hakkında Türkçe, bilgilendirici ve detaylı bir Twitter/X paylaşımı yaz.

KURALLAR:
1. X Premium kullanıyorum, uzun yazabilirsin (1500-2000 karakter ideal)
2. Konuyu detaylıca açıkla, yüzeysel kalma
3. Gerçek bilgiler ver, araştırma verilerini kullan
4. {user_voice} bir ton kullan
5. Başlık dikkat çekici olsun
6. Sonunda soru sor veya tartışma başlat
7. 1-2 emoji kullan ama abartma
8. Hashtag KULLANMA (sonra eklenecek)

FORMAT:
- Dikkat çekici giriş (1-2 cümle)
- Ana bilgiler (detaylı açıklama)
- Neden önemli? (analiz)
- Sonuç ve soru

Sadece tweet metnini yaz, başka açıklama ekleme."""

        try:
            response = ai_client._call_ai(prompt)

            if response and len(response) > 100:
                # İçeriği temizle
                content = response.strip()

                # ThreadContent oluştur
                return ThreadContent(
                    topic=topic.title,
                    full_text=content,
                    hook=content[:200] + "..." if len(content) > 200 else content,
                    body=content,
                    conclusion="",
                    hashtags=cls._generate_hashtags(topic),
                    sources=[topic.url] if topic.url else [],
                    word_count=len(content.split()),
                    char_count=len(content),
                )

        except Exception as e:
            logger.error(f"AI içerik oluşturma hatası: {e}")

        return None

    @classmethod
    def _generate_from_template(
        cls,
        topic: TrendingTopic,
        research_context: str,
        user_voice: str
    ) -> ThreadContent:
        """Şablondan bilgilendirici içerik oluştur"""

        # Kategori bazlı şablonlar
        templates = {
            "ai": """🤖 {title}

Bu gelişme yapay zeka dünyasında önemli bir adım.

📌 Ne oldu?
{description}

💡 Neden önemli?
{key_points}

🔮 Bu, yapay zeka alanında yeni bir dönemin başlangıcı olabilir.

Siz bu gelişme hakkında ne düşünüyorsunuz? Yorumlarda tartışalım 👇""",

            "tech": """💻 {title}

Teknoloji dünyasından önemli bir haber.

📌 Detaylar:
{description}

🔍 Önemli noktalar:
{key_points}

Bu gelişmeyi yakından takip edeceğiz.

Sizce bu teknoloji geleceği nasıl şekillendirecek? 👇""",

            "crypto": """₿ {title}

Kripto piyasalarında dikkat çeken gelişme.

📊 Ne oluyor?
{description}

📈 Dikkat edilmesi gerekenler:
{key_points}

⚠️ Not: Bu finansal tavsiye değildir. Kendi araştırmanızı yapın.

Piyasalar hakkında ne düşünüyorsunuz? 👇""",

            "default": """🔥 {title}

Gündemden önemli bir gelişme.

📌 Özet:
{description}

💡 Öne çıkan noktalar:
{key_points}

Bu konu hakkında düşüncelerinizi merak ediyorum 👇"""
        }

        template = templates.get(topic.category, templates["default"])

        # Key points'i formatla
        key_points_text = ""
        if topic.key_points:
            key_points_text = "\n".join([f"• {p[:150]}" for p in topic.key_points[:4]])
        else:
            key_points_text = "• Detaylar gelişiyor, takipte kalın."

        # Description
        description = topic.description[:300] if topic.description else "Bu konuda önemli gelişmeler yaşanıyor."

        # Şablonu doldur
        content = template.format(
            title=topic.title[:100],
            description=description,
            key_points=key_points_text,
        )

        return ThreadContent(
            topic=topic.title,
            full_text=content,
            hook=content[:200],
            body=content,
            conclusion="",
            hashtags=cls._generate_hashtags(topic),
            sources=[topic.url] if topic.url else [],
            word_count=len(content.split()),
            char_count=len(content),
        )

    @classmethod
    def _generate_hashtags(cls, topic: TrendingTopic) -> List[str]:
        """Konu için hashtag oluştur"""
        hashtags = []

        category_tags = {
            "ai": ["#YapayZeka", "#AI", "#Teknoloji"],
            "tech": ["#Teknoloji", "#Tech", "#Gündem"],
            "crypto": ["#Bitcoin", "#Kripto", "#BTC"],
            "world": ["#Gündem", "#Dünya", "#Haber"],
        }

        hashtags.extend(category_tags.get(topic.category, ["#Gündem"]))

        return hashtags[:2]


# Kategoriler için Türkçe isimler
TRENDING_CATEGORIES = {
    "ai": {"name": "🤖 Yapay Zeka", "desc": "AI, ChatGPT, LLM haberleri"},
    "tech": {"name": "💻 Teknoloji", "desc": "Genel teknoloji haberleri"},
    "crypto": {"name": "₿ Kripto", "desc": "Bitcoin, Ethereum, DeFi"},
    "world": {"name": "🌍 Dünya", "desc": "Dünya gündemi"},
    "all": {"name": "🔥 Tümü", "desc": "Tüm kategoriler"},
}


# Global instances
trending_discovery = TrendingDiscovery()
thread_generator = InformativeThreadGenerator()
