"""
AI Content Engine v4 - XPatla Benzeri Viral Sistem
===================================================

Özellikler:
- Quote Tweet sistemi (araştırma + akıllı yazım)
- Derin araştırma (web search + bağlam)
- Hesap yönetimi (ekleme/çıkarma, filtreleme)
- İçerik filtreleme (gm/hello atlama)
- Format seçimi: Micro, Thunder (1500), Mega (2000)
- Gelişmiş viral skor
- Demo mod (test için)

API Seçenekleri:
- Twitter API v2 (Bearer Token) - Önerilen
- Cookie Auth (auth_token + ct0) - Yedek
"""

import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import re
import urllib.parse
import os

logger = logging.getLogger(__name__)

# Bird CLI devre dışı - sadece Direct API kullanılıyor
BIRD_CLI_AVAILABLE = False

# Demo mod - gerçek API çalışmadığında örnek veri göster
DEMO_MODE = os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes")


# ==============================================================================
# DEMO VERİLERİ - Test için örnek tweetler
# ==============================================================================

DEMO_TWEETS = [
    {
        "id": "demo_1",
        "author": "OpenAI",
        "author_name": "OpenAI",
        "text": "Introducing GPT-5: Our most capable model yet. 2x faster, multimodal by default, and available today via API. Here's what's new...",
        "likes": 125000,
        "retweets": 45000,
        "url": "https://twitter.com/OpenAI/status/demo1",
    },
    {
        "id": "demo_2",
        "author": "AnthropicAI",
        "author_name": "Anthropic",
        "text": "Claude 4 is here. Extended context to 500K tokens, improved reasoning, and new computer use capabilities. Try it now.",
        "likes": 89000,
        "retweets": 32000,
        "url": "https://twitter.com/AnthropicAI/status/demo2",
    },
    {
        "id": "demo_3",
        "author": "GoogleAI",
        "author_name": "Google AI",
        "text": "Gemini 2.5 Pro: New benchmarks show significant improvements in coding, math, and multilingual tasks. Available in AI Studio.",
        "likes": 67000,
        "retweets": 21000,
        "url": "https://twitter.com/GoogleAI/status/demo3",
    },
    {
        "id": "demo_4",
        "author": "karpathy",
        "author_name": "Andrej Karpathy",
        "text": "Just tested the new models. My quick take: GPT-5 excels at creative tasks, Claude 4 at reasoning, Gemini at multimodal. No clear winner yet.",
        "likes": 45000,
        "retweets": 12000,
        "url": "https://twitter.com/karpathy/status/demo4",
    },
    {
        "id": "demo_5",
        "author": "sama",
        "author_name": "Sam Altman",
        "text": "AGI is closer than most people think. The progress in the last 6 months has been incredible. More announcements coming soon.",
        "likes": 156000,
        "retweets": 67000,
        "url": "https://twitter.com/sama/status/demo5",
    },
]


# ==============================================================================
# İÇERİK FİLTRELEME - Gereksiz tweetleri atla
# ==============================================================================

SKIP_PATTERNS = [
    # Selamlaşmalar
    r"^(gm|gn|good morning|good night|günaydın|iyi geceler|selam|merhaba|hello|hi|hey)\s*[!.]*$",
    r"^(gm|gn)\s+(everyone|all|fam|friends)",
    # Boş etkileşimler
    r"^(rt if|like if|follow me|takip|beğen)",
    r"^(thanks|thank you|teşekkür)",
    # Çok kısa ve anlamsız
    r"^.{1,15}$",  # 15 karakterden kısa
    # Sadece emoji
    r"^[\U0001F300-\U0001F9FF\s]+$",
    # Sadece mention
    r"^@\w+\s*$",
]

KEEP_PATTERNS = [
    # Duyurular
    r"(announc|releas|launch|introducing|presenting)",
    r"(duyuru|çıktı|yayınladık|tanıttık)",
    # Güncellemeler
    r"(update|upgrade|new version|v\d|güncelle)",
    # Model/Ürün
    r"(model|benchmark|api|feature|özellik)",
    # Breaking
    r"(breaking|just in|son dakika|flaş)",
]


def should_skip_tweet(text: str) -> bool:
    """Tweet atlanmalı mı? (gm, hello vs.)"""
    text_lower = text.lower().strip()

    # Çok kısa içerik
    if len(text_lower) < 20:
        # Ama önemli kelime varsa atla
        for pattern in KEEP_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        return True

    # Skip pattern'lere bakSkip pattern'lere bak
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def is_valuable_content(text: str) -> bool:
    """Değerli içerik mi? (duyuru, güncelleme vs.)"""
    text_lower = text.lower()

    for pattern in KEEP_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    # AI keywords
    ai_keywords = [
        "gpt", "claude", "gemini", "llama", "mistral",
        "openai", "anthropic", "model", "benchmark",
        "ai", "ml", "llm", "neural", "training",
    ]

    matches = sum(1 for kw in ai_keywords if kw in text_lower)
    return matches >= 2


# ==============================================================================
# HESAP YÖNETİMİ
# ==============================================================================

@dataclass
class TrackedAccount:
    """Takip edilen hesap"""
    username: str
    display_name: str
    category: str  # "ai", "football", "tech", "crypto"
    enabled: bool = True
    description: str = ""
    priority: int = 1  # 1-5, yüksek = öncelikli


