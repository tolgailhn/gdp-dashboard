"""
Viral Strategies - XPatla & Twitter Algorithm Entegrasyonu
============================================================

XPatla.com ve Twitter'ın açık kaynak algoritmasından
öğrenilen viral stratejiler.

Kaynaklar:
- XPatla.com
- Twitter/X Open Source Algorithm (github.com/twitter/the-algorithm)
- Hootsuite, SocialPilot, RecurPost araştırmaları
"""

from dataclasses import dataclass, field
from typing import Dict, List
import random
from datetime import datetime, time
import pytz


@dataclass
class TwitterAlgorithmWeights:
    """
    Twitter/X Algoritması Ağırlıkları
    Kaynak: X Open Source Algorithm (2024)
    """

    # Ana etkileşim ağırlıkları
    REPLY_WITH_ENGAGEMENT = 75.0      # Reply + author etkileşimi
    USER_REPLIES = 13.5               # Kullanıcı reply'ı
    PROFILE_CLICK_THEN_ENGAGE = 12.0  # Profil tıklama + like/reply
    CONVERSATION_CLICK_ENGAGE = 11.0  # Konuşmaya tıklama + engage
    DWELL_TIME_2MIN = 10.0            # 2+ dakika konuşmada kalma
    RETWEET = 1.0                     # Retweet
    LIKE = 0.5                        # Like
    VIDEO_WATCH_50 = 0.005            # Video %50+ izleme

    # İçerik tipi ağırlıkları
    FAV_COUNT_WEIGHT = 30             # Like sayısı ağırlığı
    RETWEET_COUNT_WEIGHT = 20         # RT sayısı ağırlığı
    DIRECT_FOLLOW_BOOST = 4           # Direkt takip boost

    # Ceza faktörleri
    OFFENSIVE_CONTENT_PENALTY = 0.2   # %80 düşüş
    EXTERNAL_LINK_PENALTY = 0.5       # Link varsa %50 düşüş riski
    SPAM_HASHTAG_PENALTY = 0.3        # 3+ hashtag spam sayılır


class ViralTimeOptimizer:
    """
    XPatla tarzı viral saat optimizasyonu
    Türkiye saatine göre en iyi paylaşım zamanları
    """

    # Türkiye için en iyi saatler (UTC+3)
    PRIME_HOURS = {
        "weekday": [
            (8, 9, "Sabah rutini - iş/okula hazırlık"),
            (12, 13, "Öğle arası - yemek molası"),
            (17, 18, "İşten çıkış - eve dönüş"),
            (21, 22, "Prime time - en aktif saat!"),
            (23, 0, "Gece kuşları - aktif tartışmalar"),
        ],
        "weekend": [
            (10, 11, "Geç kahvaltı"),
            (14, 15, "Öğleden sonra"),
            (20, 21, "Akşam dinlenmesi"),
            (23, 0, "Gece aktivitesi"),
        ]
    }

    # Günlere göre özel stratejiler
    DAY_STRATEGIES = {
        0: "Pazartesi: Motivasyon içerikleri, hafta planları",
        1: "Salı: Teknik/eğitici içerikler iyi gider",
        2: "Çarşamba: Haftanın ortası - tartışma başlat",
        3: "Perşembe: Throwback içerikleri, anılar",
        4: "Cuma: Hafif/eğlenceli içerikler",
        5: "Cumartesi: Lifestyle, hobi içerikleri",
        6: "Pazar: Düşündürücü, haftalık özet",
    }

    @classmethod
    def get_best_times_today(cls) -> List[Dict]:
        """Bugün için en iyi paylaşım saatlerini getir"""
        tz = pytz.timezone('Europe/Istanbul')
        now = datetime.now(tz)
        is_weekend = now.weekday() >= 5

        hours = cls.PRIME_HOURS["weekend" if is_weekend else "weekday"]
        current_hour = now.hour

        result = []
        for start, end, desc in hours:
            status = "✓ Şimdi!" if start <= current_hour < end else (
                "Geçti" if current_hour >= end else "Bekliyor"
            )
            result.append({
                "time": f"{start:02d}:00 - {end:02d}:00",
                "description": desc,
                "status": status,
                "is_current": start <= current_hour < end,
                "is_upcoming": current_hour < start,
            })

        return result

    @classmethod
    def get_day_strategy(cls) -> str:
        """Bugün için strateji önerisi"""
        tz = pytz.timezone('Europe/Istanbul')
        day = datetime.now(tz).weekday()
        return cls.DAY_STRATEGIES.get(day, "")


