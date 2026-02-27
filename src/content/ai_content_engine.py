"""
AI Content Engine v2 - Gerçek AI Haber Keşfi
=============================================

X'ten gerçek AI haberlerini bulur:
- Yeni model duyuruları (GPT-5, Claude 4, Gemini 2 vs.)
- Özellik güncellemeleri
- Benchmark sonuçları
- Araştırma makaleleri

Araştırma yapıp, seçtiğin tonda yeniden yazar.
"""

import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import re
import urllib.parse

logger = logging.getLogger(__name__)


# ==============================================================================
# AI HABER ARAMA SORGULARI (Hesap yerine konuya odaklan)
# ==============================================================================

AI_SEARCH_QUERIES = [
    # Model duyuruları
    "GPT-5 OR GPT5 OR GPT-4.5 announcement",
    "Claude 4 OR Claude 3.5 Opus release",
    "Gemini 2 OR Gemini Ultra new",
    "Llama 4 OR Llama 3.1 Meta release",

    # Önemli gelişmeler
    "AI breakthrough announcement",
    "new AI model release 2024",
    "OpenAI announcement new",
    "Anthropic Claude update",
    "Google AI Gemini news",

    # Türkçe aramalar
    "yapay zeka yeni model",
    "ChatGPT güncelleme",
    "AI Türkiye",
]

# Güvenilir AI hesapları (sadece bunlardan çek)
TRUSTED_AI_ACCOUNTS = [
    "OpenAI",
    "AnthropicAI",
    "GoogleAI",
    "GoogleDeepMind",
    "MetaAI",
    "MistralAI",
    "huggingface",
    "sama",  # Sam Altman
    "karpathy",  # Andrej Karpathy
    "ylecun",  # Yann LeCun
    "DrJimFan",  # Jim Fan
]

# Futbol hesapları
FOOTBALL_ACCOUNTS = {
    "Fabrizio Romano": "FabrizioRomano",
    "Transfer News": "TransferNewsCen",
}

# ==============================================================================
# YAZI TONLARI / STİLLERİ
# ==============================================================================

WRITING_STYLES = {
    "samimi": {
        "name": "🗣️ Samimi (Varsayılan)",
        "description": "Arkadaşına anlatır gibi, doğal",
        "rules": [
            "küçük harfle yaz",
            "kısa cümleler kur",
            "ya şimdi, bence, aslında gibi bağlaçlar kullan",
            "emoji az kullan (max 1-2)",
            "soru sor sonunda",
        ],
        "example": "ya şimdi openai bi şey duyurdu. gpt-5 geliyor gibi görünüyor. bence büyük iş bu, sizce?"
    },
    "profesyonel": {
        "name": "💼 Profesyonel",
        "description": "Ciddi, bilgilendirici ton",
        "rules": [
            "düzgün cümle yapısı",
            "teknik terimler kullan",
            "emoji kullanma",
            "kaynak belirt",
            "analiz ekle",
        ],
        "example": "OpenAI, GPT-5 modelini duyurdu. Yeni model, önceki versiyona göre %40 daha hızlı çalışıyor. Detaylar için kaynak linkine bakabilirsiniz."
    },
    "heyecanli": {
        "name": "🔥 Heyecanlı",
        "description": "Enerjik, dikkat çekici",
        "rules": [
            "BÜYÜK HARF başlık",
            "emoji bol kullan",
            "kısa ve vurgulu cümleler",
            "ünlem işaretleri",
            "aciliyet hissi ver",
        ],
        "example": "🚨 BREAKING: GPT-5 DUYURULDU! 🔥\n\nBu DEVASA bir gelişme!\n\nİşte bilmeniz gerekenler:\n• Daha hızlı\n• Daha akıllı\n• Daha ucuz\n\nRT yapın herkes görsün! 🚀"
    },
    "analist": {
        "name": "📊 Analist",
        "description": "Derinlemesine analiz, karşılaştırma",
        "rules": [
            "veri ve rakamlar ekle",
            "karşılaştırma yap",
            "artı ve eksileri listele",
            "gelecek tahmini yap",
            "profesyonel ton",
        ],
        "example": "GPT-5 vs Claude 3.5 karşılaştırması:\n\n📈 Benchmark sonuçları:\n• MMLU: GPT-5 %94, Claude %91\n• Kod: Yaklaşık eşit\n• Hız: GPT-5 %20 önde\n\nSonuç: Her ikisi de güçlü, kullanım amacına göre seçim yapılmalı."
    },
}

# ==============================================================================
# MODEL BİLGİSİ
# ==============================================================================

