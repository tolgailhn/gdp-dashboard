"""
AI Content Generator Module
Generates natural, human-like tweets using Claude/OpenAI APIs
Optimized for X algorithm and natural Turkish/English writing
"""
import anthropic
import openai
import json

# X Algorithm optimization guidelines
X_ALGORITHM_RULES = """
## X/Twitter Algoritma Kuralları ve Optimizasyon:

1. **İlk satır hook olmalı** - Dikkat çekici, merak uyandıran bir açılış
2. **Kısa paragraflar** - Her cümle ayrı satırda, okunması kolay
3. **Emoji kullanımı dengeli** - Fazla değil, 2-3 emoji yeterli
4. **Hashtag kuralları** - En fazla 2-3 hashtag, tweet sonunda
5. **Thread formatı** - Uzun içerikler thread olarak, her tweet 280 karakter
6. **Engagement tetikleyiciler** - Soru sorma, görüş belirtme, tartışma açma
7. **Zamanlama** - Hook ile başla, bilgi ver, sonuç/görüş ile bitir
8. **Görsel referans** - Eğer görsel varsa referans ver
9. **Kişisel dokunuş** - Robotik değil, gerçek bir insanın yazdığı gibi
10. **Call to action** - "Ne düşünüyorsunuz?", "Siz ne dersiniz?" gibi
"""

# Base system prompt for natural writing
BASE_SYSTEM_PROMPT = """Sen bir Türk teknoloji meraklısısın ve X (Twitter) kullanıcısısın.
Adın Tolga. AI ve teknoloji konularında tutkulu, güncel gelişmeleri takip eden birisin.

## KRİTİK KURALLAR:
- ASLA robotik, şabloncu veya yapay zeka tarafından yazılmış gibi görünen metinler yazma
- ASLA "Bu gelişme heyecan verici" gibi klişe cümleler kullanma
- ASLA "Yapay zeka dünyasında yeni bir sayfa açıldı" gibi gazete manşeti tarzı yazma
- ASLA emoji spam yapma
- Her tweet benzersiz olmalı, kalıp cümleler kullanılmamalı
- Gerçek bir insan gibi yaz - bazen kısa, bazen uzun cümleler, bazen argo
- Kendi görüşlerini ekle, tarafsız haber sunucu gibi yazma
- Türkçe ve İngilizce karışık yazabilirsin (Türk tech Twitter'ında normal)
- Teknik terimleri İngilizce kullanabilirsin (model, benchmark, open-source vs.)

## YAZIM TARZI ÖNEMLİ NOTLAR:
- Samimi ol ama bilgili ol
- Bazen "ya, yani, aslında, bence" gibi günlük dil kullan
- Bazen tweet'in ortasında düşünce değiştirebilirsin
- Duygularını göster - şaşkınlık, heyecan, eleştiri, şüphe
- Spesifik ol - "bu model çok iyi" yerine "bu modelin reasoning'i GPT-4'ü geçmiş coding benchmark'larında"
"""