class ViralContentFormulas:
    """
    XPatla'dan öğrenilen viral içerik formülleri
    """

    # Hook (dikkat çekici başlangıç) şablonları
    HOOKS = [
        "Kimse bundan bahsetmiyor ama...",
        "Bugün öğrendiğim şey beni şok etti:",
        "Herkes yanlış biliyor. Gerçek şu ki...",
        "{topic} hakkında söylenmesi gereken bir şey var:",
        "Thread: {topic} hakkında bilmeniz gereken her şey 🧵",
        "Bunu yapan herkes pişman oluyor:",
        "Size bir sır vereyim:",
        "{topic} konusunda 5 yıldır yaptığım hatayı keşfettim:",
        "İnanamayacaksınız ama...",
        "Unpopular opinion: {topic}...",
    ]

    # Engagement trigger (etkileşim tetikleyici) cümleleri
    ENGAGEMENT_TRIGGERS = [
        "\n\nSiz ne düşünüyorsunuz? 👇",
        "\n\nKatılıyor musunuz?",
        "\n\nYorumlarda buluşalım!",
        "\n\nBu konuda sizin deneyiminiz ne?",
        "\n\nReply atın, tartışalım!",
        "\n\nDeneyimlerinizi paylaşın 💬",
        "\n\nYanlış mıyım?",
        "\n\nBu postu kaydedin 📌",
        "\n\nRT yaparsanız daha çok kişiye ulaşır 🙏",
        "\n\nHangisini tercih edersiniz? A mı B mi?",
    ]

    # Thread başlangıç formülleri
    THREAD_STARTERS = [
        "🧵 Thread: {topic}",
        "1/ {topic} hakkında bilmeniz gereken her şey:",
        "📚 {topic} rehberi (kaydedin!):",
        "Herkesin bilmesi gereken {count} şey: 🧵",
        "1/ Son zamanlarda {topic} üzerine çok düşündüm. İşte öğrendiklerim:",
    ]

    # Viral tetikleyici kelimeler
    VIRAL_WORDS_TR = [
        "şok", "inanamayacaksınız", "gizli", "sır", "hata",
        "pişman", "keşfettim", "kimse bilmiyor", "gerçek",
        "thread", "kaydedin", "önemli", "kritik", "son dakika",
        "unpopular opinion", "hot take", "truth bomb",
    ]

    # Emoji stratejisi
    STRATEGIC_EMOJIS = {
        "hook": ["🚨", "⚡", "💥", "🔥", "👀", "❗"],
        "positive": ["✨", "💪", "🎯", "🚀", "💡", "⭐"],
        "engagement": ["👇", "💬", "🤔", "❓", "📌", "🙏"],
        "thread": ["🧵", "📚", "1️⃣", "2️⃣", "3️⃣"],
        "personal": ["😊", "😅", "🙈", "💭", "❤️"],
    }

    @classmethod
    def generate_hook(cls, topic: str) -> str:
        """Konu için hook oluştur"""
        hook = random.choice(cls.HOOKS)
        return hook.format(topic=topic, count=random.randint(5, 10))

    @classmethod
    def add_engagement_trigger(cls, tweet: str) -> str:
        """Tweet'e engagement trigger ekle"""
        trigger = random.choice(cls.ENGAGEMENT_TRIGGERS)
        if len(tweet) + len(trigger) <= 280:
            return tweet + trigger
        return tweet

    @classmethod
    def get_strategic_emoji(cls, category: str = "positive") -> str:
        """Stratejik emoji getir"""
        emojis = cls.STRATEGIC_EMOJIS.get(category, cls.STRATEGIC_EMOJIS["positive"])
        return random.choice(emojis)


