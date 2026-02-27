"""
Twitter/X AI Topic Scanner Module
Scans X for AI developments using Twitter API v2
"""
import tweepy
import datetime
import json
import re
from dataclasses import dataclass, field


@dataclass
class AITopic:
    """Represents a discovered AI topic/development from X"""
    id: str
    text: str
    author_name: str
    author_username: str
    author_profile_image: str
    created_at: datetime.datetime
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    impression_count: int = 0
    url: str = ""
    category: str = "Genel"
    relevance_score: float = 0.0
    media_urls: list = field(default_factory=list)

    @property
    def engagement_score(self) -> float:
        return (self.like_count * 1 + self.retweet_count * 2 +
                self.reply_count * 1.5)

    @property
    def time_ago(self) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - self.created_at
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)} dk önce"
        elif hours < 24:
            return f"{int(hours)} saat önce"
        else:
            return f"{int(hours / 24)} gün önce"


# Default important AI accounts to monitor
DEFAULT_AI_ACCOUNTS = [
    "OpenAI", "AnthropicAI", "GoogleDeepMind", "xaborai", "MetaAI",
    "MistralAI", "Aborai", "huggingface", "nvidia", "GoogleAI",
    "ylaboratory", "stabilityai", "midaborni", "RunwayML",
    "peraborlexity_ai", "sama", "elaboronmusk", "karpaborathy",
    "ylaborecun", "demisaborrhassabis", "aaborimasad", "daborarioamodei",
    "jimfan_ai", "alexaborialbert", "emadabormost", "ClaboremenDelangue",
    "hardmaru", "aborbor_gaborurib", "swyx", "bindureddy",
    "Qwen_LM", "aliaborbabagroup"
]

# AI-related search queries
AI_SEARCH_QUERIES = [
    "(new model OR new AI OR AI release OR LLM) -is:retweet lang:en",
    "(GPT OR Claude OR Gemini OR Llama OR Qwen OR Mistral) (release OR launch OR update OR new) -is:retweet",
    "(AI breakthrough OR machine learning OR deep learning) (new OR release OR paper) -is:retweet",
    "(artificial intelligence OR neural network) (announcement OR launched OR introducing) -is:retweet",
    "(AGI OR transformer OR diffusion model OR multimodal) (new OR update OR release) -is:retweet",
    "(AI agent OR AI tool OR AI startup) (launch OR release OR announce) -is:retweet",
    "(benchmark OR SOTA OR state-of-the-art) (AI OR model OR LLM) -is:retweet",
    "(open source OR open-source) (model OR AI OR LLM) (release OR new) -is:retweet",
]

# Spam/irrelevant patterns to filter out
SPAM_PATTERNS = [
    r"(?i)(giveaway|airdrop|free money|click here|dm me|follow back)",
    r"(?i)(crypto pump|moon soon|100x|nft mint)",
    r"(?i)(good morning|gm everyone|hello world|hi everyone)",
    r"(?i)(follow me|like and retweet|rt to win)",
    r"(?i)(affordable|cheap|discount|promo code|coupon)",
    r"(?i)(join my|subscribe to my|check my link)",
    # Promotional / corporate fluff
    r"(?i)(thank you for|teşekkür ederiz|uzun süredir|proud to announce|excited to share|thrilled to)",
    r"(?i)(we('re| are) hiring|job opening|apply now|join our team|career opportunity)",
    r"(?i)(happy birthday|congratulations|congrats to|shout ?out to)",
    r"(?i)(don'?t miss|register now|sign up today|limited time|early bird|save \d+%)",
    r"(?i)(webinar|workshop|meetup|conference|event|live stream).*?(register|join|sign up|link in bio)",
    r"(?i)(check out our|read our latest|our new blog|new blog post|read more at)",
    # Low-quality engagement bait
    r"(?i)^(agree|disagree|thoughts|this|wow|amazing|incredible|game.?changer)[.!?]?$",
    r"(?i)(retweet if|like if|who else|raise your hand|tag someone)",
    r"(?i)(alpha leak|insider info|you won'?t believe|secret.{0,10}reveal)",
]

# Minimum content quality thresholds
MIN_TWEET_LENGTH = 50  # Skip very short tweets


