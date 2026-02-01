"""
Trending Topic Discovery - Gündem Keşif Sistemi (v2)
======================================================

Reddit, Hacker News, Tech haberleri ve sosyal medyadan
şu an en çok konuşulan konuları bulur.

GERÇEK ARAŞTIRMA yaparak bilgilendirici içerik oluşturur.
X Premium uzun tweet desteği.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import re
import logging
import random
from datetime import datetime
import urllib.parse
import json

logger = logging.getLogger(__name__)


@dataclass
class TrendingTopic:
    """Trending konu verisi"""
    title: str
    source: str  # reddit, hackernews, technews, twitter
    category: str  # ai, tech, crypto, world, turkey
    url: str = ""
    description: str = ""
    upvotes: int = 0
    comments: int = 0
    time_ago: str = ""
    key_points: List[str] = field(default_factory=list)
    full_content: str = ""  # Tam içerik (araştırma sonucu)
    related_links: List[str] = field(default_factory=list)


@dataclass
class ThreadContent:
    """Thread içeriği - X Premium uzun tweet desteği"""
    topic: str
    full_text: str  # Tek uzun tweet (X Premium için)
    hook: str  # İlk kısım
    body: str  # Ana içerik
    conclusion: str  # Son kısım
    hashtags: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    word_count: int = 0
    char_count: int = 0


class TrendingDiscovery:
    """
    Trending konu keşif ve içerik oluşturma sistemi.
    Reddit, HackerNews, Tech haberleri tarar.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        })

    def get_all_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Tüm kaynaklardan trending konuları getir"""
        all_topics = []

        # Reddit
        reddit_topics = self.get_reddit_trending(category)
        all_topics.extend(reddit_topics)

        # Hacker News
        hn_topics = self.get_hackernews_trending()
        all_topics.extend(hn_topics)

        # Tech News
        tech_topics = self.get_tech_news()
        all_topics.extend(tech_topics)

        # Sırala (upvotes + comments)
        all_topics.sort(key=lambda x: x.upvotes + x.comments * 2, reverse=True)

        return all_topics[:20]

    def get_reddit_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Reddit'ten trending konuları getir"""
        topics = []

        subreddits = {
            "ai": ["artificial", "MachineLearning", "ChatGPT", "OpenAI", "LocalLLaMA"],
            "tech": ["technology", "programming", "webdev", "gadgets"],
            "crypto": ["cryptocurrency", "Bitcoin", "ethereum"],
            "world": ["worldnews", "news"],
            "turkey": ["Turkey"],
            "all": ["artificial", "technology", "worldnews", "ChatGPT", "cryptocurrency"],
        }

        subs = subreddits.get(category, subreddits["all"])

        for sub in subs[:3]:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        post_data = post.get("data", {})

                        if post_data.get("stickied") or post_data.get("promoted"):
                            continue

                        topic = TrendingTopic(
                            title=post_data.get("title", "")[:200],
                            source="reddit",
                            category=category if category != "all" else self._detect_category(post_data.get("title", "")),
                            url=f"https://reddit.com{post_data.get('permalink', '')}",
                            description=post_data.get("selftext", "")[:500],
                            upvotes=post_data.get("ups", 0),
                            comments=post_data.get("num_comments", 0),
                            time_ago=self._format_time(post_data.get("created_utc", 0)),
                        )

                        if topic.upvotes > 50:
                            topics.append(topic)

            except Exception as e:
                logger.debug(f"Reddit hatası ({sub}): {e}")
                continue

        return topics

    def get_hackernews_trending(self) -> List[TrendingTopic]:
        """Hacker News'ten trending konuları getir"""
        topics = []

        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                story_ids = response.json()[:10]

                for story_id in story_ids[:7]:
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = self.session.get(story_url, timeout=5)

                        if story_response.status_code == 200:
                            story = story_response.json()

                            topic = TrendingTopic(
                                title=story.get("title", ""),
                                source="hackernews",
                                category=self._detect_category(story.get("title", "")),
                                url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                upvotes=story.get("score", 0),
                                comments=story.get("descendants", 0),
                                time_ago=self._format_time(story.get("time", 0)),
                            )

                            topics.append(topic)

                    except Exception as e:
                        continue

        except Exception as e:
            logger.debug(f"HackerNews hatası: {e}")

        return topics

    def get_tech_news(self) -> List[TrendingTopic]:
        """Teknoloji haberlerini getir"""
        topics = []

        rss_feeds = [
            ("https://techcrunch.com/feed/", "TechCrunch"),
            ("https://www.wired.com/feed/rss", "Wired"),
        ]

        for feed_url, source in rss_feeds:
            try:
                response = self.session.get(feed_url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')[:3]

                    for item in items:
                        title = item.find('title')
                        link = item.find('link')
                        description = item.find('description')

                        if title:
                            topic = TrendingTopic(
                                title=title.get_text(strip=True)[:200],
                                source=source.lower(),
                                category=self._detect_category(title.get_text()),
                                url=link.get_text(strip=True) if link else "",
                                description=self._clean_html(description.get_text()[:500]) if description else "",
                            )
                            topics.append(topic)

            except Exception as e:
                logger.debug(f"RSS hatası ({source}): {e}")
                continue

        return topics

    def research_topic(self, topic: TrendingTopic) -> TrendingTopic:
        """
        Konu hakkında GERÇEK araştırma yap.
        Web'den detaylı bilgi topla.
        Başarısız olursa başlıktan akıllı analiz yap.
        """
        research_data = []

        # 1. Kaynak URL'den içerik çek
        if topic.url:
            content = self._fetch_article_content(topic.url)
            if content:
                research_data.append(content)
                topic.full_content = content

        # 2. Reddit yorumlarından bilgi topla
        if topic.source == "reddit" and topic.url:
            comments = self._fetch_reddit_comments(topic.url)
            if comments:
                research_data.extend(comments[:5])

        # 3. Key points çıkar
        all_text = " ".join(research_data)
        if all_text:
            topic.key_points = self._extract_key_points(all_text)

        # 4. Araştırma başarısız olduysa başlıktan akıllı analiz yap
        if not topic.key_points and not topic.full_content:
            title_analysis = self._analyze_title_smart(topic.title)
            topic.key_points = title_analysis["key_points"]
            topic.description = title_analysis["description"]
            topic.full_content = title_analysis["context"]

        return topic

    def _analyze_title_smart(self, title: str) -> Dict[str, any]:
        """
        Başlıktan akıllı analiz yap.
        Teknik terimleri, ürün adlarını, kavramları tespit et.
        """
        result = {
            "key_points": [],
            "description": "",
            "context": "",
            "entities": [],
            "concepts": []
        }

        title_lower = title.lower()

        # Teknik terim sözlüğü
        tech_terms = {
            "open source": "Açık kaynak kodlu, herkesin inceleyip katkıda bulunabileceği yazılım",
            "zero trust": "Sıfır güven modeli - hiçbir kullanıcı veya cihaza otomatik güvenilmez, her erişim doğrulanır",
            "networking": "Ağ teknolojisi - bilgisayarlar arası iletişim altyapısı",
            "vpn": "Sanal özel ağ - güvenli ve şifreli internet bağlantısı",
            "ai": "Yapay zeka - makinelerin insan benzeri öğrenme ve karar verme yeteneği",
            "machine learning": "Makine öğrenimi - verilerden öğrenen algoritmalar",
            "llm": "Büyük dil modeli - ChatGPT gibi metin üreten AI sistemleri",
            "api": "Uygulama programlama arayüzü - yazılımlar arası iletişim protokolü",
            "cloud": "Bulut bilişim - internet üzerinden sunulan hesaplama kaynakları",
            "saas": "Hizmet olarak yazılım - abonelik bazlı bulut uygulamaları",
            "kubernetes": "Konteyner orkestrasyon platformu - uygulamaları ölçeklendirme aracı",
            "docker": "Konteyner teknolojisi - uygulamaları izole ortamlarda çalıştırma",
            "blockchain": "Blok zinciri - dağıtık, değiştirilemez veri yapısı",
            "cryptocurrency": "Kripto para - şifreleme ile güvence altına alınan dijital para",
            "bitcoin": "İlk ve en büyük kripto para birimi",
            "ethereum": "Akıllı sözleşme destekli kripto para platformu",
            "startup": "Yeni kurulan, hızlı büyümeyi hedefleyen teknoloji şirketi",
            "funding": "Yatırım turu - şirketlerin dış kaynaklardan para toplaması",
            "acquisition": "Satın alma - bir şirketin başka bir şirketi alması",
            "ipo": "Halka arz - şirket hisselerinin borsada işlem görmeye başlaması",
            "security": "Güvenlik - sistemleri tehditlere karşı koruma",
            "privacy": "Gizlilik - kişisel verilerin korunması",
            "encryption": "Şifreleme - verileri okunamaz hale getirme",
            "bug": "Yazılım hatası",
            "patch": "Güvenlik yaması - hataları düzelten güncelleme",
            "vulnerability": "Güvenlik açığı - saldırganların istismar edebileceği zayıflık",
            "hack": "Siber saldırı veya yaratıcı çözüm",
            "data breach": "Veri sızıntısı - yetkisiz kişilerin verilere erişmesi",
            "ransomware": "Fidye yazılımı - verileri şifreleyip para isteyen kötü yazılım",
            "gpu": "Grafik işlemci - AI ve oyunlarda kullanılan güçlü işlemci",
            "chip": "Mikroçip - elektronik devre",
            "semiconductor": "Yarı iletken - çip üretiminde kullanılan malzeme",
            "quantum": "Kuantum teknolojisi - kuantum fiziğine dayalı hesaplama",
            "robotics": "Robot teknolojisi",
            "autonomous": "Otonom - insan müdahalesi olmadan çalışan",
            "ev": "Elektrikli araç",
            "battery": "Pil teknolojisi",
            "renewable": "Yenilenebilir enerji",
            "solar": "Güneş enerjisi",
            "spacex": "Elon Musk'ın uzay şirketi",
            "nasa": "ABD Ulusal Havacılık ve Uzay Dairesi",
            "launch": "Lansman veya fırlatma",
            "satellite": "Uydu",
            "5g": "Beşinci nesil mobil ağ teknolojisi",
            "metaverse": "Sanal evren - 3D dijital dünya",
            "vr": "Sanal gerçeklik",
            "ar": "Artırılmış gerçeklik",
        }

        # Başlıkta geçen terimleri bul
        found_terms = []
        explanations = []

        for term, explanation in tech_terms.items():
            if term in title_lower:
                found_terms.append(term)
                explanations.append(f"{term.title()}: {explanation}")

        # Key points oluştur
        if explanations:
            result["key_points"] = explanations[:4]

        # Şirket/ürün adını tespit et (başlıktaki ilk kelime genelde)
        words = title.split()
        if words:
            # Tire veya iki nokta öncesi genelde ürün/şirket adı
            if " - " in title:
                product_name = title.split(" - ")[0].strip()
            elif ": " in title:
                product_name = title.split(": ")[0].strip()
            else:
                product_name = words[0]

            result["entities"].append(product_name)

        # Genel açıklama oluştur
        if found_terms:
            if "open source" in found_terms:
                result["description"] = f"{result['entities'][0] if result['entities'] else 'Bu proje'} açık kaynak kodlu bir proje. Kaynak kodları herkese açık, topluluk katkılarına açık."

            if "zero trust" in found_terms or "security" in found_terms:
                result["description"] += " Güvenlik odaklı bir çözüm sunuyor."

            if "ai" in found_terms or "machine learning" in found_terms:
                result["description"] = f"{result['entities'][0] if result['entities'] else 'Bu'} yapay zeka teknolojisi kullanıyor."

        # Context (AI için ek bilgi)
        context_parts = [f"Konu: {title}"]
        if found_terms:
            context_parts.append(f"Tespit edilen teknoloji terimleri: {', '.join(found_terms)}")
        if result["entities"]:
            context_parts.append(f"Bahsedilen ürün/şirket: {', '.join(result['entities'])}")
        if explanations:
            context_parts.append("Terim açıklamaları:\n" + "\n".join(explanations))

        result["context"] = "\n".join(context_parts)

        # Eğer hiçbir terim bulunamadıysa genel bir açıklama yap
        if not result["key_points"]:
            result["key_points"] = [
                f"'{title}' konusu şu an gündemde",
                "Detaylar için kaynağı inceleyebilirsiniz",
            ]
            result["description"] = f"'{title}' hakkında önemli bir gelişme yaşanıyor."

        return result

    def _fetch_article_content(self, url: str) -> str:
        """Makale içeriğini çek"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # Script ve style taglerini kaldır
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()

                # Makale içeriğini bul
                article = soup.find('article') or soup.find('main') or soup.find('body')

                if article:
                    paragraphs = article.find_all('p')
                    content = " ".join([p.get_text(strip=True) for p in paragraphs[:15]])
                    return content[:3000]

        except Exception as e:
            logger.debug(f"İçerik çekme hatası: {e}")

        return ""

    def _fetch_reddit_comments(self, url: str) -> List[str]:
        """Reddit yorumlarını çek"""
        comments = []
        try:
            # Reddit JSON API
            json_url = url.rstrip('/') + '.json'
            response = self.session.get(json_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    comment_data = data[1].get("data", {}).get("children", [])

                    for comment in comment_data[:10]:
                        body = comment.get("data", {}).get("body", "")
                        if body and len(body) > 50 and "[deleted]" not in body:
                            comments.append(body[:500])

        except Exception as e:
            logger.debug(f"Reddit yorum hatası: {e}")

        return comments

    def _extract_key_points(self, text: str) -> List[str]:
        """Metinden önemli noktaları çıkar"""
        if not text:
            return []

        # Cümlelere ayır
        sentences = re.split(r'[.!?]', text)

        # Önemli cümleleri filtrele
        key_points = []
        important_words = [
            "önemli", "kritik", "yeni", "ilk", "büyük", "değişti",
            "announced", "launched", "new", "first", "major", "breaking",
            "revolutionary", "significant", "important", "update"
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40 and len(sentence) < 300:
                if any(word in sentence.lower() for word in important_words):
                    key_points.append(sentence)

        # En az 3 nokta olsun
        if len(key_points) < 3:
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 50 and len(sentence) < 250 and sentence not in key_points:
                    key_points.append(sentence)
                    if len(key_points) >= 5:
                        break

        return key_points[:7]

    def _detect_category(self, text: str) -> str:
        """Metinden kategori tespit et"""
        text_lower = text.lower()

        categories = {
            "ai": ["ai", "artificial intelligence", "machine learning", "chatgpt", "openai", "llm", "gpt", "claude", "gemini", "neural", "deep learning", "yapay zeka"],
            "crypto": ["bitcoin", "crypto", "ethereum", "blockchain", "btc", "eth", "token", "defi", "nft"],
            "tech": ["apple", "google", "microsoft", "startup", "app", "software", "programming", "code", "developer"],
            "world": ["war", "election", "president", "government", "politics", "climate", "economy"],
        }

        for cat, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return cat

        return "tech"

    def _format_time(self, timestamp: float) -> str:
        """Unix timestamp'i okunabilir formata çevir"""
        if not timestamp:
            return ""

        try:
            dt = datetime.fromtimestamp(timestamp)
            now = datetime.now()
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days} gün önce"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600} saat önce"
            else:
                return f"{diff.seconds // 60} dakika önce"
        except:
            return ""

    def _clean_html(self, text: str) -> str:
        """HTML taglerini temizle"""
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()