AVAILABLE_MODELS = {
    "claude-sonnet": {
        "id": "claude-sonnet-4-20250514",
        "name": "Claude Sonnet 4",
        "provider": "Anthropic",
        "description": "Hızlı ve dengeli (varsayılan)",
        "cost": "Orta",
    },
    "claude-opus": {
        "id": "claude-opus-4-20250514",
        "name": "Claude Opus 4",
        "provider": "Anthropic",
        "description": "En güçlü, en detaylı",
        "cost": "Yüksek",
    },
    "claude-haiku": {
        "id": "claude-haiku-4-5-20251001",
        "name": "Claude Haiku 4.5",
        "provider": "Anthropic",
        "description": "En hızlı, basit işler için",
        "cost": "Düşük",
    },
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
    is_ai_news: bool = False  # Gerçek AI haberi mi?
    topic_summary: str = ""  # Konu özeti


@dataclass
class ResearchResult:
    """Araştırma sonucu"""
    topic: str
    summary: str
    key_points: List[str]
    sources: List[str]
    related_tweets: List[str]


@dataclass
class ViralTweet:
    """Viral formatta yeniden yazılmış tweet"""
    original: SourceTweet
    rewritten_text: str
    style_used: str
    model_used: str
    research: Optional[ResearchResult] = None
    char_count: int = 0
    viral_score: float = 0.0


class AIContentEngine:
    """
    AI içerik keşif ve viral rewriter motoru v2.

    Özellikler:
    - AI haber araması (hesap yerine konu bazlı)
    - Araştırma yapıp yazma
    - Ton/stil seçimi
    - Model seçimi
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

        # Varsayılan model
        self.current_model = "claude-sonnet"

    def get_ai_news(self, hours: int = 12, limit: int = 15) -> tuple:
        """
        AI haberlerini bul - KONU BAZLI ARAMA

        Returns:
            (tweets_list, error_message)
        """
        all_tweets = []
        seen_ids = set()
        errors = []

        # 1. AI arama sorguları ile ara
        for query in AI_SEARCH_QUERIES[:6]:
            tweets, err = self._search_ai_tweets(query, hours)
            if err:
                errors.append(err)
            for tweet in tweets:
                if tweet.id not in seen_ids:
                    seen_ids.add(tweet.id)
                    all_tweets.append(tweet)

        # 2. Güvenilir hesaplardan da kontrol et
        for username in TRUSTED_AI_ACCOUNTS[:5]:
            tweets, err = self._get_user_recent_tweets(username, hours)
            if err:
                errors.append(err)
            for tweet in tweets:
                if tweet.id not in seen_ids:
                    seen_ids.add(tweet.id)
                    if self._is_ai_related(tweet.text):
                        tweet.is_ai_news = True
                        all_tweets.append(tweet)

        # 3. AI haberi olmayanları filtrele
        ai_tweets = [t for t in all_tweets if t.is_ai_news or self._is_ai_related(t.text)]

        # 4. Sırala
        ai_tweets.sort(
            key=lambda t: (t.likes + t.retweets * 2) * (2 if t.is_ai_news else 1),
            reverse=True
        )

        # Hata mesajı
        error_msg = None
        if not ai_tweets and errors:
            error_msg = errors[0]  # İlk hatayı göster

        return ai_tweets[:limit], error_msg

    def _is_ai_related(self, text: str) -> bool:
        """Metin AI ile ilgili mi?"""
        text_lower = text.lower()

        ai_keywords = [
            "gpt", "claude", "gemini", "llama", "mistral",
            "ai", "artificial intelligence", "yapay zeka",
            "machine learning", "deep learning", "neural",
            "chatgpt", "openai", "anthropic", "google ai",
            "model", "benchmark", "training", "inference",
            "llm", "language model", "transformer",
        ]

        # En az 2 keyword geçmeli
        matches = sum(1 for kw in ai_keywords if kw in text_lower)
        return matches >= 2

    def _search_ai_tweets(self, query: str, hours: int) -> tuple:
        """AI konulu tweet ara - returns (tweets, error)"""
        tweets = []
        error = None

        try:
            url = "https://twitter.com/i/api/2/search/adaptive.json"

            # Zaman filtresi
            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime("%Y-%m-%d")

            # Min engagement filtresi
            full_query = f"{query} min_faves:50 since:{since_str} -filter:replies"

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

                for tweet_id, tweet_info in list(tweets_data.items())[:10]:
                    user_id = tweet_info.get("user_id_str", "")
                    user_info = users_data.get(user_id, {})

                    text = tweet_info.get("full_text", "")

                    # RT'leri atla
                    if text.startswith("RT @"):
                        continue

                    tweet = SourceTweet(
                        id=tweet_id,
                        author=user_info.get("screen_name", "unknown"),
                        author_name=user_info.get("name", "Unknown"),
                        text=text,
                        url=f"https://twitter.com/i/status/{tweet_id}",
                        likes=tweet_info.get("favorite_count", 0),
                        retweets=tweet_info.get("retweet_count", 0),
                        replies=tweet_info.get("reply_count", 0),
                        created_at=tweet_info.get("created_at", ""),
                        is_ai_news=True,
                    )
                    tweets.append(tweet)

                logger.info(f"'{query}' aramasından {len(tweets)} tweet bulundu")
            elif response.status_code == 401:
                error = "Token geçersiz veya süresi dolmuş. Yeni token al."
            elif response.status_code == 429:
                error = "Rate limit aşıldı. Biraz bekle."
            else:
                error = f"Twitter API hatası: {response.status_code}"

        except Exception as e:
            error = f"Bağlantı hatası: {str(e)[:100]}"
            logger.debug(f"Arama hatası '{query}': {e}")

        return tweets, error

    def _get_user_recent_tweets(self, username: str, hours: int) -> tuple:
        """Kullanıcının son tweetlerini çek - returns (tweets, error)"""
        tweets = []
        error = None

        try:
            url = "https://twitter.com/i/api/2/search/adaptive.json"

            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime("%Y-%m-%d")

            params = {
                "q": f"from:{username} since:{since_str}",
                "tweet_search_mode": "live",
                "count": "10",
            }

            response = self.session.get(
                url,
                params=params,
                headers=self.base_headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get("globalObjects", {}).get("tweets", {})
                users_data = data.get("globalObjects", {}).get("users", {})

                for tweet_id, tweet_info in list(tweets_data.items())[:5]:
                    user_id = tweet_info.get("user_id_str", "")
                    user_info = users_data.get(user_id, {})

                    text = tweet_info.get("full_text", "")

                    if text.startswith("RT @"):
                        continue

                    tweet = SourceTweet(
                        id=tweet_id,
                        author=user_info.get("screen_name", username),
                        author_name=user_info.get("name", username),
                        text=text,
                        url=f"https://twitter.com/i/status/{tweet_id}",
                        likes=tweet_info.get("favorite_count", 0),
                        retweets=tweet_info.get("retweet_count", 0),
                        created_at=tweet_info.get("created_at", ""),
                    )
                    tweets.append(tweet)
            elif response.status_code == 401:
                error = "Token geçersiz"

        except Exception as e:
            error = str(e)[:50]
            logger.debug(f"@{username} hatası: {e}")

        return tweets, error

    def get_football_content(self, hours: int = 6, limit: int = 15) -> tuple:
        """Futbol haberlerini bul - returns (tweets, error)"""
        all_tweets = []
        errors = []

        queries = [
            "transfer news breaking",
            "Galatasaray OR Fenerbahçe OR Beşiktaş transfer",
            "Premier League transfer",
        ]

        for query in queries:
            tweets, err = self._search_ai_tweets(query, hours)
            if err:
                errors.append(err)
            all_tweets.extend(tweets)

        all_tweets.sort(key=lambda t: t.likes + t.retweets * 2, reverse=True)

        error_msg = errors[0] if not all_tweets and errors else None
        return all_tweets[:limit], error_msg

    # ==========================================================================
    # ARAŞTIRMA
    # ==========================================================================

    def research_topic(self, tweet: SourceTweet) -> ResearchResult:
        """
        Tweet konusunu araştır.
        - Konu ne hakkında?
        - Önemli noktalar neler?
        - Bağlam nedir?
        """
        topic = self._extract_topic(tweet.text)

        # AI ile araştırma yap
        try:
            from anthropic import Anthropic
            client = Anthropic()

            prompt = f"""Bu tweet hakkında kısa bir araştırma özeti yap:

Tweet: {tweet.text}
Yazar: @{tweet.author}

Şunları bul:
1. Konu ne hakkında? (1 cümle)
2. Neden önemli? (1 cümle)
3. Teknik detaylar (varsa, 2-3 madde)
4. Bağlam (bu gelişme neyin parçası?)

Kısa ve öz yaz, Türkçe."""

            response = client.messages.create(
                model=AVAILABLE_MODELS[self.current_model]["id"],
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            # Key points çıkar
            key_points = []
            for line in summary.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    key_points.append(line.lstrip('-•0123456789. '))

            return ResearchResult(
                topic=topic,
                summary=summary,
                key_points=key_points[:5],
                sources=[tweet.url],
                related_tweets=[],
            )

        except Exception as e:
            logger.error(f"Araştırma hatası: {e}")

            # Fallback - basit özet
            return ResearchResult(
                topic=topic,
                summary=f"@{tweet.author} bu konuda paylaşım yaptı.",
                key_points=[tweet.text[:200]],
                sources=[tweet.url],
                related_tweets=[],
            )

    def _extract_topic(self, text: str) -> str:
        """Tweet'ten ana konuyu çıkar"""
        # İlk cümleyi al
        sentences = re.split(r'[.!?\n]', text)
        if sentences:
            return sentences[0].strip()[:100]
        return text[:100]

    # ==========================================================================
    # VİRAL REWRITER
    # ==========================================================================

    def rewrite_viral(
        self,
        tweet: SourceTweet,
        style: str = "samimi",
        do_research: bool = True,
        model: str = None
    ) -> ViralTweet:
        """
        Tweet'i seçilen stilde yeniden yaz.

        Args:
            tweet: Kaynak tweet
            style: Yazım stili (samimi, profesyonel, heyecanli, analist)
            do_research: Önce araştırma yap mı?
            model: Kullanılacak model (None = varsayılan)
        """
        # Model seç
        model_key = model or self.current_model
        model_info = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS["claude-sonnet"])

        # Stil bilgisi
        style_info = WRITING_STYLES.get(style, WRITING_STYLES["samimi"])

        # Araştırma yap
        research = None
        if do_research:
            research = self.research_topic(tweet)

        # AI ile yeniden yaz
        try:
            from anthropic import Anthropic
            client = Anthropic()

            # Stil kurallarını formatla
            rules = "\n".join([f"- {r}" for r in style_info["rules"]])

            research_context = ""
            if research:
                research_context = f"""
ARAŞTIRMA SONUCU:
{research.summary}

ÖNEMLİ NOKTALAR:
{chr(10).join(['- ' + p for p in research.key_points])}
"""

            prompt = f"""Bu tweet'i kendi tarzımda yeniden yaz.

ORİJİNAL TWEET:
@{tweet.author}: {tweet.text}

{research_context}

YAZIM STİLİ: {style_info['name']}
{style_info['description']}

KURALLAR:
{rules}

ÖRNEK:
{style_info['example']}

ÖNEMLİ:
- Türkçe yaz
- İngilizce kelime kullanma (teknik terimler hariç)
- Orijinal tweet'in bilgisini kullan ama KOPYALAMA
- İnsansı, doğal bir dil kullan
- 800-1500 karakter arası

Sadece tweet metnini yaz, başka bir şey ekleme."""

            response = client.messages.create(
                model=model_info["id"],
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            rewritten = response.content[0].text.strip()

            # Tırnak işaretlerini temizle
            rewritten = rewritten.strip('"\'')

            return ViralTweet(
                original=tweet,
                rewritten_text=rewritten,
                style_used=style,
                model_used=model_info["name"],
                research=research,
                char_count=len(rewritten),
                viral_score=self._calculate_viral_score(rewritten, tweet),
            )

        except Exception as e:
            logger.error(f"Rewrite hatası: {e}")

            # Fallback
            return ViralTweet(
                original=tweet,
                rewritten_text=f"📢 {tweet.text[:500]}",
                style_used=style,
                model_used="Template",
                research=research,
                char_count=len(tweet.text),
                viral_score=30.0,
            )

    def _calculate_viral_score(self, text: str, source: SourceTweet) -> float:
        """Viral potansiyel skoru"""
        score = 50.0

        # Hook varsa +10
        if text.startswith(('🚨', '⚡', '🔥', 'ya ', 'Ya ')):
            score += 10

        # Soru varsa +10
        if '?' in text:
            score += 10

        # Satır atlama varsa +5
        if '\n\n' in text:
            score += 5

        # Kaynak yüksek engagement'lı ise +15
        if source.likes > 1000:
            score += 15
        elif source.likes > 100:
            score += 10

        # Uygun uzunluk (500-1500 arası) +10
        if 500 <= len(text) <= 1500:
            score += 10

        return min(score, 100.0)

    # ==========================================================================
    # GÜNDEM
    # ==========================================================================

    def get_trending_topics(self) -> List[dict]:
        """Türkiye gündemini çek"""
        topics = []

        try:
            url = "https://twitter.com/i/api/2/guide.json"
            params = {"count": "20"}

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
            logger.debug(f"Trending hatası: {e}")

        return topics[:20]


# Export için
AI_ACCOUNTS = {name: name for name in TRUSTED_AI_ACCOUNTS}


# ==============================================================================
# TEST
# ==============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = AIContentEngine()

    print("=== AI Haberleri (son 12 saat) ===")
    tweets = engine.get_ai_news(hours=12, limit=5)

    for i, tweet in enumerate(tweets, 1):
        print(f"\n{i}. @{tweet.author}: {tweet.text[:100]}...")
        print(f"   ❤️ {tweet.likes} | 🔄 {tweet.retweets}")

    if tweets:
        print("\n=== Araştırma + Viral Rewrite ===")
        viral = engine.rewrite_viral(tweets[0], style="samimi", do_research=True)
        print(f"Model: {viral.model_used}")
        print(f"Stil: {viral.style_used}")
        print(viral.rewritten_text)
        print(f"\nViral Score: {viral.viral_score}/100")
