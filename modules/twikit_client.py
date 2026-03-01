"""
Twikit Client Module
Sync wrapper for twikit's async API for free Twitter search operations.
Uses cookie-based auth to avoid Twitter API costs.
"""
import asyncio
import datetime
import re
from pathlib import Path

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

DATA_DIR = Path(__file__).parent.parent / "data"
COOKIES_PATH = DATA_DIR / "twikit_cookies.json"


def _run_async(coro):
    """Run an async coroutine synchronously, compatible with Streamlit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def adapt_query_for_web(query: str, since_date: str = None) -> str:
    """Adapt Twitter API v2 search operators to web search format."""
    q = query.replace("-is:retweet", "-filter:retweets")
    q = re.sub(r'\blang:\w+\b', '', q)
    if since_date:
        q += f" since:{since_date}"
    return re.sub(r'\s+', ' ', q).strip()


class TwikitSearchClient:
    """Sync wrapper for twikit async client, focused on search/read operations."""

    def __init__(self, username: str = "", password: str = "",
                 email: str = "", totp_secret: str = ""):
        self.username = username
        self.password = password
        self.email = email
        self.totp_secret = totp_secret
        self._client = None
        self._authenticated = False
        self.last_error = ""  # Store last error for UI display

    def _get_client(self):
        if self._client is None:
            from twikit import Client
            self._client = Client('tr')
        return self._client

    def authenticate(self) -> bool:
        """Authenticate with Twitter. Returns True on success."""
        return _run_async(self._auth_async())

    async def _auth_async(self) -> bool:
        client = self._get_client()
        self.last_error = ""

        # Try loading saved cookies first
        if COOKIES_PATH.exists():
            try:
                client.load_cookies(str(COOKIES_PATH))
                self._authenticated = True
                return True
            except Exception as e:
                self.last_error = f"Cookie yükleme hatası: {e}"
                # Cookies corrupted, delete and try fresh login
                try:
                    COOKIES_PATH.unlink()
                except Exception:
                    pass

        # Login with credentials
        if not (self.username and self.password):
            self.last_error = "Kullanıcı adı ve şifre gerekli"
            return False

        try:
            login_kwargs = {
                "auth_info_1": self.username,
                "auth_info_2": self.email or self.username,
                "password": self.password,
            }

            # Add TOTP for 2FA if provided
            if self.totp_secret:
                try:
                    import pyotp
                    totp = pyotp.TOTP(self.totp_secret)
                    login_kwargs["totp_secret"] = self.totp_secret
                except ImportError:
                    pass

            await client.login(**login_kwargs)
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            client.save_cookies(str(COOKIES_PATH))
            self._authenticated = True
            return True
        except Exception as e:
            error_str = str(e)
            error_type = type(e).__name__

            # Provide user-friendly error messages
            if "ConnectError" in error_type or "name resolution" in error_str:
                self.last_error = (
                    "Twitter'a bağlanılamıyor. İnternet bağlantısını kontrol edin. "
                    "Streamlit Cloud kullanıyorsanız, uygulamanın internete erişimi olduğundan emin olun."
                )
            elif "400" in error_str or "Bad Request" in error_str:
                self.last_error = (
                    "Twitter giriş isteği reddedildi (400). "
                    "Kullanıcı adı/şifre yanlış olabilir veya Twitter geçici sorun yaşıyor olabilir."
                )
            elif "403" in error_str or "Forbidden" in error_str:
                self.last_error = (
                    "Twitter hesabınız kilitlenmiş veya askıya alınmış olabilir (403). "
                    "Twitter.com'dan hesabınıza giriş yapıp kontrol edin."
                )
            elif "challenge" in error_str.lower() or "verification" in error_str.lower():
                self.last_error = (
                    "Twitter doğrulama istiyor! "
                    "Önce twitter.com'dan tarayıcıyla giriş yapın, "
                    "doğrulamayı tamamlayın, sonra tekrar deneyin."
                )
            elif "2fa" in error_str.lower() or "totp" in error_str.lower():
                self.last_error = (
                    "İki faktörlü doğrulama (2FA) gerekli! "
                    "secrets.toml'a twikit_totp_secret ekleyin "
                    "veya Twitter'dan geçici olarak 2FA'yı kapatın."
                )
            elif "rate" in error_str.lower() or "429" in error_str:
                self.last_error = (
                    "Çok fazla giriş denemesi (rate limit). "
                    "15-30 dakika bekleyip tekrar deneyin."
                )
            elif "locked" in error_str.lower():
                self.last_error = (
                    "Twitter hesabınız kilitli. "
                    "twitter.com'dan giriş yapıp hesabı açın, sonra tekrar deneyin."
                )
            else:
                self.last_error = f"{error_type}: {error_str}"

            print(f"Twikit login error: {error_type}: {e}")
            return False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    def search_tweets(self, query: str, count: int = 20,
                      since_date: str = None) -> list[dict]:
        """Search tweets. Returns list of tweet dicts."""
        if not self._authenticated:
            return []
        adapted = adapt_query_for_web(query, since_date)
        return _run_async(self._search_async(adapted, count))

    async def _search_async(self, query: str, count: int) -> list[dict]:
        results = []
        try:
            client = self._get_client()
            tweets = await client.search_tweet(query, 'Latest', count=count)
            for tweet in tweets:
                results.append(self._tweet_to_dict(tweet))
        except Exception as e:
            print(f"Twikit search error: {e}")
        return results

    def get_user_tweets(self, username: str, count: int = 10) -> list[dict]:
        """Get recent tweets from a user. Returns list of tweet dicts."""
        if not self._authenticated:
            return []
        return _run_async(self._user_tweets_async(username, count))

    async def _user_tweets_async(self, username: str, count: int) -> list[dict]:
        results = []
        try:
            client = self._get_client()
            user = await client.get_user_by_screen_name(username)
            if not user:
                return results

            tweets = await client.get_user_tweets(user.id, 'Tweets', count=count)
            for tweet in tweets:
                d = self._tweet_to_dict(tweet)
                d['author_name'] = user.name or username
                d['author_username'] = user.screen_name or username
                d['author_profile_image'] = getattr(user, 'profile_image_url', '') or ''
                results.append(d)
        except Exception as e:
            print(f"Twikit user tweets error ({username}): {e}")
        return results

    def _tweet_to_dict(self, tweet) -> dict:
        """Convert a twikit Tweet object to a standardized dict."""
        # Parse datetime
        created_at = None
        try:
            created_at = tweet.created_at_datetime
        except Exception:
            pass

        if not created_at:
            try:
                created_at = datetime.datetime.strptime(
                    tweet.created_at, "%a %b %d %H:%M:%S %z %Y"
                )
            except Exception:
                created_at = datetime.datetime.now(datetime.timezone.utc)

        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=datetime.timezone.utc)

        # User info
        user = getattr(tweet, 'user', None)

        # Media URLs
        media_urls = []
        for m in (getattr(tweet, 'media', None) or []):
            url = getattr(m, 'url', None) or getattr(m, 'media_url_https', None)
            if url:
                media_urls.append(url)

        return {
            'id': str(getattr(tweet, 'id', '')),
            'text': getattr(tweet, 'full_text', '') or getattr(tweet, 'text', ''),
            'author_name': getattr(user, 'name', 'Unknown') if user else 'Unknown',
            'author_username': getattr(user, 'screen_name', 'unknown') if user else 'unknown',
            'author_profile_image': (getattr(user, 'profile_image_url', '') or '') if user else '',
            'created_at': created_at,
            'like_count': getattr(tweet, 'favorite_count', 0) or 0,
            'retweet_count': getattr(tweet, 'retweet_count', 0) or 0,
            'reply_count': getattr(tweet, 'reply_count', 0) or 0,
            'impression_count': getattr(tweet, 'view_count', 0) or 0,
            'media_urls': media_urls,
        }

    def get_user_info(self, username: str) -> dict | None:
        """Get user profile info. Returns dict with user data."""
        if not self._authenticated:
            return None
        return _run_async(self._user_info_async(username))

    async def _user_info_async(self, username: str) -> dict | None:
        try:
            client = self._get_client()
            user = await client.get_user_by_screen_name(username)
            if not user:
                return None

            return {
                "id": str(getattr(user, 'id', '')),
                "name": getattr(user, 'name', ''),
                "username": getattr(user, 'screen_name', username),
                "bio": getattr(user, 'description', ''),
                "followers_count": getattr(user, 'followers_count', 0) or 0,
                "following_count": getattr(user, 'friends_count', 0) or 0,
                "tweet_count": getattr(user, 'statuses_count', 0) or 0,
                "is_blue_verified": getattr(user, 'is_blue_verified', False) or False,
                "profile_image_url": getattr(user, 'profile_image_url', '') or '',
                "profile_banner_url": getattr(user, 'profile_banner_url', '') or '',
            }
        except Exception as e:
            print(f"Twikit user info error ({username}): {e}")
            return None

    def get_user_followers(self, username: str, limit: int = 200,
                           verified_only: bool = False,
                           progress_callback=None) -> list[dict]:
        """
        Get followers of a user. Optionally filter to verified (blue tick) only.
        Returns list of user dicts.
        """
        if not self._authenticated:
            return []
        return _run_async(self._user_followers_async(
            username, limit, verified_only, progress_callback
        ))

    async def _user_followers_async(self, username: str, limit: int,
                                     verified_only: bool,
                                     progress_callback) -> list[dict]:
        results = []
        try:
            client = self._get_client()
            user = await client.get_user_by_screen_name(username)
            if not user:
                return results

            cursor = None
            fetched = 0
            max_pages = (limit // 20) + 1

            for page in range(max_pages):
                if fetched >= limit:
                    break

                if progress_callback:
                    progress_callback(f"@{username} takipçileri çekiliyor... ({fetched}/{limit})")

                try:
                    if cursor:
                        followers = await cursor.next()
                    else:
                        followers = await client.get_user_followers(user.id, count=20)

                    if not followers:
                        break

                    cursor = followers

                    for follower in followers:
                        is_verified = getattr(follower, 'is_blue_verified', False) or False

                        if verified_only and not is_verified:
                            continue

                        results.append({
                            "id": str(getattr(follower, 'id', '')),
                            "name": getattr(follower, 'name', ''),
                            "username": getattr(follower, 'screen_name', ''),
                            "bio": getattr(follower, 'description', '') or '',
                            "followers_count": getattr(follower, 'followers_count', 0) or 0,
                            "following_count": getattr(follower, 'friends_count', 0) or 0,
                            "is_blue_verified": is_verified,
                            "profile_image_url": getattr(follower, 'profile_image_url', '') or '',
                        })
                        fetched += 1

                        if fetched >= limit:
                            break

                except Exception as e:
                    print(f"Followers pagination error: {e}")
                    break

        except Exception as e:
            print(f"Twikit followers error ({username}): {e}")
        return results

    def clear_cookies(self):
        """Remove saved cookies to force re-login."""
        if COOKIES_PATH.exists():
            COOKIES_PATH.unlink()
        self._authenticated = False
