"""
Twitter/X Voice Profile - Kullanıcı Ses Profili
================================================

Bu modül kullanıcının Twitter yazım tarzını öğrenir ve
tweetlerin kullanıcının ağzından yazılmasını sağlar.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)

# Profil dosyası konumu
PROFILE_DIR = Path(__file__).parent.parent.parent / "data"
PROFILE_FILE = PROFILE_DIR / "voice_profile.json"


@dataclass
class VoiceProfile:
    """Kullanıcının Twitter ses profili"""

    # Temel bilgiler
    twitter_username: str = ""
    display_name: str = ""
    bio: str = ""

    # Yazım tarzı
    tone: str = "samimi"  # samimi, profesyonel, mizahi, ciddi, provokatif
    language_style: str = "günlük"  # günlük, resmi, argo, karma

    # İçerik tercihleri
    main_topics: List[str] = field(default_factory=list)  # Ana konular
    avoid_topics: List[str] = field(default_factory=list)  # Kaçınılacak konular

    # Emoji ve format tercihleri
    emoji_usage: str = "orta"  # yok, az, orta, çok
    favorite_emojis: List[str] = field(default_factory=list)
    use_hashtags: bool = True
    max_hashtags: int = 2
    use_thread: bool = True

    # Yazım özellikleri
    sentence_style: str = "kısa"  # kısa, orta, uzun
    punctuation_style: str = "normal"  # minimal, normal, ekspresif (!!!, ???)
    caps_usage: str = "normal"  # yok, normal, vurgu için

    # Örnek tweetler (eğitim için)
    sample_tweets: List[str] = field(default_factory=list)

    # Viral taktikler tercihi
    use_questions: bool = True  # Soru sorma
    use_controversy: bool = False  # Tartışmalı görüşler
    use_humor: bool = True  # Mizah
    use_personal_stories: bool = True  # Kişisel hikayeler
    use_hot_takes: bool = True  # Cesur yorumlar

    # Kişisel bilgiler (içerik için)
    profession: str = ""
    interests: List[str] = field(default_factory=list)
    location: str = "Türkiye"
    age_group: str = ""  # genç, orta, yetişkin

    def to_prompt(self) -> str:
        """Profili AI prompt'una dönüştür"""

        emoji_map = {
            "yok": "Emoji kullanma.",
            "az": "Nadiren emoji kullan (max 1).",
            "orta": "Uygun yerlerde emoji kullan (1-2).",
            "çok": "Bol emoji kullan."
        }

        tone_map = {
            "samimi": "arkadaşça ve samimi",
            "profesyonel": "profesyonel ve bilgilendirici",
            "mizahi": "esprili ve eğlenceli",
            "ciddi": "ciddi ve düşündürücü",
            "provokatif": "kışkırtıcı ve dikkat çekici"
        }

        prompt_parts = [
            f"Sen @{self.twitter_username} kullanıcısının Twitter hesabı için içerik yazıyorsun.",
            f"Kullanıcı hakkında: {self.bio}" if self.bio else "",
            f"Meslek/Alan: {self.profession}" if self.profession else "",
            "",
            "YAZIM TARZI:",
            f"- Ton: {tone_map.get(self.tone, self.tone)}",
            f"- Dil: {self.language_style} Türkçe",
            f"- Cümle yapısı: {self.sentence_style} cümleler",
            f"- {emoji_map.get(self.emoji_usage, '')}",
        ]

        if self.favorite_emojis:
            prompt_parts.append(f"- Tercih edilen emojiler: {' '.join(self.favorite_emojis)}")

        if self.main_topics:
            prompt_parts.append(f"\nANA KONULAR: {', '.join(self.main_topics)}")

        if self.avoid_topics:
            prompt_parts.append(f"KAÇINILACAK KONULAR: {', '.join(self.avoid_topics)}")

        prompt_parts.append("\nVIRAL TAKTİKLER:")
        if self.use_questions:
            prompt_parts.append("- Takipçilere sorular sor, etkileşim iste")
        if self.use_humor:
            prompt_parts.append("- Uygun yerlerde mizah kullan")
        if self.use_hot_takes:
            prompt_parts.append("- Cesur ve özgün görüşler paylaş")
        if self.use_personal_stories:
            prompt_parts.append("- Kişisel deneyimlerden bahset")

        if self.sample_tweets:
            prompt_parts.append("\nÖRNEK TWEETLER (bu tarzda yaz):")
            for i, tweet in enumerate(self.sample_tweets[:5], 1):
                prompt_parts.append(f"{i}. \"{tweet}\"")

        prompt_parts.extend([
            "",
            "ÖNEMLİ KURALLAR:",
            "- Maximum 280 karakter",
            f"- Maximum {self.max_hashtags} hashtag kullan" if self.use_hashtags else "- Hashtag kullanma",
            "- Doğal ve otantik ol, reklam gibi yazma",
            "- Kullanıcının kendi ağzından yazıyormuş gibi yaz",
        ])

        return "\n".join([p for p in prompt_parts if p])

    def save(self):
        """Profili dosyaya kaydet"""
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        logger.info(f"Profil kaydedildi: {PROFILE_FILE}")

    @classmethod
    def load(cls) -> 'VoiceProfile':
        """Profili dosyadan yükle"""
        if PROFILE_FILE.exists():
            try:
                with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                logger.error(f"Profil yükleme hatası: {e}")
        return cls()


