"""
Twikit Client Module
Sync wrapper for twikit's async API for free Twitter search operations.
Uses cookie-based auth to avoid Twitter API costs.

Async strategy: A single event loop is reused across calls. Each call
runs in a fresh thread via loop.run_until_complete() so that asyncio
is properly detected by sniffio/httpx. A threading lock ensures only
one call uses the loop at a time. The loop is never closed, so twikit's
internal httpx sessions remain valid across calls.
"""
import asyncio
import builtins
import contextlib
import datetime
import re
import threading
from pathlib import Path

LOGIN_TIMEOUT = 30  # seconds — login hangs if Twitter asks for interactive input

DATA_DIR = Path(__file__).parent.parent / "data"
COOKIES_PATH = DATA_DIR / "twikit_cookies.json"


def _safe_int(val) -> int:
    """Safely convert a value to int (twikit sometimes returns strings)."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


class _AsyncRunner:
    """Run async coroutines from sync code without nest_asyncio.

    A single daemon thread owns the event loop and ALL async work happens
    there — Client creation, HTTP requests, everything. This ensures
    httpx's internal connection pools and twikit's state stay in one
    thread. sniffio.thread_local.name is set once in the daemon thread
    so httpx can always detect asyncio.
    """

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait()  # Wait until loop is running

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        # Set sniffio thread_local ONCE for this thread — all coroutines
        # run here, so sniffio will always detect asyncio.
        try:
            import sniffio
            sniffio.thread_local.name = "asyncio"
        except Exception:
            pass
        self._ready.set()
        self._loop.run_forever()

    def run(self, coro, timeout=120):
        """Submit a coroutine to the daemon thread's loop and wait."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)


# Module-level runner shared by all TwikitSearchClient instances
_runner = _AsyncRunner()


