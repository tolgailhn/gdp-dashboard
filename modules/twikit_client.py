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
                 email: str = ""):
        self.username = username
        self.password = password
        self.email = email
        self._client = None
        self._authenticated = False

    def _get_client(self):
        if self._client is None:
            from twikit import Client
            self._client = Client('en-US')
        return self._client

    def authenticate(self) -> bool:
        """Authenticate with Twitter. Returns True on success."""
        return _run_async(self._auth_async())

    async def _auth_async(self) -> bool:
        client = self._get_client()

        # Try loading saved cookies first
        if COOKIES_PATH.exists():
            try:
                client.load_cookies(str(COOKIES_PATH))
                self._authenticated = True
                return True
            except Exception:
                pass

        # Login with credentials
        if not (self.username and self.password):
            return False

        try:
            await client.login(
                auth_info_1=self.username,
                auth_info_2=self.email or self.username,
                password=self.password,
            )
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            client.save_cookies(str(COOKIES_PATH))
            self._authenticated = True
            return True
        except Exception as e:
            print(f"Twikit login error: {e}")
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

    def clear_cookies(self):
        """Remove saved cookies to force re-login."""
        if COOKIES_PATH.exists():
            COOKIES_PATH.unlink()
        self._authenticated = False
