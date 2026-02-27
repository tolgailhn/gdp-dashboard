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
    X/Twitter, Reddit, HackerNews tarar.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        # Twitter API config - Bearer Token (pay-per-use)
        import urllib.parse
        self.twitter_bearer_token = urllib.parse.unquote("AAAAAAAAAAAAAAAAAAAAAI%2BY7wEAAAAAC3B4B3daAmvOj%2FBsB5v5M6PjJ6Y%3DHgtVtwVgHII7npxqKc4swFhHsAZ9hr7Yg1tOwVYUe564wzPEj7")
        self.twitter_auth_token = ""
        self.twitter_ct0 = ""

        try:
            from config.settings import config, get_secret
            # env'den override
            env_bearer = get_secret("TWITTER_BEARER_TOKEN", "")
            env_auth = get_secret("TWITTER_AUTH_TOKEN", "")
            env_ct0 = get_secret("TWITTER_CT0", "")
            if env_bearer:
                self.twitter_bearer_token = urllib.parse.unquote(env_bearer)
            if env_auth:
                self.twitter_auth_token = env_auth
            if env_ct0:
                self.twitter_ct0 = env_ct0
        except:
            pass

    def get_all_trending(self, category: str = "all") -> List[TrendingTopic]:
        """tüm kaynaklardan trending konuları getir - önce x, sonra reddit"""
        all_topics = []

        # 1. önce x/twitter trendlerini dene
        x_topics = self.get_x_trending()
        all_topics.extend(x_topics)

        # 2. reddit'i dene
        reddit_topics = self.get_reddit_trending(category)
        all_topics.extend(reddit_topics)

        # 3. hiçbiri olmazsa hackernews
        if not all_topics:
            logger.warning("x ve reddit'ten veri alınamadı, hackernews deneniyor...")
            hn_topics = self.get_hackernews_trending()
            all_topics.extend(hn_topics)

        # sırala
        all_topics.sort(key=lambda x: x.upvotes + x.comments * 2, reverse=True)

        return all_topics[:15]

    def get_x_trending(self) -> List[TrendingTopic]:
        """x/twitter'dan türkiye trendlerini çek"""
        topics = []

        # 1. bearer token varsa API v2 kullan (pay-per-use)
        if self.twitter_bearer_token:
            topics = self._get_x_trends_api_v2()
            if topics:
                logger.info(f"x api v2'den {len(topics)} trend alındı")
                return topics

        # 2. cookie auth varsa graphql api kullan (yedek)
        if self.twitter_auth_token and self.twitter_ct0:
            topics = self._get_x_trends_graphql()
            if topics:
                logger.info(f"x graphql'den {len(topics)} trend alındı")
                return topics

        # 3. api yoksa alternatif kaynakları dene
        topics = self._get_x_trends_scrape()
        return topics

    def _get_x_trends_graphql(self) -> List[TrendingTopic]:
        """twitter graphql api ile trendleri çek (cookie auth)"""
        if not self.twitter_auth_token or not self.twitter_ct0:
            return []

        topics = []
        try:
            # twitter graphql endpoint
            url = "https://twitter.com/i/api/graphql/gCxVCBwLgT0Dv3KGxTNYlQ/GenericTimelineById"

            # explore/tabs endpoint daha iyi çalışıyor
            url = "https://twitter.com/i/api/2/guide.json"
            params = {
                "include_profile_interstitial_type": "1",
                "include_blocking": "1",
                "include_blocked_by": "1",
                "include_followed_by": "1",
                "include_want_retweets": "1",
                "include_mute_edge": "1",
                "include_can_dm": "1",
                "include_can_media_tag": "1",
                "include_ext_has_nft_avatar": "1",
                "skip_status": "1",
                "cards_platform": "Web-12",
                "include_cards": "1",
                "include_ext_alt_text": "true",
                "include_quote_count": "true",
                "include_reply_count": "1",
                "tweet_mode": "extended",
                "include_entities": "true",
                "include_user_entities": "true",
                "include_ext_media_color": "true",
                "include_ext_media_availability": "true",
                "send_error_codes": "true",
                "simple_quoted_tweet": "true",
                "count": "20",
                "cursor": "",
                "ext": "mediaStats,highlightedLabel",
            }

            headers = {
                "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                "Cookie": f"auth_token={self.twitter_auth_token}; ct0={self.twitter_ct0}",
                "X-Csrf-Token": self.twitter_ct0,
                "X-Twitter-Auth-Type": "OAuth2Session",
                "X-Twitter-Active-User": "yes",
                "X-Twitter-Client-Language": "tr",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Referer": "https://twitter.com/explore",
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                # timeline'dan trendleri çıkar
                timeline = data.get("timeline", {}).get("instructions", [])

                for instruction in timeline:
                    entries = instruction.get("addEntries", {}).get("entries", [])
                    for entry in entries:
                        content = entry.get("content", {})
                        items = content.get("timelineModule", {}).get("items", [])

                        for item in items:
                            trend_data = item.get("item", {}).get("content", {}).get("trend", {})
                            if trend_data:
                                name = trend_data.get("name", "")
                                tweet_count = trend_data.get("trendMetadata", {}).get("metaDescription", "")

                                # tweet sayısını parse et
                                volume = 0
                                if tweet_count:
                                    import re
                                    numbers = re.findall(r'[\d,]+', tweet_count)
                                    if numbers:
                                        volume = int(numbers[0].replace(",", ""))

                                topic = TrendingTopic(
                                    title=name,
                                    source="twitter",
                                    category=self._detect_category(name),
                                    url=f"https://twitter.com/search?q={urllib.parse.quote(name)}",
                                    description=tweet_count or "x'te trend",
                                    upvotes=volume,
                                    comments=0,
                                    time_ago="şimdi",
                                )
                                topics.append(topic)

                if topics:
                    return topics[:15]

        except Exception as e:
            logger.debug(f"x graphql hatası: {e}")

        # fallback: search ile ai konularını bul
        return self._search_x_topics()

    def _search_x_topics(self, query: str = "AI OR yapay zeka OR ChatGPT OR teknoloji") -> List[TrendingTopic]:
        """x'te belirli konuları ara (cookie auth ile)"""
        if not self.twitter_auth_token or not self.twitter_ct0:
            return []

        topics = []
        try:
            # twitter search api
            url = "https://twitter.com/i/api/2/search/adaptive.json"
            params = {
                "q": query,
                "tweet_search_mode": "live",
                "query_source": "typed_query",
                "count": "20",
                "result_filter": "top",
            }

            headers = {
                "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                "Cookie": f"auth_token={self.twitter_auth_token}; ct0={self.twitter_ct0}",
                "X-Csrf-Token": self.twitter_ct0,
                "X-Twitter-Auth-Type": "OAuth2Session",
                "X-Twitter-Active-User": "yes",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                tweets = data.get("globalObjects", {}).get("tweets", {})

                for tweet_id, tweet_data in list(tweets.items())[:10]:
                    text = tweet_data.get("full_text", "")[:150]
                    likes = tweet_data.get("favorite_count", 0)
                    retweets = tweet_data.get("retweet_count", 0)

                    topic = TrendingTopic(
                        title=text,
                        source="twitter",
                        category="ai",
                        url=f"https://twitter.com/i/status/{tweet_id}",
                        description=f"❤️ {likes:,} | 🔄 {retweets:,}",
                        upvotes=likes + retweets,
                        comments=0,
                        time_ago="güncel",
                    )
                    topics.append(topic)

                logger.info(f"x search'ten {len(topics)} tweet bulundu")

        except Exception as e:
            logger.debug(f"x search hatası: {e}")

        return topics

    def _get_x_trends_api(self) -> List[TrendingTopic]:
        """twitter api v2 ile trendleri çek"""
        if not self.twitter_bearer_token:
            return []

        try:
            # türkiye woeid: 23424969
            url = "https://api.twitter.com/1.1/trends/place.json?id=23424969"
            headers = {
                "Authorization": f"Bearer {self.twitter_bearer_token}",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    trends = data[0].get("trends", [])

                    for trend in trends[:10]:
                        name = trend.get("name", "")
                        tweet_volume = trend.get("tweet_volume") or 0

                        topic = TrendingTopic(
                            title=name,
                            source="twitter",
                            category=self._detect_category(name),
                            url=trend.get("url", ""),
                            description=f"şu an x'te gündemde",
                            upvotes=tweet_volume,
                            comments=0,
                            time_ago="şimdi",
                        )
                        topics.append(topic)

                    logger.info(f"x api'den {len(topics)} trend alındı")
                    return topics

        except Exception as e:
            logger.debug(f"twitter api hatası: {e}")

        return []

    def _get_x_trends_api_v2(self) -> List[TrendingTopic]:
        """Twitter API v2 ile popüler içerikleri çek (pay-per-use)"""
        if not self.twitter_bearer_token:
            return []

        topics = []
        try:
            # API v2 ile popüler tweet'leri ara (Türkçe)
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                "Authorization": f"Bearer {self.twitter_bearer_token}",
                "User-Agent": "GDP-Dashboard/1.0",
            }

            # Türkçe popüler konuları ara
            params = {
                "query": "lang:tr -is:retweet",
                "max_results": "20",
                "tweet.fields": "public_metrics,created_at",
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                tweets = data.get("data", [])

                # Tweet'lerden hashtag ve konuları çıkar
                import re
                seen_topics = set()
                for tweet in tweets:
                    text = tweet.get("text", "")
                    metrics = tweet.get("public_metrics", {})

                    # Hashtag'leri bul
                    hashtags = re.findall(r'#(\w+)', text)

                    for tag in hashtags:
                        if tag.lower() not in seen_topics and len(tag) > 2:
                            seen_topics.add(tag.lower())
                            topic = TrendingTopic(
                                title=f"#{tag}",
                                source="twitter",
                                category=self._detect_category(tag),
                                url=f"https://twitter.com/search?q=%23{tag}",
                                description="X'te gündemde",
                                upvotes=metrics.get("like_count", 0),
                                comments=metrics.get("reply_count", 0),
                                time_ago="şimdi",
                            )
                            topics.append(topic)

                if topics:
                    logger.info(f"API v2'den {len(topics)} trend bulundu")
                    return topics[:10]

            elif response.status_code == 401:
                logger.warning("API v2: Bearer Token geçersiz")
            elif response.status_code == 403:
                logger.warning("API v2: Erişim reddedildi")

        except Exception as e:
            logger.debug(f"API v2 trend hatası: {e}")

        return topics

    def _get_x_trends_scrape(self) -> List[TrendingTopic]:
        """alternatif kaynaklardan x trendlerini çek"""
        topics = []

        # trends24.in sitesinden türkiye trendlerini çek
        try:
            url = "https://trends24.in/turkey/"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # trend listesini bul
                trend_cards = soup.select('.trend-card__list li a')

                for i, trend in enumerate(trend_cards[:15]):
                    name = trend.get_text(strip=True)
                    if not name or name.startswith("http"):
                        continue

                    topic = TrendingTopic(
                        title=name,
                        source="twitter",
                        category=self._detect_category(name),
                        url=f"https://twitter.com/search?q={urllib.parse.quote(name)}",
                        description="x'te trend olan konu",
                        upvotes=1000 - (i * 50),  # sıralamaya göre tahmini
                        comments=0,
                        time_ago="şimdi",
                    )
                    topics.append(topic)

                if topics:
                    logger.info(f"trends24'ten {len(topics)} trend alındı")
                    return topics

        except Exception as e:
            logger.debug(f"trends24 hatası: {e}")

        # getdaytrends.com sitesinden dene
        try:
            url = "https://getdaytrends.com/turkey/"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                trend_items = soup.select('.main-trend-name a, .trend-name a')

                for i, trend in enumerate(trend_items[:15]):
                    name = trend.get_text(strip=True)
                    if not name:
                        continue

                    topic = TrendingTopic(
                        title=name,
                        source="twitter",
                        category=self._detect_category(name),
                        url=f"https://twitter.com/search?q={urllib.parse.quote(name)}",
                        description="x'te trend olan konu",
                        upvotes=1000 - (i * 50),
                        comments=0,
                        time_ago="şimdi",
                    )
                    topics.append(topic)

                if topics:
                    logger.info(f"getdaytrends'ten {len(topics)} trend alındı")

        except Exception as e:
            logger.debug(f"getdaytrends hatası: {e}")

        return topics

    def get_hackernews_trending(self) -> List[TrendingTopic]:
        """Hacker News'ten trending konuları getir (Reddit backup)"""
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

                            # HTML temizle
                            title = self._clean_html(story.get("title", ""))
                            text = self._clean_html(story.get("text", "") or "")

                            topic = TrendingTopic(
                                title=title,
                                source="hackernews",
                                category=self._detect_category(title),
                                url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                description=text[:500] if text else "",
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

    def get_reddit_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Reddit'ten trending konuları getir - retry ile"""
        topics = []

        subreddits = {
            "ai": ["artificial", "MachineLearning", "ChatGPT", "OpenAI", "LocalLLaMA"],
            "tech": ["technology", "programming", "webdev", "gadgets"],
            "crypto": ["cryptocurrency", "Bitcoin", "ethereum"],
            "world": ["worldnews", "news"],
            "turkey": ["Turkey"],
            "all": ["technology", "artificial", "ChatGPT", "programming", "worldnews"],
        }

        subs = subreddits.get(category, subreddits["all"])

        for sub in subs[:4]:
            try:
                # Reddit JSON API - retry ile
                import time

                for attempt in range(2):
                    try:
                        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=7&raw_json=1"
                        response = self.session.get(url, timeout=15)

                        if response.status_code == 200:
                            break
                        elif response.status_code == 429:
                            # Rate limited, bekle
                            time.sleep(2)
                            continue
                    except:
                        time.sleep(1)
                        continue

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        continue

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

                        if topic.upvotes > 20:  # Daha düşük eşik
                            topics.append(topic)

            except Exception as e:
                logger.warning(f"Reddit hatası ({sub}): {e}")
                continue

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
        Başarısız olursa başlıktan akıllı analiz yap.
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
        if all_text:
            topic.key_points = self._extract_key_points(all_text)

        # 4. Araştırma başarısız olduysa başlıktan akıllı analiz yap
        if not topic.key_points and not topic.full_content:
            title_analysis = self._analyze_title_smart(topic.title)
            topic.key_points = title_analysis["key_points"]
            topic.description = title_analysis["description"]
            topic.full_content = title_analysis["context"]

        return topic

    def _analyze_title_smart(self, title: str) -> Dict[str, any]:
        """
        Başlıktan akıllı analiz yap.
        Teknik terimleri, ürün adlarını, kavramları tespit et.
        """
        result = {
            "key_points": [],
            "description": "",
            "context": "",
            "entities": [],
            "concepts": []
        }

        title_lower = title.lower()

        # Teknik terim sözlüğü
        tech_terms = {
            "open source": "Açık kaynak kodlu, herkesin inceleyip katkıda bulunabileceği yazılım",
            "zero trust": "Sıfır güven modeli - hiçbir kullanıcı veya cihaza otomatik güvenilmez, her erişim doğrulanır",
            "networking": "Ağ teknolojisi - bilgisayarlar arası iletişim altyapısı",
            "vpn": "Sanal özel ağ - güvenli ve şifreli internet bağlantısı",
            "ai": "Yapay zeka - makinelerin insan benzeri öğrenme ve karar verme yeteneği",
            "machine learning": "Makine öğrenimi - verilerden öğrenen algoritmalar",
            "llm": "Büyük dil modeli - ChatGPT gibi metin üreten AI sistemleri",
            "api": "Uygulama programlama arayüzü - yazılımlar arası iletişim protokolü",
            "cloud": "Bulut bilişim - internet üzerinden sunulan hesaplama kaynakları",
            "saas": "Hizmet olarak yazılım - abonelik bazlı bulut uygulamaları",
            "kubernetes": "Konteyner orkestrasyon platformu - uygulamaları ölçeklendirme aracı",
            "docker": "Konteyner teknolojisi - uygulamaları izole ortamlarda çalıştırma",
            "blockchain": "Blok zinciri - dağıtık, değiştirilemez veri yapısı",
            "cryptocurrency": "Kripto para - şifreleme ile güvence altına alınan dijital para",
            "bitcoin": "İlk ve en büyük kripto para birimi",
            "ethereum": "Akıllı sözleşme destekli kripto para platformu",
            "startup": "Yeni kurulan, hızlı büyümeyi hedefleyen teknoloji şirketi",
            "funding": "Yatırım turu - şirketlerin dış kaynaklardan para toplaması",
            "acquisition": "Satın alma - bir şirketin başka bir şirketi alması",
            "ipo": "Halka arz - şirket hisselerinin borsada işlem görmeye başlaması",
            "security": "Güvenlik - sistemleri tehditlere karşı koruma",
            "privacy": "Gizlilik - kişisel verilerin korunması",
            "encryption": "Şifreleme - verileri okunamaz hale getirme",
            "bug": "Yazılım hatası",
            "patch": "Güvenlik yaması - hataları düzelten güncelleme",
            "vulnerability": "Güvenlik açığı - saldırganların istismar edebileceği zayıflık",
            "hack": "Siber saldırı veya yaratıcı çözüm",
            "data breach": "Veri sızıntısı - yetkisiz kişilerin verilere erişmesi",
            "ransomware": "Fidye yazılımı - verileri şifreleyip para isteyen kötü yazılım",
            "gpu": "Grafik işlemci - AI ve oyunlarda kullanılan güçlü işlemci",
            "chip": "Mikroçip - elektronik devre",
            "semiconductor": "Yarı iletken - çip üretiminde kullanılan malzeme",
            "quantum": "Kuantum teknolojisi - kuantum fiziğine dayalı hesaplama",
            "robotics": "Robot teknolojisi",
            "autonomous": "Otonom - insan müdahalesi olmadan çalışan",
            "ev": "Elektrikli araç",
            "battery": "Pil teknolojisi",
            "renewable": "Yenilenebilir enerji",
            "solar": "Güneş enerjisi",
            "spacex": "Elon Musk'ın uzay şirketi",
            "nasa": "ABD Ulusal Havacılık ve Uzay Dairesi",
            "launch": "Lansman veya fırlatma",
            "satellite": "Uydu",
            "5g": "Beşinci nesil mobil ağ teknolojisi",
            "metaverse": "Sanal evren - 3D dijital dünya",
            "vr": "Sanal gerçeklik",
            "ar": "Artırılmış gerçeklik",
        }

        # Başlıkta geçen terimleri bul
        found_terms = []
        explanations = []

        for term, explanation in tech_terms.items():
            if term in title_lower:
                found_terms.append(term)
                explanations.append(f"{term.title()}: {explanation}")

        # Key points oluştur
        if explanations:
            result["key_points"] = explanations[:4]

        # Şirket/ürün adını tespit et (başlıktaki ilk kelime genelde)
        words = title.split()
        if words:
            # Tire veya iki nokta öncesi genelde ürün/şirket adı
            if " - " in title:
                product_name = title.split(" - ")[0].strip()
            elif ": " in title:
                product_name = title.split(": ")[0].strip()
            else:
                product_name = words[0]

            result["entities"].append(product_name)

        # Genel açıklama oluştur
        if found_terms:
            if "open source" in found_terms:
                result["description"] = f"{result['entities'][0] if result['entities'] else 'Bu proje'} açık kaynak kodlu bir proje. Kaynak kodları herkese açık, topluluk katkılarına açık."

            if "zero trust" in found_terms or "security" in found_terms:
                result["description"] += " Güvenlik odaklı bir çözüm sunuyor."

            if "ai" in found_terms or "machine learning" in found_terms:
                result["description"] = f"{result['entities'][0] if result['entities'] else 'Bu'} yapay zeka teknolojisi kullanıyor."

        # Context (AI için ek bilgi)
        context_parts = [f"Konu: {title}"]
        if found_terms:
            context_parts.append(f"Tespit edilen teknoloji terimleri: {', '.join(found_terms)}")
        if result["entities"]:
            context_parts.append(f"Bahsedilen ürün/şirket: {', '.join(result['entities'])}")
        if explanations:
            context_parts.append("Terim açıklamaları:\n" + "\n".join(explanations))

        result["context"] = "\n".join(context_parts)

        # Eğer hiçbir terim bulunamadıysa genel bir açıklama yap
        if not result["key_points"]:
            result["key_points"] = [
                f"'{title}' konusu şu an gündemde",
                "Detaylar için kaynağı inceleyebilirsiniz",
            ]
            result["description"] = f"'{title}' hakkında önemli bir gelişme yaşanıyor."

        return result

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
        """HTML taglerini ve özel karakterleri temizle"""
        if not text:
            return ""
        # HTML taglerini kaldır
        clean = re.sub(r'<[^>]+>', ' ', text)
        # HTML entities
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&#x27;', "'")
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&#39;', "'")
        # Fazla boşlukları temizle
        clean = re.sub(r'\s+', ' ', clean)
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

        # Başlıktan konu özeti çıkar
        title = topic.title

        prompt = f"""sen bi arkadaşına konu anlatıyorsun gibi yaz. robotik değil, samimi.

konu: {title}

ÖNEMLİ KURALLAR:
- küçük harfle yaz (başlık hariç hep küçük)
- türkçe yaz, ingilizce kelime kullanma
- emoji kullanma ya da çok az kullan (max 1)
- "bu nedir, neden önemli" gibi kalıplar kullanma
- doğal konuş, sanki mesajlaşıyorsun gibi

nasıl yazmalısın:
- kısa cümleler kur
- "ya şimdi şöyle bi durum var" gibi başla
- "bence", "aslında", "yani" gibi bağlaçlar kullan
- bazen düşünceni sor "sizce nasıl olur?"
- çok resmi olma, samimi ol

ÖRNEK (bu tarz yaz):

meta bi özellik getirmiş, tüm cihazlardan tek tıkla çıkış yapabiliyosun artık

yani şöyle düşün, telefonunu kaybettin diyelim. normalde her cihaza tek tek girip çıkış yapman lazımdı. şimdi bi tuşla hepsinden atıyosun kendini

bence güzel bi hareket. geç kaldılar ama olsun, hiç yoktan iyidir

siz ne düşünüyosunuz bu konuda?

YAZIM:
- 800-1200 karakter arası
- hashtag ekleme
- sadece türkçe metin yaz"""

        try:
            response = ai_client._call_ai(prompt)

            if response and len(response) > 150:
                content = response.strip().strip('"\'')

                # İngilizce kelime kontrolü - çok fazla varsa template'e geç
                eng_words = ['the ', 'is ', 'are ', 'was ', 'were ', 'have ', 'has ', 'will ', 'would ', 'could ', 'should ', 'this ', 'that ', 'with ', 'from ', 'for ', 'and ', 'but ', 'or ']
                eng_count = sum(1 for w in eng_words if w.lower() in content.lower())

                if eng_count > 3:
                    # Çok fazla İngilizce var, template kullan
                    logger.warning(f"AI çok fazla İngilizce kullandı ({eng_count} kelime), template'e geçiliyor")
                    return None

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
        """Şablondan içerik oluştur - Başlıktan AKILLI bilgi çıkar"""

        title = topic.title

        # Başlıktan detaylı bilgi çıkar
        analysis = cls._analyze_title_for_content(title)

        content = cls._build_smart_content(analysis, topic.category)

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
    def _analyze_title_for_content(cls, title: str) -> dict:
        """Başlıktan detaylı analiz çıkar"""
        import re

        analysis = {
            "company": "",
            "action": "",
            "subject": "",
            "details": [],
            "title_tr": title,
        }

        title_lower = title.lower()

        # Şirket/ürün adı (ilk kelime veya parantez öncesi)
        if "(" in title:
            analysis["company"] = title.split("(")[0].strip()
        elif " - " in title:
            analysis["company"] = title.split(" - ")[0].strip()
        elif ": " in title:
            analysis["company"] = title.split(": ")[0].strip()
        else:
            analysis["company"] = title.split()[0] if title.split() else "Bu konu"

        # Y Combinator tespiti
        yc_match = re.search(r'\(YC ([WSF]\d{2})\)', title)
        if yc_match:
            batch = yc_match.group(1)
            season = {"W": "Kış", "S": "Yaz", "F": "Güz"}.get(batch[0], "")
            year = f"20{batch[1:]}"
            analysis["details"].append(f"Y Combinator {season} {year} programı mezunu bir startup")
            analysis["details"].append("Y Combinator, dünyanın en prestijli startup hızlandırıcısı (Airbnb, Dropbox, Stripe buradan çıktı)")

        # İşe alım tespiti
        if "hiring" in title_lower or "job" in title_lower or "career" in title_lower:
            analysis["action"] = "işe_alim"

            # Pozisyon tespiti
            positions = {
                "researcher": "Araştırmacı",
                "engineer": "Mühendis",
                "developer": "Geliştirici",
                "designer": "Tasarımcı",
                "manager": "Yönetici",
                "scientist": "Bilim İnsanı",
                "analyst": "Analist",
                "intern": "Stajyer",
            }
            for eng, tr in positions.items():
                if eng in title_lower:
                    analysis["subject"] = tr
                    break

            # Alan tespiti
            fields = {
                "ml": "Makine Öğrenimi",
                "machine learning": "Makine Öğrenimi",
                "ai": "Yapay Zeka",
                "data": "Veri",
                "backend": "Backend",
                "frontend": "Frontend",
                "fullstack": "Full Stack",
                "mobile": "Mobil",
                "devops": "DevOps",
                "security": "Güvenlik",
            }
            for eng, tr in fields.items():
                if eng in title_lower:
                    analysis["subject"] = f"{tr} {analysis['subject']}".strip()
                    analysis["details"].append(f"{tr} alanında uzman arıyorlar")
                    break

        # Lansman/duyuru tespiti
        elif "launch" in title_lower or "release" in title_lower or "announce" in title_lower:
            analysis["action"] = "lansman"
            analysis["details"].append("Yeni bir ürün/özellik duyuruldu")

        # Satın alma tespiti
        elif "acqui" in title_lower or "bought" in title_lower or "purchase" in title_lower:
            analysis["action"] = "satin_alma"
            analysis["details"].append("Önemli bir satın alma/birleşme haberi")

        # Yatırım tespiti
        elif "funding" in title_lower or "raise" in title_lower or "series" in title_lower or "million" in title_lower:
            analysis["action"] = "yatirim"
            # Miktar bul
            amount_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(M|B|million|billion)?', title, re.IGNORECASE)
            if amount_match:
                amount = amount_match.group(1)
                unit = amount_match.group(2) or ""
                if unit.upper() in ["M", "MILLION"]:
                    analysis["details"].append(f"{amount} milyon dolar yatırım aldılar")
                elif unit.upper() in ["B", "BILLION"]:
                    analysis["details"].append(f"{amount} milyar dolar yatırım aldılar")

        # Açık kaynak tespiti
        elif "open source" in title_lower or "opensource" in title_lower:
            analysis["action"] = "acik_kaynak"
            analysis["details"].append("Açık kaynak bir proje - herkes kullanabilir ve katkıda bulunabilir")

        return analysis

    @classmethod
    def _build_smart_content(cls, analysis: dict, category: str) -> str:
        """Analiz sonucuna göre akıllı içerik oluştur"""

        company = analysis["company"]
        action = analysis["action"]
        subject = analysis["subject"]
        details = analysis["details"]

        # Detayları bullet point olarak formatla
        # İnsansı içerik oluştur (küçük harf, samimi, doğal)
        details_clean = "\n".join([f"- {d.lower()}" for d in details]) if details else ""
        company_lower = company.lower() if company else "bu şirket"

        if action == "işe_alim":
            return f"""{company} ekip arkadaşı arıyor

{company_lower}, {(subject.lower() if subject else 'yeni pozisyonlar')} için birilerini arıyormuş

{details_clean}

ya şimdi şöyle bi durum var, teknoloji sektöründe iş bulmak isteyenler için fırsatlar artıyor. özellikle yapay zeka ve yazılım tarafında yetenekli insanlara ihtiyaç var

türkiyeden de başvurulabiliyor bu tarz pozisyonlara. uzaktan çalışma imkanı sunanlar da var

siz hangi alanda çalışmak isterdiniz?"""

        elif action == "yatirim":
            return f"""{company} yatırım almış

{company_lower} ciddi bi yatırım kapattı

{details_clean}

yatırımcılar bu şirkete güveniyor demek ki. büyüme planları var, sektörde rekabet kızışıyor

aslında teknoloji tarafında yatırımlar hız kesmiyor. bu tarz haberler sektörün nereye gittiğini gösteriyor biraz

girişimcilik hakkında ne düşünüyorsunuz?"""

        elif action == "lansman":
            return f"""{company} yeni bi şey duyurdu

{company_lower} ilginç bi duyuru yaptı

{details_clean}

teknoloji sürekli gelişiyor ya, yeni araçlar çıkıyor. rekabet arttıkça biz kullanıcılar kazanıyoruz aslında

bu tarz yenilikleri takip etmekte fayda var. bugün çıkan bi araç yarın işini kolaylaştırabilir

yeni teknolojileri denemeyi sever misiniz?"""

        elif action == "acik_kaynak":
            return f"""{company} açık kaynak

{company_lower} açık kaynak bi proje

{details_clean}

açık kaynak neden önemli biliyo musunuz? herkes kullanabilir, ücretsiz. topluluk geliştiriyor, şeffaf

linux, git, python... hepsi açık kaynak. teknolojinin temeli bunlar aslında

siz açık kaynak projelere katkıda bulunuyo musunuz?"""

        else:
            # Genel template
            return f"""{company} gündemde

{company_lower} hakkında konuşuluyor

{details_clean}

teknoloji camiası bu konuyu tartışıyor. farklı görüşler var

bence takip etmekte fayda var. teknoloji dünyasında her gün yeni şeyler oluyor

siz bu konu hakkında ne düşünüyorsunuz?"""

    @classmethod
    def _simple_translate_title(cls, text: str) -> str:
        """Yaygın İngilizce kelimeleri Türkçe'ye çevir"""
        import re

        # Kapsamlı çeviri sözlüğü
        translations = {
            # Cümle kalıpları
            "What I learned": "Öğrendiklerim",
            "How to": "Nasıl yapılır",
            "Why you should": "Neden yapmalısınız",
            "It is free": "Ücretsiz",
            "It was the first": "İlk olarak",
            "I've been using": "Kullanıyorum",
            "I tried": "Denedim",
            "I preferred": "Tercih ettim",
            "can be played": "oynanabilir",
            "requires no subscription": "abonelik gerektirmiyor",
            "standalone": "bağımsız",
            "point-and-click": "tıkla-oyna tarzı",
            "adventure games": "macera oyunları",
            "graphical": "grafiksel",

            # Fiiller
            "building": "geliştirme",
            "creating": "oluşturma",
            "coding": "kodlama",
            "writing": "yazma",
            "testing": "test etme",
            "importing": "içe aktarma",
            "integrating": "entegre etme",
            "streamlines": "kolaylaştırıyor",
            "launches": "çıkardı",
            "announces": "duyurdu",
            "released": "yayınladı",
            "including": "dahil olmak üzere",
            "using": "kullanarak",

            # Sıfatlar
            "opinionated": "belirli kurallara sahip",
            "minimal": "minimal/sade",
            "free": "ücretsiz",
            "new": "yeni",
            "first": "ilk",
            "best": "en iyi",
            "top": "en popüler",
            "multiple": "birden fazla",
            "Windows-based": "Windows tabanlı",

            # İsimler - Teknoloji
            "agent": "ajan/asistan",
            "AI": "yapay zeka",
            "machine learning": "makine öğrenimi",
            "open source": "açık kaynak",
            "startup": "girişim",
            "update": "güncelleme",
            "security": "güvenlik",
            "privacy": "gizlilik",
            "data": "veri",
            "cloud": "bulut",
            "app": "uygulama",
            "tool": "araç",
            "tools": "araçlar",
            "feature": "özellik",
            "features": "özellikler",
            "platform": "platform",
            "platforms": "platformlar",
            "IDE": "geliştirme ortamı",
            "scripts": "scriptler",
            "graphics": "grafikler",
            "games": "oyunlar",
            "game": "oyun",
            "Game Studio": "Oyun Stüdyosu",

            # Zaman ifadeleri
            "In the past": "Geçtiğimiz",
            "three years": "üç yıl",
            "a year": "bir yıl",
            "half": "buçuk",

            # Bağlaçlar
            "and": "ve",
            "or": "veya",
            "but": "ama",
            "for": "için",
            "with": "ile",
            "from": "dan",
            "into": "içine",
            "finally": "sonunda",

            # Artikeller (kaldır)
            "The ": "",
            "A ": "",
            "An ": "",
        }

        result = text
        # Uzun ifadeleri önce çevir (sıralama önemli)
        sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

        for eng, tr in sorted_translations:
            if eng.lower() in result.lower():
                result = re.sub(re.escape(eng), tr, result, flags=re.IGNORECASE)

        return result.strip()

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
    "ai": {"name": "🤖 AI / Teknoloji", "desc": "AI, ChatGPT, LLM haberleri"},
    "football": {"name": "⚽ Futbol", "desc": "Transfer, maç sonuçları"},
    "all": {"name": "🔥 Gündem", "desc": "Türkiye gündemi"},
}


# Global instances
trending_discovery = TrendingDiscovery()
thread_generator = InformativeThreadGenerator()