class ViralChecklist:
    """
    Tweet yayınlamadan önce kontrol listesi
    XPatla + Twitter Algorithm bilgisine dayalı
    """

    CHECKLIST_ITEMS = [
        {
            "id": "length",
            "check": "280 karakterin altında mı?",
            "tip": "Kısa tweetler (100-150 karakter) daha iyi performans gösterir",
            "weight": 1.3,
        },
        {
            "id": "question",
            "check": "Soru içeriyor mu?",
            "tip": "Reply en değerli etkileşim (13.5x ağırlık)",
            "weight": 1.5,
        },
        {
            "id": "hook",
            "check": "Dikkat çekici başlangıç var mı?",
            "tip": "İlk cümle kanca görevi görmeli",
            "weight": 1.4,
        },
        {
            "id": "emoji",
            "check": "1-2 emoji kullanıldı mı?",
            "tip": "Emoji dikkat çeker ama çok olursa spam görünür",
            "weight": 1.2,
        },
        {
            "id": "hashtag",
            "check": "1-2 hashtag var mı?",
            "tip": "3+ hashtag spam olarak algılanır",
            "weight": 1.1,
        },
        {
            "id": "no_link",
            "check": "Harici link YOK mu?",
            "tip": "Link tweet reach'ini %50 düşürebilir",
            "weight": 1.5,
        },
        {
            "id": "cta",
            "check": "Etkileşim çağrısı var mı?",
            "tip": "'Siz ne düşünüyorsunuz?' gibi bir CTA ekle",
            "weight": 1.4,
        },
        {
            "id": "timing",
            "check": "Prime time'da mı paylaşılacak?",
            "tip": "21:00-22:00 arası en iyi zaman",
            "weight": 1.3,
        },
        {
            "id": "visual",
            "check": "Görsel eklenecek mi?",
            "tip": "Görsel tweetler 3x daha fazla etkileşim alır",
            "weight": 1.5,
        },
        {
            "id": "controversy",
            "check": "Tartışma potansiyeli var mı?",
            "tip": "Polarize edici içerikler daha çok reply alır",
            "weight": 1.6,
        },
    ]

    @classmethod
    def check_tweet(cls, tweet: str, has_image: bool = False, post_time: datetime = None) -> Dict:
        """Tweet'i kontrol et ve skor ver"""
        import re

        results = []
        total_score = 5.0

        # Length check
        length_ok = len(tweet) <= 280
        short_bonus = len(tweet) < 150
        results.append({
            "check": cls.CHECKLIST_ITEMS[0]["check"],
            "passed": length_ok,
            "bonus": short_bonus,
            "tip": cls.CHECKLIST_ITEMS[0]["tip"] if short_bonus else "Biraz kısalt"
        })
        if short_bonus:
            total_score *= 1.3

        # Question check
        has_question = "?" in tweet
        results.append({
            "check": cls.CHECKLIST_ITEMS[1]["check"],
            "passed": has_question,
            "tip": cls.CHECKLIST_ITEMS[1]["tip"]
        })
        if has_question:
            total_score *= 1.5

        # Hook check (viral words)
        has_hook = any(word in tweet.lower() for word in ViralContentFormulas.VIRAL_WORDS_TR[:10])
        results.append({
            "check": cls.CHECKLIST_ITEMS[2]["check"],
            "passed": has_hook,
            "tip": cls.CHECKLIST_ITEMS[2]["tip"]
        })
        if has_hook:
            total_score *= 1.4

        # Emoji check
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0]+")
        emojis = emoji_pattern.findall(tweet)
        emoji_ok = 1 <= len(emojis) <= 3
        results.append({
            "check": cls.CHECKLIST_ITEMS[3]["check"],
            "passed": emoji_ok,
            "tip": cls.CHECKLIST_ITEMS[3]["tip"]
        })
        if emoji_ok:
            total_score *= 1.2

        # Hashtag check
        hashtag_count = tweet.count('#')
        hashtag_ok = 1 <= hashtag_count <= 2
        results.append({
            "check": cls.CHECKLIST_ITEMS[4]["check"],
            "passed": hashtag_ok,
            "tip": cls.CHECKLIST_ITEMS[4]["tip"]
        })
        if hashtag_ok:
            total_score *= 1.1
        elif hashtag_count > 3:
            total_score *= 0.7  # Penalty

        # No link check
        has_link = "http" in tweet.lower() or "www." in tweet.lower()
        no_link = not has_link
        results.append({
            "check": cls.CHECKLIST_ITEMS[5]["check"],
            "passed": no_link,
            "tip": cls.CHECKLIST_ITEMS[5]["tip"]
        })
        if has_link:
            total_score *= 0.5  # Penalty

        # CTA check
        cta_words = ["düşünüyorsunuz", "katılıyor", "yorumlarda", "paylaşın", "rt", "kaydedin", "takip"]
        has_cta = any(word in tweet.lower() for word in cta_words)
        results.append({
            "check": cls.CHECKLIST_ITEMS[6]["check"],
            "passed": has_cta,
            "tip": cls.CHECKLIST_ITEMS[6]["tip"]
        })
        if has_cta:
            total_score *= 1.4

        # Image check
        results.append({
            "check": cls.CHECKLIST_ITEMS[8]["check"],
            "passed": has_image,
            "tip": cls.CHECKLIST_ITEMS[8]["tip"]
        })
        if has_image:
            total_score *= 1.5

        # Normalize score to 1-10
        final_score = min(10, max(1, total_score))

        # Viral potential
        if final_score >= 8:
            potential = "🔥 YÜKSEK - Viral potansiyeli var!"
        elif final_score >= 6:
            potential = "📈 ORTA - İyi performans beklenir"
        elif final_score >= 4:
            potential = "📊 DÜŞÜK-ORTA - Birkaç iyileştirme yap"
        else:
            potential = "⚠️ DÜŞÜK - Önerileri uygula"

        return {
            "score": round(final_score, 1),
            "potential": potential,
            "checks": results,
            "passed_count": sum(1 for r in results if r.get("passed", False)),
            "total_checks": len(results),
        }