# Category keywords for classification
CATEGORY_KEYWORDS = {
    "Yeni Model": ["new model", "release", "launch", "introducing", "announce", "unveiled"],
    "Model Güncelleme": ["update", "upgrade", "improved", "v2", "v3", "v4", "new version", "patch"],
    "Araştırma": ["paper", "research", "study", "findings", "arxiv", "published"],
    "Benchmark": ["benchmark", "SOTA", "state-of-the-art", "outperforms", "beats", "score"],
    "Açık Kaynak": ["open source", "open-source", "github", "huggingface", "weights released"],
    "API/Platform": ["API", "platform", "developer", "SDK", "endpoint", "pricing"],
    "AI Ajanlar": ["agent", "agentic", "autonomous", "tool use", "function calling"],
    "Görüntü/Video": ["image", "video", "diffusion", "generation", "Sora", "DALL-E", "Midjourney"],
    "Endüstri": ["acquisition", "funding", "partnership", "billion", "valuation", "IPO"],
}


def is_spam(text: str) -> bool:
    """Check if a tweet is likely spam or irrelevant"""
    # Too short to be meaningful AI content
    if len(text.strip()) < MIN_TWEET_LENGTH:
        return True

    # Pattern-based filtering
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text):
            return True

    # Link-only tweets (just a URL with minimal text)
    text_no_urls = re.sub(r'https?://\S+', '', text).strip()
    if len(text_no_urls) < 30:
        return True

    return False


def categorize_topic(text: str) -> str:
    """Categorize a tweet into an AI topic category"""
    text_lower = text.lower()
    best_category = "Genel"
    best_score = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category


def calculate_relevance(topic: AITopic, time_range_hours: int) -> float:
    """Calculate relevance score based on engagement, recency, and content"""
    # Engagement component (0-40 points)
    engagement = min(40, (topic.engagement_score / 100) * 40)

    # Recency component (0-30 points)
    now = datetime.datetime.now(datetime.timezone.utc)
    hours_old = (now - topic.created_at).total_seconds() / 3600
    recency = max(0, 30 * (1 - hours_old / time_range_hours))

    # Content quality component (0-30 points)
    text = topic.text
    quality = 0
    if len(text) > 100:
        quality += 10
    if any(kw in text.lower() for cat_kws in CATEGORY_KEYWORDS.values() for kw in cat_kws):
        quality += 10
    if "http" in text or "pic.twitter" in text:
        quality += 5
    if topic.author_username.lower() in [a.lower() for a in DEFAULT_AI_ACCOUNTS]:
        quality += 5

    return engagement + recency + quality


