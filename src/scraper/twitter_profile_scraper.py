"""
Twitter/X Profile Scraper
==========================

Kullanıcının Twitter profilini ve tweet'lerini çekerek
yazım tarzını analiz eder.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
import logging
import json
from pathlib import Path
from dataclasses import dataclass, asdict
import random

logger = logging.getLogger(__name__)

# Nitter instances (Twitter frontend alternatifleri)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.unixfox.eu",
]


@dataclass
class TwitterProfile:
    """Twitter profil bilgileri"""
    username: str
    display_name: str = ""
    bio: str = ""
    location: str = ""
    website: str = ""
    join_date: str = ""
    following_count: int = 0
    followers_count: int = 0
    tweets_count: int = 0
    profile_image: str = ""


@dataclass
class TweetData:
    """Tweet verisi"""
    text: str
    date: str = ""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    has_media: bool = False
    has_link: bool = False


class TwitterProfileScraper:
    """Twitter profil ve tweet scraper"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def scrape_profile(self, username: str) -> Optional[TwitterProfile]:
        """
        Kullanıcının Twitter profilini çek
        """
        username = username.replace("@", "").strip()

        # Nitter instancelarını dene
        for instance in NITTER_INSTANCES:
            try:
                url = f"{instance}/{username}"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    return self._parse_profile(response.text, username)

            except Exception as e:
                logger.debug(f"{instance} başarısız: {e}")
                continue

        logger.warning(f"Profil çekilemedi: @{username}")
        return None

    def scrape_tweets(self, username: str, count: int = 20) -> List[TweetData]:
        """
        Kullanıcının son tweet'lerini çek
        """
        username = username.replace("@", "").strip()
        tweets = []

        for instance in NITTER_INSTANCES:
            try:
                url = f"{instance}/{username}"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    tweets = self._parse_tweets(response.text, count)
                    if tweets:
                        break

            except Exception as e:
                logger.debug(f"{instance} tweet çekme başarısız: {e}")
                continue

        return tweets

    def _parse_profile(self, html: str, username: str) -> TwitterProfile:
        """HTML'den profil bilgilerini çıkar"""
        soup = BeautifulSoup(html, 'lxml')

        profile = TwitterProfile(username=username)

        try:
            # Display name
            name_elem = soup.select_one('.profile-card-fullname')
            if name_elem:
                profile.display_name = name_elem.get_text(strip=True)

            # Bio
            bio_elem = soup.select_one('.profile-bio')
            if bio_elem:
                profile.bio = bio_elem.get_text(strip=True)

            # Location
            loc_elem = soup.select_one('.profile-location')
            if loc_elem:
                profile.location = loc_elem.get_text(strip=True)

            # Stats
            stats = soup.select('.profile-stat-num')
            if len(stats) >= 3:
                profile.tweets_count = self._parse_count(stats[0].get_text())
                profile.following_count = self._parse_count(stats[1].get_text())
                profile.followers_count = self._parse_count(stats[2].get_text())

        except Exception as e:
            logger.error(f"Profil parse hatası: {e}")

        return profile

    def _parse_tweets(self, html: str, count: int) -> List[TweetData]:
        """HTML'den tweet'leri çıkar"""
        soup = BeautifulSoup(html, 'lxml')
        tweets = []

        try:
            tweet_elements = soup.select('.timeline-item')[:count]

            for elem in tweet_elements:
                # Tweet metni
                content_elem = elem.select_one('.tweet-content')
                if not content_elem:
                    continue

                text = content_elem.get_text(strip=True)
                if not text:
                    continue

                tweet = TweetData(text=text)

                # Tarih
                date_elem = elem.select_one('.tweet-date a')
                if date_elem:
                    tweet.date = date_elem.get('title', '')

                # Stats
                stats = elem.select('.tweet-stat')
                for stat in stats:
                    stat_text = stat.get_text(strip=True)
                    icon = stat.select_one('.icon')
                    if icon:
                        icon_class = icon.get('class', [])
                        if 'icon-comment' in str(icon_class):
                            tweet.replies = self._parse_count(stat_text)
                        elif 'icon-retweet' in str(icon_class):
                            tweet.retweets = self._parse_count(stat_text)
                        elif 'icon-heart' in str(icon_class):
                            tweet.likes = self._parse_count(stat_text)

                # Media kontrolü
                if elem.select_one('.attachments'):
                    tweet.has_media = True

                # Link kontrolü
                if 'http' in text or elem.select_one('.card-container'):
                    tweet.has_link = True

                tweets.append(tweet)

        except Exception as e:
            logger.error(f"Tweet parse hatası: {e}")

        return tweets

    def _parse_count(self, text: str) -> int:
        """Sayı metnini parse et (1.5K -> 1500)"""
        if not text:
            return 0

        text = text.strip().replace(',', '').replace('.', '')

        try:
            if 'K' in text.upper():
                return int(float(text.upper().replace('K', '')) * 1000)
            elif 'M' in text.upper():
                return int(float(text.upper().replace('M', '')) * 1000000)
            else:
                return int(text)
        except:
            return 0

    def analyze_writing_style(self, tweets: List[TweetData]) -> Dict:
        """
        Tweet'lerden yazım tarzını analiz et
        """
        if not tweets:
            return {}

        texts = [t.text for t in tweets]

        # Emoji analizi
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0]+")
        all_emojis = []
        emoji_count = 0
        for text in texts:
            found = emoji_pattern.findall(text)
            all_emojis.extend(found)
            if found:
                emoji_count += 1

        # Ortalama uzunluk
        avg_length = sum(len(t) for t in texts) / len(texts) if texts else 0

        # Soru kullanımı
        question_count = sum(1 for t in texts if '?' in t)

        # Hashtag kullanımı
        hashtag_pattern = re.compile(r'#\w+')
        all_hashtags = []
        hashtag_count = 0
        for text in texts:
            found = hashtag_pattern.findall(text)
            all_hashtags.extend(found)
            if found:
                hashtag_count += 1

        # Mention kullanımı
        mention_count = sum(1 for t in texts if '@' in t)

        # Büyük harf kullanımı (vurgu)
        caps_words = sum(len(re.findall(r'\b[A-ZÇĞİÖŞÜ]{2,}\b', t)) for t in texts)

        # Ünlem kullanımı
        exclamation_count = sum(t.count('!') for t in texts)

        # Ton analizi (basit)
        positive_words = ['harika', 'süper', 'müthiş', 'güzel', 'muhteşem', 'başarı', 'sevgi', '❤️', '🔥', '💪']
        negative_words = ['kötü', 'berbat', 'rezalet', 'yazık', 'üzücü', 'maalesef']
        question_words = ['nasıl', 'neden', 'niçin', 'ne zaman', 'kim', 'nerede', 'hangisi']

        positive_score = sum(1 for t in texts for w in positive_words if w.lower() in t.lower())
        negative_score = sum(1 for t in texts for w in negative_words if w.lower() in t.lower())
        question_score = sum(1 for t in texts for w in question_words if w.lower() in t.lower())

        # En iyi performans gösteren tweetler
        best_tweets = sorted(tweets, key=lambda t: t.likes + t.retweets * 2 + t.replies * 3, reverse=True)[:5]

        analysis = {
            "tweet_count": len(tweets),
            "avg_length": round(avg_length),
            "emoji_usage": "çok" if emoji_count > len(tweets) * 0.5 else ("orta" if emoji_count > len(tweets) * 0.2 else "az"),
            "favorite_emojis": list(set(all_emojis))[:10],
            "question_ratio": round(question_count / len(tweets) * 100) if tweets else 0,
            "hashtag_ratio": round(hashtag_count / len(tweets) * 100) if tweets else 0,
            "common_hashtags": list(set(all_hashtags))[:10],
            "mention_ratio": round(mention_count / len(tweets) * 100) if tweets else 0,
            "caps_usage": "vurgu için" if caps_words > len(tweets) else "normal",
            "punctuation_style": "ekspresif" if exclamation_count > len(tweets) * 2 else "normal",
            "tone": "pozitif" if positive_score > negative_score else ("sorgulayıcı" if question_score > 3 else "nötr"),
            "sentence_style": "kısa" if avg_length < 100 else ("orta" if avg_length < 180 else "uzun"),
            "best_performing_tweets": [t.text for t in best_tweets],
            "avg_engagement": {
                "likes": round(sum(t.likes for t in tweets) / len(tweets)) if tweets else 0,
                "retweets": round(sum(t.retweets for t in tweets) / len(tweets)) if tweets else 0,
                "replies": round(sum(t.replies for t in tweets) / len(tweets)) if tweets else 0,
            },
            "media_ratio": round(sum(1 for t in tweets if t.has_media) / len(tweets) * 100) if tweets else 0,
            "link_ratio": round(sum(1 for t in tweets if t.has_link) / len(tweets) * 100) if tweets else 0,
        }

        return analysis


# Global instance
twitter_scraper = TwitterProfileScraper()