class XPatlaInspiredTips:
    """
    XPatla'dan ilham alan pratik ipuçları
    """

    DAILY_TIPS = [
        "💡 İlk 30 dakika kritik! Tweet attıktan sonra aktif ol ve gelen yorumlara hızlıca cevap ver.",
        "🎯 Kendi tweetlerine reply at - bu engagement'ı artırır ve thread gibi görünür.",
        "🔥 Tartışmalı görüş paylaş - insanlar katılmasa bile reply atacaklar (13.5x değerli!).",
        "📊 Rakiplerini analiz et - onların viral tweetlerinden ilham al ama kopyalama.",
        "⏰ Prime time: 21:00-22:00 Türkiye saati en aktif dilim.",
        "🚫 Link paylaşma! Algoritma harici linkleri cezalandırır. Link'i reply'a koy.",
        "🧵 Thread yap - kullanıcılar daha uzun süre kalır, algoritma bunu ödüllendirir.",
        "❓ Soru sor - 'Siz ne düşünüyorsunuz?' basit ama etkili.",
        "📸 Görsel ekle - görselli tweetler 3x daha fazla etkileşim alır.",
        "🔄 Viral tweetlere quote tweet yap - onların kitlesinden faydalanırsın.",
        "📌 En iyi tweetini pinle - yeni takipçiler ilk onu görür.",
        "🎭 Kişisel hikaye paylaş - insanlar bağlanabilecekleri içerikleri sever.",
        "⚡ Gündem konularına hızlı yorum yap - timing çok önemli.",
        "💬 Büyük hesaplara akıllıca reply at - onların takipçileri seni görebilir.",
        "📈 Tutarlı ol - her gün 3-5 tweet hedefle.",
    ]

    CONTENT_IDEAS = [
        "Kendi alanınla ilgili '5 şey' listesi",
        "Popüler bir konuya karşı görüş (hot take)",
        "Kişisel başarısızlık hikayesi + öğrenilen ders",
        "Sektörel insider bilgi",
        "Gündemdeki konuya özgün yorum",
        "Thread formatında rehber",
        "Karşılaştırma (X vs Y)",
        "Tahmin/öngörü paylaşımı",
        "'Bunu yapma' tavsiyeleri",
        "Behind-the-scenes içerik",
    ]

    @classmethod
    def get_daily_tip(cls) -> str:
        """Günün ipucunu getir"""
        return random.choice(cls.DAILY_TIPS)

    @classmethod
    def get_content_ideas(cls, count: int = 3) -> List[str]:
        """İçerik fikirleri getir"""
        return random.sample(cls.CONTENT_IDEAS, min(count, len(cls.CONTENT_IDEAS)))


# Export
viral_time_optimizer = ViralTimeOptimizer()
viral_formulas = ViralContentFormulas()
viral_checklist = ViralChecklist()
xpatla_tips = XPatlaInspiredTips()