# Varsayılan AI hesapları
DEFAULT_AI_ACCOUNTS: List[TrackedAccount] = [
    TrackedAccount("OpenAI", "OpenAI", "ai", True, "GPT modelleri", 5),
    TrackedAccount("AnthropicAI", "Anthropic", "ai", True, "Claude modelleri", 5),
    TrackedAccount("GoogleAI", "Google AI", "ai", True, "Gemini, Bard", 4),
    TrackedAccount("GoogleDeepMind", "DeepMind", "ai", True, "AlphaFold, Gemini", 4),
    TrackedAccount("MetaAI", "Meta AI", "ai", True, "Llama modelleri", 4),
    TrackedAccount("MistralAI", "Mistral AI", "ai", True, "Mistral modelleri", 3),
    TrackedAccount("xaboringcompany", "X AI (Grok)", "ai", True, "Grok modeli", 3),
    TrackedAccount("huggingface", "Hugging Face", "ai", True, "Açık kaynak AI", 3),
    TrackedAccount("sama", "Sam Altman", "ai", True, "OpenAI CEO", 4),
    TrackedAccount("karpathy", "Andrej Karpathy", "ai", True, "AI eğitimci", 4),
    TrackedAccount("ylecun", "Yann LeCun", "ai", True, "Meta Chief AI", 3),
    TrackedAccount("DrJimFan", "Jim Fan", "ai", True, "NVIDIA AI", 3),
    TrackedAccount("EMostaque", "Emad Mostaque", "ai", True, "Stability AI", 2),
]

DEFAULT_FOOTBALL_ACCOUNTS: List[TrackedAccount] = [
    TrackedAccount("FabrizioRomano", "Fabrizio Romano", "football", True, "Transfer haberleri", 5),
    TrackedAccount("David_Ornstein", "David Ornstein", "football", True, "Athletic", 4),
    TrackedAccount("Transfermarkt", "Transfermarkt", "football", True, "Transfer verileri", 3),
]


