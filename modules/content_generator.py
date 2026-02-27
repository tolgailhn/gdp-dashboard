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

## KRİTİK KURALLAR - BUNLARI KESİNLİKLE YAPMA:
- ASLA robotik, şabloncu veya yapay zeka tarafından yazılmış gibi görünen metinler yazma
- ASLA "Bu gelişme heyecan verici" gibi klişe cümleler kullanma
- ASLA "Yapay zeka dünyasında yeni bir sayfa açıldı" gibi gazete manşeti tarzı yazma
- ASLA emoji spam yapma
- ASLA "İşte detaylar:", "Gelin birlikte bakalım", "Özetlemek gerekirse" gibi sunum kalıpları kullanma
- ASLA "dikkat çekici", "çığır açan", "devrim niteliğinde", "oyun değiştirici" gibi abartılı sıfatlar kullanma
- ASLA "bu bağlamda", "bu doğrultuda", "son olarak", "sonuç olarak" gibi akademik geçişler kullanma
- ASLA hashtag'leri tweet'in ortasına koyma, gerekliyse en sona 1-2 tane
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

## GERÇEK İNSAN TWEET ÖRNEKLERİ (bu tarz ve tonlamada yaz):

Örnek 1: "Qwen'in yeni modeli çıkmış ya, ben bi baktım - coding'de GPT-4o seviyesine gelmiş. Özellikle function calling kısmı çok iyi olmuş, açık kaynak olması da cabası"

Örnek 2: "Anthropic sessizce Claude'un context window'unu 200K'ya çıkarmış. Test ettim, uzun dökümanları gerçekten anlıyor, önceki gibi hallucination yapmıyor ortalarında"

Örnek 3: "ya bu Llama 4'ü gördünüz mü, Meta ciddi ciddi open-source'da liderliği almaya çalışıyor. Fine-tuning maliyeti de düşmüş epey, küçük takımlar için güzel haber"

Örnek 4: "Google DeepMind'ın yeni paper'ı var reasoning üzerine - kısaca: chain-of-thought'u model seviyesinde entegre etmişler, MATH benchmark'ta %15+ artış. Bu yaklaşım bence önümüzdeki 6 ayda standart olur"

Örnek 5: "Hızlı bir karşılaştırma yaptım:\n\nClaude Sonnet: hızlı, coding'de iyi\nGPT-4o: genel amaçlı, stabil\nGemini Pro: multimodal'da güçlü\n\nGünlük kullanım için hala Claude tercihim ama proje bazlı değişiyor"
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

ASLA orijinal tweet'i Türkçeye çevirme veya tekrarlama!
Tweet'in KONUSU hakkında KENDİ YORUMUNU yaz.

