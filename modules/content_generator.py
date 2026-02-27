"""
AI Content Generator Module
Generates natural, human-like tweets using Claude/OpenAI APIs
Optimized for X algorithm and natural Turkish/English writing
"""
import anthropic
import openai
import json

# X Algorithm optimization guidelines — based on real algorithm data (2025-2026)
X_ALGORITHM_RULES = """
## X/Twitter Algoritma Kuralları (Gerçek Veriler, 2025-2026):

### Engagement Puanlama (Algoritma ağırlıkları):
- Retweet = 20x puan (en değerli!)
- Reply = 13.5x puan
- Profil tıklaması = 12x puan
- Link tıklaması = 11x puan
- Bookmark = 10x puan
- Like = 1x puan (en düşük!)

### Dwell Time (Okuma Süresi):
- Algoritma kullanıcının tweet'te ne kadar süre harcadığını ölçer
- Uzun süre okunan tweet'ler daha fazla gösterilir
- Bu yüzden: merak uyandır, paragrafları kısa tut, okumaya teşvik et

### FORMAT KURALLARI (ÇOK ÖNEMLİ):
1. İLK SATIR = HOOK: Konuyu tanıtan ama merak uyandıran doğal bir giriş cümlesi
2. SATIR ARALIK BIRAK: Her düşünce/paragraf arasında boş satır bırak (\\n\\n)
3. KISA PARAGRAFLAR: Her paragraf 1-3 cümle. Metin duvarı YASAK
4. SCANNABLE: Göz gezdirince bile ana fikir anlaşılmalı
5. HASHTAG: En sona 1-2 alakalı hashtag koy (#AI #OpenAI gibi)
6. EMOJİ: Stratejik kullan (0-2 tane), spam yapma
7. KAPANIŞ: Soru veya güçlü bir görüşle bitir (reply tetikler, 13.5x puan)
8. EXTERNAL LINK KOYMA: X linke ceza veriyor, link paylaşma

### HOOK YAZMA KURALLARI (ÇOK ÖNEMLİ):
Okuyan "devamını merak ediyorum" demeli. Konu ne olduğunu söyle ama ne olduğunu henüz açıklama.

İYİ HOOK ÖRNEKLERİ:
- "Blackbox CLI tarafı sessiz sedasız 'terminal ama IDE'den güçlü' noktasına yürümeye başladı."
- "Alibaba Qwen tarafı sessiz sedasız çok acayip bir şeye dönüştü."
- "110 milyar dolar tek turda. Amazon 50, NVIDIA 30, SoftBank 30."
- "Google DeepMind bir şey yaptı ve bu sefer gerçekten önemli."
- "Meta'nın açık kaynak stratejisi artık sadece PR değil, piyasayı değiştiriyor."
- "OpenAI'ın yeni hamlesi herkesin gözünden kaçtı ama etkisi büyük olacak."

KÖTÜ HOOK ÖRNEKLERİ (BUNLARI ASLA YAZMA):
- "Heyecan verici bir gelişme!" ← klişe, boş
- "Yapay zeka dünyasında önemli bir gelişme yaşandı" ← gazete manşeti
- "İşte son dakika..." ← clickbait
- "Bugün çok önemli bir şey oldu" ← ne olduğu belli değil, boş

### NEDEN BU FORMAT?
- Retweet en değerli → İnsanların paylaşmak isteyeceği cesur fikirler yaz
- Reply 13.5x → Sonunda soru sor, tartışma aç
- Dwell time → Paragrafları kısa tut, merak uyandır, okuttur
- Profil tıklaması 12x → Bilgili ve ilginç yaz, "bu kim?" dedirt
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

## GERÇEK İNSAN TWEET ÖRNEKLERİ (bu tarz, tonlama, hook ve formatta yaz):

Örnek 1 (hook + kısa analiz):
"Alibaba Qwen tarafı sessiz sedasız çok acayip bir şeye dönüştü.

Qwen3.5 yaklaşık 400B parametre, MoE + Gated Delta Networks mimarisi kullanıyor. Multimodal tarafı da var - görsel, ses, kod hepsini anlıyor.

Asıl mesele şu: NVIDIA sadece PR yapmıyor, "gel bunu bizim platformda deploy et" diyor. Yani rekabet artık model isimlerinde değil, altyapı stack'inde.

Bence asıl savaş burada kopacak. Kim inference altyapısını kontrol ederse, o kazanır.

#Qwen #NVIDIA #AI"

Örnek 2 (hook + orta):
"Blackbox CLI tarafı sessiz sedasız 'terminal ama IDE'den güçlü' noktasına yürümeye başladı.

/sonnet yaz model değişsin, /opus yaz değişsin. Claude ve Codex built-in. Git worktree desteği de var.

Terminal'in bu kadar güçlü olması gerekmiyordu aslında ama piyasa oraya gidiyor. Cursor, Windsurf derken şimdi terminal tarafı da yarışa girdi.

Sizce IDE'ler mi kazanır yoksa terminal-first yaklaşım mı?

#BlackboxAI #DevTools"

Örnek 3 (hook + detaylı analiz):
"110 milyar dolar tek turda. Amazon 50, NVIDIA 30, SoftBank 30. Ön değerleme 730 milyar.

Bu artık bir yapay zeka şirketi değil, küçük bir ülke ekonomisi. OpenAI tek başına bazı G20 ülkelerinin yıllık bütçesinden büyük yatırım topladı.

Bir düşün, NVIDIA hem çip satıyor hem de en büyük müşterisine yatırım yapıyor. Yani hem tedarikçisin hem ortaksın. Bu ilişki yapısı klasik iş modellerine sığmıyor.

Amazon tarafı da ilginç. AWS zaten Anthropic'e milyarlar dökmüştü, şimdi OpenAI'a da 50 milyar. İki rakibe birden yatırım yapıyorsun çünkü asıl savaş model değil, altyapı.

Bu kadar parayı gerçekten ürüne mi dönüştürecekler yoksa compute yarışında buharlaşıp mı gidecek?

#OpenAI #AI"

Örnek 4 (hook + karşılaştırma):
"Google DeepMind reasoning tarafında sessizce ciddi bir hamle yaptı.

Chain-of-thought'u model seviyesinde entegre etmişler, MATH benchmark'ta %15+ artış var. OpenAI zaten o1'de bunu yapıyordu ama Google'ın yaklaşımı daha verimli görünüyor.

Bu yaklaşım bence önümüzdeki 6 ayda standart olur. Herkes kendi reasoning stack'ini kuracak.

#DeepMind #AI"
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
                             research_summary: str = "",
                             length_preference: str = "orta") -> str:
        """Generate a quote tweet with optional deep research context"""
        if not self.client:
            raise ValueError("API client not initialized. Check your API key.")

        system_prompt = self._build_system_prompt(style, user_samples)

        if research_summary:
            # Override system prompt for research mode
            system_prompt = self._build_research_system_prompt(user_samples, length_preference)
            # Build length-aware instructions
            length_instructions = self._get_length_instructions(length_preference)
            # RESEARCH MODE: AI has full context, write analytical post
            user_prompt = f"""Görevin: Aşağıdaki araştırma bilgilerini DERİNLEMESİNE oku. Tüm rakamları, ilişkileri, stratejik detayları anla. Sonra bu konu hakkında KENDİ ANALİZİNİ Türkçe yaz.

