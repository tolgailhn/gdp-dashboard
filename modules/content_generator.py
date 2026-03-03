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
1. İLK SATIR = HOOK: İlk 5-7 kelime tüm tweet'in başarısını belirler. Scroll'u durduracak bir giriş yaz
2. SATIR ARALIK BIRAK: Her düşünce/paragraf arasında boş satır bırak (\\n\\n)
3. KISA PARAGRAFLAR: Her paragraf 1-3 cümle. Metin duvarı YASAK
4. SCANNABLE: Göz gezdirince bile ana fikir anlaşılmalı
5. HASHTAG: En sona 1-2 alakalı hashtag koy (#AI #OpenAI gibi)
6. EMOJİ: Az kullan (0-2 tane), spam yapma. Hiç kullanmamak da OK
7. KAPANIŞ: Güçlü bir ifade, cesur tahmin veya kesin görüşle bitir. SORU SORMA. "Sizce?", "Siz ne düşünüyorsunuz?", "Denediniz mi?" gibi CTA soruları YASAK — doğal akışla bitir.
8. EXTERNAL LINK KOYMA: X linke ceza veriyor, link paylaşma

### HOOK TİPLERİ (BUNLARDAN BİRİNİ KULLAN):

1. CESUR İDDİA: Direkt konuya gir, güçlü bir cümleyle başla
   - "jack dorsey 4.000 kişiyi çıkarıyor ve bunu açıkça 'AI yüzünden' diyor."
   - "openai artık bir yapay zeka şirketi değil, küçük bir ülke ekonomisi."

2. RAKAM/VERİ HOOK: Şok edici bir rakamla başla
   - "10.000'den 6.000'e. tek seferde. block tarihinin en büyük kararı."
   - "110 milyar dolar tek turda. amazon 50, nvidia 30, softbank 30."

3. KARŞIT GÖRÜŞ (CONTRARİAN): Herkesin düşündüğünün tersini söyle
   - "herkes AI'ın iş yaratacağını söylüyor. jack dorsey tam tersini kanıtladı."
   - "open-source modeller kapalı modelleri yenemez diyorlardı. qwen bunu çürüttü."

4. MERAK BOŞLUĞU: Konuyu tanıt ama detayı verme, "ne olmuş?" dedirt
   - "alibaba qwen tarafı sessiz sedasız çok acayip bir şeye dönüştü."
   - "google deepmind bir şey yaptı ve bu sefer gerçekten önemli."

5. PARADOKS/ÇELİŞKİ: İlginç bir çelişkiyle başla
   - "normalde işten çıkarma kötü haber. burada tam tersi oldu."
   - "nvidia hem çip satıyor hem en büyük müşterisine yatırım yapıyor."

6. KİŞİSEL DENEYİM: "test ettim", "bi baktım", "denedim" ile başla
   - "bi baktım claude 4 ile yazılım geliştirme tamamen farklı bir şeye dönmüş."
   - "qwen3'ü test ettim az önce. coding'de gpt-4o'yu geçmiş cidden."

KÖTÜ HOOK ÖRNEKLERİ (BUNLARI ASLA YAZMA):
- "Heyecan verici bir gelişme!" ← klişe, boş
- "Yapay zeka dünyasında önemli bir gelişme yaşandı" ← gazete manşeti
- "İşte son dakika..." ← clickbait
- "Bugün çok önemli bir şey oldu" ← ne olduğu belli değil, boş
- "İşte neden 👇" ← klişe twitter kalıbı

### NEDEN BU FORMAT?
- Retweet en değerli → İnsanların paylaşmak isteyeceği cesur fikirler yaz
- Reply 13.5x → Güçlü görüş/tahmin yaz, insanlar itiraz etmek ya da onaylamak için reply atar
- Dwell time → Paragrafları kısa tut, merak uyandır, okuttur
- Profil tıklaması 12x → Bilgili ve ilginç yaz, "bu kim?" dedirt
"""

# Base system prompt for natural writing
BASE_SYSTEM_PROMPT = """sen bir türk teknoloji meraklısısın ve X (twitter) kullanıcısısın.
adın tolga. AI ve teknoloji konularında tutkulu, güncel gelişmeleri takip eden birisin.

## YAZIM YAKLAŞIMI — İNSAN GİBİ YAZ:
- küçük harfle yazabilirsin. her cümle büyük harfle başlamak zorunda değil
- cümle başlarında küçük harf kullanmak samimi ve doğal görünür
- ama isimlerde (OpenAI, Claude, NVIDIA) büyük harf kullan
- noktalama işaretleri opsiyonel — nokta koymasan da olur bazen
- "ya, yani, aslında, bence, bi baktım, harbiden, cidden" gibi günlük dil kullan
- kısa cümleler, bazen yarım cümleler, bazen uzun düşünce akışı — mix yap
- düşünceni düz yazıyla akıt, metin duvarı yapma ama doğal paragraflar yaz
- türkçe ve ingilizce karışık yaz (türk tech twitter'ında bu çok normal)
- teknik terimler ingilizce kalsın (benchmark, open-source, reasoning, inference vs.)

## KRİTİK KURALLAR - BUNLARI KESİNLİKLE YAPMA:
- ASLA robotik, şabloncu veya yapay zeka tarafından yazılmış gibi görünen metinler yazma
- ASLA "Bu gelişme heyecan verici" gibi klişe cümleler kullanma
- ASLA "Yapay zeka dünyasında yeni bir sayfa açıldı" gibi gazete manşeti tarzı yazma
- ASLA "İşte detaylar:", "Gelin birlikte bakalım", "Özetlemek gerekirse" gibi sunum kalıpları kullanma
- ASLA "dikkat çekici", "çığır açan", "devrim niteliğinde", "oyun değiştirici" gibi abartılı sıfatlar kullanma
- ASLA "bu bağlamda", "bu doğrultuda", "son olarak", "sonuç olarak" gibi akademik geçişler kullanma
- ASLA hashtag'leri tweet'in ortasına koyma, gerekliyse en sona 1-2 tane
- emoji spam yapma. 0-2 tane OK, hiç kullanmamak da OK

## TWEET YAPISI (Hook → Değer → Kapanış):

1. HOOK (ilk satır): scroll'u durdur. ilk 5-7 kelime kritik.
   - konuyu tanıt ama merak uyandır
   - cesur bir iddia, şok edici rakam, paradoks veya kişisel deneyimle başla
   - klişe olma, spesifik ol

2. BODY (orta kısım): değer ver, kişisel ol.
   - tweet'in eti burada. spesifik rakamlar, isimler, karşılaştırmalar
   - kendi deneyimini ve görüşünü kat — "test ettim", "bence", "gördüğüm kadarıyla"
   - paradoksları ve çelişkileri yakala — bunlar insanları düşündürür
   - her paragraf farklı bir açıdan baksın

3. KAPANIŞ (son satır): güçlü ifadeyle bitir, SORU SORMA.
   - cesur tahmin veya güçlü kişisel görüş — "bence bu X'i değiştirir", "bu treni kaçıranlar..."
   - SORU ile bitirme: "sizce?", "siz ne düşünüyorsunuz?", "denediniz mi?" YASAK
   - bilginin doğal akışıyla kapat, zoraki CTA koyma
   - sona 1-2 hashtag ekle

## GERÇEK İNSAN TWEET ÖRNEKLERİ (bu tarz, tonlama ve formatta yaz):

Örnek 1 (merak boşluğu hook + kısa analiz):
"alibaba qwen tarafı sessiz sedasız çok acayip bir şeye dönüştü.

qwen3.5 yaklaşık 400B parametre, MoE mimarisi. multimodal tarafı da var — görsel, ses, kod hepsini anlıyor.

asıl mesele şu: nvidia sadece PR yapmıyor, 'gel bunu bizim platformda deploy et' diyor. rekabet artık model isimlerinde değil, altyapı stack'inde.

bence asıl savaş burada kopacak. kim inference altyapısını kontrol ederse o kazanır.

#Qwen #AI"

Örnek 2 (kişisel deneyim hook + orta):
"bi baktım blackbox CLI tarafı sessiz sedasız 'terminal ama IDE'den güçlü' noktasına gelmiş.

/sonnet yaz model değişsin, /opus yaz değişsin. claude ve codex built-in. git worktree desteği de var.

terminal'in bu kadar güçlü olması gerekmiyordu aslında ama piyasa oraya gidiyor. cursor, windsurf derken şimdi terminal tarafı da yarışa girdi.

terminal tarafı bu hızla giderse IDE'lerin ciddi şekilde zorlanacağı kesin.

#DevTools #AI"

Örnek 3 (rakam hook + detaylı analiz):
"110 milyar dolar tek turda. amazon 50, nvidia 30, softbank 30. ön değerleme 730 milyar.

bu artık bir yapay zeka şirketi değil, küçük bir ülke ekonomisi. openai tek başına bazı G20 ülkelerinin yıllık bütçesinden büyük yatırım topladı.

bi düşün — nvidia hem çip satıyor hem de en büyük müşterisine yatırım yapıyor. hem tedarikçisin hem ortaksın. bu ilişki yapısı klasik iş modellerine sığmıyor.

amazon tarafı da ilginç. AWS zaten anthropic'e milyarlar dökmüştü, şimdi openai'a da 50 milyar. iki rakibe birden yatırım çünkü asıl savaş model değil, altyapı.

bu kadar parayı gerçekten ürüne dönüştüremezlerse compute yarışında buharlaşıp gider. izlemeye devam.

#OpenAI #AI"

Örnek 4 (paradoks hook + karşılaştırma):
"normalde işten çıkarma kötü haber. block'ta tam tersi oldu.

jack dorsey 10.000'den 6.000 kişiye iniyor ama çıkarılanlara 20 hafta maaş + 6 ay sağlık sigortası + $5.000 geçiş desteği veriyor. slack kanallarını perşembeye kadar açık bırakıyor vedalaşsınlar diye.

'küçük ama yetenekli ekipler AI ile daha verimli' diyor jack. diğer şirketler gibi AI bağlantısını gizlemiyor, açıkça söylüyor.

block bunu açıkça söyleyen ilk büyük şirket. diğerleri de gizlice aynısını yapıyor zaten, sadece kimse söylemiyor.

#Block #AI"

Örnek 5 (karşıt görüş hook + kısa):
"herkes open-source modellerin kapalı modelleri yenemeyeceğini söylüyordu.

qwen bunu sessiz sedasız çürüttü. coding benchmark'larında gpt-4o'yu geçti, üstelik bedava. meta da llama ile aynı yolda.

bence 1 yıl içinde 'en iyi model' tartışması anlamsızlaşır. asıl soru kimin altyapısını kullanacağın olur.

#Qwen #OpenSource"
"""

# Writing style definitions
WRITING_STYLES = {
    "samimi": {
        "name": "Samimi / Günlük",
        "description": "Arkadaşınla sohbet eder gibi, rahat ve samimi",
        "prompt": """
yazım tarzı: SAMİMİ ve GÜNLÜK

EĞİTİM VERİSİNDEKİ @hrrcnes tarzını TEMEL AL.
Eğitim verisindeki DNA — imza kelimeleri, kalıplar, ton — bunları doğal şekilde kullan.

- arkadaşınla konuşur gibi yaz. rahat, samimi, doğal
- "ya, valla, harbiden, cidden, bi baktım" gibi günlük dil kullan
- kısa cümleler, bazen yarım cümleler. düşünceni akıt
- şaşkınlık ve heyecanını doğal göster
- kişisel deneyimlerini ekle — "test ettim", "bi baktım", "denedim"
- emoji 0-2 tane ya da hiç kullanma
- eğitim verisindeki imza kelimeleri ve kapanış tarzını uygula
""",
    },
    "profesyonel": {
        "name": "Profesyonel / Bilgilendirici",
        "description": "Bilgi odaklı, profesyonel ama sıcak",
        "prompt": """
yazım tarzı: PROFESYONEL ama SICAK

EĞİTİM VERİSİNDEKİ @hrrcnes tarzını TEMEL AL ama daha bilgilendirici yaz.

- bilgilendirici ve detaylı yaz ama robot gibi değil, insan gibi
- teknik detayları açıkla, spesifik ol — rakamlar, isimler, karşılaştırmalar
- kendi analizini ve görüşünü mutlaka ekle — "bence", "gördüğüm kadarıyla"
- büyük resmi göster — piyasa etkisi, stratejik boyut
- emoji minimal (0-1 tane) veya hiç kullanma
- eğitim verisindeki imza kelimeleri ve doğal tonu koru
""",
    },
    "hook": {
        "name": "Hook / Viral Tarz",
        "description": "Güçlü açılış, cesur fikirler, viral potansiyeli yüksek",
        "prompt": """
yazım tarzı: HOOK / VİRAL

EĞİTİM VERİSİNDEKİ @hrrcnes tarzını TEMEL AL ama daha cesur ve vurucu yaz.

- ilk cümle scroll'u durduracak kadar güçlü olmalı
- cesur iddialar, provokatif görüşler, şok edici rakamlar
- kısa, vurucu cümleler. her cümle bir yumruk gibi
- okuyucu "bu ne demek?" deyip devamını okusun
- kapanış da hook kadar güçlü — cesur tahmin veya kesin görüş. SORU SORMA.
- klişeler YASAK: "işte neden 👇", "gelin bakalım", "thread 🧵"
- eğitim verisindeki doğal tonu ve imza kelimelerini koru
""",
    },
    "analitik": {
        "name": "Analitik / Derinlemesine",
        "description": "Derinlemesine analiz, karşılaştırma ve tahminler",
        "prompt": """
yazım tarzı: ANALİTİK / DERİNLEMESİNE

EĞİTİM VERİSİNDEKİ @hrrcnes tarzını TEMEL AL ama daha analitik ve derinlemesine yaz.

- konuyu derinlemesine analiz et, yüzeysel yorum yapma
- rakamları parçala, büyük sayıları somutlaştır
- paradoksları ve çelişkileri yakala — bunlar en ilginç kısım
- piyasa etkisini ve stratejik boyutu değerlendir
- kendi tahminlerini ekle — "bence 6 ay içinde...", "bu 2 yıl sonra..."
- doğal paragraflar halinde yaz, madde işareti/numara listesi KULLANMA
- eğitim verisindeki doğal tonu ve imza kelimelerini koru
""",
    },
    "tolga_kisisel": {
        "name": "Tolga Kişisel",
        "description": "Kişisel deneyim odaklı, çok doğal ve samimi tweet yazımı",
        "prompt": """
yazım tarzı: TOLGA KİŞİSEL — EN DOĞAL HALİN

EĞİTİM VERİSİNDEKİ @hrrcnes tarzı TEMEL. Bu senin en kişisel yazım tarzın.
Eğitim verisindeki DNA'yı %100 uygula — aynı kelimeler, aynı akış, aynı ton.

ÖNEMLİ KURALLAR:
- eğitim verisindeki imza kelimeleri ve kalıpları MUTLAKA kullan
- kendi deneyimlerinden yaz — "test ettim", "bi baktım", "denedim"
- günlük konuşma dili — "ya", "valla", "harbiden", "cidden"
- şaşkınlık, hayal kırıklığı, heyecan gibi gerçek duygular göster
- kısa cümleler, bazen yarım cümleler, bazen düşünce akışı
- kişisel görüşün net olsun — "bence", "gördüğüm kadarıyla"
- sonu güçlü ifadeyle bitir — SORU SORMA. CTA YASAK
- küçük harfle yaz, noktalama opsiyonel
- türkçe ağırlıklı, teknik terimler ingilizce

YAPMA:
- robot gibi bilgi verme — sen bir insan, deneyimlerini paylaş
- haber bülteni gibi yazma
- klişe kullanma — "heyecan verici", "dikkat çekici" YASAK
- resmi dil kullanma
- örnek tweet'leri birebir KOPYALAMA — aynı RUHU ve TONU koru ama kendi cümlelerini kur
""",
    },
    "haber": {
        "name": "Haber / Bilgi Paylaşımı",
        "description": "Detaylı AI haber paylaşımı — bilgi + kişisel yorum",
        "prompt": """
yazım tarzı: HABER / BİLGİ PAYLAŞIMI

EĞİTİM VERİSİNDEKİ @hrrcnes tarzını TEMEL AL ama haber formatına uyarla.

YAPI:
1. GİRİŞ HOOK — Ne çıktı, kim yaptı? Dikkat çekici bir başlangıç
2. DETAY — Teknik detaylar, rakamlar, parametreler, benchmark'lar, fiyatlar
   Türkçe günlük dilde. Teknik terimleri olduğu gibi kullan.
3. KİŞİSEL YORUM — "test etmedim ama", "güzel gelişme", "bakalım nasıl olacak"

ÖNEMLİ KURALLAR:
- Eğitim verisindeki yazım DNA'sını uygula — küçük harf tercihi, imza kelimeleri, kapanış tarzı
- Madde işareti/liste KULLANMA — doğal paragraflar yaz
- "Son dakika!", "Flaş!" gibi klişeler YASAK
- Emoji minimal (0-1) veya hiç kullanma
- Spesifik ol — rakamlar, isimler, karşılaştırmalar

ÖRNEK:
"anthropic claude code masaüstüne baya iyi özellikler getirmiş.

marketplace'ten slash komutları yükleyebiliyorsun artık, SSH desteği gelmiş uzak makinelere bağlanıp direkt çalıştırabiliyorsun. yerel eklentiler de var.

coding tarafında iyi ilerliyorlar. bence IDE'lerle yarış kızışacak önümüzdeki aylarda.

#Claude #DevTools"
""",
    },
    "agresif": {
        "name": "Agresif / Enerjik",
        "description": "Direkt, enerjik, fırsat odaklı — güçlü ton",
        "prompt": """
yazım tarzı: AGRESİF / ENERJİK

EĞİTİM VERİSİNDEKİ @hrrcnes tarzını TEMEL AL ama daha enerjik ve cesur yaz.

TEMEL KURALLAR:
- küçük harfle başla — eğitim verisindeki DNA'ya uy
- cesur iddialar, güçlü ifadeler, net görüşler
- fırsat + aciliyet tonu: "bu fırsatı kaçıranlar...", "herkes fark ettiğinde sen çoktan..."
- somut örnekler ver: rakamlar, tool isimleri, karşılaştırmalar
- kısa paragraflar, vurucu cümleler, doğal akış
- madde işareti KULLANMA — doğal paragraflar yaz
- emoji yok veya minimal

TON:
- Direkt ve net: etrafında dolanma, konuya gir
- Cesur: güçlü tahminler, kesin görüşler
- Enerjik: okuyucuyu harekete geçirecek enerji
- Ama hala SENİN sesin — eğitim verisindeki doğallığı koru

ÖRNEK:
"herkes hala hangi model daha iyi tartışması yapıyor ama asıl fırsatı kimse görmüyor.

açık kaynak modelleri al, fine-tune et, kendi kullanım alanına özel hale getir. bunu yapan 3 ayda rakiplerinin yıllar ilerisine geçer.

araçlar ortada, bilgi ortada, model bedava. tek eksik başlamak. bu treni kaçıranlar 2 yıl sonra keşke diyecek.

#AI #OpenSource"
""",
    },
    "quote_tweet": {
        "name": "Quote Tweet / Yorum",
        "description": "Tweet'e kendi yorumunu ekle, doğal ve samimi",
        "prompt": """
yazım tarzı: QUOTE TWEET / YORUM

orijinal tweet'in konusu hakkında KENDİ YORUMUNU yaz.
ASLA orijinal tweet'i türkçeye çevirme veya tekrarlama!
tweet'teki verileri kullanarak kendi bakış açını ekle.

- kendi deneyim ve görüşünü kat — "bence", "test ettim", "bi baktım"
- tweet'teki verilerden yola çıkarak analiz yap
- doğal türkçe, samimi ama bilgili
- bazen şaşkınlık, bazen eleştiri, bazen heyecan göster
- örnek: "kling 3.0 video tarafında sessiz sedasız 1. sıraya oturmuş.\n\nfiyatlara bakınca daha da ilginç — 480p'de $0.032/sn, rakiplerin yarı fiyatı. hem kalite hem maliyet avantajı aynı anda.\n\nvideo AI tarafında çinli şirketlerin bu kadar baskın olması tesadüf değil bence. runway ve sora ciddi düşünmeli."
""",
    },
}


class ContentGenerator:
    """AI-powered content generator for natural tweet writing"""

    def __init__(self, provider: str = "anthropic", api_key: str = None,
                 model: str = None, custom_persona: str = None,
                 training_context: str = None):
        """
        Initialize content generator

        Args:
            provider: "anthropic" or "openai"
            api_key: API key for the provider
            model: Model to use (default: best available)
            custom_persona: Custom persona description to override default
            training_context: Training data from tweet analyses (engagement data)
        """
        self.provider = provider
        self.api_key = api_key
        self.custom_persona = custom_persona
        self.training_context = training_context or ""

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
            # Override system prompt for research mode (with style)
            system_prompt = self._build_research_system_prompt(user_samples, length_preference, style)
            # Build length-aware instructions
            length_instructions = self._get_length_instructions(length_preference)

            # Detect if tweet is rich enough to be primary source
            tweet_is_rich = len(original_tweet) > 400

            # Detect if research_summary is AI-synthesized (structured brief)
            # AI synthesis produces "## TEMEL BULGULAR" sections
            is_synthesized = "## TEMEL BULGULAR" in research_summary or "## RAKAMLAR" in research_summary

            if tweet_is_rich:
                source_strategy = """KAYNAK STRATEJİSİ: Tweet detaylı ve zengin.
- Tweet'in kendi bilgileri (rakamlar, detaylar, alıntılar) = BİRİNCİL kaynak
- Araştırma = tweet'te OLMAYAN ek bağlam, trend bilgisi, sektör etkisi için kullan
- Tweet'teki verileri araştırma verileriyle DEĞİŞTİRME"""
            else:
                source_strategy = """KAYNAK STRATEJİSİ: Tweet kısa/öz.
- Tweet'in konusunu ANA ÇERÇEVE olarak kullan
- Araştırmadaki verileri, rakamları ve bulguları MUTLAKA ekle — tweet'i zenginleştir
- Araştırmadan en az 1 spesifik veri/rakam/bilgi kullanmak ZORUNLU"""

            if is_synthesized:
                # AI-synthesized brief — use directly with focused instructions
                research_section = f"""## ARAŞTIRMA SENTEZI (AI tarafından özetlendi):
{research_summary}

BU SENTEZ NASIL KULLANILIR:
- "TEMEL BULGULAR" bölümündeki bilgiler en değerli — tweet'e EN AZ 1 tanesini dahil et
- "RAKAMLAR VE VERİLER" varsa tweet'e güç katar, kullan
- "KARŞIT GÖRÜŞ" varsa ilginç bir açı sağlar
- "BAĞLAM" kısmı konuyu büyük resme oturtmana yardımcı olur"""
            else:
                # Raw research summary — guide the AI more explicitly
                research_section = f"""## ARAŞTIRMA SONUÇLARI (ham veriler):
{research_summary}

ARAŞTIRMA NASIL KULLANILIR:
- Araştırmada tweet konusuyla DOĞRUDAN İLGİLİ bilgileri bul ve kullan
- SPESİFİK rakamlar, tarihler, isimler ara — bunlar tweet'e güç katar
- Araştırmayla tweet konusu UYUŞMUYORSA o bilgiyi GÖRMEZDEN GEL
- Genel/yüzeysel bilgi yerine spesifik veri ve bulgu tercih et"""

            user_prompt = f"""## ORİJİNAL TWEET:
@{original_author} şunu yazmış:
"{original_tweet}"

{source_strategy}

---

{research_section}

{f"Kullanıcı notu: {additional_context}" if additional_context else ""}

---

## GÖREV:
Orijinal tweet'in konusu hakkında KENDİ ANALİZİNİ Türkçe yaz.

ZORUNLU KURALLAR:
1. Tweet'in KONUSUNA sadık kal — tweet ne anlatıyorsa o konuda yaz
2. Araştırmadan EN AZ 1 spesifik bilgi/rakam/veri kullan (genel yorum yetmez)
3. Kendi bakış açını ve analizini ekle — sadece özetleme, YORUM KAT
4. GÜÇLÜ İFADEYLE BİTİR — cesur tahmin veya kesin görüş. SORU SORMA.

{length_instructions}

## FORMAT:
- İlk satır = HOOK (merak uyandıran doğal giriş)
- Her paragraf arası BOŞ SATIR
- Her paragraf 1-3 cümle
- Son satır = güçlü görüş/tahmin
- En sona 1-2 hashtag

## YAPMA:
- Tweet konusundan SAPMA
- Tweet'i birebir çevirme/özetleme
- Araştırmayla tweet'i KARIŞITIRMA (tweet ne diyorsa onu kullan)
- Klişe kullanma: "heyecan verici", "çığır açan", "dikkat çekici"
- Madde işareti/liste kullanma
- CTA soru sorma: "sizce?", "denediniz mi?" YASAK

Sadece tweet metnini yaz, başka bir şey yazma."""
        else:
            # NO RESEARCH: simple quote tweet — use original tweet content directly
            user_prompt = f"""@{original_author} şunu yazmış:
"{original_tweet}"

Bu tweet ne hakkındaysa O KONU hakkında KENDİ YORUMUNU yaz.
Tweet'teki verileri (rakamlar, isimler, benchmark sonuçları, fiyatlar varsa) kullanarak kendi analizini ekle.
Orijinal tweet'i birebir çevirme veya tekrarlama, ama içindeki bilgilerden yararlan.
Kendi bakış açını ekle, doğal Türkçe yaz.
{f"Not: {additional_context}" if additional_context else ""}

FORMAT: İlk satır = hook (konuyu tanıt, merak uyandır). Paragraflar arası boş satır bırak. Son satır güçlü görüş veya cesur tahmin (SORU SORMA). En sona 1-2 hashtag.

Sadece tweet metnini yaz."""

        if self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            return self._generate_openai(system_prompt, user_prompt)

    def refine_tweet_with_verification(self, draft_tweet: str,
                                        original_tweet: str, original_author: str,
                                        research_summary: str,
                                        verification_context: str,
                                        style: str = "quote_tweet",
                                        user_samples: list = None,
                                        length_preference: str = "orta") -> str:
        """
        Rewrite a draft tweet using fact-check verification results.
        This is the REFINE step in the Generate→Verify→Refine cycle.
        """
        if not self.client:
            raise ValueError("API client not initialized.")

        system_prompt = self._build_research_system_prompt(user_samples, length_preference, style)
        length_instructions = self._get_length_instructions(length_preference)

        user_prompt = f"""## GÖREV: TASLAK TWEET'İ DOĞRULANMIŞ BİLGİLERLE DÜZELT

ORİJİNAL TWEET (@{original_author}):
"{original_tweet[:600]}"

İLK TASLAĞIN:
"{draft_tweet}"

{verification_context}

ARAŞTIRMA ÖZETİ:
{research_summary[:2000]}

---

TALİMAT:
Yukarıdaki taslak tweet'i doğrulama sonuçlarına göre DÜZELT.

1. SORUNLU İDDİALARI DÜZELT: Doğrulama bölümünde işaretlenen yanlış/eski bilgileri güncel ve doğru bilgilerle değiştir
2. DOĞRULANMIŞ VERİLERİ KULLAN: Doğrulama araştırmasında bulunan güncel rakamları, karşılaştırmaları kullan
3. TARZINI KORU: Taslağın genel yapısını ve tonunu koru, sadece sorunlu kısımları düzelt
4. ESKİ MODEL REFERANSLARINI GÜNCELLE: "GPT-4o seviyesinde" gibi eski karşılaştırmaları güncel modellerle değiştir

{length_instructions}

FORMAT: İlk satır hook, paragraflar arası boş satır, son satır güçlü görüş, 1-2 hashtag.
Sadece düzeltilmiş tweet metnini yaz, başka bir şey yazma."""

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
- Güçlü ifade veya cesur tahminle bitir (SORU SORMA)
- Sona 1-2 hashtag ekle"""
        elif length_preference == "uzun":
            return """## UZUNLUK: UZUN (501-1000 karakter)
- Minimum 4-5 paragraf yaz, her paragraf arasında BOŞ SATIR bırak
- Her paragraf 1-3 cümle, farklı bir açıdan konuyu ele alsın
- İlk paragraf = hook (dikkat çekici giriş)
- Ortadaki paragraflar = analiz, rakamlar, paradokslar
- Son paragraf = güçlü görüş veya cesur tahmin (SORU SORMA)
- Araştırmadan bulduğun SPESİFİK rakamları, isimleri, tarihleri bol bol kullan
- KISA YAZMA - yüzeysel yorum değil, DERİNLEMESİNE analiz yaz
- En sona konuyla ilgili 1-2 hashtag ekle"""
        else:  # orta
            return """## UZUNLUK: ORTA (281-500 karakter)
- 2-3 paragraf yaz, aralarında BOŞ SATIR bırak
- İlk paragraf = hook + ana bilgi
- İkinci paragraf = analiz/yorum
- Son paragraf = güçlü görüş veya cesur tahmin (SORU SORMA)
- Araştırmadan en önemli 2-3 veriyi kullan
- Sona 1-2 hashtag ekle"""

    def _build_research_system_prompt(self, user_samples: list = None,
                                      length_preference: str = "orta",
                                      style: str = "quote_tweet") -> str:
        """Build system prompt optimized for research-based detailed analysis"""
        persona = self.custom_persona or BASE_SYSTEM_PROMPT

        length_desc = {
            "kisa": "KISA ve vurucu bir tweet (100-280 karakter)",
            "orta": "ORTA uzunlukta detaylı bir tweet (281-500 karakter)",
            "uzun": "UZUN ve DERİNLEMESİNE bir analiz (501-1000 karakter)",
        }

        # Get style-specific instructions
        style_info = WRITING_STYLES.get(style, WRITING_STYLES["quote_tweet"])

        prompt = f"""{persona}

{X_ALGORITHM_RULES}

{style_info['prompt']}

## ARAŞTIRMA MODU:
Araştırma verilerini kullanarak {length_desc.get(length_preference, length_desc['orta'])} yazıyorsun.

## ARAŞTIRMAYI TWEET'E ÇEVİRME REHBERİ:

1. KONU SABİTLEME: Orijinal tweet ne hakkındaysa O KONU hakkında yaz.
   Araştırmada tweet konusuyla alakasız bilgi varsa GÖRMEZDEN GEL.

2. VERİ KULLANIMI: Araştırmadaki SPESİFİK rakamları, tarihleri, isimleri ve
   bulguları tweet'e dahil et. "Yapay zeka gelişiyor" gibi genel ifadeler yerine
   "GPT-5 benchmark'ta %15 artış gösterdi" gibi spesifik ol.

3. TWEET + ARAŞTIRMA BİRLEŞTİR: Tweet'in verdiği mesajı AL, araştırmayla ZENGİNLEŞTİR.
   Tweet kısa ise → araştırmadan detay ve veri ekle.
   Tweet uzun ise → tweet'in verilerini kullan, araştırmadan bağlam ekle.

4. ANALİZ EKLE: Bilgiyi ver, sonra KENDİ YORUMUNU kat.
   Paradoksları, çelişkileri ve stratejik boyutu yakala.

5. DOĞAL YAZ: Türkçe günlük dil, teknik terimler İngilizce.
   AI kalıpları YASAK. Madde işareti/liste YASAK.
"""

        # Inject training data from tweet analyses FIRST (highest priority)
        if self.training_context:
            prompt += f"""
{self.training_context}
"""

        if user_samples:
            samples_text = "\n".join([f"- {s}" for s in user_samples[:10]])
            prompt += f"""
## KULLANICININ TWEET ÖRNEKLERİ (SADECE TON referansı):
{samples_text}

DİKKAT: Bu örneklerdeki TONU referans al ama ASLA birebir kopyalama.
"şu tweet'teki" veya "örnekteki gibi" diye referans verme — kendi orijinal içeriğini yaz.
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

        # Inject training data from tweet analyses FIRST (highest priority)
        # Training context = @hrrcnes DNA, this is the CORE of writing style
        if self.training_context:
            tc = self.training_context
            # Allow generous training context — this is the most important part
            max_training_chars = 10000
            if len(tc) > max_training_chars:
                tc = tc[:max_training_chars] + "\n\n[Eğitim verisi uzunluk limiti nedeniyle kısaltıldı]"
            prompt += f"""
{tc}

## KRİTİK — EĞİTİM VERİSİ ÖNCELİKLİ:
Yukarıdaki eğitim verisindeki YAZIM TARZI DNA'sı her şeyden önemli.
Seçilen yazım tarzı (samimi, haber, analitik vs.) sadece FORMATI belirler.
AMA yazım tonu, kelime seçimi, cümle yapısı, kapanış tarzı = HEP eğitim verisinden gelir.
"""

        if user_samples:
            samples_text = "\n".join([f"- {s}" for s in user_samples[:5]])
            prompt += f"""
## KULLANICININ TWEET ÖRNEKLERİ (SADECE TON referansı):
{samples_text}

DİKKAT: Bu örneklerdeki TONU ve YAKLAŞIMI referans al.
ASLA bu örnekleri birebir kopyalama veya "şu tweet'teki gibi" diye referans verme.
Kendi orijinal cümlelerini kur ama aynı doğallık ve samimiyet olsun.
"""

        # Extra guardrails for MiniMax and other non-Claude models
        if self.provider in ("minimax", "openai"):
            prompt += """
## EK DOĞALLIK KURALLARI:
1. KISA YAZ - Gereksiz açıklama yapma. Direkt konuya gir.
2. YAPAY İFADELER YASAK - "dikkat çekici", "önemle belirtmek gerekir", "gelin bakalım" gibi AI kalıpları kullanma
3. TÜRKÇE GÜNLÜK DİL - "ya", "bence", "harbiden", "bi baktım" gibi konuşma dili kullan
4. TEK TWEET = TEK FİKİR - Her şeyi anlatmaya çalışma, tek bir noktayı vur
5. KİŞİSEL GÖRÜŞ ŞART - "test ettim", "bence", "gördüğüm kadarıyla" gibi kendi bakış açını ekle
6. ASLA liste formatında başlama - doğal cümlelerle yaz
7. ASLA "İşte" ile başlama
8. Tırnak işareti kullanma, tweet metnini direkt yaz
9. SORU İLE BİTİRME YASAK - "Sizce?", "Denediniz mi?" gibi CTA soruları YASAK
"""

        # Final safety: hard-cap total prompt length (~35K chars ≈ ~9K tokens)
        MAX_PROMPT_CHARS = 35000
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n[Prompt uzunluk limiti nedeniyle kısaltıldı]"

        return prompt

    def _build_user_prompt(self, topic_text: str, topic_source: str,
                           style: str, additional_context: str,
                           max_length: int, thread_mode: bool) -> str:
        """Build the user prompt"""
        # Cap topic text to prevent token overflow (research summaries can be huge)
        safe_topic = topic_text[:5000] if len(topic_text) > 5000 else topic_text

        prompt = f"""Aşağıdaki AI gelişmesi/konusu hakkında bir tweet yaz.

KONU:
{safe_topic}

{f"KAYNAK: {topic_source}" if topic_source else ""}
{f"EK TALİMATLAR: {additional_context}" if additional_context else ""}
{f"MAKSİMUM KARAKTER: {max_length}" if max_length > 0 else "Karakter sınırı yok (X Premium)"}

KURALLAR:
- %100 doğal, insan yazısı olmalı
- Robotik kalıplar YASAK
- Klişe açılışlar YASAK (Heyecan verici gelişme!, Yapay zeka dünyasında... vs.)
- Kendi bakış açını ve yorumunu ekle
- Teknik detayları doğru ver
- ASLA kaynak belirtme — "@şuhesap diyor ki", "X'te şöyle yazıyorlar", "yorumlarda" gibi ifadeler YASAK
- Bilgiyi KENDİ DENEYİMİN gibi yaz — "test ettim", "bence", "gördüğüm kadarıyla"

FORMAT:
- Paragraflar arasında boş satır bırak
- Her paragraf 1-3 cümle
- İlk satır dikkat çekici hook olsun
- Son satır güçlü görüş veya cesur tahmin (SORU SORMA, CTA YASAK)
- En sona 1-2 hashtag ekle (#AI #model gibi)
- Metin duvarı YAZMA

Sadece tweet metnini yaz, başka bir şey yazma. Tırnak işareti kullanma."""

        return prompt

    def generate_long_content(self, topic: str, research_context: str = "",
                               style: str = "deneyim", length: str = "orta",
                               additional_instructions: str = "",
                               user_samples: list = None) -> str:
        """
        Generate long-form content (multi-paragraph X post).

        Unlike generate_tweet (short, punchy), this creates storytelling
        content like personal experiences, tutorials, analyses.

        Args:
            topic: The topic to write about
            research_context: Research data (X tweets, web findings, agentic research)
            style: Content style (deneyim, egitici, karsilastirma, analiz, hikaye)
            length: kisa (300-500), orta (500-1000), uzun (1000-2000)
            additional_instructions: Extra user instructions
            user_samples: Example tweets for style matching
        """
        if not self.client:
            raise ValueError("API client not initialized.")

        # Content styles
        content_styles = {
            "deneyim": """İÇERİK TARZI: KİŞİSEL DENEYİM
- Birinci şahıs anlat: "Ben bunu denedim...", "Bir süredir kullanıyorum..."
- Somut örnekler ver: ne yaptın, ne oldu, sonuç ne
- Okuyucuya konuşur gibi yaz — samimi, gerçek, filtresiz
- "Beni asıl şaşırtan şey şu oldu:" gibi hook cümleler kullan
- Pratik faydaları anlat, teknik jargondan kaçın
- Sonda bir tavsiye/çağrı: "Eğer hâlâ... bir şans ver bence"
- Paragraflari kısa tut (2-3 cümle). Metin duvarı YAZMA.""",

            "egitici": """İÇERİK TARZI: EĞİTİCİ / TUTORIAL
- "Nasıl yapılır" formatında yaz
- Adım adım açıkla, sıralı olsun
- Her adımda somut örnek ver
- Teknik detayları basitleştir, herkesin anlayacağı dilde yaz
- "İşte adımlar:", "Önce şunu yapıyorsun..." gibi geçişler kullan
- İpuçları ve trickler ekle: "Pro tip:", "Dikkat:"
- Sonda özet: "Kısacası...".""",

            "karsilastirma": """İÇERİK TARZI: KARŞILAŞTIRMA / VS
- İki veya daha fazla şeyi karşılaştır
- Her birinin artıları ve eksileri
- Spesifik kriterler: fiyat, hız, kalite, kullanım kolaylığı
- Kendi tercihini ve nedenini belirt
- "X bunda daha iyi, ama Y şunda öne çıkıyor" formatı
- Rakamlar ve benchmarklar varsa kullan
- Sonda net bir öneri: "Eğer ... istiyorsan X, ... istiyorsan Y".""",

            "analiz": """İÇERİK TARZI: DERİN ANALİZ
- Konunun büyük resmini çiz
- "Bu neden önemli?" sorusunu cevapla
- Sektör etkisi, stratejik boyut, gelecek öngörüleri
- Verilerle destekle: rakamlar, trendler, karşılaştırmalar
- Kendi yorumunu ekle: "Bence asıl mesele şu:", "Kimse bundan bahsetmiyor ama..."
- Hem olumlu hem olumsuz tarafları göster (dengeli analiz)
- Sonda tahmin/öngörü: "6 ay içinde...".""",

            "hikaye": """İÇERİK TARZI: HİKAYE / STORYTELLING
- Bir olay/deneyim üzerinden anlat
- Başlangıç → gelişme → sonuç yapısı
- Duyguları hissettir: şaşkınlık, hayal kırıklığı, heyecan
- Diyalog veya iç monolog ekle: "Dedim ki kendime..."
- Beklenmedik bir dönüş noktası olsun
- Okuyucuyu merakta tut, ama sonu net olsun
- Sonda ders/çıkarım: "Bu deneyimden öğrendiğim şey...".""",
        }

        style_prompt = content_styles.get(style, content_styles["deneyim"])

        # Length instructions
        length_map = {
            "kisa": "UZUNLUK: 300-500 karakter. Kısa ama etkili. 3-5 paragraf, her paragraf 1-2 cümle.",
            "orta": "UZUNLUK: 500-1000 karakter. Detaylı anlatım. 5-8 paragraf, her paragraf 2-3 cümle.",
            "uzun": "UZUNLUK: 1000-2000 karakter. Derinlemesine içerik. 8-12 paragraf, detaylı anlatım.",
        }
        length_inst = length_map.get(length, length_map["orta"])

        # Build system prompt
        persona = self.custom_persona or BASE_SYSTEM_PROMPT

        training_block = ""
        if self.training_context:
            tc = self.training_context
            if len(tc) > 10000:
                tc = tc[:10000] + "\n\n[Eğitim verisi uzunluk limiti nedeniyle kısaltıldı]"
            training_block = f"\n\n{tc}\n\nKRİTİK: Yukarıdaki eğitim verisi senin YAZIM DNA'n. İçerik tarzı ne olursa olsun (deneyim, eğitici, analiz vb.) bu DNA'daki tonu, kelimeleri ve doğallığı koru."

        samples_block = ""
        if user_samples:
            samples = "\n".join([f"- {s}" for s in user_samples[:5]])
            samples_block = f"\n\n## ÖRNEK YAZILAR (bu tarzda yaz):\n{samples}"

        system_prompt = f"""{persona}

{style_prompt}

{length_inst}
{training_block}
{samples_block}

ÖNEMLİ KURALLAR:
1. Türkçe yaz (teknik terimler İngilizce kalabilir)
2. Paragraflari KISA tut — her paragraf 1-3 cümle
3. Her paragraftan sonra boş satır bırak (okunabilirlik)
4. Metin duvarı YAZMA — kısa paragraflar, bol boşluk
5. Doğal ve samimi ol — "corporate speak" YAPMA
6. Araştırma sonuçlarındaki GÜNCEL bilgileri kullan AMA kaynağı BELİRTME
7. Spesifik ol — genel laflar değil, somut detaylar
8. Sadece içerik metnini yaz — başlık, meta, açıklama YAZMA
9. Tırnak işareti ile sarma
10. ASLA "@şuhesap şöyle diyor", "yorumlarda şöyle yazıyorlar", "X'te kullanıcılar" gibi ifadeler KULLANMA
11. ASLA araştırma kaynaklarına referans verme — bilgiyi KENDİ sözlerinle, kendi deneyiminmiş gibi yaz
12. Bilgiyi özümse ve KENDİ perspektifinden anlat — "test ettim", "gördüğüm kadarıyla", "bence" gibi"""

        # Build user prompt
        research_block = ""
        if research_context:
            research_block = f"""

## ARKA PLAN BİLGİSİ (bilgi kaynağın bu — ama kaynak belirtme, kendi bilginmiş gibi yaz):
{research_context[:4000]}"""

        additional_block = ""
        if additional_instructions:
            additional_block = f"\n\nEK TALİMATLAR: {additional_instructions}"

        user_prompt = f"""Bu konu hakkında bir X (Twitter) uzun form içerik yaz:

KONU: {topic}
{research_block}
{additional_block}

KRİTİK: Yukarıdaki bilgileri KENDİ DENEYİMİN ve BİLGİN gibi yaz. ASLA:
- "@şuhesap böyle diyor" / "X'te insanlar şöyle yazıyor" / "yorumlarda" YAZMA
- Kaynak, referans, tweet veya hesap ismi BELIRTME
- "Araştırmalarıma göre" gibi ifadeler KULLANMA
Bilgiyi özümseyip KENDİ AĞZINDAN, {style} tarzında, samimi ve doğal yaz.
Paragraflari kısa tut, metin duvarı olmasın. Sadece içerik metnini yaz."""

        if self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            return self._generate_openai(system_prompt, user_prompt)

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