# Writing style definitions
WRITING_STYLES = {
    "samimi": {
        "name": "Samimi / Günlük",
        "description": "Arkadaşınla sohbet eder gibi, rahat ve samimi",
        "prompt": """
Yazım tarzı: SAMİMİ ve GÜNLÜK
- Arkadaşınla WhatsApp'ta konuşur gibi yaz
- "ya, valla, harbiden, lan, cidden" gibi ifadeler kullanabilirsin
- Kısa cümleler, bazen yarım cümleler
- Emoji kullanabilirsin ama abartma (1-2 tane)
- Şaşkınlık ve heyecanını doğal göster
- Örnek: "Qwen yeni model çıkarmış ya, ben test ettim az önce - coding'de GPT-4o'yu geçmiş cidden. Özellikle math reasoning kısmı çok iyi olmuş. Bunu açık kaynak yapmaları da ayrı güzel."
""",
    },
    "profesyonel": {
        "name": "Profesyonel / Bilgilendirici",
        "description": "Bilgi odaklı, profesyonel ama sıcak",
        "prompt": """
Yazım tarzı: PROFESYONEL ama SICAK
- Bilgilendirici ve detaylı yaz
- Teknik detayları açıkla ama herkesin anlayacağı şekilde
- Kendi analizini ve görüşünü ekle
- Sayılar ve karşılaştırmalar kullan
- Emoji minimal (0-1 tane)
- Örnek: "Anthropic'in yeni Claude modeli ilginç bir yaklaşımla gelmiş. Extended thinking özelliği reasoning benchmark'larında önemli bir fark yaratmış. Özellikle MATH ve GPQA'da %15+ iyileşme var. Bu, chain-of-thought'un model seviyesinde entegrasyonu açısından önemli bir adım."
""",
    },
    "hook": {
        "name": "Hook / Viral Tarz",
        "description": "Dikkat çekici açılış, viral potansiyeli yüksek",
        "prompt": """
Yazım tarzı: HOOK / VİRAL
- İlk cümle MUTLAKA dikkat çekici olmalı (şok edici bilgi, soru, cesur iddia)
- Merak uyandır, "devamını okumak istiyorum" hissi ver
- Kısa, punchline tarzı cümleler
- Thread formatına uygun (ilk tweet hook, sonrakiler bilgi)
- Güçlü bir kapanış (görüş, tahmin veya soru)
- Örnek: "OpenAI sessizce bir şey yaptı ve kimse fark etmedi.\n\nGPT-4'ün yeni versiyonu API'de live oldu. Fark:\n- Coding %40 daha iyi\n- 2x hızlı\n- Fiyat aynı\n\nBu Google'ın Gemini planlarını ciddi etkiler. İşte neden 👇"
""",
    },
    "analitik": {
        "name": "Analitik / Derinlemesine",
        "description": "Derinlemesine analiz, karşılaştırma ve tahminler",
        "prompt": """
Yazım tarzı: ANALİTİK / DERİNLEMESİNE
- Konuyu derinlemesine analiz et
- Karşılaştırmalar yap (önceki modeller, rakipler)
- Sayısal veriler ve benchmark'lar kullan
- Piyasa etkisini değerlendir
- Kendi tahminlerini ekle
- Thread formatı ideal
- Örnek: "Llama 4'ün açık kaynak stratejisi üzerine bir analiz:\n\n1/ Meta'nın bu hamlesi sadece bir model release değil. Piyasaya etkisi:\n\n- OpenAI'ın enterprise fiyatlamasına baskı\n- Küçük şirketler için fine-tuning maliyeti %80 düşüyor\n- Avrupa'daki AI regülasyonlarına karşı bir hamle\n\n2/ Benchmark'lara bakınca..."
""",
    },
    "quote_tweet": {
        "name": "Quote Tweet",
        "description": "Başka bir tweete yorum/quote tweet",
        "prompt": """
Yazım tarzı: QUOTE TWEET
- Orijinal tweet'e tepki ver, yorum yap
- Kendi perspektifini ekle
- Kısa ve etkili ol (1-3 cümle ideal)
- Orijinal tweet'i tekrarlama, ona ek bilgi veya farklı bakış açısı ekle
- Bazen espri, bazen ciddi analiz
- Örnek: "Bunu test ettim - gerçekten çalışıyor. Özellikle Türkçe'de bile reasoning kalitesi fark edilir seviyede artmış. Fine-tuning yapanlar için game changer olabilir."
""",
    },
}