class TwitterScanner:
    """Main scanner class for finding AI topics on X/Twitter"""

    def __init__(self, bearer_token: str = None, api_key: str = None,
                 api_secret: str = None, access_token: str = None,
                 access_secret: str = None):
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Twitter API client"""
        if self.bearer_token:
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
                wait_on_rate_limit=True
            )

    def scan_ai_topics(self, time_range_hours: int = 24,
                       max_results_per_query: int = 20,
                       custom_accounts: list = None,
                       custom_queries: list = None) -> list[AITopic]:
        """
        Scan X for AI-related topics and developments

        Args:
            time_range_hours: How far back to search (6, 12, or 24 hours)
            max_results_per_query: Max tweets per search query
            custom_accounts: Additional accounts to monitor
            custom_queries: Additional search queries

        Returns:
            List of AITopic objects sorted by relevance
        """
        if not self.client:
            raise ValueError("Twitter API client not initialized. Check your API keys.")

        all_topics = []
        seen_ids = set()

        start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=time_range_hours)

        # Search queries
        queries = AI_SEARCH_QUERIES.copy()
        if custom_queries:
            queries.extend(custom_queries)

        # Search by queries
        for query in queries:
            try:
                topics = self._search_tweets(query, start_time, max_results_per_query)
                for topic in topics:
                    if topic.id not in seen_ids:
                        seen_ids.add(topic.id)
                        all_topics.append(topic)
            except Exception as e:
                print(f"Query error: {query} - {e}")
                continue

        # Search by monitored accounts
        accounts = list(DEFAULT_AI_ACCOUNTS)
        if custom_accounts:
            accounts.extend(custom_accounts)

        for account in accounts:
            try:
                topics = self._get_user_tweets(account, start_time, 10)
                for topic in topics:
                    if topic.id not in seen_ids:
                        seen_ids.add(topic.id)
                        all_topics.append(topic)
            except Exception as e:
                print(f"Account error: {account} - {e}")
                continue

        # Filter spam and calculate relevance
        filtered_topics = []
        for topic in all_topics:
            if not is_spam(topic.text):
                topic.category = categorize_topic(topic.text)
                topic.relevance_score = calculate_relevance(topic, time_range_hours)
                filtered_topics.append(topic)

        # Sort by relevance score
        filtered_topics.sort(key=lambda t: t.relevance_score, reverse=True)

        return filtered_topics

    def _search_tweets(self, query: str, start_time: datetime.datetime,
                       max_results: int) -> list[AITopic]:
        """Search tweets using Twitter API v2"""
        topics = []

        try:
            response = self.client.search_recent_tweets(
                query=query,
                start_time=start_time,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics", "author_id", "entities"],
                user_fields=["name", "username", "profile_image_url"],
                media_fields=["url", "preview_image_url"],
                expansions=["author_id", "attachments.media_keys"]
            )

            if not response.data:
                return topics

            # Build user lookup
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = user

            # Build media lookup
            media = {}
            if response.includes and "media" in response.includes:
                for m in response.includes["media"]:
                    media[m.media_key] = m

            for tweet in response.data:
                author = users.get(tweet.author_id)
                if not author:
                    continue

                # Get media URLs
                media_urls = []
                if tweet.data.get("attachments", {}).get("media_keys"):
                    for mk in tweet.data["attachments"]["media_keys"]:
                        if mk in media:
                            m = media[mk]
                            url = getattr(m, 'url', None) or getattr(m, 'preview_image_url', None)
                            if url:
                                media_urls.append(url)

                metrics = tweet.public_metrics or {}

                topic = AITopic(
                    id=str(tweet.id),
                    text=tweet.text,
                    author_name=author.name,
                    author_username=author.username,
                    author_profile_image=getattr(author, 'profile_image_url', ''),
                    created_at=tweet.created_at,
                    like_count=metrics.get("like_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    reply_count=metrics.get("reply_count", 0),
                    impression_count=metrics.get("impression_count", 0),
                    url=f"https://x.com/{author.username}/status/{tweet.id}",
                    media_urls=media_urls,
                )
                topics.append(topic)

        except tweepy.TooManyRequests:
            print("Rate limit reached, waiting...")
        except Exception as e:
            print(f"Search error: {e}")

        return topics

    def _get_user_tweets(self, username: str, start_time: datetime.datetime,
                         max_results: int) -> list[AITopic]:
        """Get recent tweets from a specific user"""
        topics = []

        try:
            # Get user ID first
            user = self.client.get_user(username=username,
                                        user_fields=["profile_image_url"])
            if not user.data:
                return topics

            user_data = user.data

            response = self.client.get_users_tweets(
                id=user_data.id,
                start_time=start_time,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics", "entities"],
                exclude=["retweets", "replies"]
            )

            if not response.data:
                return topics

            for tweet in response.data:
                metrics = tweet.public_metrics or {}

                topic = AITopic(
                    id=str(tweet.id),
                    text=tweet.text,
                    author_name=user_data.name,
                    author_username=user_data.username,
                    author_profile_image=getattr(user_data, 'profile_image_url', ''),
                    created_at=tweet.created_at,
                    like_count=metrics.get("like_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    reply_count=metrics.get("reply_count", 0),
                    impression_count=metrics.get("impression_count", 0),
                    url=f"https://x.com/{user_data.username}/status/{tweet.id}",
                )
                topics.append(topic)

        except Exception as e:
            print(f"User tweets error ({username}): {e}")

        return topics

    def get_tweet_by_id(self, tweet_id: str) -> AITopic | None:
        """Fetch a specific tweet by its ID"""
        try:
            response = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=["created_at", "public_metrics", "author_id"],
                user_fields=["name", "username", "profile_image_url"],
                expansions=["author_id"]
            )

            if not response.data:
                return None

            tweet = response.data
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = user

            author = users.get(tweet.author_id)
            metrics = tweet.public_metrics or {}

            return AITopic(
                id=str(tweet.id),
                text=tweet.text,
                author_name=author.name if author else "Unknown",
                author_username=author.username if author else "unknown",
                author_profile_image=getattr(author, 'profile_image_url', '') if author else '',
                created_at=tweet.created_at,
                like_count=metrics.get("like_count", 0),
                retweet_count=metrics.get("retweet_count", 0),
                reply_count=metrics.get("reply_count", 0),
                impression_count=metrics.get("impression_count", 0),
                url=f"https://x.com/{author.username if author else 'unknown'}/status/{tweet.id}",
            )
        except Exception as e:
            print(f"Get tweet error: {e}")
            return None