{research_summary}

{f"Kullanıcı notu: {additional_context}" if additional_context else ""}

## GÖREV:
Yukarıdaki TÜM bilgileri (thread, web araştırması, diğer yorumlar) derinlemesine analiz et.
Araştırmadaki spesifik rakamları, isimleri, ilişkileri kullanarak analiz yaz.

## NASIL YAZMALISIN (ÇOK ÖNEMLİ):

1. **RAKAM DAĞILIMI YAP**: Toplu rakamı parçalarına ayır. "110 milyar" deme, "Amazon 50, NVIDIA 30, SoftBank 30" de.

2. **PARADOKS VE ÇELİŞKİLERİ BUL**: İlişkilerdeki ilginçlikleri yakala.
   Örnek: "NVIDIA hem çip satıyor hem de en büyük müşterisine yatırım yapıyor. Hem tedarikçisin hem ortaksın."

3. **MAKRO KARŞILAŞTIRMALAR YAP**: Büyük rakamları somutlaştır.
   Örnek: "OpenAI tek başına bazı G20 ülkelerinin yıllık bütçesinden büyük yatırım topladı."

4. **STRATEJİK ANALİZ YAP**: Neden böyle olduğunu açıkla.
   Örnek: "Asıl savaş model değil, altyapı. Kim compute sağlarsa o kazanır."