def adapt_query_for_web(query: str, since_date: str = None) -> str:
    """Adapt Twitter API v2 search operators to web search format."""
    q = query.replace("-is:retweet", "-filter:retweets")
    q = q.replace("-is:reply", "-filter:replies")
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

    def _run(self, coro, timeout=120):
        """Run an async coroutine in the persistent event loop thread."""
        return _runner.run(coro, timeout=timeout)

    async def _get_client(self):
        """Get or create twikit Client INSIDE the daemon thread.

        Client and its httpx.AsyncClient must live in the same thread
        as the event loop to avoid weak reference / connection errors.
        """
        if self._client is None:
            from twikit import Client
            self._client = Client('tr')
        else:
            # Verify internal httpx client is still alive
            # If it's None or garbage collected, recreate the client
            try:
                http = getattr(self._client, 'http', None) or getattr(self._client, '_session', None)
                if http is None:
                    from twikit import Client
                    self._client = Client('tr')
            except (TypeError, ReferenceError):
                from twikit import Client
                self._client = Client('tr')
        return self._client

    def authenticate(self) -> bool:
        """Authenticate with Twitter. Returns True on success."""
        return self._run(self._auth_async())

    class _InputBlockedError(Exception):
        """Raised when twikit's login() calls input() for interactive verification."""
        pass

    @staticmethod
    @contextlib.contextmanager
    def _block_input():
        """Temporarily replace builtins.input so that twikit login cannot hang.

        twikit calls input('>>> ') when Twitter asks for interactive
        verification (LoginAcid) or 2FA without a TOTP secret. In a
        Streamlit context there is no stdin, so the call blocks forever.
        This context manager makes input() raise immediately with a
        descriptive error instead.
        """
        original_input = builtins.input

        def _raise_on_input(prompt=""):
            raise TwikitSearchClient._InputBlockedError(
                f"Twitter interaktif doğrulama istiyor (prompt: {prompt!r}). "
                "Streamlit ortamında stdin olmadığı için giriş yapılamaz."
            )

        builtins.input = _raise_on_input
        try:
            yield
        finally:
            builtins.input = original_input

    async def _auth_async(self) -> bool:
        client = await self._get_client()
        self.last_error = ""

        # 1. Try cookies from st.secrets (persistent on Streamlit Cloud)
        try:
            import streamlit as _st
            secret_auth = _st.secrets.get("twikit_auth_token", "")
            secret_ct0 = _st.secrets.get("twikit_ct0", "")
            if secret_auth and secret_ct0:
                client.set_cookies({
                    "auth_token": secret_auth,
                    "ct0": secret_ct0,
                })
                self._authenticated = True
                return True
        except Exception:
            pass

        # 2. Try loading saved cookies via twikit's cookies_file param
        #    (will be loaded automatically by login() if file exists)
        #    But also try manual load for cookie-only auth (no credentials)
        if COOKIES_PATH.exists():
            try:
                client.load_cookies(str(COOKIES_PATH))
                self._authenticated = True
                return True
            except Exception as e:
                self.last_error = f"Cookie yükleme hatası: {e}"
                try:
                    COOKIES_PATH.unlink()
                except Exception:
                    pass

        # 3. Login with credentials
        if not (self.username and self.password):
            self.last_error = "Kullanıcı adı ve şifre gerekli"
            return False

        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            login_kwargs = {
                "auth_info_1": self.username,
                "auth_info_2": self.email or self.username,
                "password": self.password,
                "enable_ui_metrics": False,  # js2py not installed, avoid hang
                "cookies_file": str(COOKIES_PATH),  # auto-save on success
            }

            # Add TOTP for 2FA if provided
            if self.totp_secret:
                login_kwargs["totp_secret"] = self.totp_secret

            # Block input() AND enforce timeout to prevent infinite hangs
            with self._block_input():
                await asyncio.wait_for(
                    client.login(**login_kwargs),
                    timeout=LOGIN_TIMEOUT,
                )

            self._authenticated = True
            return True

        except TwikitSearchClient._InputBlockedError as e:
            # Twitter asked for interactive verification
            error_str = str(e)
            if "2fa" in error_str.lower() or "totp" in error_str.lower():
                self.last_error = (
                    "İki faktörlü doğrulama (2FA) gerekli! "
                    "Ayarlar'da TOTP secret girin veya "
                    "Twitter'dan geçici olarak 2FA'yı kapatın."
                )
            else:
                self.last_error = (
                    "Twitter ek doğrulama istiyor (e-posta/telefon onayı). "
                    "Önce twitter.com'dan tarayıcıyla giriş yapıp doğrulamayı tamamlayın, "
                    "sonra tekrar deneyin."
                )
            print(f"Twikit login blocked (interactive input): {e}")
            return False

        except asyncio.TimeoutError:
            self.last_error = (
                f"Twitter giriş {LOGIN_TIMEOUT} saniyede tamamlanamadı (timeout). "
                "Twitter sunucuları yavaş olabilir veya hesap doğrulama bekliyor olabilir. "
                "twitter.com'dan giriş yapıp hesabı kontrol edin."
            )
            print(f"Twikit login timeout ({LOGIN_TIMEOUT}s)")
            return False

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
                    "Ayarlar'da TOTP secret girin "
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
        return self._run(self._search_async(adapted, count))

    async def _search_async(self, query: str, count: int) -> list[dict]:
        results = []
        try:
            client = await self._get_client()
            tweets = await client.search_tweet(query, 'Latest', count=count)
            for tweet in tweets:
                results.append(self._tweet_to_dict(tweet))
        except Exception as e:
            err_name = type(e).__name__
            # 404/401/TypeError usually means cookies expired or client broken — try re-auth once
            retryable = ("NotFound", "Unauthorized", "TypeError",
                         "ReferenceError", "AttributeError")
            if err_name in retryable and self.username and self.password:
                print(f"Twikit search {err_name}, attempting client reset + re-auth...")
                self._authenticated = False
                self._client = None  # Reset client completely
                if await self._auth_async():
                    try:
                        client = await self._get_client()
                        tweets = await client.search_tweet(query, 'Latest', count=count)
                        for tweet in tweets:
                            results.append(self._tweet_to_dict(tweet))
                        return results
                    except Exception as e2:
                        self.last_error = f"Yeniden deneme hatası: {type(e2).__name__}: {e2}"
                else:
                    self.last_error = f"Cookie'ler geçersiz, yeniden giriş başarısız: {self.last_error}"
            else:
                self.last_error = f"Arama hatası: {err_name}: {e}"
            print(f"Twikit search error: {e}")
        return results

    def get_user_tweets(self, username: str, count: int = 10,
                        progress_callback=None) -> list[dict]:
        """Get recent tweets from a user with pagination. Returns list of tweet dicts."""
        if not self._authenticated:
            return []
        return self._run(self._user_tweets_async(username, count, progress_callback))

    async def _user_tweets_async(self, username: str, count: int,
                                  progress_callback=None) -> list[dict]:
        results = []
        try:
            client = await self._get_client()
            user = await client.get_user_by_screen_name(username)
            if not user:
                self.last_error = f"@{username} kullanıcısı bulunamadı"
                return results

            cursor = None
            seen_ids = set()
            max_pages = (count // 20) + 2  # Safety limit

            for page in range(max_pages):
                if len(results) >= count:
                    break

                if progress_callback:
                    progress_callback(
                        f"@{username}: {len(results)}/{count} tweet çekiliyor... (sayfa {page + 1})"
                    )

                try:
                    if cursor:
                        tweets = await cursor.next()
                    else:
                        tweets = await client.get_user_tweets(
                            user.id, 'Tweets', count=min(count, 20)
                        )

                    if not tweets:
                        break

                    cursor = tweets
                    new_count = 0

                    for tweet in tweets:
                        tweet_id = str(getattr(tweet, 'id', ''))
                        if tweet_id in seen_ids:
                            continue
                        seen_ids.add(tweet_id)

                        d = self._tweet_to_dict(tweet)
                        d['author_name'] = user.name or username
                        d['author_username'] = user.screen_name or username
                        d['author_profile_image'] = getattr(user, 'profile_image_url', '') or ''
                        results.append(d)
                        new_count += 1

                        if len(results) >= count:
                            break

                    # No new tweets found, stop paginating
                    if new_count == 0:
                        break

                except Exception as page_err:
                    err_name = type(page_err).__name__
                    if err_name in ("StopIteration", "StopAsyncIteration"):
                        break  # No more pages
                    print(f"Twikit pagination error (page {page + 1}): {page_err}")
                    self.last_error = f"Sayfa {page + 1} hatası: {err_name}: {page_err}"
                    break

        except Exception as e:
            err_name = type(e).__name__
            self.last_error = f"Kullanıcı tweet hatası (@{username}): {err_name}: {e}"
            print(f"Twikit user tweets error ({username}): {err_name}: {e}")

            # 401/404/TypeError usually means cookies expired or client broken — try re-auth once
            retryable = ("NotFound", "Unauthorized", "Forbidden",
                         "TwitterException", "TypeError", "ReferenceError",
                         "AttributeError")
            if err_name in retryable and self.username and self.password:
                print(f"Twikit user tweets {err_name}, attempting client reset + re-auth...")
                self._authenticated = False
                self._client = None  # Reset client completely
                if await self._auth_async():
                    try:
                        return await self._user_tweets_async(username, count, progress_callback)
                    except Exception as e2:
                        self.last_error = f"Yeniden deneme hatası: {type(e2).__name__}: {e2}"
                else:
                    self.last_error = f"Cookie'ler geçersiz, yeniden giriş başarısız: {self.last_error}"

        return results

    def _tweet_to_dict(self, tweet) -> dict:
        """Convert a twikit Tweet object to a standardized dict."""
        # Parse datetime — try property first, then standard Twitter format
        created_at = None
        try:
            created_at = tweet.created_at_datetime
        except Exception:
            raw_date = getattr(tweet, 'created_at', None)
            if raw_date and isinstance(raw_date, str):
                for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%fZ"):
                    try:
                        created_at = datetime.datetime.strptime(raw_date, fmt)
                        break
                    except ValueError:
                        continue
        if not created_at:
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
            'text': (getattr(tweet, 'full_text', '')
                     or getattr(tweet, 'text', '')
                     or ''),
            'author_name': getattr(user, 'name', 'Unknown') if user else 'Unknown',
            'author_username': getattr(user, 'screen_name', 'unknown') if user else 'unknown',
            'author_profile_image': (getattr(user, 'profile_image_url', '') or '') if user else '',
            'author_followers_count': _safe_int(getattr(user, 'followers_count', 0)) if user else 0,
            'created_at': created_at,
            'like_count': _safe_int(getattr(tweet, 'favorite_count', 0)),
            'retweet_count': _safe_int(getattr(tweet, 'retweet_count', 0)),
            'reply_count': _safe_int(getattr(tweet, 'reply_count', 0)),
            'impression_count': _safe_int(getattr(tweet, 'view_count', 0)),
            'media_urls': media_urls,
        }

    def get_user_info(self, username: str) -> dict | None:
        """Get user profile info. Returns dict with user data."""
        if not self._authenticated:
            return None
        return self._run(self._user_info_async(username))

    async def _user_info_async(self, username: str) -> dict | None:
        try:
            client = await self._get_client()
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
            self.last_error = f"Kullanıcı bilgi hatası (@{username}): {type(e).__name__}: {e}"
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
        return self._run(self._user_followers_async(
            username, limit, verified_only, progress_callback
        ))

    async def _user_followers_async(self, username: str, limit: int,
                                     verified_only: bool,
                                     progress_callback) -> list[dict]:
        results = []
        try:
            client = await self._get_client()
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
        self._client = None  # Also reset client to force fresh start