@dataclass
class TweetReview:
    """Tweet inceleme sonucu"""
    original_tweet: str
    improved_tweet: str
    score: int  # 1-10
    issues: List[str]
    suggestions: List[str]
    viral_potential: str  # düşük, orta, yüksek
    estimated_engagement: str


class TweetOptimizer:
    """Tweet optimizasyon ve viral analiz"""

    # Twitter algoritması ağırlıkları
    VIRAL_FACTORS = {
        "question": 1.5,      # Soru içeriyor
        "emoji": 1.2,         # Emoji var
        "short": 1.3,         # Kısa (< 100 karakter)
        "hashtag": 1.1,       # 1-2 hashtag
        "controversy": 1.8,   # Tartışmalı/dikkat çekici
        "personal": 1.4,      # Kişisel hikaye
        "trending": 1.6,      # Gündem konusu
        "call_to_action": 1.5, # Etkileşim çağrısı
        "thread_hook": 1.4,   # Thread başlangıcı
    }

    # Viral tetikleyici kelimeler
    VIRAL_TRIGGERS_TR = [
        "inanamayacaksınız", "şok", "bomba", "flaş", "son dakika",
        "herkes bunu konuşuyor", "viral", "rekor", "tarihte ilk",
        "kimse bilmiyor", "gizli", "sır", "gerçek ortaya çıktı",
        "bunu yapan kazanır", "hata yapmayın", "pişman olmayın",
        "thread", "🧵", "1/", "başlıyoruz"
    ]

    # Etkileşim çağrıları
    ENGAGEMENT_HOOKS_TR = [
        "siz ne düşünüyorsunuz?",
        "yorumlarda buluşalım",
        "rt yapar mısınız?",
        "katılıyor musunuz?",
        "sizce hangisi?",
        "deneyimlerinizi paylaşın",
        "bu postu kaydedin",
        "takip edin, kaçırmayın"
    ]

    @classmethod
    def analyze_viral_potential(cls, tweet: str) -> Dict:
        """Tweet'in viral potansiyelini analiz et"""

        score = 5.0  # Başlangıç skoru
        factors_found = []
        suggestions = []

        tweet_lower = tweet.lower()

        # Uzunluk kontrolü
        if len(tweet) < 100:
            score *= cls.VIRAL_FACTORS["short"]
            factors_found.append("✓ Kısa ve öz")
        elif len(tweet) > 250:
            suggestions.append("Tweet'i kısaltmayı dene (ideal: 100-150 karakter)")

        # Soru kontrolü
        if "?" in tweet:
            score *= cls.VIRAL_FACTORS["question"]
            factors_found.append("✓ Soru içeriyor (etkileşim artırır)")
        else:
            suggestions.append("Sonuna bir soru ekle (etkileşimi artırır)")

        # Emoji kontrolü
        import re
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0]+")
        if emoji_pattern.search(tweet):
            score *= cls.VIRAL_FACTORS["emoji"]
            factors_found.append("✓ Emoji kullanılmış")
        else:
            suggestions.append("1-2 emoji ekle (dikkat çeker)")

        # Hashtag kontrolü
        hashtag_count = tweet.count('#')
        if 1 <= hashtag_count <= 2:
            score *= cls.VIRAL_FACTORS["hashtag"]
            factors_found.append("✓ Optimal hashtag sayısı")
        elif hashtag_count > 3:
            suggestions.append("Hashtag sayısını azalt (max 2)")
        elif hashtag_count == 0:
            suggestions.append("1-2 alakalı hashtag ekle")

        # Viral tetikleyici kelimeler
        for trigger in cls.VIRAL_TRIGGERS_TR:
            if trigger in tweet_lower:
                score *= 1.2
                factors_found.append(f"✓ Dikkat çekici: '{trigger}'")
                break

        # Etkileşim çağrısı
        has_cta = False
        for hook in cls.ENGAGEMENT_HOOKS_TR:
            if hook in tweet_lower:
                score *= cls.VIRAL_FACTORS["call_to_action"]
                factors_found.append("✓ Etkileşim çağrısı var")
                has_cta = True
                break

        if not has_cta:
            suggestions.append("Etkileşim çağrısı ekle (ör: 'Siz ne düşünüyorsunuz?')")

        # Thread kontrolü
        if "🧵" in tweet or "thread" in tweet_lower or tweet.startswith("1/"):
            score *= cls.VIRAL_FACTORS["thread_hook"]
            factors_found.append("✓ Thread formatı (daha fazla görünürlük)")

        # Final skor (max 10)
        final_score = min(10, score)

        # Viral potansiyel seviyesi
        if final_score >= 8:
            viral_level = "🔥 YÜKSEK"
            engagement_est = "Yüksek etkileşim bekleniyor"
        elif final_score >= 6:
            viral_level = "📈 ORTA"
            engagement_est = "Orta düzey etkileşim bekleniyor"
        else:
            viral_level = "📉 DÜŞÜK"
            engagement_est = "Düşük etkileşim riski - iyileştir"

        return {
            "score": round(final_score, 1),
            "viral_potential": viral_level,
            "factors_found": factors_found,
            "suggestions": suggestions,
            "engagement_estimate": engagement_est,
            "character_count": len(tweet),
            "hashtag_count": hashtag_count
        }

    @classmethod
    def get_improvement_tips(cls) -> List[str]:
        """Genel iyileştirme ipuçları"""
        return [
            "🎯 İlk 30 dakika kritik - hemen etkileşime geç",
            "⏰ En iyi saatler: 08:00, 12:00, 19:00, 21:00",
            "🔄 Reply'lara hızlı cevap ver (algoritma sever)",
            "📊 Görsel ekle (1.5x daha fazla etkileşim)",
            "🧵 Thread yap (daha fazla süre = daha fazla skor)",
            "❓ Soru sor (13.5x reply ağırlığı!)",
            "🚫 Link ekleme (algoritma cezalandırır)",
            "💬 Tartışma başlat (engagement patlar)",
        ]


