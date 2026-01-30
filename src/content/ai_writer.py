"""
AI İçerik Oluşturma Modülü
==========================

OpenAI GPT ve Anthropic Claude kullanarak tweet içeriği oluşturma.
Twitter algoritmasına göre optimize edilmiş içerik üretimi.

Özellikler:
- Trend bazlı içerik oluşturma
- Kısa/uzun tweet otomatik seçimi
- Thread oluşturma
- Hashtag önerisi
- Emoji kullanımı (opsiyonel)
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

import sys
sys.path.append(str(__file__).rsplit('/', 3)[0])
from config.settings import config

logger = logging.getLogger(__name__)


class TweetLength(Enum):
    """Tweet uzunluk türleri"""
    SHORT = "short"      # 1-140 karakter
    MEDIUM = "medium"    # 141-200 karakter
    LONG = "long"        # 201-280 karakter
    THREAD = "thread"    # 280+ karakter (çoklu tweet)


class TweetType(Enum):
    """Tweet türleri"""
    INFORMATIVE = "informative"      # Bilgilendirici
    OPINION = "opinion"              # Görüş/yorum
    QUESTION = "question"            # Soru (etkileşim artırıcı)
    ENGAGING = "engaging"            # Etkileşim odaklı
    TRENDING = "trending"            # Gündem yorumu
    EDUCATIONAL = "educational"      # Eğitici
    HUMOROUS = "humorous"            # Mizahi


@dataclass
class GeneratedTweet:
    """Oluşturulan tweet veri sınıfı"""
    text: str
    length_type: TweetLength
    tweet_type: TweetType
    hashtags: List[str]
    suggested_image_query: str
    thread_parts: List[str] = None
    engagement_prediction: str = "medium"

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "length_type": self.length_type.value,
            "tweet_type": self.tweet_type.value,
            "hashtags": self.hashtags,
            "suggested_image_query": self.suggested_image_query,
            "thread_parts": self.thread_parts,
            "engagement_prediction": self.engagement_prediction,
            "char_count": len(self.text),
        }


class AIContentWriter:
    """
    AI tabanlı tweet içerik oluşturucu

    Bu sınıf OpenAI veya Anthropic API kullanarak:
    - Trend bazlı tweet oluşturur
    - İçerik uzunluğunu otomatik belirler
    - Hashtag önerir
    - Thread oluşturur
    """

    def __init__(self):
        """AI writer'ı başlat"""
        self.provider = config.ai.get_active_provider()
        self.client = None

        self._setup_client()

    def _setup_client(self):
        """AI istemcisini kur"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=config.ai.openai_api_key)
                logger.info("OpenAI istemcisi başlatıldı")

            elif self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic(api_key=config.ai.anthropic_api_key)
                logger.info("Anthropic istemcisi başlatıldı")

            else:
                logger.warning("AI sağlayıcı yapılandırılmamış, demo modda çalışılacak")

        except ImportError as e:
            logger.error(f"AI kütüphanesi yüklü değil: {e}")
        except Exception as e:
            logger.error(f"AI istemci hatası: {e}")

    @property
    def is_available(self) -> bool:
        """AI istemcisinin kullanılabilir olup olmadığını kontrol et"""
        return self.client is not None

    # ========================================================================
    # ANA İÇERİK OLUŞTURMA
    # ========================================================================

    def generate_tweet(
        self,
        topic: str,
        context: str = "",
        tweet_type: TweetType = None,
        preferred_length: TweetLength = None,
        include_hashtags: bool = True,
        persona: str = None,
        language: str = "tr"
    ) -> GeneratedTweet:
        """
        Tweet içeriği oluştur

        Args:
            topic: Konu/trend
            context: Ek bağlam bilgisi
            tweet_type: Tweet türü (otomatik seçilir)
            preferred_length: Tercih edilen uzunluk (otomatik seçilir)
            include_hashtags: Hashtag ekle
            persona: Kişilik/üslup
            language: Dil

        Returns:
            Oluşturulan tweet
        """

        # Tweet türünü ve uzunluğunu belirle
        if tweet_type is None:
            tweet_type = self._determine_tweet_type(topic, context)

        if preferred_length is None:
            preferred_length = self._determine_optimal_length(topic, tweet_type)

        # Prompt oluştur
        prompt = self._build_generation_prompt(
            topic=topic,
            context=context,
            tweet_type=tweet_type,
            length=preferred_length,
            include_hashtags=include_hashtags,
            persona=persona,
            language=language
        )

        # AI ile içerik oluştur
        if self.is_available:
            response = self._call_ai(prompt)
        else:
            response = self._generate_demo_content(topic, tweet_type)

        # Yanıtı parse et
        return self._parse_ai_response(response, tweet_type, preferred_length)

    def generate_thread(
        self,
        topic: str,
        context: str = "",
        num_tweets: int = 3,
        persona: str = None
    ) -> GeneratedTweet:
        """
        Thread (tweet zinciri) oluştur

        Args:
            topic: Konu
            context: Bağlam
            num_tweets: Tweet sayısı
            persona: Kişilik

        Returns:
            Thread içeren GeneratedTweet
        """

        prompt = f"""
        Sen bir Twitter/X uzmanısın. Aşağıdaki konu hakkında {num_tweets} tweetlik bir thread oluştur.

        KONU: {topic}
        {"BAĞLAM: " + context if context else ""}
        {"KİŞİLİK: " + persona if persona else ""}

        KURALLAR:
        1. Her tweet maksimum 280 karakter olmalı
        2. İlk tweet dikkat çekici olmalı (hook)
        3. Tweetler arasında mantıksal akış olmalı
        4. Son tweet bir çağrı içermeli (CTA)
        5. Her tweeti "---" ile ayır
        6. Tweet numarası ekle (1/, 2/, vb.)
        7. Türkçe yaz
        8. Doğal ve samimi bir dil kullan
        9. Son tweete uygun 2-3 hashtag ekle

        FORMAT:
        1/ [İlk tweet - hook]
        ---
        2/ [İkinci tweet - detay]
        ---
        3/ [Son tweet - CTA + hashtag'ler]

        GORSEL_ONERISI: [Thread için uygun görsel arama terimi]
        """

        if self.is_available:
            response = self._call_ai(prompt)
        else:
            response = self._generate_demo_thread(topic, num_tweets)

        return self._parse_thread_response(response, topic)

    def generate_trending_tweet(
        self,
        trend_name: str,
        trend_context: str,
        top_tweets: List[Dict] = None,
        persona: str = None
    ) -> GeneratedTweet:
        """
        Gündemdeki bir konu hakkında tweet oluştur

        Args:
            trend_name: Trend adı
            trend_context: Trend hakkında bağlam
            top_tweets: En popüler tweetler (örnek için)
            persona: Kişilik

        Returns:
            Oluşturulan tweet
        """

        examples = ""
        if top_tweets:
            examples = "\n\nÖRNEK POPÜLER TWEETLER:\n"
            for i, tweet in enumerate(top_tweets[:3], 1):
                examples += f"{i}. {tweet.get('text', '')[:100]}...\n"

        prompt = f"""
        Sen bir Twitter/X içerik uzmanısın. Gündemdeki bir konu hakkında etkileşim alacak bir tweet yaz.

        GÜNDEM: {trend_name}
        BAĞLAM: {trend_context}
        {examples}
        {"KİŞİLİK/ÜSLUP: " + persona if persona else ""}

        KURALLAR:
        1. Kendi özgün bakış açını sun
        2. Trend hakkında bilgili görün
        3. Etkileşim alacak şekilde yaz (soru, görüş, bilgi)
        4. Maksimum 280 karakter
        5. 1-3 uygun hashtag ekle
        6. Türkçe yaz
        7. Doğal ol, robot gibi yazma
        8. Gündem hakkında değerli bir şey söyle

        TWEET:
        [Tweet metni buraya]

        HASHTAG'LER: [hashtag1, hashtag2]
        GORSEL_ONERISI: [Görsel için arama terimi]
        ETKILESIM_TAHMINI: [düşük/orta/yüksek]
        """

        if self.is_available:
            response = self._call_ai(prompt)
        else:
            response = self._generate_demo_trending(trend_name)

        return self._parse_ai_response(response, TweetType.TRENDING, TweetLength.LONG)

    def improve_tweet(self, original_tweet: str) -> GeneratedTweet:
        """
        Mevcut bir tweeti iyileştir

        Args:
            original_tweet: Orijinal tweet

        Returns:
            İyileştirilmiş tweet
        """

        prompt = f"""
        Sen bir Twitter/X içerik uzmanısın. Aşağıdaki tweeti daha etkili hale getir.

        ORİJİNAL TWEET:
        {original_tweet}

        KURALLAR:
        1. Aynı mesajı koru ama daha etkili sun
        2. Dikkat çekici bir açılış kullan
        3. Gereksiz kelimeleri çıkar
        4. Etkileşim artırıcı öğeler ekle
        5. Maksimum 280 karakter
        6. 1-2 uygun hashtag öner

        İYİLEŞTİRİLMİŞ TWEET:
        [Yeni tweet metni]

        HASHTAG'LER: [hashtag1, hashtag2]
        GORSEL_ONERISI: [Görsel önerisi]
        """

        if self.is_available:
            response = self._call_ai(prompt)
        else:
            response = original_tweet  # Demo modda değişiklik yok

        return self._parse_ai_response(response, TweetType.INFORMATIVE, TweetLength.MEDIUM)

    # ========================================================================
    # YARDIMCI METODLAR
    # ========================================================================

    def _determine_tweet_type(self, topic: str, context: str) -> TweetType:
        """Konu ve bağlama göre en uygun tweet türünü belirle"""

        topic_lower = topic.lower()

        # Anahtar kelime bazlı basit sınıflandırma
        if any(word in topic_lower for word in ["nasıl", "nedir", "neden", "ne zaman"]):
            return TweetType.EDUCATIONAL

        if any(word in topic_lower for word in ["düşünce", "görüş", "fikir"]):
            return TweetType.OPINION

        if "?" in topic or any(word in topic_lower for word in ["sence", "sizce"]):
            return TweetType.QUESTION

        if any(word in topic_lower for word in ["son dakika", "flaş", "gündem"]):
            return TweetType.TRENDING

        # Varsayılan
        return TweetType.INFORMATIVE

    def _determine_optimal_length(self, topic: str, tweet_type: TweetType) -> TweetLength:
        """En uygun tweet uzunluğunu belirle"""

        # Soru ve etkileşim tweetleri kısa olmalı
        if tweet_type in [TweetType.QUESTION, TweetType.ENGAGING]:
            return TweetLength.SHORT

        # Eğitici içerik uzun olabilir
        if tweet_type == TweetType.EDUCATIONAL:
            return TweetLength.LONG

        # Trend yorumları orta
        if tweet_type == TweetType.TRENDING:
            return TweetLength.MEDIUM

        # Varsayılan
        return TweetLength.MEDIUM

    def _build_generation_prompt(
        self,
        topic: str,
        context: str,
        tweet_type: TweetType,
        length: TweetLength,
        include_hashtags: bool,
        persona: str,
        language: str
    ) -> str:
        """AI için prompt oluştur"""

        length_guide = {
            TweetLength.SHORT: "Kısa ve öz, maksimum 140 karakter",
            TweetLength.MEDIUM: "Orta uzunlukta, 140-200 karakter arası",
            TweetLength.LONG: "Detaylı, 200-280 karakter arası",
        }

        type_guide = {
            TweetType.INFORMATIVE: "Bilgilendirici ve değer katan",
            TweetType.OPINION: "Güçlü bir görüş içeren",
            TweetType.QUESTION: "Düşündürücü bir soru soran",
            TweetType.ENGAGING: "Etkileşim almaya yönelik",
            TweetType.TRENDING: "Gündem hakkında özgün bir bakış",
            TweetType.EDUCATIONAL: "Öğretici ve aydınlatıcı",
            TweetType.HUMOROUS: "Hafif ve eğlenceli",
        }

        prompt = f"""
        Sen profesyonel bir Twitter/X içerik yazarısın. Aşağıdaki kriterlere göre bir tweet yaz.

        KONU: {topic}
        {"BAĞLAM: " + context if context else ""}

        TWEET TÜRÜ: {type_guide.get(tweet_type, "Bilgilendirici")}
        UZUNLUK: {length_guide.get(length, "Orta uzunlukta")}
        DİL: {"Türkçe" if language == "tr" else language}
        {"KİŞİLİK/ÜSLUP: " + persona if persona else "Samimi ve profesyonel"}

        TWITTER ALGORİTMASI İPUÇLARI:
        - İlk birkaç kelime çok önemli (hook)
        - Reply almaya teşvik et (soru sor, görüş iste)
        - Değer kat (bilgi, eğlence, düşündürme)
        - Doğal ol, reklam gibi olmasın

        TWEET:
        [Sadece tweet metnini yaz, açıklama ekleme]

        {"HASHTAG'LER: [uygun hashtag'leri virgülle ayırarak yaz]" if include_hashtags else ""}
        GORSEL_ONERISI: [Bu tweet için uygun görsel arama terimi]
        ETKILESIM_TAHMINI: [düşük/orta/yüksek]
        """

        return prompt

    def _call_ai(self, prompt: str) -> str:
        """AI API'yi çağır"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=config.ai.openai_model,
                    messages=[
                        {"role": "system", "content": "Sen bir Twitter/X içerik uzmanısın. Türkçe yanıt ver."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=config.ai.max_tokens,
                    temperature=config.ai.temperature
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=config.ai.anthropic_model,
                    max_tokens=config.ai.max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"AI API hatası: {e}")
            return ""

        return ""

    def _parse_ai_response(
        self,
        response: str,
        tweet_type: TweetType,
        length: TweetLength
    ) -> GeneratedTweet:
        """AI yanıtını parse et"""

        if not response:
            return self._create_fallback_tweet(tweet_type)

        # Tweet metnini çıkar
        text = response
        hashtags = []
        image_query = ""
        engagement = "medium"

        # TWEET: bloğunu bul
        if "TWEET:" in response:
            parts = response.split("TWEET:")
            if len(parts) > 1:
                text = parts[1].split("\n")[0].strip()
                if not text:
                    lines = parts[1].strip().split("\n")
                    text = lines[0] if lines else response

        # Hashtag'leri çıkar
        if "HASHTAG" in response.upper():
            hashtag_match = re.search(r"HASHTAG[^\[]*\[([^\]]+)\]", response, re.IGNORECASE)
            if hashtag_match:
                hashtags = [h.strip().replace("#", "") for h in hashtag_match.group(1).split(",")]

        # Görsel önerisini çıkar
        if "GORSEL" in response.upper():
            image_match = re.search(r"GORSEL[^\[]*\[([^\]]+)\]", response, re.IGNORECASE)
            if image_match:
                image_query = image_match.group(1).strip()

        # Etkileşim tahminini çıkar
        if "ETKILESIM" in response.upper():
            if "yüksek" in response.lower():
                engagement = "high"
            elif "düşük" in response.lower():
                engagement = "low"

        # Tweet metnini temizle
        text = text.strip().strip('"').strip("'")

        # Karakter limitini kontrol et
        if len(text) > 280:
            text = text[:277] + "..."

        return GeneratedTweet(
            text=text,
            length_type=length,
            tweet_type=tweet_type,
            hashtags=hashtags[:config.algorithm.max_hashtags],
            suggested_image_query=image_query,
            engagement_prediction=engagement
        )

    def _parse_thread_response(self, response: str, topic: str) -> GeneratedTweet:
        """Thread yanıtını parse et"""

        parts = response.split("---")
        thread_tweets = []

        for part in parts:
            cleaned = part.strip()
            if cleaned and not cleaned.startswith("GORSEL") and not cleaned.startswith("FORMAT"):
                # Tweet numarasını temizle
                cleaned = re.sub(r"^\d+[/\\)]\s*", "", cleaned)
                if cleaned and len(cleaned) <= 280:
                    thread_tweets.append(cleaned)

        if not thread_tweets:
            thread_tweets = [f"{topic} hakkında bilmeniz gerekenler..."]

        # Görsel önerisini çıkar
        image_query = topic
        if "GORSEL" in response.upper():
            image_match = re.search(r"GORSEL[^\[]*\[([^\]]+)\]", response, re.IGNORECASE)
            if image_match:
                image_query = image_match.group(1).strip()

        # Hashtag'leri son tweetten çıkar
        hashtags = []
        last_tweet = thread_tweets[-1] if thread_tweets else ""
        hashtag_matches = re.findall(r"#(\w+)", last_tweet)
        hashtags = hashtag_matches[:3]

        return GeneratedTweet(
            text=thread_tweets[0] if thread_tweets else topic,
            length_type=TweetLength.THREAD,
            tweet_type=TweetType.EDUCATIONAL,
            hashtags=hashtags,
            suggested_image_query=image_query,
            thread_parts=thread_tweets,
            engagement_prediction="high"
        )

    def _create_fallback_tweet(self, tweet_type: TweetType) -> GeneratedTweet:
        """Fallback tweet oluştur"""
        return GeneratedTweet(
            text="[İçerik oluşturulamadı - lütfen tekrar deneyin]",
            length_type=TweetLength.SHORT,
            tweet_type=tweet_type,
            hashtags=[],
            suggested_image_query="",
            engagement_prediction="low"
        )

    def _generate_demo_content(self, topic: str, tweet_type: TweetType) -> str:
        """Demo içerik oluştur (AI yokken)"""

        templates = {
            TweetType.INFORMATIVE: f"{topic} hakkında bilmeniz gereken en önemli şey şu ki, bu alanda sürekli gelişmeler yaşanıyor.",
            TweetType.OPINION: f"{topic} konusunda bence herkesin gözden kaçırdığı bir nokta var. Siz ne düşünüyorsunuz?",
            TweetType.QUESTION: f"{topic} denince aklınıza ilk ne geliyor? Yorumlarda buluşalım!",
            TweetType.ENGAGING: f"Bu {topic} gerçeğini kaç kişi biliyordu? RT yapın, herkes öğrensin!",
            TweetType.TRENDING: f"Gündemdeki {topic} hakkında şunu söylemem lazım...",
            TweetType.EDUCATIONAL: f"{topic} nedir ve neden önemli? Hızlıca açıklayalım:",
            TweetType.HUMOROUS: f"{topic} ile ilgili en komik şey şu ki...",
        }

        text = templates.get(tweet_type, f"{topic} hakkında düşüncelerim...")

        return f"""
        TWEET: {text}
        HASHTAG'LER: [{topic.replace(' ', '')}, Gündem, Trending]
        GORSEL_ONERISI: [{topic}]
        ETKILESIM_TAHMINI: [orta]
        """

    def _generate_demo_thread(self, topic: str, num_tweets: int) -> str:
        """Demo thread oluştur"""

        thread = f"""
        1/ {topic} hakkında bilmeniz gereken {num_tweets} önemli şey var. Thread başlıyor!
        ---
        2/ İlk olarak, {topic} alanında son yıllarda büyük gelişmeler yaşandı. Bu değişimler herkesi etkiliyor.
        ---
        3/ Sonuç olarak, {topic} konusunda bilinçli olmak artık bir tercih değil, zorunluluk. Siz ne düşünüyorsunuz?

        #{topic.replace(' ', '')} #Bilgi #Thread

        GORSEL_ONERISI: [{topic}]
        """
        return thread

    def _generate_demo_trending(self, trend_name: str) -> str:
        """Demo trending tweet oluştur"""
        return f"""
        TWEET: {trend_name} gündemde ve herkesin bir fikri var. Benim görüşüm ise şu: Bu konuyu daha geniş perspektiften değerlendirmemiz gerekiyor.

        HASHTAG'LER: [{trend_name.replace('#', '').replace(' ', '')}, Gündem]
        GORSEL_ONERISI: [{trend_name}]
        ETKILESIM_TAHMINI: [orta]
        """


# Singleton instance
ai_writer = AIContentWriter()