İyi quote tweet örnekleri:
- "Bunu test ettim, coding'de gerçekten fark var. Özellikle Türkçe prompt'larda bile reasoning kalitesi artmış"
- "Herkes bunu konuşuyor ama asıl ilginç olan pricing kısmı - API fiyatını %40 düşürmüşler, bu küçük startuplar için büyük fark yaratır"
- "ya bunu gördüm de hemen denedim, bi önceki versiyona göre context window'u gerçekten uzun dökümanları anlıyor artık"
- "Bence asıl rekabet burada başlıyor. Open-source tarafı bu kadar güçlenince OpenAI'ın fiyat politikası değişmek zorunda"
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
        elif provider == "minimax":
            self.model = model or "MiniMax-M2.5"
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.minimax.io/v1",
            ) if api_key else None
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
                             user_samples: list = None,
                             research_summary: str = "") -> str:
        """Generate a quote tweet with optional deep research context"""
        if not self.client:
            raise ValueError("API client not initialized. Check your API key.")

        system_prompt = self._build_system_prompt(style, user_samples)

        if research_summary:
            # Override system prompt for research mode - remove "KISA YAZ" constraints
            system_prompt = self._build_research_system_prompt(user_samples)
            # RESEARCH MODE: AI has full context, write detailed analytical post
            user_prompt = f"""Görevin: Aşağıdaki araştırma bilgilerini DERİNLEMESİNE oku. Tüm rakamları, ilişkileri, stratejik detayları anla. Sonra bu konu hakkında DETAYLİ ANALİTİK bir Türkçe tweet/thread yaz.

{research_summary}

{f"Kullanıcı notu: {additional_context}" if additional_context else ""}

## GÖREV:
Yukarıdaki TÜM bilgileri (thread, web araştırması, diğer yorumlar) derinlemesine analiz et.
Araştırmadaki spesifik rakamları, isimleri, ilişkileri kullanarak UZUN ve DETAYLİ bir analiz yaz.

## NASIL YAZMALISIN (ÇOK ÖNEMLİ):

1. **RAKAM DAĞILIMI YAP**: Toplu rakamı parçalarına ayır. "110 milyar" deme, "Amazon 50, NVIDIA 30, SoftBank 30" de.

2. **PARADOKS VE ÇELİŞKİLERİ BUL**: İlişkilerdeki ilginçlikleri yakala.
   Örnek: "NVIDIA hem çip satıyor hem de en büyük müşterisine yatırım yapıyor. Hem tedarikçisin hem ortaksın."
   Örnek: "Amazon hem Anthropic'e hem OpenAI'a yatırım yapıyor. İki rakibe birden para döküyorsun."

3. **MAKRO KARŞILAŞTIRMALAR YAP**: Büyük rakamları somutlaştır.
   Örnek: "OpenAI tek başına bazı G20 ülkelerinin yıllık bütçesinden büyük yatırım topladı."
   Örnek: "Bu para ile X tane startup fonlanabilirdi."

4. **STRATEJİK ANALİZ YAP**: Neden böyle olduğunu açıkla.
   Örnek: "Asıl savaş model değil, altyapı. Kim compute sağlarsa o kazanır."

5. **PROVOKATIF SORUYLA BİTİR**: Okuyucuyu düşündürecek bir soruyla kapat.
   Örnek: "Bu kadar parayı gerçekten ürüne mi dönüştürecekler yoksa compute yarışında buharlaşıp mı gidecek?"

## UZUNLUK VE FORMAT:
- KISA YAZMA! Minimum 4-5 paragraf yaz. Detaylı analiz istiyorum.
- Her paragraf farklı bir açıdan konuyu ele alsın
- Araştırmadan bulduğun SPESİFİK rakamları, isimleri, tarihleri kullan
- Düz metin yaz, madde işareti veya liste formatı kullanma
- Doğal Türkçe günlük dil kullan, teknik terimler İngilizce kalabilir

## ÖRNEK ÇIKTI (bu tarz ve uzunlukta yaz):
"110 milyar dolar tek turda. Amazon 50, nvidia 30, softbank 30. Ön değerleme 730 milyar.

Bu artık bir yapay zeka şirketi değil, küçük bir ülke ekonomisi. Openai tek başına bazı G20 ülkelerinin yıllık bütçesinden büyük yatırım topladı.

Bir düşün, nvidia hem çip satıyor hem de en büyük müşterisine yatırım yapıyor. Yani hem tedarikçisin hem ortaksın. Bu ilişki yapısı klasik iş modellerine sığmıyor.

Amazon tarafı da ilginç. Aws zaten anthropice milyarlar dökmüştü, şimdi openaia da 50 milyar. İki rakibe birden yatırım yapıyorsun çünkü asıl savaş model değil, altyapı.

Sama şükran mesajı yazmış ama ben şunu merak ediyorum: bu kadar parayı gerçekten ürüne mi dönüştürecekler yoksa compute yarışında buharlaşıp mı gidecek?"

## YAPMA:
- Orijinal tweet'i Türkçeye çevirme veya özetleme
- "Heyecan verici", "çığır açan", "dikkat çekici gelişme" gibi klişeler kullanma
- Orijinal tweet'teki cümleleri tekrarlama
- KISA YAZMA - 1-3 cümlelik yüzeysel yorum yazma, DERİNLEMESİNE analiz yaz
- Madde işareti, numara listesi kullanma - düz paragraflar halinde yaz

Sadece tweet metnini yaz, başka bir şey yazma."""
        else:
            # NO RESEARCH: simple quote tweet
            user_prompt = f"""@{original_author} şunu yazmış:
"{original_tweet}"

Bu konu hakkında KENDİ YORUMUNU yaz. Orijinal tweet'i çevirme veya tekrarlama.
Kendi bakış açını ekle, kısa tut (1-3 cümle), doğal Türkçe yaz.
{f"Not: {additional_context}" if additional_context else ""}

Sadece tweet metnini yaz."""

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

    def _build_research_system_prompt(self, user_samples: list = None) -> str:
        """Build system prompt optimized for research-based detailed analysis"""
        persona = self.custom_persona or BASE_SYSTEM_PROMPT

        prompt = f"""{persona}

## ARAŞTIRMA MODU - DETAYLİ ANALİZ:
Bu modda KISA tweet yazmıyorsun. Araştırma verilerini kullanarak DETAYLİ ANALİTİK bir yazı yazıyorsun.

KURALLAR:
- Minimum 4-5 paragraf yaz, detaylı ol
- Araştırmadan SPESİFİK rakamlar, isimler ve veriler kullan
- Paradoksları, çelişkileri ve ilginç ilişkileri yakala
- Makro karşılaştırmalar yap (ülke bütçeleri, piyasa değerleri vs.)
- Stratejik analiz yap - "neden" sorusunu cevapla
- Provokatif bir soruyla bitir
- Düz paragraflar halinde yaz, liste/madde işareti kullanma
- Doğal Türkçe yaz, teknik terimler İngilizce kalabilir
- Robotik AI kalıpları YASAK
"""

        if user_samples:
            samples_text = "\n".join([f"- {s}" for s in user_samples[:10]])
            prompt += f"""
## KULLANICININ GERÇEK TWEET ÖRNEKLERİ (bu tarzda yaz):
{samples_text}
"""

        return prompt

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

        # Extra guardrails for MiniMax and other non-Claude models
        if self.provider in ("minimax", "openai"):
            prompt += """
## EK DOĞALLIK KURALLARI (ÇOK ÖNEMLİ):
Bu bir tweet, blog yazısı değil. Şu kurallara kesinlikle uy:

1. KISA YAZ - Gereksiz açıklama yapma. Direkt konuya gir.
2. YAPAY İFADELER YASAK - "dikkat çekici", "önemle belirtmek gerekir", "gelin bakalım", "kısacası" gibi AI kalıpları kullanma
3. TÜRKÇE GÜNLÜK DİL - "ya", "bence", "harbiden", "bi baktım", "valla" gibi konuşma dili kullan
4. TEK TWEET = TEK FİKİR - Her şeyi anlatmaya çalışma, tek bir noktayı vur
5. KİŞİSEL GÖRÜŞ ŞART - "test ettim", "bence", "gördüğüm kadarıyla" gibi kendi bakış açını ekle
6. ASLA liste formatında başlama - "1. şu 2. bu" şeklinde başlama, doğal cümlelerle yaz
7. ASLA "İşte" ile başlama
8. Tırnak işareti ("") kullanma, tweet metnini direkt yaz
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
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.9,
        )
        return response.content[0].text.strip()

    def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using OpenAI-compatible API (OpenAI, MiniMax, etc.)"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.9,
        )
        text = response.choices[0].message.content.strip()
        # Strip <think> tags from reasoning models (MiniMax, etc.)
        import re
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        return text

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
