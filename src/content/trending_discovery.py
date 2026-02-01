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
        # Daha güçlü headers - Reddit bot engellemesini aş
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def get_all_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Sadece Reddit'ten trending konuları getir"""
        all_topics = []

        # Sadece Reddit kullan (en kaliteli kaynak)
        reddit_topics = self.get_reddit_trending(category)
        all_topics.extend(reddit_topics)

        # Reddit başarısız olduysa HackerNews'i dene
        if not all_topics:
            logger.warning("Reddit'ten veri alınamadı, HackerNews deneniyor...")
            hn_topics = self.get_hackernews_trending()
            all_topics.extend(hn_topics)

        # Sırala (upvotes + comments)
        all_topics.sort(key=lambda x: x.upvotes + x.comments * 2, reverse=True)

        return all_topics[:15]

    def get_hackernews_trending(self) -> List[TrendingTopic]:
        """Hacker News'ten trending konuları getir (Reddit backup)"""
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

    def get_reddit_trending(self, category: str = "all") -> List[TrendingTopic]:
        """Reddit'ten trending konuları getir - retry ile"""
        topics = []

        subreddits = {
            "ai": ["artificial", "MachineLearning", "ChatGPT", "OpenAI", "LocalLLaMA"],
            "tech": ["technology", "programming", "webdev", "gadgets"],
            "crypto": ["cryptocurrency", "Bitcoin", "ethereum"],
            "world": ["worldnews", "news"],
            "turkey": ["Turkey"],
            "all": ["technology", "artificial", "ChatGPT", "programming", "worldnews"],
        }

        subs = subreddits.get(category, subreddits["all"])

        for sub in subs[:4]:
            try:
                # Reddit JSON API - retry ile
                import time

                for attempt in range(2):
                    try:
                        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=7&raw_json=1"
                        response = self.session.get(url, timeout=15)

                        if response.status_code == 200:
                            break
                        elif response.status_code == 429:
                            # Rate limited, bekle
                            time.sleep(2)
                            continue
                    except:
                        time.sleep(1)
                        continue

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        continue

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

                        if topic.upvotes > 20:  # Daha düşük eşik
                            topics.append(topic)

            except Exception as e:
                logger.warning(f"Reddit hatası ({sub}): {e}")
                continue

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

        # Başlıktan konu özeti çıkar
        title = topic.title

        prompt = f"""SEN TÜRKÇE YAZAN BİR İÇERİK ÜRETİCİSİSİN.

🚨 EN ÖNEMLİ KURAL: SADECE TÜRKÇE YAZ!
- İngilizce kelime YASAK
- İngilizce cümle YASAK
- Teknik terim varsa Türkçe karşılığını yaz

KONU BAŞLIĞI: {title}

BU KONUYU TÜRKÇE ANLAT. Konuyu biliyormuş gibi, uzman gibi açıkla.

YAZI YAPISI:
1. Dikkat çekici başlık (emoji ile)
2. "Bu nedir?" kısmı - basitçe açıkla
3. "Neden önemli?" - 3-4 madde halinde
4. "Benim görüşüm" - kişisel yorum
5. Soru ile bitir (etkileşim için)

ÖRNEK:
🚀 Mass hesabından çıkış yapılması: Meta'nın yeni hamlesi

Meta, kullanıcıların tüm cihazlardan tek tıkla çıkış yapabilmesini sağlayan yeni bir özellik getirdi.

Bu ne demek?
Artık hesabınıza giriş yaptığınız tüm cihazları görebilir ve tek tuşla hepsinden çıkış yapabilirsiniz.

Neden önemli?
• Güvenlik açısından büyük kolaylık
• Kayıp/çalıntı cihazlarda hesap koruması
• Şüpheli girişleri anında tespit edebilme

Bence bu özellik çok geç geldi ama geç olsun güç olmasın. Özellikle güvenliğine önem verenler için vazgeçilmez olacak.

Siz hesap güvenliği için ne tür önlemler alıyorsunuz? 👇

YAZIM KURALLARI:
- 1000-1500 karakter
- Samimi ama bilgilendirici
- 2-3 emoji maximum
- Hashtag EKLEME
- SADECE Türkçe metin yaz, başka bir şey yazma"""

        try:
            response = ai_client._call_ai(prompt)

            if response and len(response) > 150:
                content = response.strip().strip('"\'')

                # İngilizce kelime kontrolü - çok fazla varsa template'e geç
                eng_words = ['the ', 'is ', 'are ', 'was ', 'were ', 'have ', 'has ', 'will ', 'would ', 'could ', 'should ', 'this ', 'that ', 'with ', 'from ', 'for ', 'and ', 'but ', 'or ']
                eng_count = sum(1 for w in eng_words if w.lower() in content.lower())

                if eng_count > 3:
                    # Çok fazla İngilizce var, template kullan
                    logger.warning(f"AI çok fazla İngilizce kullandı ({eng_count} kelime), template'e geçiliyor")
                    return None

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
        """Şablondan içerik oluştur - İngilizce veri KULLANMA, sadece Türkçe yaz"""

        # Başlıktan ürün/konu adını çıkar
        title = topic.title
        if " - " in title:
            product_name = title.split(" - ")[0].strip()
            topic_desc = title.split(" - ")[1].strip() if len(title.split(" - ")) > 1 else ""
        elif ": " in title:
            product_name = title.split(": ")[0].strip()
            topic_desc = title.split(": ")[1].strip() if len(title.split(": ")) > 1 else ""
        else:
            words = title.split()
            product_name = words[0] if words else "Bu konu"
            topic_desc = " ".join(words[1:]) if len(words) > 1 else ""

        # Kategori bazlı Türkçe içerik (İngilizce araştırma verisini KULLANMA)
        templates = {
            "ai": f"""🤖 Yapay Zeka Dünyasından Sıcak Gelişme!

{product_name} hakkında konuşalım.

Bu ne?
Yapay zeka alanında yeni bir gelişme var. Reddit'te çok konuşuluyor ve teknoloji camiası heyecanlı.

Neden önemli?
• AI araçları her geçen gün daha erişilebilir hale geliyor
• Geliştiriciler ve kullanıcılar için yeni fırsatlar doğuyor
• Bu tarz yenilikler sektörü şekillendiriyor

Benim görüşüm:
Yapay zeka alanı inanılmaz hızlı ilerliyor. Bugün "deneysel" dediğimiz şeyler yarın günlük hayatımızın parçası oluyor.

Siz AI araçlarını ne için kullanıyorsunuz? 👇""",

            "tech": f"""💻 Teknoloji Gündeminden Önemli Bir Haber!

{product_name} - bu ismi duymuş olabilirsiniz.

Ne oldu?
Teknoloji dünyasında yeni bir gelişme var. Özellikle yazılım ve açık kaynak camiasında gündem oldu.

Dikkat çeken noktalar:
• Açık kaynak projelerin gücü bir kez daha ortaya çıktı
• Topluluk desteği çok önemli
• Herkesin kullanabileceği araçlar artıyor

Neden takip etmelisiniz?
Teknoloji demokratikleşiyor. Eskiden büyük şirketlerin tekelinde olan araçlar artık herkesin erişimine açık.

Bu tarz projeleri takip ediyor musunuz? 👇""",

            "crypto": f"""₿ Kripto Dünyasından Güncel Haber!

{product_name} konusunda neler oluyor?

Durum:
Kripto piyasasında her gün yeni gelişmeler yaşanıyor. Bu da onlardan biri.

Dikkat edilecekler:
• Piyasa volatilitesi her zaman yüksek
• DYOR (Kendi araştırmanı yap) kuralı geçerli
• Risk yönetimi şart

⚠️ Önemli: Bu yatırım tavsiyesi değildir. Sadece bilgilendirme amaçlıdır.

Kripto hakkında ne düşünüyorsunuz? 👇""",

            "world": f"""🌍 Dünya Gündeminden Bir Gelişme!

{product_name} konusu gündemde.

Ne oldu?
Dünya genelinde önemli bir gelişme yaşandı. Sosyal medyada çok konuşuluyor.

Önemli noktalar:
• Bu gelişme birçok kişiyi etkileyebilir
• Uzun vadeli sonuçları olabilir
• Takip etmekte fayda var

Sizce bu gelişme nasıl sonuçlanır? 👇""",

            "default": f"""🔥 Gündemden Sıcak Bir Konu!

{product_name} bugün çok konuşuluyor.

Neler oluyor?
Reddit ve teknoloji çevrelerinde bu konu gündem oldu. İlgi çekici gelişmeler var.

Öne çıkanlar:
• Konu hakkında farklı görüşler mevcut
• Detaylar henüz netleşiyor
• Takipte kalmakta fayda var

Bu konu hakkında ne düşünüyorsunuz? Yorumlarınızı bekliyorum 👇"""
        }

        content = templates.get(topic.category, templates["default"])

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
