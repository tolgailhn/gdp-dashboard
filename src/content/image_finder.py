"""
Görsel Arama ve İndirme Modülü
==============================

Unsplash ve Pexels API kullanarak konu ile ilgili görseller bulma ve indirme.
Twitter için optimize edilmiş görsel boyutları.

Özellikler:
- Ücretsiz yüksek kaliteli görseller
- Twitter optimal oranı (16:9)
- Otomatik indirme ve önbellekleme
"""

import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import hashlib
from datetime import datetime
import os

import sys
sys.path.append(str(__file__).rsplit('/', 3)[0])
from config.settings import config

logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    """Görsel sonuç veri sınıfı"""
    id: str
    url: str
    thumbnail_url: str
    download_url: str
    width: int
    height: int
    photographer: str
    photographer_url: str
    source: str  # "unsplash" veya "pexels"
    alt_text: str
    local_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "download_url": self.download_url,
            "width": self.width,
            "height": self.height,
            "photographer": self.photographer,
            "photographer_url": self.photographer_url,
            "source": self.source,
            "alt_text": self.alt_text,
            "local_path": self.local_path,
        }


class ImageFinder:
    """
    Görsel arama ve indirme sınıfı

    Bu sınıf Unsplash ve Pexels API kullanarak:
    - Konu bazlı görsel arar
    - Twitter için optimize eder
    - Yerel olarak kaydeder
    """

    def __init__(self):
        """Image finder'ı başlat"""
        self.unsplash_key = config.image.unsplash_access_key
        self.pexels_key = config.image.pexels_api_key

        # Görsel kaydetme dizinini oluştur
        self.images_dir = config.image.images_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_available(self) -> bool:
        """API anahtarlarının mevcut olup olmadığını kontrol et"""
        return bool(self.unsplash_key or self.pexels_key)

    # ========================================================================
    # UNSPLASH API
    # ========================================================================

    def search_unsplash(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape"
    ) -> List[ImageResult]:
        """
        Unsplash'ta görsel ara

        Args:
            query: Arama sorgusu
            per_page: Sonuç sayısı
            orientation: Yönlendirme (landscape, portrait, squarish)

        Returns:
            Görsel sonuçları listesi
        """
        if not self.unsplash_key:
            logger.warning("Unsplash API anahtarı yok")
            return []

        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": orientation,
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for photo in data.get("results", []):
                # Twitter için uygun URL (regular boyut ~1080px)
                urls = photo.get("urls", {})

                result = ImageResult(
                    id=photo["id"],
                    url=urls.get("regular", ""),
                    thumbnail_url=urls.get("thumb", ""),
                    download_url=urls.get("full", ""),
                    width=photo.get("width", 0),
                    height=photo.get("height", 0),
                    photographer=photo.get("user", {}).get("name", "Unknown"),
                    photographer_url=photo.get("user", {}).get("links", {}).get("html", ""),
                    source="unsplash",
                    alt_text=photo.get("alt_description", query),
                )
                results.append(result)

            logger.info(f"Unsplash'ta '{query}' için {len(results)} görsel bulundu")
            return results

        except Exception as e:
            logger.error(f"Unsplash arama hatası: {e}")
            return []

    # ========================================================================
    # PEXELS API
    # ========================================================================

    def search_pexels(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape"
    ) -> List[ImageResult]:
        """
        Pexels'te görsel ara

        Args:
            query: Arama sorgusu
            per_page: Sonuç sayısı
            orientation: Yönlendirme

        Returns:
            Görsel sonuçları listesi
        """
        if not self.pexels_key:
            logger.warning("Pexels API anahtarı yok")
            return []

        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": orientation,
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for photo in data.get("photos", []):
                src = photo.get("src", {})

                result = ImageResult(
                    id=str(photo["id"]),
                    url=src.get("large", ""),
                    thumbnail_url=src.get("tiny", ""),
                    download_url=src.get("original", ""),
                    width=photo.get("width", 0),
                    height=photo.get("height", 0),
                    photographer=photo.get("photographer", "Unknown"),
                    photographer_url=photo.get("photographer_url", ""),
                    source="pexels",
                    alt_text=photo.get("alt", query),
                )
                results.append(result)

            logger.info(f"Pexels'te '{query}' için {len(results)} görsel bulundu")
            return results

        except Exception as e:
            logger.error(f"Pexels arama hatası: {e}")
            return []

    # ========================================================================
    # BİRLEŞİK ARAMA
    # ========================================================================

    def search(
        self,
        query: str,
        per_page: int = None,
        prefer_source: str = None
    ) -> List[ImageResult]:
        """
        Tüm kaynaklarda görsel ara

        Args:
            query: Arama sorgusu
            per_page: Sonuç sayısı
            prefer_source: Tercih edilen kaynak ("unsplash" veya "pexels")

        Returns:
            Görsel sonuçları listesi
        """
        per_page = per_page or config.image.images_per_search
        results = []

        # Tercih edilen kaynaktan başla
        if prefer_source == "pexels" or (not self.unsplash_key and self.pexels_key):
            results.extend(self.search_pexels(query, per_page))
            if len(results) < per_page:
                results.extend(self.search_unsplash(query, per_page - len(results)))
        else:
            results.extend(self.search_unsplash(query, per_page))
            if len(results) < per_page:
                results.extend(self.search_pexels(query, per_page - len(results)))

        # Demo mod (API yoksa)
        if not results:
            results = self._get_demo_images(query)

        return results[:per_page]

    def find_best_image(self, query: str) -> Optional[ImageResult]:
        """
        En uygun tek görseli bul

        Args:
            query: Arama sorgusu

        Returns:
            En iyi görsel sonucu
        """
        results = self.search(query, per_page=3)

        if not results:
            return None

        # En iyi orana sahip olanı seç (16:9'a yakın)
        target_ratio = 16 / 9

        def ratio_score(img: ImageResult) -> float:
            if img.height == 0:
                return float('inf')
            ratio = img.width / img.height
            return abs(ratio - target_ratio)

        results.sort(key=ratio_score)
        return results[0]

    # ========================================================================
    # GÖRSEL İNDİRME
    # ========================================================================

    def download_image(self, image: ImageResult, filename: str = None) -> Optional[str]:
        """
        Görsel indir ve yerel olarak kaydet

        Args:
            image: İndirilecek görsel
            filename: Dosya adı (opsiyonel)

        Returns:
            Yerel dosya yolu veya None
        """
        try:
            # Dosya adı oluştur
            if not filename:
                hash_str = hashlib.md5(image.url.encode()).hexdigest()[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{image.source}_{hash_str}_{timestamp}.jpg"

            filepath = self.images_dir / filename

            # İndir
            response = requests.get(image.url, timeout=30, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Görsel indirildi: {filepath}")
            image.local_path = str(filepath)
            return str(filepath)

        except Exception as e:
            logger.error(f"Görsel indirme hatası: {e}")
            return None

    def find_and_download(self, query: str) -> Optional[str]:
        """
        Görsel bul ve indir (tek adımda)

        Args:
            query: Arama sorgusu

        Returns:
            İndirilen dosyanın yolu veya None
        """
        image = self.find_best_image(query)

        if not image:
            logger.warning(f"'{query}' için görsel bulunamadı")
            return None

        return self.download_image(image)

    # ========================================================================
    # YARDIMCI METODLAR
    # ========================================================================

    def _get_demo_images(self, query: str) -> List[ImageResult]:
        """Demo görsel verisi (API yokken)"""
        return [
            ImageResult(
                id="demo_1",
                url=f"https://via.placeholder.com/1200x675?text={query.replace(' ', '+')}",
                thumbnail_url=f"https://via.placeholder.com/200x112?text={query.replace(' ', '+')}",
                download_url=f"https://via.placeholder.com/1920x1080?text={query.replace(' ', '+')}",
                width=1200,
                height=675,
                photographer="Demo User",
                photographer_url="",
                source="demo",
                alt_text=f"Demo image for {query}",
            )
        ]

    def cleanup_old_images(self, days: int = 7) -> int:
        """
        Eski görselleri temizle

        Args:
            days: Kaç günden eski görseller silinsin

        Returns:
            Silinen dosya sayısı
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for filepath in self.images_dir.glob("*"):
            if filepath.is_file() and filepath.stat().st_mtime < cutoff:
                try:
                    filepath.unlink()
                    deleted += 1
                except Exception as e:
                    logger.error(f"Dosya silme hatası: {e}")

        logger.info(f"{deleted} eski görsel silindi")
        return deleted

    def get_attribution_text(self, image: ImageResult) -> str:
        """
        Görsel için atıf metni oluştur

        Args:
            image: Görsel

        Returns:
            Atıf metni
        """
        if image.source == "unsplash":
            return f"Photo by {image.photographer} on Unsplash"
        elif image.source == "pexels":
            return f"Photo by {image.photographer} on Pexels"
        return f"Photo by {image.photographer}"


# Singleton instance
image_finder = ImageFinder()