# @ilhntolga için varsayılan profil
DEFAULT_PROFILE_DATA = {
    "twitter_username": "ilhntolga",
    "display_name": "Tolga",
    "bio": "",
    "tone": "samimi",
    "language_style": "günlük",
    "main_topics": ["teknoloji", "girişimcilik", "yapay zeka", "gündem"],
    "avoid_topics": [],
    "emoji_usage": "orta",
    "favorite_emojis": ["🔥", "💪", "🚀", "👀", "💡"],
    "use_hashtags": True,
    "max_hashtags": 2,
    "use_thread": True,
    "sentence_style": "kısa",
    "punctuation_style": "normal",
    "caps_usage": "normal",
    "sample_tweets": [],
    "use_questions": True,
    "use_controversy": True,
    "use_humor": True,
    "use_personal_stories": True,
    "use_hot_takes": True,
    "profession": "",
    "interests": ["teknoloji", "iş dünyası", "kişisel gelişim"],
    "location": "Türkiye",
    "age_group": "",
}


def load_or_create_default() -> VoiceProfile:
    """
    Profili yükle veya varsayılan oluştur.
    İlk açılışta @ilhntolga profili otomatik oluşturulur.
    """
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return VoiceProfile(**data)
        except Exception as e:
            logger.error(f"Profil yükleme hatası: {e}")

    # Varsayılan profili oluştur ve kaydet
    profile = VoiceProfile(**DEFAULT_PROFILE_DATA)
    profile.save()
    logger.info("Varsayılan profil oluşturuldu: @ilhntolga")
    return profile


# Varsayılan profil
default_profile = load_or_create_default()