5. **PROVOKATIF SORUYLA BİTİR**: Okuyucuyu düşündürecek bir soruyla kapat.

{length_instructions}

## ÇIKTI FORMATI (KRİTİK - BUNA UYMAZSAN BAŞARISIZ OLURSUN):
Tweet'i şu formatta yaz:
- İlk satır = HOOK: Konuyu tanıt ama merak uyandır. "[Konu] tarafı sessiz sedasız X noktasına geldi" gibi doğal, merak uyandıran bir cümle
- Her paragraf arasında BİR BOŞ SATIR bırak
- Her paragraf 1-3 cümle olsun
- Hook'tan sonra konuya gir, detayları anlat
- Son satır = SORU veya GÜÇLÜ GÖRÜŞ
- En sona 1-2 hashtag ekle (#AI #OpenAI #Qwen gibi)
- METIN DUVARI yazma! Paragraflar arasında mutlaka boşluk olacak!

## ÖRNEK ÇIKTI 1 (hook + analiz + hashtag formatına dikkat et):

Alibaba Qwen tarafı sessiz sedasız çok acayip bir şeye dönüştü.

Qwen3.5 yaklaşık 400B parametre, MoE mimarisi kullanıyor. Multimodal tarafı da var - görsel, ses, kod hepsini anlıyor.

NVIDIA sadece PR yapmıyor, "gel bunu bizim platformda deploy et" diyor. Yani rekabet artık model isimlerinde değil, altyapı stack'inde.

Bence asıl savaş burada kopacak. Kim inference altyapısını kontrol ederse, o kazanır.

#Qwen #NVIDIA #AI

## ÖRNEK ÇIKTI 2 (hook + detaylı analiz):

OpenAI tarafı resmen küçük bir ülke ekonomisine dönüştü. 110 milyar dolar tek turda.

Amazon 50, NVIDIA 30, SoftBank 30 milyar koymuş. Ön değerleme 730 milyar. Bazı G20 ülkelerinin yıllık bütçesinden büyük.

Bir düşün, NVIDIA hem çip satıyor hem de en büyük müşterisine yatırım yapıyor. Hem tedarikçisin hem ortaksın.

Amazon da ilginç. AWS zaten Anthropic'e milyarlar dökmüştü, şimdi OpenAI'a da 50 milyar. Asıl savaş model değil, altyapı.

Bu kadar parayı gerçekten ürüne mi dönüştürecekler yoksa compute yarışında buharlaşıp mı gidecek?

#OpenAI #AI

## YAPMA:
- Orijinal tweet'i Türkçeye çevirme veya özetleme
- "Heyecan verici", "çığır açan", "dikkat çekici gelişme" gibi klişeler kullanma
- Orijinal tweet'teki cümleleri tekrarlama
- Madde işareti veya numara listesi kullanma
- Metin duvarı (paragraflar arası boşluk olmadan) yazma
- Hashtag'siz bırakma

Sadece tweet metnini yaz, başka bir şey yazma."""
        else:
            # NO RESEARCH: simple quote tweet
            user_prompt = f"""@{original_author} şunu yazmış:
"{original_tweet}"

Bu konu hakkında KENDİ YORUMUNU yaz. Orijinal tweet'i çevirme veya tekrarlama.
Kendi bakış açını ekle, doğal Türkçe yaz.
{f"Not: {additional_context}" if additional_context else ""}

FORMAT: Paragraflar arası boş satır bırak. İlk satır dikkat çekici. Son satır soru veya görüş. En sona 1-2 hashtag.

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

    def _get_length_instructions(self, length_preference: str) -> str:
        """Return length-specific instructions for the prompt"""
        if length_preference == "kisa":
            return """## UZUNLUK: KISA (100-280 karakter)
- 1-2 kısa paragraf, aralarında boş satır
- En önemli 1 insight'ı seç ve onu vur
- Araştırmadan en çarpıcı tek bir veriyi kullan
- Provokatif bir cümleyle bitir
- Sona 1-2 hashtag ekle"""
        elif length_preference == "uzun":
            return """## UZUNLUK: UZUN (501-1000 karakter)
- Minimum 4-5 paragraf yaz, her paragraf arasında BOŞ SATIR bırak
- Her paragraf 1-3 cümle, farklı bir açıdan konuyu ele alsın
- İlk paragraf = hook (dikkat çekici giriş)
- Ortadaki paragraflar = analiz, rakamlar, paradokslar
- Son paragraf = soru veya güçlü görüş
- Araştırmadan bulduğun SPESİFİK rakamları, isimleri, tarihleri bol bol kullan
- KISA YAZMA - yüzeysel yorum değil, DERİNLEMESİNE analiz yaz
- En sona konuyla ilgili 1-2 hashtag ekle"""
        else:  # orta
            return """## UZUNLUK: ORTA (281-500 karakter)
- 2-3 paragraf yaz, aralarında BOŞ SATIR bırak
- İlk paragraf = hook + ana bilgi
- İkinci paragraf = analiz/yorum
- Son paragraf = kişisel görüş veya soru
- Araştırmadan en önemli 2-3 veriyi kullan
- Sona 1-2 hashtag ekle"""

    def _build_research_system_prompt(self, user_samples: list = None,
                                      length_preference: str = "orta") -> str:
        """Build system prompt optimized for research-based detailed analysis"""
        persona = self.custom_persona or BASE_SYSTEM_PROMPT

        length_desc = {
            "kisa": "KISA ve vurucu bir tweet (100-280 karakter)",
            "orta": "ORTA uzunlukta detaylı bir tweet (281-500 karakter)",
            "uzun": "UZUN ve DERİNLEMESİNE bir analiz (501-1000 karakter)",
        }

        prompt = f"""{persona}

{X_ALGORITHM_RULES}

## ARAŞTIRMA MODU:
Araştırma verilerini kullanarak {length_desc.get(length_preference, length_desc['orta'])} yazıyorsun.

KURALLAR:
- Araştırmadan SPESİFİK rakamlar, isimler ve veriler kullan
- Paradoksları, çelişkileri ve ilginç ilişkileri yakala
- Stratejik analiz yap - "neden" sorusunu cevapla
- Doğal Türkçe yaz, teknik terimler İngilizce kalabilir
- Robotik AI kalıpları YASAK

## YAZIYI FORMATLA (KRİTİK):
- İlk satır HOOK olmalı: "[Konu] tarafı sessiz sedasız X noktasına geldi" gibi doğal, merak uyandıran giriş. Konuyu tanıt ama detayı henüz verme. ASLA klişe hook kullanma!
- Her düşünce/paragraf arasında BOŞ SATIR bırak (\\n\\n ile ayır)
- Her paragraf 1-3 cümle olsun. METIN DUVARI yazma!
- Hook'tan sonra konuya gir, araştırma verilerini kullanarak detayları anlat
- Son satır SORU veya GÜÇLÜ GÖRÜŞ olmalı
- En sona konuyla ilgili 1-2 hashtag ekle (#AI #OpenAI gibi)
- Liste/madde işareti kullanma, doğal paragraflar halinde yaz
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

FORMAT:
- Paragraflar arasında boş satır bırak
- Her paragraf 1-3 cümle
- İlk satır dikkat çekici hook olsun
- Son satır soru veya güçlü görüş
- En sona 1-2 hashtag ekle (#AI #model gibi)
- Metin duvarı YAZMA

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
