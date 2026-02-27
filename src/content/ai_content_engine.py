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

Kurulum: npm install -g @steipete/bird
"""

import subprocess
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import re
import urllib.parse
import shutil
import os

logger = logging.getLogger(__name__)

# Bird CLI var mı kontrol et
BIRD_CLI_AVAILABLE = shutil.which("bird") is not None

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

    def __init__(self, auth_token: str = None, ct0: str = None):
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

        # Hesap yöneticisi
        self.account_manager = AccountManager()

        # Varsayılan ayarlar
        self.current_model = "claude-sonnet"
        self.current_format = "thunder"
        self.current_style = "samimi"

    # ==========================================================================
    # BAĞLANTI TESTİ
    # ==========================================================================

    def test_connection(self) -> Tuple[bool, str]:
        """
        Twitter/X bağlantısını test et.

        Returns:
            (success, message)
        """
        # 1. Bird CLI ile dene
        if BIRD_CLI_AVAILABLE:
            try:
                cmd = [
                    "bird", "search", "test",
                    "--auth-token", self.auth_token,
                    "--ct0", self.ct0,
                    "--count", "1",
                    "--timeout", "10000"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

                if result.returncode == 0:
                    return True, "✅ Bağlantı başarılı (bird CLI)"

                stderr = result.stderr.strip() if result.stderr else ""
                if "401" in stderr or "Unauthorized" in stderr:
                    return False, "❌ Token geçersiz veya süresi dolmuş. Yeni token al."
                elif "rate" in stderr.lower():
                    return False, "⚠️ Rate limit - biraz bekle ve tekrar dene"
                elif "fetch failed" in stderr.lower():
                    return False, "❌ Ağ bağlantısı başarısız. İnternet bağlantını kontrol et."
                else:
                    return False, f"❌ Hata: {stderr[:100]}"

            except subprocess.TimeoutExpired:
                return False, "❌ Bağlantı zaman aşımı (15s)"
            except Exception as e:
                return False, f"❌ Hata: {str(e)[:50]}"

        # 2. Bird CLI yoksa direct API ile test et
        try:
            url = "https://twitter.com/i/api/2/search/adaptive.json"
            params = {"q": "test", "count": "1"}
            response = self.session.get(url, params=params, headers=self.base_headers, timeout=10)

            if response.status_code == 200:
                return True, "✅ Bağlantı başarılı (Direct API)"
            elif response.status_code == 401:
                return False, "❌ Token geçersiz veya süresi dolmuş. Yeni token al."
            elif response.status_code == 429:
                return False, "⚠️ Rate limit - biraz bekle ve tekrar dene"
            else:
                return False, f"❌ API hatası: {response.status_code}"

        except Exception as e:
            return False, f"❌ Bağlantı hatası: {str(e)[:50]}"

    def update_tokens(self, auth_token: str, ct0: str):
        """Token'ları güncelle"""
        self.auth_token = auth_token
        self.ct0 = ct0
        self.base_headers["Cookie"] = f"auth_token={auth_token}; ct0={ct0}"
        self.base_headers["X-Csrf-Token"] = ct0

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
        """Tweet ara - bird CLI veya direct API"""
        if BIRD_CLI_AVAILABLE:
            return self._search_with_bird(query, hours)
        else:
            return self._search_with_api(query, hours)

    def _get_user_tweets(self, username: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Kullanıcı tweetlerini çek - bird CLI veya direct API"""
        if BIRD_CLI_AVAILABLE:
            return self._get_user_tweets_bird(username, hours)
        else:
            return self._get_user_tweets_api(username, hours)

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

    def _search_with_bird(self, query: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Bird CLI ile arama"""
        tweets = []
        error = None

        try:
            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime("%Y-%m-%d")

            cmd = [
                "bird", "search", f"{query} since:{since_str}",
                "--auth-token", self.auth_token,
                "--ct0", self.ct0,
                "--json", "--count", "20"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)

                if isinstance(data, list):
                    for item in data[:15]:
                        text = item.get("text", "") or item.get("full_text", "")

                        if text.startswith("RT @"):
                            continue

                        tweet = SourceTweet(
                            id=str(item.get("id", "")),
                            author=item.get("user", {}).get("screen_name", "") or item.get("author", ""),
                            author_name=item.get("user", {}).get("name", "") or item.get("authorName", ""),
                            text=text,
                            url=item.get("url", f"https://twitter.com/i/status/{item.get('id', '')}"),
                            likes=item.get("favorite_count", 0) or item.get("likes", 0),
                            retweets=item.get("retweet_count", 0) or item.get("retweets", 0),
                            replies=item.get("reply_count", 0),
                            created_at=item.get("created_at", ""),
                        )
                        tweets.append(tweet)
            else:
                stderr = result.stderr.strip() if result.stderr else ""
                if "401" in stderr:
                    error = "Token geçersiz"
                elif "rate" in stderr.lower():
                    error = "Rate limit"
                else:
                    error = f"bird hatası: {stderr[:50]}"

        except subprocess.TimeoutExpired:
            error = "Zaman aşımı"
        except Exception as e:
            error = str(e)[:50]

        return tweets, error

    def _get_user_tweets_bird(self, username: str, hours: int) -> Tuple[List[SourceTweet], str]:
        """Bird CLI ile kullanıcı tweetleri"""
        tweets = []
        error = None

        try:
            cmd = [
                "bird", "user-tweets", username,
                "--auth-token", self.auth_token,
                "--ct0", self.ct0,
                "--json", "--count", "15"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                cutoff = datetime.now() - timedelta(hours=hours)

                if isinstance(data, list):
                    for item in data[:10]:
                        text = item.get("text", "") or item.get("full_text", "")

                        if text.startswith("RT @"):
                            continue

                        tweet = SourceTweet(
                            id=str(item.get("id", "")),
                            author=username,
                            author_name=item.get("user", {}).get("name", username),
                            text=text,
                            url=f"https://twitter.com/{username}/status/{item.get('id', '')}",
                            likes=item.get("favorite_count", 0) or item.get("likes", 0),
                            retweets=item.get("retweet_count", 0),
                            created_at=item.get("created_at", ""),
                        )
                        tweets.append(tweet)
            else:
                error = result.stderr[:50] if result.stderr else "bird hatası"

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