class AccountManager:
    """Takip edilen hesapları yönet"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.expanduser("~/.gdp_dashboard/accounts.json")
        self.accounts: Dict[str, TrackedAccount] = {}
        self._load_accounts()

    def _load_accounts(self):
        """Hesapları yükle veya varsayılanları kullan"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        acc = TrackedAccount(**item)
                        self.accounts[acc.username.lower()] = acc
                return
            except Exception as e:
                logger.warning(f"Hesap dosyası okunamadı: {e}")

        # Varsayılanları yükle
        for acc in DEFAULT_AI_ACCOUNTS + DEFAULT_FOOTBALL_ACCOUNTS:
            self.accounts[acc.username.lower()] = acc

    def _save_accounts(self):
        """Hesapları kaydet"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            data = [
                {
                    "username": acc.username,
                    "display_name": acc.display_name,
                    "category": acc.category,
                    "enabled": acc.enabled,
                    "description": acc.description,
                    "priority": acc.priority,
                }
                for acc in self.accounts.values()
            ]
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_account(self, username: str, display_name: str = None,
                    category: str = "ai", description: str = "") -> TrackedAccount:
        """Yeni hesap ekle"""
        username_clean = username.lstrip("@").lower()

        if username_clean in self.accounts:
            return self.accounts[username_clean]

        acc = TrackedAccount(
            username=username_clean,
            display_name=display_name or username_clean,
            category=category,
            enabled=True,
            description=description,
            priority=2,
        )
        self.accounts[username_clean] = acc
        self._save_accounts()
        return acc

    def remove_account(self, username: str) -> bool:
        """Hesap kaldır"""
        username_clean = username.lstrip("@").lower()
        if username_clean in self.accounts:
            del self.accounts[username_clean]
            self._save_accounts()
            return True
        return False

    def toggle_account(self, username: str) -> bool:
        """Hesabı aç/kapa"""
        username_clean = username.lstrip("@").lower()
        if username_clean in self.accounts:
            self.accounts[username_clean].enabled = not self.accounts[username_clean].enabled
            self._save_accounts()
            return self.accounts[username_clean].enabled
        return False

    def get_accounts(self, category: str = None, enabled_only: bool = True) -> List[TrackedAccount]:
        """Hesapları getir"""
        accounts = list(self.accounts.values())

        if category:
            accounts = [a for a in accounts if a.category == category]

        if enabled_only:
            accounts = [a for a in accounts if a.enabled]

        # Önceliğe göre sırala
        accounts.sort(key=lambda a: -a.priority)
        return accounts

    def get_usernames(self, category: str = None) -> List[str]:
        """Aktif hesap kullanıcı adlarını getir"""
        return [a.username for a in self.get_accounts(category=category)]


# ==============================================================================
# İÇERİK FORMATLARI (XPatla benzeri)
# ==============================================================================

class ContentFormat(Enum):
    """Tweet format türleri"""
    MICRO = ("micro", 280, "Kısa ve öz")
    STANDARD = ("standard", 500, "Normal tweet")
    EXTENDED = ("extended", 1000, "Uzun tweet")
    THUNDER = ("thunder", 1500, "Derinlemesine analiz")
    MEGA = ("mega", 2000, "Kapsamlı içerik")

    def __init__(self, key: str, max_chars: int, description: str):
        self.key = key
        self.max_chars = max_chars
        self.description = description


CONTENT_FORMATS = {
    "micro": ContentFormat.MICRO,
    "standard": ContentFormat.STANDARD,
    "extended": ContentFormat.EXTENDED,
    "thunder": ContentFormat.THUNDER,
    "mega": ContentFormat.MEGA,
}


# ==============================================================================
# YAZI TONLARI / STİLLERİ
# ==============================================================================

WRITING_STYLES = {
    "samimi": {
        "name": "🗣️ Samimi",
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
        "example": "OpenAI, GPT-5 modelini duyurdu. Yeni model, önceki versiyona göre %40 daha hızlı çalışıyor."
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
        "example": "🚨 BREAKING: GPT-5 DUYURULDU! 🔥\n\nBu DEVASA bir gelişme!\n\n• Daha hızlı\n• Daha akıllı\n\nRT yapın! 🚀"
    },
    "analist": {
        "name": "📊 Analist",
        "description": "Derinlemesine analiz, karşılaştırma",
        "rules": [
            "veri ve rakamlar ekle",
            "karşılaştırma yap",
            "artı ve eksileri listele",
            "gelecek tahmini yap",
        ],
        "example": "GPT-5 vs Claude 4 karşılaştırması:\n\n📈 Benchmark:\n• MMLU: GPT-5 %94, Claude %91\n• Hız: GPT-5 %20 önde"
    },
    "egitici": {
        "name": "📚 Eğitici",
        "description": "Öğretici, adım adım açıklama",
        "rules": [
            "basit dil kullan",
            "adım adım anlat",
            "örnekler ver",
            "sonunda özet yap",
        ],
        "example": "GPT-5 nedir?\n\n1. OpenAI'ın yeni modeli\n2. GPT-4'ten 2x hızlı\n3. Multimodal (görsel+metin)\n\nÖzetle: AI'da yeni çağ başlıyor."
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


# ==============================================================================
# VERİ YAPILARI
# ==============================================================================

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
    is_valuable: bool = False
    quoted_tweet: Optional['SourceTweet'] = None  # Quote edilen tweet
    content_type: str = ""  # "announcement", "opinion", "news", "thread"


@dataclass
class ResearchResult:
    """Derin araştırma sonucu"""
    topic: str
    summary: str
    key_points: List[str]
    technical_details: List[str]
    context: str  # Bu gelişme neyin parçası?
    comparison: str  # Rakiplerle karşılaştırma
    why_important: str  # Neden önemli?
    sources: List[str]
    related_tweets: List[str]


@dataclass
class QuoteTweet:
    """Quote tweet verisi"""
    original: SourceTweet
    quote_text: str
    style_used: str
    format_used: str
    model_used: str
    research: Optional[ResearchResult] = None
    char_count: int = 0
    viral_score: float = 0.0
    hook: str = ""  # Dikkat çekici açılış
    value_add: str = ""  # Eklenen değer


@dataclass
class ViralTweet:
    """Viral formatta tweet"""
    original: SourceTweet
    rewritten_text: str
    style_used: str
    format_used: str
    model_used: str
    research: Optional[ResearchResult] = None
    char_count: int = 0
    viral_score: float = 0.0


# ==============================================================================
# AI ARAMA SORGULARI
# ==============================================================================

AI_SEARCH_QUERIES = [
    # Model duyuruları
    "GPT-5 OR GPT5 announcement",
    "Claude 4 OR Claude Opus release",
    "Gemini 2 Ultra new",
    "Llama 4 Meta release",

    # Önemli gelişmeler
    "OpenAI announcement breaking",
    "Anthropic Claude update new",
    "Google AI Gemini news",
    "AI breakthrough 2024 2025",

    # Türkçe
    "yapay zeka yeni model",
    "ChatGPT güncelleme",
]


# ==============================================================================
# ANA MOTOR
# ==============================================================================

class AIContentEngine:
    """
    AI içerik keşif ve viral yazım motoru v4.

    XPatla benzeri özellikler:
    - Quote tweet sistemi
    - Derin araştırma
    - Hesap yönetimi
    - İçerik filtreleme
    - Format seçimi (micro → mega)
    """

    def __init__(self, auth_token: str = None, ct0: str = None, bearer_token: str = None):
        # Cookie auth (eski yöntem - yedek)
        self.auth_token = auth_token if auth_token else ""
        self.ct0 = ct0 if ct0 else ""

        # Twitter API v2 Bearer Token (resmi API)
        # URL decode yap (eğer encoded ise)
        if bearer_token:
            self.bearer_token = urllib.parse.unquote(bearer_token)
        else:
            self.bearer_token = ""

        self.session = requests.Session()

        # Cookie auth headers (yedek)
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

        # Twitter API v2 headers (resmi)
        self.api_v2_headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "GDP-Dashboard/1.0",
            "Accept": "application/json",
        }

        # Hesap yöneticisi
        self.account_manager = AccountManager()

        # Varsayılan ayarlar
        self.current_model = "claude-sonnet"
        self.current_format = "thunder"
        self.current_style = "samimi"

        # API modu: "v2" (resmi) veya "cookie" (yedek)
        self.api_mode = "v2" if self.bearer_token else "cookie"

    # ==========================================================================
    # BAĞLANTI TESTİ
    # ==========================================================================

    def test_connection(self) -> Tuple[bool, str]:
        """
        Twitter/X bağlantısını test et.

        Returns:
            (success, message)
        """
        # 1. Önce Twitter API v2 ile dene (resmi API)
        if self.bearer_token:
            try:
                url = "https://api.twitter.com/2/tweets/search/recent"
                params = {"query": "AI", "max_results": "10"}
                response = self.session.get(
                    url,
                    params=params,
                    headers=self.api_v2_headers,
                    timeout=10
                )

                if response.status_code == 200:
                    self.api_mode = "v2"
                    return True, "✅ Twitter API v2 bağlantısı başarılı!"
                elif response.status_code == 401:
                    return False, "❌ Bearer Token geçersiz. Developer Portal'dan kontrol et."
                elif response.status_code == 403:
                    return False, "❌ API erişimi reddedildi. App ayarlarını kontrol et."
                elif response.status_code == 429:
                    return False, "⚠️ Rate limit - biraz bekle (15 dk)"
                else:
                    # v2 başarısız, cookie auth dene
                    pass

            except Exception as e:
                logger.warning(f"API v2 test failed: {e}")

        # 2. Cookie auth ile dene (yedek)
        if self.auth_token and self.ct0:
            try:
                url = "https://twitter.com/i/api/2/search/adaptive.json"
                params = {"q": "test", "count": "1"}
                response = self.session.get(url, params=params, headers=self.base_headers, timeout=10)

                if response.status_code == 200:
                    self.api_mode = "cookie"
                    return True, "✅ Cookie auth bağlantısı başarılı!"
                elif response.status_code == 401:
                    return False, "❌ Cookie token geçersiz veya süresi dolmuş."
                elif response.status_code == 429:
                    return False, "⚠️ Rate limit - biraz bekle"
                elif response.status_code == 403:
                    return False, "❌ Erişim reddedildi."
                else:
                    return False, f"❌ API hatası: {response.status_code}"

            except Exception as e:
                return False, f"❌ Cookie auth hatası: {str(e)[:50]}"

        return False, "❌ Token ayarlanmamış. Bearer Token veya Cookie Token gir."

    def update_tokens(self, auth_token: str = None, ct0: str = None, bearer_token: str = None):
        """Token'ları güncelle"""
        if auth_token:
            self.auth_token = auth_token
            self.base_headers["Cookie"] = f"auth_token={auth_token}; ct0={self.ct0}"
        if ct0:
            self.ct0 = ct0
            self.base_headers["Cookie"] = f"auth_token={self.auth_token}; ct0={ct0}"
            self.base_headers["X-Csrf-Token"] = ct0
        if bearer_token:
            self.bearer_token = urllib.parse.unquote(bearer_token)
            self.api_v2_headers["Authorization"] = f"Bearer {self.bearer_token}"
            self.api_mode = "v2"

    # ==========================================================================
    # HESAP YÖNETİMİ
    # ==========================================================================

    def get_tracked_accounts(self, category: str = None) -> List[TrackedAccount]:
        """Takip edilen hesapları getir"""
        return self.account_manager.get_accounts(category=category)

    def add_account(self, username: str, category: str = "ai",
                    display_name: str = None, description: str = "") -> TrackedAccount:
        """Hesap ekle"""
        return self.account_manager.add_account(
            username=username,
            display_name=display_name,
            category=category,
            description=description,
        )

    def remove_account(self, username: str) -> bool:
        """Hesap kaldır"""
        return self.account_manager.remove_account(username)

    def toggle_account(self, username: str) -> bool:
        """Hesabı aç/kapa"""
        return self.account_manager.toggle_account(username)

    # ==========================================================================
    # İÇERİK KEŞFİ (FİLTRELİ)
    # ==========================================================================

    def get_ai_news(self, hours: int = 12, limit: int = 15) -> Tuple[List[SourceTweet], str]:
        """
        AI haberlerini bul - FİLTRELİ

        gm, hello gibi tweetleri atlar.
        Sadece değerli içeriği gösterir.
        Demo mod: API çalışmazsa örnek veri gösterir.
        """
        all_tweets = []
        seen_ids = set()
        errors = []

        # 1. Arama sorguları ile ara
        for query in AI_SEARCH_QUERIES[:6]:
            tweets, err = self._search_tweets(query, hours)
            if err:
                errors.append(err)
            for tweet in tweets:
                if tweet.id not in seen_ids:
                    seen_ids.add(tweet.id)

                    # Filtreleme
                    if should_skip_tweet(tweet.text):
                        continue

                    if is_valuable_content(tweet.text):
                        tweet.is_valuable = True

                    all_tweets.append(tweet)

        # 2. Takip edilen hesaplardan çek
        ai_accounts = self.account_manager.get_usernames(category="ai")
        for username in ai_accounts[:10]:
            tweets, err = self._get_user_tweets(username, hours)
            if err:
                errors.append(err)
            for tweet in tweets:
                if tweet.id not in seen_ids:
                    seen_ids.add(tweet.id)

                    # Filtreleme
                    if should_skip_tweet(tweet.text):
                        continue

                    if is_valuable_content(tweet.text):
                        tweet.is_valuable = True
                        all_tweets.append(tweet)

        # 3. Sırala (değerli + yüksek etkileşim önce)
        all_tweets.sort(
            key=lambda t: (
                (10 if t.is_valuable else 0) +
                (t.likes + t.retweets * 2)
            ),
            reverse=True
        )

        # 4. Eğer hiç tweet bulunamadıysa ve hata varsa
        if not all_tweets and errors:
            # Demo mod veya tüm API'ler başarısız
            if DEMO_MODE or all(
                "bağlantı" in e.lower() or "connection" in e.lower() or
                "fetch" in e.lower() or "timeout" in e.lower()
                for e in errors[:3] if e
            ):
                # Demo verileri döndür
                demo_tweets = self._get_demo_tweets()
                return demo_tweets[:limit], "⚠️ Demo mod: Gerçek veriler alınamadı. Örnek veriler gösteriliyor."

            return [], errors[0]

        return all_tweets[:limit], None

    def _get_demo_tweets(self) -> List[SourceTweet]:
        """Demo tweetleri döndür"""
        tweets = []
        for item in DEMO_TWEETS:
            tweet = SourceTweet(
                id=item["id"],
                author=item["author"],
                author_name=item["author_name"],
                text=item["text"],
                url=item["url"],
                likes=item["likes"],
                retweets=item["retweets"],
                is_valuable=True,
            )
            tweets.append(tweet)
        return tweets

    def get_football_news(self, hours: int = 6, limit: int = 15) -> Tuple[List[SourceTweet], str]:
        """Futbol haberlerini bul - FİLTRELİ"""
        all_tweets = []
        errors = []

        # Futbol hesaplarından çek
        football_accounts = self.account_manager.get_usernames(category="football")
        for username in football_accounts:
            tweets, err = self._get_user_tweets(username, hours)
            if err:
                errors.append(err)
            for tweet in tweets:
                if not should_skip_tweet(tweet.text):
                    all_tweets.append(tweet)

        # Arama sorguları
        queries = [
            "transfer breaking here we go",
            "Galatasaray OR Fenerbahçe transfer",
        ]
        for query in queries:
            tweets, err = self._search_tweets(query, hours)
            if err:
                errors.append(err)
            for tweet in tweets:
                if not should_skip_tweet(tweet.text):
                    all_tweets.append(tweet)

        all_tweets.sort(key=lambda t: t.likes + t.retweets * 2, reverse=True)

        error_msg = errors[0] if not all_tweets and errors else None
        return all_tweets[:limit], error_msg

    # ==========================================================================
    # DERİN ARAŞTIRMA
    # ==========================================================================

    def deep_research(self, tweet: SourceTweet) -> ResearchResult:
        """
        Tweet konusunu derinlemesine araştır.

        XPatla benzeri:
        - Konu ne hakkında?
        - Teknik detaylar
        - Neden önemli?
        - Rakiplerle karşılaştırma
        - Bağlam
        """
        try:
            from anthropic import Anthropic
            client = Anthropic()

            prompt = f"""Bu tweet hakkında kapsamlı bir araştırma yap:

TWEET:
@{tweet.author}: {tweet.text}

ARAŞTIRMA YAPILACAKLAR:

1. KONU ÖZETİ (2-3 cümle):
   - Bu tweet ne hakkında?
   - Ana mesaj ne?

2. TEKNİK DETAYLAR (madde madde):
   - Varsa model özellikleri
   - Benchmark sonuçları
   - API değişiklikleri
   - Fiyatlandırma bilgisi

3. NEDEN ÖNEMLİ? (1-2 cümle):
   - Bu gelişme neden dikkat çekmeli?
   - Kullanıcıları nasıl etkiler?

4. KARŞILAŞTIRMA:
   - Rakip ürünlerle kıyasla
   - Önceki versiyonla kıyasla

5. BAĞLAM:
   - Bu gelişme hangi trendin parçası?
   - Sektörde ne anlama geliyor?

6. ÖNEMLİ NOKTALAR (5 madde):
   - Öne çıkan 5 nokta

Türkçe ve teknik doğrulukla yaz."""

            response = client.messages.create(
                model=AVAILABLE_MODELS[self.current_model]["id"],
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()

            # Parse et
            key_points = []
            technical_details = []

            for line in result_text.split('\n'):
                line = line.strip()
                if line.startswith(('-', '•', '*')) or (line and line[0].isdigit() and '.' in line[:3]):
                    clean_line = line.lstrip('-•*0123456789. ')
                    if clean_line:
                        if any(kw in clean_line.lower() for kw in ['benchmark', 'api', 'model', 'hız', 'fiyat']):
                            technical_details.append(clean_line)
                        else:
                            key_points.append(clean_line)

            return ResearchResult(
                topic=self._extract_topic(tweet.text),
                summary=result_text[:500],
                key_points=key_points[:5],
                technical_details=technical_details[:5],
                context="",
                comparison="",
                why_important="",
                sources=[tweet.url],
                related_tweets=[],
            )

        except Exception as e:
            logger.error(f"Araştırma hatası: {e}")

            return ResearchResult(
                topic=self._extract_topic(tweet.text),
                summary=tweet.text[:200],
                key_points=[tweet.text[:100]],
                technical_details=[],
                context="",
                comparison="",
                why_important="",
                sources=[tweet.url],
                related_tweets=[],
            )

    # ==========================================================================
    # QUOTE TWEET SİSTEMİ
    # ==========================================================================

    def generate_quote_tweet(
        self,
        tweet: SourceTweet,
        style: str = None,
        format_key: str = None,
        do_research: bool = True,
    ) -> QuoteTweet:
        """
        Akıllı quote tweet oluştur.

        XPatla benzeri:
        1. Araştırma yap
        2. Hook yaz (dikkat çekici açılış)
        3. Değer ekle (kendi yorumun)
        4. CTA ekle (call to action)
        """
        style = style or self.current_style
        format_key = format_key or self.current_format

        style_info = WRITING_STYLES.get(style, WRITING_STYLES["samimi"])
        format_info = CONTENT_FORMATS.get(format_key, ContentFormat.THUNDER)
        model_info = AVAILABLE_MODELS[self.current_model]

        # Araştırma
        research = None
        if do_research:
            research = self.deep_research(tweet)

        try:
            from anthropic import Anthropic
            client = Anthropic()

            research_context = ""
            if research:
                research_context = f"""
ARAŞTIRMA SONUCU:
{research.summary}

TEKNİK DETAYLAR:
{chr(10).join(['• ' + d for d in research.technical_details[:3]])}

ÖNEMLİ NOKTALAR:
{chr(10).join(['• ' + p for p in research.key_points[:3]])}
"""

            prompt = f"""Bu tweet'e akıllı bir quote tweet yaz.

ORİJİNAL TWEET:
@{tweet.author}: {tweet.text}

{research_context}

QUOTE TWEET YAPISI:
1. HOOK (dikkat çekici açılış, 1 satır)
2. DEĞER EKLEME (kendi yorumun, analiz, ek bilgi)
3. SONUÇ/CTA (çağrı veya soru)

YAZIM STİLİ: {style_info['name']}
{style_info['description']}

KURALLAR:
{chr(10).join(['- ' + r for r in style_info['rules']])}

FORMAT: {format_info.description}
MAX KARAKTER: {format_info.max_chars}

ÖNEMLİ:
- Türkçe yaz
- Orijinal tweet'i KOPYALAMA, kendi yorumunu ekle
- Bilgi ekle, değer kat
- Sadece RT değil, neden önemli olduğunu anlat
- İnsansı ve doğal yaz

Sadece quote tweet metnini yaz, başka bir şey ekleme."""

            response = client.messages.create(
                model=model_info["id"],
                max_tokens=format_info.max_chars + 200,
                messages=[{"role": "user", "content": prompt}]
            )

            quote_text = response.content[0].text.strip().strip('"\'')

            # Karakter limitini kontrol et
            if len(quote_text) > format_info.max_chars:
                quote_text = quote_text[:format_info.max_chars - 3] + "..."

            # Hook'u çıkar (ilk satır)
            lines = quote_text.split('\n')
            hook = lines[0] if lines else ""

            return QuoteTweet(
                original=tweet,
                quote_text=quote_text,
                style_used=style,
                format_used=format_key,
                model_used=model_info["name"],
                research=research,
                char_count=len(quote_text),
                viral_score=self._calculate_viral_score_v2(quote_text, tweet),
                hook=hook,
                value_add="Araştırma ve analiz eklendi" if research else "",
            )

        except Exception as e:
            logger.error(f"Quote tweet hatası: {e}")

            return QuoteTweet(
                original=tweet,
                quote_text=f"Bu önemli bir gelişme 👇",
                style_used=style,
                format_used=format_key,
                model_used="Fallback",
                char_count=25,
                viral_score=30.0,
            )

    # ==========================================================================
    # VİRAL REWRITER (GELİŞTİRİLMİŞ)
    # ==========================================================================

    def rewrite_viral(
        self,
        tweet: SourceTweet,
        style: str = None,
        format_key: str = None,
        do_research: bool = True,
    ) -> ViralTweet:
        """Tweet'i viral formatta yeniden yaz"""
        style = style or self.current_style
        format_key = format_key or self.current_format

        style_info = WRITING_STYLES.get(style, WRITING_STYLES["samimi"])
        format_info = CONTENT_FORMATS.get(format_key, ContentFormat.THUNDER)
        model_info = AVAILABLE_MODELS[self.current_model]

        # Araştırma
        research = None
        if do_research:
            research = self.deep_research(tweet)

        try:
            from anthropic import Anthropic
            client = Anthropic()

            research_context = ""
            if research:
                research_context = f"""
ARAŞTIRMA:
{research.summary}

DETAYLAR:
{chr(10).join(['• ' + p for p in research.key_points[:4]])}
"""

            prompt = f"""Bu tweet'i kendi tarzımda yeniden yaz.

ORİJİNAL:
@{tweet.author}: {tweet.text}

{research_context}

STİL: {style_info['name']}
{chr(10).join(['- ' + r for r in style_info['rules']])}

ÖRNEK:
{style_info['example']}

FORMAT: {format_info.description} (max {format_info.max_chars} karakter)

Türkçe, doğal, insansı yaz. Sadece tweet metnini ver."""

            response = client.messages.create(
                model=model_info["id"],
                max_tokens=format_info.max_chars + 200,
                messages=[{"role": "user", "content": prompt}]
            )

            rewritten = response.content[0].text.strip().strip('"\'')

            if len(rewritten) > format_info.max_chars:
                rewritten = rewritten[:format_info.max_chars - 3] + "..."

            return ViralTweet(
                original=tweet,
                rewritten_text=rewritten,
                style_used=style,
                format_used=format_key,
                model_used=model_info["name"],
                research=research,
                char_count=len(rewritten),
                viral_score=self._calculate_viral_score_v2(rewritten, tweet),
            )

        except Exception as e:
            logger.error(f"Rewrite hatası: {e}")

            return ViralTweet(
                original=tweet,
                rewritten_text=tweet.text[:500],
                style_used=style,
                format_used=format_key,
                model_used="Fallback",
                char_count=len(tweet.text),
                viral_score=30.0,
            )

    # ==========================================================================
    # VİRAL SKOR v2
    # ==========================================================================

    def _calculate_viral_score_v2(self, text: str, source: SourceTweet) -> float:
        """Gelişmiş viral skor hesaplama"""
        score = 40.0

        # 1. Hook kalitesi (0-20)
        hooks = ['🚨', '⚡', '🔥', '💡', 'ya ', 'Ya ', 'BREAKING', 'SON DAKİKA']
        if any(text.startswith(h) for h in hooks):
            score += 15
        elif text[0].isupper() if text else False:
            score += 5

        # 2. Soru içeriyorsa (+10)
        if '?' in text:
            score += 10

        # 3. Liste/bullet varsa (+10)
        if any(c in text for c in ['•', '-', '1.', '2.', '✓', '✅']):
            score += 10

        # 4. Satır atlama (+5)
        if '\n\n' in text:
            score += 5

        # 5. Uzunluk optimizasyonu
        text_len = len(text)
        if 500 <= text_len <= 1200:
            score += 10
        elif 300 <= text_len <= 1500:
            score += 5

        # 6. Kaynak etkileşimi
        if source.likes > 5000:
            score += 15
        elif source.likes > 1000:
            score += 10
        elif source.likes > 100:
            score += 5

        # 7. CTA varsa (+5)
        cta_patterns = ['sizce', 'ne düşünüyorsunuz', 'rt', 'paylaş', 'yorum']
        if any(p in text.lower() for p in cta_patterns):
            score += 5

        return min(score, 100.0)

    # ==========================================================================
    # TWITTER API METHODLARI
    # ==========================================================================

    def _search_tweets(self, query: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Tweet ara - API v2 öncelikli"""
        if self.api_mode == "v2" and self.bearer_token:
            return self._search_with_api_v2(query, hours)
        return self._search_with_api(query, hours)

    def _get_user_tweets(self, username: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Kullanıcı tweetlerini çek - API v2 öncelikli"""
        if self.api_mode == "v2" and self.bearer_token:
            return self._get_user_tweets_api_v2(username, hours)
        return self._get_user_tweets_api(username, hours)

    def _search_with_api_v2(self, query: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Twitter API v2 ile arama (resmi API)"""
        tweets = []
        error = None

        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            params = {
                "query": f"{query} -is:retweet lang:en OR lang:tr",
                "max_results": "20",
                "tweet.fields": "created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "username,name",
            }

            response = self.session.get(url, params=params, headers=self.api_v2_headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get("data", [])
                users_data = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

                for tweet_data in tweets_data[:15]:
                    author_id = tweet_data.get("author_id", "")
                    user_info = users_data.get(author_id, {})
                    metrics = tweet_data.get("public_metrics", {})

                    tweet = SourceTweet(
                        id=tweet_data.get("id", ""),
                        author=user_info.get("username", ""),
                        author_name=user_info.get("name", ""),
                        text=tweet_data.get("text", ""),
                        url=f"https://twitter.com/i/status/{tweet_data.get('id', '')}",
                        likes=metrics.get("like_count", 0),
                        retweets=metrics.get("retweet_count", 0),
                        replies=metrics.get("reply_count", 0),
                        created_at=tweet_data.get("created_at", ""),
                    )
                    tweets.append(tweet)

            elif response.status_code == 401:
                error = "Bearer Token geçersiz"
            elif response.status_code == 403:
                error = "API erişimi reddedildi"
            elif response.status_code == 429:
                error = "Rate limit - 15 dk bekle"
            else:
                error = f"API v2 hatası: {response.status_code}"

        except Exception as e:
            error = str(e)[:50]

        return tweets, error

    def _get_user_tweets_api_v2(self, username: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Twitter API v2 ile kullanıcı tweetleri"""
        tweets = []
        error = None

        try:
            # Önce user ID al
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_response = self.session.get(user_url, headers=self.api_v2_headers, timeout=10)

            if user_response.status_code != 200:
                return [], f"Kullanıcı bulunamadı: {username}"

            user_data = user_response.json().get("data", {})
            user_id = user_data.get("id")

            if not user_id:
                return [], f"User ID alınamadı: {username}"

            # Tweetleri çek
            url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                "max_results": "15",
                "tweet.fields": "created_at,public_metrics",
                "exclude": "retweets,replies",
            }

            response = self.session.get(url, params=params, headers=self.api_v2_headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get("data", [])

                for tweet_data in tweets_data[:10]:
                    metrics = tweet_data.get("public_metrics", {})

                    tweet = SourceTweet(
                        id=tweet_data.get("id", ""),
                        author=username,
                        author_name=user_data.get("name", username),
                        text=tweet_data.get("text", ""),
                        url=f"https://twitter.com/{username}/status/{tweet_data.get('id', '')}",
                        likes=metrics.get("like_count", 0),
                        retweets=metrics.get("retweet_count", 0),
                        created_at=tweet_data.get("created_at", ""),
                    )
                    tweets.append(tweet)

            elif response.status_code == 429:
                error = "Rate limit"
            else:
                error = f"API v2 hatası: {response.status_code}"

        except Exception as e:
            error = str(e)[:50]

        return tweets, error

    def _search_with_api(self, query: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Direct Twitter API ile arama (bird CLI olmadan)"""
        tweets = []
        error = None

        try:
            url = "https://twitter.com/i/api/2/search/adaptive.json"
            params = {
                "q": query,
                "tweet_search_mode": "live",
                "query_source": "typed_query",
                "count": "20",
                "result_filter": "top",
            }

            response = self.session.get(url, params=params, headers=self.base_headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get("globalObjects", {}).get("tweets", {})
                users_data = data.get("globalObjects", {}).get("users", {})

                for tweet_id, tweet_data in list(tweets_data.items())[:15]:
                    text = tweet_data.get("full_text", "")

                    # RT'leri atla
                    if text.startswith("RT @"):
                        continue

                    user_id = tweet_data.get("user_id_str", "")
                    user_info = users_data.get(user_id, {})

                    tweet = SourceTweet(
                        id=str(tweet_id),
                        author=user_info.get("screen_name", ""),
                        author_name=user_info.get("name", ""),
                        text=text,
                        url=f"https://twitter.com/i/status/{tweet_id}",
                        likes=tweet_data.get("favorite_count", 0),
                        retweets=tweet_data.get("retweet_count", 0),
                        replies=tweet_data.get("reply_count", 0),
                        created_at=tweet_data.get("created_at", ""),
                    )
                    tweets.append(tweet)
            elif response.status_code == 401:
                error = "Token geçersiz veya süresi dolmuş"
            elif response.status_code == 429:
                error = "Rate limit - biraz bekle"
            else:
                error = f"API hatası: {response.status_code}"

        except Exception as e:
            error = str(e)[:50]

        return tweets, error

    def _get_user_tweets_api(self, username: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Direct Twitter API ile kullanıcı tweetleri (bird CLI olmadan)"""
        tweets = []
        error = None

        try:
            # from: ile kullanıcı tweetlerini ara
            url = "https://twitter.com/i/api/2/search/adaptive.json"
            params = {
                "q": f"from:{username}",
                "tweet_search_mode": "live",
                "query_source": "typed_query",
                "count": "15",
            }

            response = self.session.get(url, params=params, headers=self.base_headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                tweets_data = data.get("globalObjects", {}).get("tweets", {})
                users_data = data.get("globalObjects", {}).get("users", {})

                cutoff = datetime.now() - timedelta(hours=hours)

                for tweet_id, tweet_data in list(tweets_data.items())[:10]:
                    text = tweet_data.get("full_text", "")

                    # RT'leri atla
                    if text.startswith("RT @"):
                        continue

                    user_id = tweet_data.get("user_id_str", "")
                    user_info = users_data.get(user_id, {})

                    tweet = SourceTweet(
                        id=str(tweet_id),
                        author=user_info.get("screen_name", username),
                        author_name=user_info.get("name", username),
                        text=text,
                        url=f"https://twitter.com/{username}/status/{tweet_id}",
                        likes=tweet_data.get("favorite_count", 0),
                        retweets=tweet_data.get("retweet_count", 0),
                        created_at=tweet_data.get("created_at", ""),
                    )
                    tweets.append(tweet)
            elif response.status_code == 401:
                error = "Token geçersiz"
            else:
                error = f"API hatası: {response.status_code}"

        except Exception as e:
            error = str(e)[:50]

        return tweets, error

    def _extract_topic(self, text: str) -> str:
        """Ana konuyu çıkar"""
        sentences = re.split(r'[.!?\n]', text)
        if sentences:
            return sentences[0].strip()[:100]
        return text[:100]


# ==============================================================================
# EXPORTS
# ==============================================================================

# Geriye uyumluluk için
TRUSTED_AI_ACCOUNTS = [a.username for a in DEFAULT_AI_ACCOUNTS]
AI_ACCOUNTS = {a.username: a.display_name for a in DEFAULT_AI_ACCOUNTS}


# ==============================================================================
# TEST
# ==============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = AIContentEngine()

    print("=== Takip Edilen Hesaplar ===")
    for acc in engine.get_tracked_accounts(category="ai")[:5]:
        status = "✓" if acc.enabled else "✗"
        print(f"  {status} @{acc.username} - {acc.description}")

    print("\n=== AI Haberleri (Filtreli) ===")
    tweets, error = engine.get_ai_news(hours=12, limit=5)

    if error:
        print(f"Hata: {error}")

    for i, tweet in enumerate(tweets, 1):
        valuable = "⭐" if tweet.is_valuable else ""
        print(f"\n{i}. {valuable} @{tweet.author}: {tweet.text[:80]}...")
        print(f"   ❤️ {tweet.likes} | 🔄 {tweet.retweets}")

    if tweets:
        print("\n=== Quote Tweet Örneği ===")
        quote = engine.generate_quote_tweet(
            tweets[0],
            style="samimi",
            format_key="thunder",
            do_research=True,
        )
        print(f"Viral Skor: {quote.viral_score}/100")
        print(f"Karakter: {quote.char_count}")
        print(quote.quote_text)