class ContentGenerator:
    """AI-powered content generator for natural tweet writing"""

    def __init__(self, provider: str = "anthropic", api_key: str = None,
                 model: str = None, custom_persona: str = None):
        """
        Initialize content generator

        Args:
            provider: "anthropic" or "openai"
            api_key: API key for the provider
            model: Model to use (default: best available)
            custom_persona: Custom persona description to override default
        """
        self.provider = provider
        self.api_key = api_key
        self.custom_persona = custom_persona

        if provider == "anthropic":
            self.model = model or "claude-sonnet-4-6"
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        elif provider == "openai":
            self.model = model or "gpt-4o"
            self.client = openai.OpenAI(api_key=api_key) if api_key else None
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate_tweet(self, topic_text: str, topic_source: str = "",
                       style: str = "samimi", additional_context: str = "",
                       max_length: int = 0, thread_mode: bool = False,
                       user_samples: list = None) -> str:
        """
        Generate a natural tweet about a topic

        Args:
            topic_text: The AI topic/development to write about
            topic_source: Source URL or username
            style: Writing style key
            additional_context: Extra context or instructions
            max_length: Max character limit (0 = no limit / premium)
            thread_mode: Whether to generate a thread
            user_samples: Sample tweets from user for style matching

        Returns:
            Generated tweet text
        """
        if not self.client:
            raise ValueError("API client not initialized. Check your API key.")

        system_prompt = self._build_system_prompt(style, user_samples)
        user_prompt = self._build_user_prompt(
            topic_text, topic_source, style, additional_context,
            max_length, thread_mode
        )

        if self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            return self._generate_openai(system_prompt, user_prompt)

    def generate_quote_tweet(self, original_tweet: str, original_author: str,
                             style: str = "quote_tweet",
                             additional_context: str = "",
                             user_samples: list = None) -> str:
        """
        Generate a quote tweet response

        Args:
            original_tweet: The tweet being quoted
            original_author: Author of the original tweet
            style: Writing style
            additional_context: Extra instructions
            user_samples: Sample tweets for style matching

        Returns:
            Generated quote tweet text
        """
        if not self.client:
            raise ValueError("API client not initialized. Check your API key.")

        system_prompt = self._build_system_prompt("quote_tweet", user_samples)

        user_prompt = f"""Aşağıdaki tweet'e bir quote tweet yaz.

Orijinal Tweet (@{original_author}):
"{original_tweet}"

{f"Ek talimatlar: {additional_context}" if additional_context else ""}

KURALLAR:
- Orijinal tweet'i tekrarlama
- Kendi bakış açını ekle
- Kısa ve etkili ol (1-3 cümle ideal)
- %100 doğal insan yazısı, robotik olmasın
- Varsa teknik detay ekle veya düzelt
- Kendi deneyiminden/bilginden yararlan

Sadece quote tweet metnini yaz, başka bir şey yazma."""

        if self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            return self._generate_openai(system_prompt, user_prompt)

    def generate_thread(self, topic_text: str, topic_source: str = "",
                        style: str = "analitik", num_tweets: int = 5,
                        additional_context: str = "",
                        user_samples: list = None) -> list[str]:
        """
        Generate a tweet thread

        Args:
            topic_text: The topic to write about
            topic_source: Source URL
            style: Writing style
            num_tweets: Number of tweets in thread
            additional_context: Extra instructions
            user_samples: Sample tweets for style matching

        Returns:
            List of tweet texts forming a thread
        """
        if not self.client:
            raise ValueError("API client not initialized. Check your API key.")

        system_prompt = self._build_system_prompt(style, user_samples)

        user_prompt = f"""Aşağıdaki konu hakkında {num_tweets} tweet'lik bir thread yaz.

Konu:
{topic_text}

{f"Kaynak: {topic_source}" if topic_source else ""}
{f"Ek talimatlar: {additional_context}" if additional_context else ""}

THREAD KURALLARI:
- İlk tweet güçlü bir hook olmalı (merak uyandırmalı)
- Her tweet max 280 karakter
- Her tweet kendi başına da anlam ifade etmeli
- Son tweet güçlü bir kapanış/görüş olmalı
- Tweet'leri 1/, 2/, 3/ şeklinde numaralandır
- Doğal geçişler kullan
- %100 doğal insan yazısı

Her tweet'i --- ile ayır. Sadece tweet metinlerini yaz."""

        if self.provider == "anthropic":
            raw = self._generate_anthropic(system_prompt, user_prompt)
        else:
            raw = self._generate_openai(system_prompt, user_prompt)

        # Parse thread into individual tweets
        tweets = [t.strip() for t in raw.split("---") if t.strip()]
        return tweets

    def rewrite_tweet(self, draft: str, style: str = "samimi",
                      instructions: str = "") -> str:
        """Rewrite/improve an existing draft tweet"""
        if not self.client:
            raise ValueError("API client not initialized. Check your API key.")

        system_prompt = self._build_system_prompt(style)

        user_prompt = f"""Aşağıdaki tweet taslağını yeniden yaz. Daha doğal, daha etkileyici yap.

Taslak:
"{draft}"

{f"Özel talimatlar: {instructions}" if instructions else ""}

KURALLAR:
- Anlamı koru ama daha doğal yaz
- Seçilen yazım tarzına uygun olsun
- Robotik ifadeleri temizle
- Daha etkileyici ve engaging yap

Sadece yeni tweet metnini yaz."""

        if self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            return self._generate_openai(system_prompt, user_prompt)

    def _build_system_prompt(self, style: str, user_samples: list = None) -> str:
        """Build the complete system prompt"""
        persona = self.custom_persona or BASE_SYSTEM_PROMPT

        style_info = WRITING_STYLES.get(style, WRITING_STYLES["samimi"])

        prompt = f"""{persona}

{X_ALGORITHM_RULES}

{style_info['prompt']}
"""

        if user_samples:
            samples_text = "\n".join([f"- {s}" for s in user_samples[:10]])
            prompt += f"""
## KULLANICININ GERÇEK TWEET ÖRNEKLERİ (bu tarzda yaz):
{samples_text}

Bu örneklerdeki yazım tarzını, kelime seçimini, cümle yapısını ve tonlamayı analiz et.
Yeni tweet'i bu tarzda yaz. Birebir kopyalama ama aynı ruh ve tarz olsun.
"""

        return prompt

    def _build_user_prompt(self, topic_text: str, topic_source: str,
                           style: str, additional_context: str,
                           max_length: int, thread_mode: bool) -> str:
        """Build the user prompt"""
        prompt = f"""Aşağıdaki AI gelişmesi/konusu hakkında bir tweet yaz.

KONU:
{topic_text}

{f"KAYNAK: {topic_source}" if topic_source else ""}
{f"EK TALİMATLAR: {additional_context}" if additional_context else ""}
{f"MAKSİMUM KARAKTER: {max_length}" if max_length > 0 else "Karakter sınırı yok (X Premium)"}

KURALLAR:
- %100 doğal, insan yazısı olmalı
- Robotik kalıplar YASAK
- Klişe açılışlar YASAK (Heyecan verici gelişme!, Yapay zeka dünyasında... vs.)
- Kendi bakış açını ve yorumunu ekle
- Teknik detayları doğru ver
- X algoritmasına uygun formatla

Sadece tweet metnini yaz, başka bir şey yazma. Tırnak işareti kullanma."""

        return prompt

    def _generate_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using Anthropic Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.9,
        )
        return response.content[0].text.strip()

    def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()

    def analyze_writing_style(self, sample_tweets: list[str]) -> str:
        """
        Analyze user's writing style from sample tweets
        Returns a style description that can be used as custom_persona
        """
        if not self.client:
            raise ValueError("API client not initialized.")

        samples = "\n".join([f"{i+1}. {t}" for i, t in enumerate(sample_tweets[:20])])

        prompt = f"""Aşağıdaki tweet örneklerini analiz et ve yazarın yazım tarzını detaylı olarak tanımla.

Tweet örnekleri:
{samples}

Şunları analiz et ve raporla:
1. Genel ton (samimi, profesyonel, espirili, ciddi?)
2. Cümle yapısı (kısa/uzun, basit/karmaşık)
3. Kelime tercihleri ve sık kullanılan ifadeler
4. Emoji kullanımı
5. Türkçe-İngilizce karışım oranı
6. Konu sunuş tarzı (direkt bilgi, soru ile açma, hook kullanımı)
7. Kişisel görüş ekleme tarzı
8. Hashtag kullanımı

Bu analizi, AI'ın aynı tarzda tweet yazabilmesi için bir "yazım profili" olarak formatla."""

        system = "Sen bir yazım tarzı analisti̇si̇n. Tweet'leri analiz edip yazarın benzersiz tarzını tespit ediyorsun."

        if self.provider == "anthropic":
            return self._generate_anthropic(system, prompt)
        else:
            return self._generate_openai(system, prompt)


def get_available_styles() -> dict:
    """Get all available writing styles"""
    return WRITING_STYLES


def get_style_info(style_key: str) -> dict:
    """Get info about a specific writing style"""
    return WRITING_STYLES.get(style_key, WRITING_STYLES["samimi"])
