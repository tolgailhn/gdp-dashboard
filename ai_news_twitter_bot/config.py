"""Configuration for the AI News Twitter Bot."""

# RSS feeds for AI/tech news sources
AI_NEWS_FEEDS = [
    # Major tech outlets - AI sections
    "https://feeds.feedburner.com/TechCrunch/",
    "https://venturebeat.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    # AI-focused sources
    "https://www.artificialintelligence-news.com/feed/",
    "https://aiweekly.co/issues.rss",
    "https://importai.net/feed",
    # Research
    "https://openai.com/news/rss.xml",
    "https://www.deepmind.com/blog/rss.xml",
    "https://huggingface.co/blog/feed.xml",
]

# Keywords that signal an article is AI-related
AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "large language model", "llm", "gpt", "claude", "gemini",
    "openai", "anthropic", "google deepmind", "meta ai",
    "neural network", "generative ai", "ai model", "ai agent",
    "chatgpt", "mistral", "llama", "diffusion model",
    "multimodal", "transformer", "fine-tuning", "rag",
    "autonomous ai", "ai safety", "alignment", "agi",
]

# How many top articles to select and tweet about
TOP_N_ARTICLES = 3

# Tolga İlhan persona for Claude prompt
TOLGA_ILHAN_PERSONA = """
Sen Tolga İlhan'sın. Türk teknoloji dünyasının önde gelen isimlerinden biri olarak:

- Yapay zeka ve teknoloji gelişmelerini takip ediyorsun
- Okuyanı düşündüren, sorgulayan bir üslubun var
- Hem teknik hem de felsefi bir perspektiften bakıyorsun
- Türk okuyucuya hitap ediyorsun ama global trendlere hakimsin
- Zaman zaman ironik ve meraklı bir ton kullanıyorsun
- "Bence", "ilginç olan şu ki", "şunu söylemek lazım" gibi kişisel ifadeler kullanıyorsun
- Tweet'lerin sonu bazen soru işaretiyle ya da düşündürücü bir cümleyle bitiyor
- Emoji kullanımın ölçülü ama etkili (🤖, 🧠, 🚀, 🤔, ⚡ gibi)
- Türkçe yazıyorsun, teknik terimler gerektiğinde orijinal haliyle kalabilir
"""
