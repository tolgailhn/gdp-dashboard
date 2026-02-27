"""
AI Content Engine - X İçerik Keşif ve Viral Rewriter
=====================================================

Takip ettiğin AI hesaplarının tweetlerini çeker,
viral formatta senin gibi yeniden yazar.

Özellikler:
- Belirli AI hesaplarını takip
- Son X saat içindeki tweetleri çek
- Viral tweet kuralları ile yeniden yaz
- Hook + Teknik anlatım + CTA formatı
"""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import re
import urllib.parse

logger = logging.getLogger(__name__)


# ==============================================================================
# TAKİP EDİLECEK AI HESAPLARI
# ==============================================================================

AI_ACCOUNTS = {
    # Şirket hesapları
    "OpenAI": "OpenAI",
    "Anthropic": "AnthropicAI",
    "Google DeepMind": "GoogleDeepMind",
    "Google AI": "GoogleAI",
    "Meta AI": "MetaAI",
    "Mistral AI": "MistralAI",
    "xAI": "xaboratory",
    "Hugging Face": "huggingface",
    "Stability AI": "StabilityAI",
    "Midjourney": "midaboratory",
    "Runway": "runwayml",
    "Perplexity": "peraboratority_ai",

    # Önemli kişiler
    "Sam Altman": "sama",
    "Elon Musk": "elonmusk",
    "Andrej Karpathy": "karpathy",
    "Yann LeCun": "ylecun",
    "Jim Fan": "DrJimFan",
    "Emad Mostaque": "EMostaque",
    "Dario Amodei": "DarioAmodei",

    # AI haber/içerik
    "AI Breakfast": "aiaboratorteakfast",
    "The AI Daily": "theaidaily",
}

# Futbol hesapları
FOOTBALL_ACCOUNTS = {
    "Fabrizio Romano": "FabrizioRomano",
    "Yağız Sabuncuoğlu": "yaboratorgaboratorsaboratornc",
    "Sercan Hamzaoğlu": "seraboratorcanhamzaogl",
    "Nexus": "NexusTransfer",
}

# ==============================================================================
# VİRAL TWEET KURALLARI
# ==============================================================================

VIRAL_RULES = {
    "hook_templates": [
        "🚨 BREAKING: {topic}",
        "Bu büyük bir gelişme: {topic}",
        "{topic} - ve bu her şeyi değiştirecek",
        "Dikkat: {topic} açıklandı",
        "🔥 {topic} hakkında bilmeniz gereken her şey:",
        "Herkes {topic}'dan bahsediyor. İşte neden önemli:",
        "{topic} geldi. İşte detaylar:",
        "⚡ Az önce {topic} duyuruldu",
    ],

    "structure": {
        "hook": "İlk cümle dikkat çekmeli - şok edici, merak uyandıran",
        "context": "Neden önemli? Bağlam ver",
        "details": "Teknik detaylar - ama basit anlat",
        "impact": "Bu seni nasıl etkiler?",
        "cta": "Etkileşim çağrısı - soru sor veya düşünce iste",
    },

    "formatting": {
        "use_emojis": True,  # Ama abartma
        "line_breaks": True,  # Her cümle ayrı satır
        "bullet_points": True,  # Listeler kullan
        "max_length": 2000,  # X Premium
        "hashtag_count": 2,  # Max 2-3 hashtag
    },

    "engagement_triggers": [
        "Ne düşünüyorsunuz?",
        "Siz bu konuda ne düşünüyorsunuz?",
        "Yorumlarda tartışalım",
        "Bu sizi nasıl etkileyecek?",
        "Katılıyor musunuz?",
        "RT'leyin herkes görsün",
    ],
}


@dataclass
class SourceTweet:
    """Kaynak tweet verisi"""
    id: str
    author: str
    author_name: str
    text: str
    url: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    created_at: str = ""
    media_urls: List[str] = field(default_factory=list)


@dataclass
class ViralTweet:
    """Viral formatta yeniden yazılmış tweet"""
    original: SourceTweet
    rewritten_text: str
    hook: str
    body: str
    cta: str
    hashtags: List[str] = field(default_factory=list)
    char_count: int = 0
    viral_score: float = 0.0  # 0-100 arası tahmin