class InformativeThreadGenerator:
    """
    Bilgilendirici, detaylı içerik oluşturucu.
    X Premium uzun tweet desteği (25.000 karakter).

    Çağla Üren tarzı: Araştırma + Bilgi + Analiz
    """

    @classmethod
    def generate_informative_content(
        cls,
        topic: TrendingTopic,
        ai_client=None,
        user_voice: str = "samimi",
        max_length: int = 2000
    ) -> ThreadContent:
        """
        AI kullanarak bilgilendirici içerik oluştur.
        Gerçek araştırma verilerini kullanır.
        """

        # Araştırma verilerini hazırla
        research_context = cls._prepare_research_context(topic)

        # AI varsa kullan
        if ai_client and hasattr(ai_client, '_call_ai'):
            content = cls._generate_with_ai(ai_client, topic, research_context, user_voice, max_length)
            if content:
                return content

        # AI yoksa şablondan oluştur (ama araştırma verilerini kullan)
        return cls._generate_from_template(topic, research_context, user_voice)

    @classmethod
    def _prepare_research_context(cls, topic: TrendingTopic) -> str:
        """Araştırma verilerini context olarak hazırla"""
        context_parts = []

        context_parts.append(f"KONU: {topic.title}")

        if topic.description:
            context_parts.append(f"ÖZET: {topic.description}")

        if topic.full_content:
            context_parts.append(f"DETAYLI İÇERİK: {topic.full_content[:1500]}")

        if topic.key_points:
            points = "\n".join([f"- {p}" for p in topic.key_points])
            context_parts.append(f"ÖNEMLİ NOKTALAR:\n{points}")

        if topic.source:
            context_parts.append(f"KAYNAK: {topic.source}")

        return "\n\n".join(context_parts)

    @classmethod
    def _generate_with_ai(
        cls,
        ai_client,
        topic: TrendingTopic,
        research_context: str,
        user_voice: str,
        max_length: int
    ) -> Optional[ThreadContent]:
        """AI ile içerik oluştur"""

        prompt = f"""Sen @ilhntolga hesabından tweet atan bir Türk teknoloji uzmanısın. Konuları BİLİYORMUŞ gibi, UZMAN gibi anlatıyorsun.

⚠️ KRİTİK KURAL - %100 TÜRKÇE:
- Aşağıdaki İngilizce metinleri TÜRKÇE'YE ÇEVİR
- Hiçbir İngilizce kelime/cümle KALMAMALI
- Teknik terimleri Türkçe açıkla (parantez içinde İngilizce olabilir)

📝 ANLATIM TARZI - UZMAN GİBİ:
- "Araştırdım, buldum" DEĞİL
- Konuyu zaten biliyormuş gibi anlat
- "X nedir biliyor musunuz?", "Şöyle açıklayayım:", "Kısaca anlatayım:"
- Öğretici, bilgilendirici ama samimi

KONU: {topic.title}

ARAŞTIRMA VERİLERİ (TÜRKÇE'YE ÇEVİR!):
{research_context}

ÖRNEK YAZI:
🎮 Point-and-click macera oyunu yapımcıları için müjde!

Adventure Game Studio (AGS) nedir biliyor musunuz? Grafik tabanlı macera oyunları yapmanızı sağlayan ücretsiz bir araç.

Şöyle açıklayayım:
• Tamamen ücretsiz, abonelik yok
• Windows üzerinde çalışıyor, grafik ekleme, script yazma, test etme hepsi tek yerde
• Yaptığın oyunlar Linux, iOS, Android'de de çalışıyor

Neden önemli?
Eskiden bu tarz oyun yapmak için ya büyük bütçe ya da ciddi programlama bilgisi gerekiyordu. AGS ile herkes oyun geliştirebilir.

Oyun geliştirmeyle ilgilenen var mı? Hangi araçları kullanıyorsunuz? 👇

TALİMATLAR:
1. 1200-1800 karakter yaz
2. Konuyu DETAYLI açıkla, yüzeysel kalma
3. Teknik terimleri Türkçe anlat
4. 2-3 emoji max
5. Hashtag EKLEME
6. SADECE tweet metnini yaz"""

        try:
            response = ai_client._call_ai(prompt)

            if response and len(response) > 150:
                content = response.strip().strip('"\'')

                return ThreadContent(
                    topic=topic.title,
                    full_text=content,
                    hook=content[:200] + "..." if len(content) > 200 else content,
                    body=content,
                    conclusion="",
                    hashtags=cls._generate_hashtags(topic),
                    sources=[topic.url] if topic.url else [],
                    word_count=len(content.split()),
                    char_count=len(content),
                )

        except Exception as e:
            logger.error(f"AI içerik oluşturma hatası: {e}")

        return None

    @classmethod
    def _generate_from_template(
        cls,
        topic: TrendingTopic,
        research_context: str,
        user_voice: str
    ) -> ThreadContent:
        """Şablondan bilgilendirici içerik oluştur - Uzman anlatımı"""

        # Başlığı Türkçeleştir
        title_tr = cls._simple_translate_title(topic.title)

        # Ürün adı
        product_name = topic.title.split(" - ")[0].split(":")[0].strip() if " - " in topic.title or ":" in topic.title else topic.title.split()[0]

        # Key points - Türkçeleştir
        key_points_text = ""
        if topic.key_points:
            formatted_points = []
            for p in topic.key_points[:4]:
                # Basit Türkçeleştirme
                p_tr = cls._simple_translate_title(p)
                formatted_points.append(f"• {p_tr[:180]}")
            key_points_text = "\n".join(formatted_points)
        else:
            key_points_text = "• Detaylar için kaynağı inceleyebilirsiniz"

        # Description - Türkçeleştir
        if topic.description and len(topic.description) > 50:
            description = cls._simple_translate_title(topic.description[:400])
        elif topic.full_content and len(topic.full_content) > 50:
            description = cls._simple_translate_title(topic.full_content[:400])
        else:
            description = f"{product_name} hakkında bilmeniz gerekenler var."

        # UZMAN ANLATIM ŞABLONLARI
        templates = {
            "ai": """🤖 Yapay zeka dünyasından önemli bir gelişme

{title_tr} nedir biliyor musunuz? Kısaca anlatayım.

{description}

Önemli detaylar:
{key_points}

Neden takip etmelisiniz?
AI araçları artık sadece büyük şirketlerin değil, herkesin kullanabileceği seviyeye geldi. {product_name} bunun güzel bir örneği.

Bu alanda hangi araçları kullanıyorsunuz? 👇""",

            "tech": """💻 Teknoloji dünyasından bir gelişme anlatayım

{title_tr} - bu ne demek açıklayayım.

{description}

Detaylar:
{key_points}

Neden önemli?
Açık kaynak projeler teknoloji dünyasını demokratikleştiriyor. {product_name} gibi araçlar sayesinde herkes üretici olabiliyor.

Siz bu tarz araçlar kullanıyor musunuz? 👇""",

            "crypto": """₿ Kripto piyasasından bir güncelleme

{title_tr} konusunu açıklayayım.

{description}

Dikkat edilmesi gerekenler:
{key_points}

⚠️ Önemli: Bu yatırım tavsiyesi değil. Her zaman kendi araştırmanızı yapın.

Piyasa hakkında ne düşünüyorsunuz? 👇""",

            "world": """🌍 Dünya gündeminden bir gelişme

{title_tr} - ne olduğunu anlatayım.

{description}

Önemli noktalar:
{key_points}

Bu gelişmenin etkilerini birlikte takip edelim. Sizin yorumunuz nedir? 👇""",

            "default": """🔥 Gündemden bir konu anlatayım

{title_tr} - bu ne demek açıklayayım.

{description}

Bilmeniz gerekenler:
{key_points}

Bu konuda düşüncelerinizi merak ediyorum 👇"""
        }

        template = templates.get(topic.category, templates["default"])

        content = template.format(
            title_tr=title_tr,
            description=description,
            key_points=key_points_text,
            product_name=product_name,
        )

        return ThreadContent(
            topic=topic.title,
            full_text=content,
            hook=content[:200],
            body=content,
            conclusion="",
            hashtags=cls._generate_hashtags(topic),
            sources=[topic.url] if topic.url else [],
            word_count=len(content.split()),
            char_count=len(content),
        )

    @classmethod
    def _simple_translate_title(cls, text: str) -> str:
        """Yaygın İngilizce kelimeleri Türkçe'ye çevir"""
        import re

        # Kapsamlı çeviri sözlüğü
        translations = {
            # Cümle kalıpları
            "What I learned": "Öğrendiklerim",
            "How to": "Nasıl yapılır",
            "Why you should": "Neden yapmalısınız",
            "It is free": "Ücretsiz",
            "It was the first": "İlk olarak",
            "I've been using": "Kullanıyorum",
            "I tried": "Denedim",
            "I preferred": "Tercih ettim",
            "can be played": "oynanabilir",
            "requires no subscription": "abonelik gerektirmiyor",
            "standalone": "bağımsız",
            "point-and-click": "tıkla-oyna tarzı",
            "adventure games": "macera oyunları",
            "graphical": "grafiksel",

            # Fiiller
            "building": "geliştirme",
            "creating": "oluşturma",
            "coding": "kodlama",
            "writing": "yazma",
            "testing": "test etme",
            "importing": "içe aktarma",
            "integrating": "entegre etme",
            "streamlines": "kolaylaştırıyor",
            "launches": "çıkardı",
            "announces": "duyurdu",
            "released": "yayınladı",
            "including": "dahil olmak üzere",
            "using": "kullanarak",

            # Sıfatlar
            "opinionated": "belirli kurallara sahip",
            "minimal": "minimal/sade",
            "free": "ücretsiz",
            "new": "yeni",
            "first": "ilk",
            "best": "en iyi",
            "top": "en popüler",
            "multiple": "birden fazla",
            "Windows-based": "Windows tabanlı",

            # İsimler - Teknoloji
            "agent": "ajan/asistan",
            "AI": "yapay zeka",
            "machine learning": "makine öğrenimi",
            "open source": "açık kaynak",
            "startup": "girişim",
            "update": "güncelleme",
            "security": "güvenlik",
            "privacy": "gizlilik",
            "data": "veri",
            "cloud": "bulut",
            "app": "uygulama",
            "tool": "araç",
            "tools": "araçlar",
            "feature": "özellik",
            "features": "özellikler",
            "platform": "platform",
            "platforms": "platformlar",
            "IDE": "geliştirme ortamı",
            "scripts": "scriptler",
            "graphics": "grafikler",
            "games": "oyunlar",
            "game": "oyun",
            "Game Studio": "Oyun Stüdyosu",

            # Zaman ifadeleri
            "In the past": "Geçtiğimiz",
            "three years": "üç yıl",
            "a year": "bir yıl",
            "half": "buçuk",

            # Bağlaçlar
            "and": "ve",
            "or": "veya",
            "but": "ama",
            "for": "için",
            "with": "ile",
            "from": "dan",
            "into": "içine",
            "finally": "sonunda",

            # Artikeller (kaldır)
            "The ": "",
            "A ": "",
            "An ": "",
        }

        result = text
        # Uzun ifadeleri önce çevir (sıralama önemli)
        sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

        for eng, tr in sorted_translations:
            if eng.lower() in result.lower():
                result = re.sub(re.escape(eng), tr, result, flags=re.IGNORECASE)

        return result.strip()

    @classmethod
    def _generate_hashtags(cls, topic: TrendingTopic) -> List[str]:
        """Konu için hashtag oluştur"""
        hashtags = []

        category_tags = {
            "ai": ["#YapayZeka", "#AI", "#Teknoloji"],
            "tech": ["#Teknoloji", "#Tech", "#Gündem"],
            "crypto": ["#Bitcoin", "#Kripto", "#BTC"],
            "world": ["#Gündem", "#Dünya", "#Haber"],
        }

        hashtags.extend(category_tags.get(topic.category, ["#Gündem"]))

        return hashtags[:2]


# Kategoriler için Türkçe isimler
TRENDING_CATEGORIES = {
    "ai": {"name": "🤖 Yapay Zeka", "desc": "AI, ChatGPT, LLM haberleri"},
    "tech": {"name": "💻 Teknoloji", "desc": "Genel teknoloji haberleri"},
    "crypto": {"name": "₿ Kripto", "desc": "Bitcoin, Ethereum, DeFi"},
    "world": {"name": "🌍 Dünya", "desc": "Dünya gündemi"},
    "all": {"name": "🔥 Tümü", "desc": "Tüm kategoriler"},
}


# Global instances
trending_discovery = TrendingDiscovery()
thread_generator = InformativeThreadGenerator()