class AIContentEngine:
    """
    AI içerik keşif ve viral rewriter motoru.

    Kullanım:
    >>> engine = AIContentEngine(auth_token, ct0)
    >>> tweets = engine.get_ai_content(hours=12)
    >>> viral = engine.rewrite_viral(tweets[0])
    """

    def __init__(self, auth_token: str = None, ct0: str = None):
        # Twitter auth
        self.auth_token = auth_token or "75dbe5f8894451b851b2d362d6bec9760d59272b"
        self.ct0 = ct0 or "9b77d23bbc8b17f6289acce782f90070201db154d3507f32acd5999039766982512ebd8cc4b54b1461448dc62c1167a599e1dac53304d6cd2d5ce4a63041c367a31fd8de37425c287c0fadf1908d3324"

        self.session = requests.Session()
        self.base_headers = {
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "Cookie": f"auth_token={self.auth_token}; ct0={self.ct0}",
            "X-Csrf-Token": self.ct0,
            "X-Twitter-Auth-Type": "OAuth2Session",
            "X-Twitter-Active-User": "yes",
            "X-Twitter-Client-Language": "tr",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "*/*",
        }

        # AI generator (lazy load)
        self._ai_generator = None

    @property
    def ai_generator(self):
        """Lazy load AI generator"""
        if self._ai_generator is None:
            try:
                from src.content.tweet_generator import TweetGenerator
                self._ai_generator = TweetGenerator()
            except:
                pass
        return self._ai_generator

    # ==========================================================================
    # TWEET ÇEKME
    # ==========================================================================

    def get_ai_content(self, hours: int = 12, limit: int = 20) -> List[SourceTweet]:
        """
        AI hesaplarından son X saat içindeki tweetleri çek.

        Args:
            hours: Kaç saat geriye git
            limit: Max kaç tweet

        Returns:
            SourceTweet listesi, engagement'a göre sıralı
        """
        all_tweets = []

        # 1. Önce takip edilen hesapların tweetlerini çek
        for name, username in list(AI_ACCOUNTS.items())[:15]:  # İlk 15 hesap
            tweets = self._get_user_tweets(username, hours)
            all_tweets.extend(tweets)

        # 2. AI arama sorguları
        search_queries = [
            "GPT-5 OR GPT5 OR Claude OR Gemini",
            "AI model release OR announcement",
            "yapay zeka yeni model",
            "ChatGPT update OR feature",
            "LLM benchmark OR breakthrough",
        ]

        for query in search_queries:
            tweets = self._search_tweets(query, hours)
            all_tweets.extend(tweets)

        # Duplicate'leri kaldır
        seen_ids = set()
        unique_tweets = []
        for tweet in all_tweets:
            if tweet.id not in seen_ids:
                seen_ids.add(tweet.id)
                unique_tweets.append(tweet)

        # Engagement'a göre sırala
        unique_tweets.sort(
            key=lambda t: t.likes + t.retweets * 2 + t.replies * 3,
            reverse=True
        )

        return unique_tweets[:limit]

    def get_football_content(self, hours: int = 6, limit: int = 15) -> List[SourceTweet]:
        """Futbol hesaplarından içerik çek"""
        all_tweets = []

        for name, username in FOOTBALL_ACCOUNTS.items():
            tweets = self._get_user_tweets(username, hours)
            all_tweets.extend(tweets)

        # Transfer aramaları
        queries = [
            "transfer news OR imza",
            "Galatasaray OR Fenerbahçe OR Beşiktaş transfer",
        ]

        for query in queries:
            tweets = self._search_tweets(query, hours)
            all_tweets.extend(tweets)

        # Sırala
        all_tweets.sort(key=lambda t: t.likes + t.retweets * 2, reverse=True)
        return all_tweets[:limit]

    def _get_user_tweets(self, username: str, hours: int = 12) -> List[SourceTweet]:
        """Belirli bir kullanıcının son tweetlerini çek"""
        tweets = []

        try:
            # User timeline endpoint
            # Önce user_id'yi bul
            user_id = self._get_user_id(username)
            if not user_id:
                return []

            url = "https://twitter.com/i/api/graphql/V7H0Ap3_Hh2FyS75OCDO3Q/UserTweets"

            variables = {
                "userId": user_id,
                "count": 20,
                "includePromotedContent": False,
                "withQuickPromoteEligibilityTweetFields": True,
                "withVoice": True,
                "withV2Timeline": True,
            }

            features = {
                "rweb_lists_timeline_redesign_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "tweetypie_unmention_optimization_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": False,
                "tweet_awards_web_tipping_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "responsive_web_media_download_video_enabled": False,
                "responsive_web_enhance_cards_enabled": False,
            }

            params = {
                "variables": json.dumps(variables),
                "features": json.dumps(features),
            }

            response = self.session.get(
                url,
                params=params,
                headers=self.base_headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                tweets = self._parse_timeline_tweets(data, username, hours)
                logger.info(f"@{username}'dan {len(tweets)} tweet alındı")

        except Exception as e:
            logger.debug(f"@{username} tweet çekme hatası: {e}")

        return tweets

    def _get_user_id(self, username: str) -> Optional[str]:
        """Username'den user_id bul"""
        try:
            url = "https://twitter.com/i/api/graphql/G3KGOASz96M-Qu0nwmGXNg/UserByScreenName"

            variables = {
                "screen_name": username,
                "withSafetyModeUserFields": True,
            }

            features = {
                "hidden_profile_likes_enabled": True,
                "hidden_profile_subscriptions_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "subscriptions_verification_info_is_identity_verified_enabled": True,
                "subscriptions_verification_info_verified_since_enabled": True,
                "highlights_tweets_tab_ui_enabled": True,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True,
            }

            params = {
                "variables": json.dumps(variables),
                "features": json.dumps(features),
            }

            response = self.session.get(
                url,
                params=params,
                headers=self.base_headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                user_data = data.get("data", {}).get("user", {}).get("result", {})
                return user_data.get("rest_id")

        except Exception as e:
            logger.debug(f"User ID bulunamadı @{username}: {e}")

        return None

    def _search_tweets(self, query: str, hours: int = 12) -> List[SourceTweet]:
        """Twitter'da arama yap"""
        tweets = []

        try:
            url = "https://twitter.com/i/api/2/search/adaptive.json"

            # Zaman filtresi
            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime("%Y-%m-%d")

            full_query = f"{query} since:{since_str} min_faves:100"

            params = {
                "q": full_query,
                "tweet_search_mode": "live",
                "query_source": "typed_query",
                "count": "20",
                "result_filter": "top",
            }

            response = self.session.get(
                url,
                params=params,
                headers=self.base_headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get("globalObjects", {}).get("tweets", {})
                users_data = data.get("globalObjects", {}).get("users", {})

                for tweet_id, tweet_info in list(tweets_data.items())[:15]:
                    user_id = tweet_info.get("user_id_str", "")
                    user_info = users_data.get(user_id, {})

                    tweet = SourceTweet(
                        id=tweet_id,
                        author=user_info.get("screen_name", "unknown"),
                        author_name=user_info.get("name", "Unknown"),
                        text=tweet_info.get("full_text", ""),
                        url=f"https://twitter.com/i/status/{tweet_id}",
                        likes=tweet_info.get("favorite_count", 0),
                        retweets=tweet_info.get("retweet_count", 0),
                        replies=tweet_info.get("reply_count", 0),
                        created_at=tweet_info.get("created_at", ""),
                    )
                    tweets.append(tweet)

        except Exception as e:
            logger.debug(f"Arama hatası '{query}': {e}")

        return tweets

    def _parse_timeline_tweets(self, data: dict, username: str, hours: int) -> List[SourceTweet]:
        """GraphQL timeline response'unu parse et"""
        tweets = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        try:
            instructions = (
                data.get("data", {})
                .get("user", {})
                .get("result", {})
                .get("timeline_v2", {})
                .get("timeline", {})
                .get("instructions", [])
            )

            for instruction in instructions:
                entries = instruction.get("entries", [])

                for entry in entries:
                    content = entry.get("content", {})
                    item_content = content.get("itemContent", {})
                    tweet_results = item_content.get("tweet_results", {})
                    result = tweet_results.get("result", {})

                    # Tweet verisini çıkar
                    legacy = result.get("legacy", {})
                    if not legacy:
                        continue

                    # Zaman kontrolü
                    created_at_str = legacy.get("created_at", "")
                    if created_at_str:
                        try:
                            created_at = datetime.strptime(
                                created_at_str,
                                "%a %b %d %H:%M:%S %z %Y"
                            )
                            if created_at.replace(tzinfo=None) < cutoff_time:
                                continue
                        except:
                            pass

                    tweet = SourceTweet(
                        id=legacy.get("id_str", ""),
                        author=username,
                        author_name=result.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("name", username),
                        text=legacy.get("full_text", ""),
                        url=f"https://twitter.com/{username}/status/{legacy.get('id_str', '')}",
                        likes=legacy.get("favorite_count", 0),
                        retweets=legacy.get("retweet_count", 0),
                        replies=legacy.get("reply_count", 0),
                        created_at=created_at_str,
                    )
                    tweets.append(tweet)

        except Exception as e:
            logger.debug(f"Timeline parse hatası: {e}")

        return tweets

    # ==========================================================================
    # VİRAL REWRITER
    # ==========================================================================

    def rewrite_viral(self, source: SourceTweet, style: str = "informative") -> ViralTweet:
        """
        Kaynak tweet'i viral formatta yeniden yaz.

        Args:
            source: Orijinal tweet
            style: "informative", "opinion", "thread"

        Returns:
            ViralTweet objesi
        """
        # AI ile yeniden yaz
        if self.ai_generator:
            return self._rewrite_with_ai(source, style)
        else:
            return self._rewrite_template(source, style)

    def _rewrite_with_ai(self, source: SourceTweet, style: str) -> ViralTweet:
        """AI kullanarak viral tweet oluştur"""

        prompt = f"""Sen bir viral tweet yazarısın. Aşağıdaki tweet'i kendi dilinde yeniden yaz.

KAYNAK TWEET:
@{source.author}: {source.text}

VİRAL TWEET KURALLARI:
1. HOOK: İlk cümle dikkat çekmeli (🚨, ⚡, 🔥 gibi emoji ile başlayabilir)
2. BAĞLAM: Neden önemli olduğunu açıkla
3. DETAYLAR: Teknik bilgileri basit anlat
4. ETKİ: Bu gelişme insanları nasıl etkiler
5. CTA: Sonunda etkileşim çağrısı (soru sor)

FORMAT:
- Her önemli nokta yeni satırda
- Bullet point kullan (•)
- 1-2 hashtag ekle
- Max 2000 karakter (X Premium)

STİL: {style}
- informative: Bilgilendirici, nesnel
- opinion: Yorum ekle, düşünceni söyle
- thread: Uzun, detaylı anlatım

Sadece tweet metnini yaz, başka bir şey yazma."""

        try:
            from anthropic import Anthropic
            client = Anthropic()

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            rewritten = response.content[0].text.strip()

            # Parse et
            lines = rewritten.split('\n')
            hook = lines[0] if lines else ""
            body = '\n'.join(lines[1:-1]) if len(lines) > 2 else rewritten
            cta = lines[-1] if len(lines) > 1 else ""

            # Hashtag'leri çıkar
            hashtags = re.findall(r'#\w+', rewritten)

            return ViralTweet(
                original=source,
                rewritten_text=rewritten,
                hook=hook,
                body=body,
                cta=cta,
                hashtags=hashtags,
                char_count=len(rewritten),
                viral_score=self._calculate_viral_score(rewritten, source),
            )

        except Exception as e:
            logger.error(f"AI rewrite hatası: {e}")
            return self._rewrite_template(source, style)

    def _rewrite_template(self, source: SourceTweet, style: str) -> ViralTweet:
        """Template ile viral tweet oluştur (AI yoksa)"""

        # Basit template
        hook = f"🚨 {source.author_name}'dan önemli paylaşım:"
        body = f"\n\n{source.text[:500]}"
        cta = "\n\nNe düşünüyorsunuz? 👇"

        # Hashtag ekle
        hashtags = ["#AI", "#Teknoloji"]
        hashtag_str = " ".join(hashtags)

        full_text = f"{hook}{body}{cta}\n\n{hashtag_str}"

        return ViralTweet(
            original=source,
            rewritten_text=full_text,
            hook=hook,
            body=body,
            cta=cta,
            hashtags=hashtags,
            char_count=len(full_text),
            viral_score=50.0,  # Default
        )

    def _calculate_viral_score(self, text: str, source: SourceTweet) -> float:
        """Viral potansiyel skoru hesapla"""
        score = 50.0  # Base

        # Hook varsa +10
        if text.startswith(('🚨', '⚡', '🔥', 'BREAKING', 'Bu büyük')):
            score += 10

        # Soru varsa +10
        if '?' in text:
            score += 10

        # Emoji varsa +5
        if re.search(r'[\U0001F300-\U0001F9FF]', text):
            score += 5

        # Line break varsa +5
        if '\n\n' in text:
            score += 5

        # Kaynak engagement yüksekse +15
        if source.likes > 1000:
            score += 15
        elif source.likes > 100:
            score += 10

        # Hashtag varsa +5
        if '#' in text:
            score += 5

        return min(score, 100.0)

    # ==========================================================================
    # GÜNDEM (TRENDING)
    # ==========================================================================

    def get_trending_topics(self) -> List[dict]:
        """Türkiye gündemini çek"""
        topics = []

        try:
            url = "https://twitter.com/i/api/2/guide.json"

            params = {
                "include_profile_interstitial_type": "1",
                "count": "20",
            }

            response = self.session.get(
                url,
                params=params,
                headers=self.base_headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
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
                                volume = trend_data.get("trendMetadata", {}).get("metaDescription", "")

                                topics.append({
                                    "name": name,
                                    "volume": volume,
                                    "url": f"https://twitter.com/search?q={urllib.parse.quote(name)}",
                                })

        except Exception as e:
            logger.debug(f"Trending çekme hatası: {e}")

        return topics[:20]


# ==============================================================================
# TEST
# ==============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = AIContentEngine()

    print("=== AI İçerikleri (son 12 saat) ===")
    tweets = engine.get_ai_content(hours=12, limit=5)

    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. @{tweet.author}: {tweet.text[:100]}...")
        print(f"   ❤️ {tweet.likes} | 🔄 {tweet.retweets}")

    if tweets:
        print("\n=== Viral Rewrite ===")
        viral = engine.rewrite_viral(tweets[0])
        print(viral.rewritten_text)
        print(f"\nViral Score: {viral.viral_score}/100")
