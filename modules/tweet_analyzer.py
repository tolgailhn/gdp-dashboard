"""
Tweet Analyzer Module
Pulls tweets from any account via Twikit and analyzes engagement patterns.
Used to "train" AI (in-context learning) with real high-performing tweet data.
"""
import json
import datetime
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
ANALYSES_DIR = DATA_DIR / "tweet_analyses"


def _safe_int(val) -> int:
    """Safely convert a value to int (twikit sometimes returns strings)."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def pull_user_tweets(twikit_client, username: str, count: int = 500,
                     progress_callback=None) -> list[dict]:
    """
    Pull last N tweets from a user via Twikit with full pagination.
    Returns list of tweet dicts with engagement data.
    """
    if not twikit_client or not twikit_client.is_authenticated:
        raise ValueError("Twikit client not authenticated")

    tweets = twikit_client.get_user_tweets(
        username, count=count, progress_callback=progress_callback
    )

    if progress_callback:
        progress_callback(f"@{username}: {len(tweets)} tweet çekildi. Analiz yapılıyor...")

    return tweets


def calculate_engagement_score(tweet: dict) -> float:
    """
    Calculate weighted engagement score based on X algorithm weights.
    RT = 20x, Reply = 13.5x, Like = 1x, Bookmark ≈ 10x
    """
    rt = _safe_int(tweet.get("retweet_count", 0))
    reply = _safe_int(tweet.get("reply_count", 0))
    like = _safe_int(tweet.get("like_count", 0))
    impressions = _safe_int(tweet.get("impression_count", 0))

    score = (rt * 20) + (reply * 13.5) + (like * 1)

    # Engagement rate bonus (if impressions available)
    if impressions > 0:
        engagement_rate = (rt + reply + like) / impressions
        score *= (1 + engagement_rate)

    return round(score, 2)


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from tweet text."""
    # Remove URLs, mentions, hashtags for keyword extraction
    clean = re.sub(r'https?://\S+', '', text)
    clean = re.sub(r'@\w+', '', clean)
    clean = re.sub(r'#(\w+)', r'\1', clean)  # Keep hashtag words
    clean = re.sub(r'[^\w\s]', ' ', clean)

    # Turkish + English stop words
    stop_words = {
        'bir', 'bu', 'da', 'de', 've', 'ile', 'için', 'var', 'yok', 'ama',
        'çok', 'daha', 'en', 'gibi', 'ben', 'sen', 'biz', 'siz', 'onlar',
        'ne', 'nasıl', 'neden', 'kadar', 'olan', 'olan', 'olarak', 'sonra',
        'the', 'is', 'at', 'in', 'on', 'and', 'or', 'to', 'a', 'an', 'of',
        'for', 'it', 'this', 'that', 'with', 'are', 'was', 'be', 'has',
        'have', 'from', 'by', 'not', 'but', 'its', 'they', 'their', 'you',
        'we', 'can', 'all', 'will', 'just', 'been', 'than', 'more', 'so',
        'şu', 'her', 'hem', 'mi', 'mı', 'mu', 'mü', 'ki', 'ya',
        'diyor', 'olan', 'oldu', 'olur', 'olmuş', 'olan', 'ise', 'bunu',
    }

    words = clean.lower().split()
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    return keywords


def analyze_tweets(tweets: list[dict]) -> dict:
    """
    Full engagement analysis of pulled tweets.
    Returns structured analysis data.
    Saves ALL tweet texts (originals separated from RTs) for style training.
    """
    if not tweets:
        return {"error": "No tweets to analyze"}

    # Calculate engagement scores
    for tweet in tweets:
        tweet["engagement_score"] = calculate_engagement_score(tweet)

    # Separate original tweets from retweets
    original_tweets = []
    retweet_tweets = []
    for t in tweets:
        text = t.get("text", "")
        tweet_data = {
            "text": text,
            "engagement_score": t["engagement_score"],
            "like_count": t.get("like_count", 0),
            "retweet_count": t.get("retweet_count", 0),
            "reply_count": t.get("reply_count", 0),
            "impression_count": t.get("impression_count", 0),
            "created_at": str(t.get("created_at", "")),
        }
        if text.startswith("RT @"):
            retweet_tweets.append(tweet_data)
        else:
            original_tweets.append(tweet_data)

    # Sort by engagement score
    sorted_tweets = sorted(tweets, key=lambda t: t["engagement_score"], reverse=True)
    sorted_originals = sorted(original_tweets, key=lambda t: t["engagement_score"], reverse=True)

    # Top performing tweets (backwards compatible)
    top_tweets = []
    for t in sorted_tweets[:30]:
        top_tweets.append({
            "text": t.get("text", ""),
            "engagement_score": t["engagement_score"],
            "like_count": t.get("like_count", 0),
            "retweet_count": t.get("retweet_count", 0),
            "reply_count": t.get("reply_count", 0),
            "impression_count": t.get("impression_count", 0),
            "created_at": str(t.get("created_at", "")),
        })

    # Keyword-engagement correlation
    keyword_engagement = {}
    keyword_count = Counter()
    all_keywords = []

    for tweet in tweets:
        keywords = extract_keywords(tweet.get("text", ""))
        score = tweet["engagement_score"]
        all_keywords.extend(keywords)

        for kw in set(keywords):  # unique per tweet
            if kw not in keyword_engagement:
                keyword_engagement[kw] = {"total_score": 0, "count": 0}
            keyword_engagement[kw]["total_score"] += score
            keyword_engagement[kw]["count"] += 1
            keyword_count[kw] += 1

    # Average engagement per keyword
    keyword_avg = {}
    for kw, data in keyword_engagement.items():
        if data["count"] >= 3:  # At least 3 tweets with this keyword
            keyword_avg[kw] = round(data["total_score"] / data["count"], 2)

    # Sort by average engagement
    top_keywords = sorted(keyword_avg.items(), key=lambda x: x[1], reverse=True)[:30]
    most_used = keyword_count.most_common(30)

    # Tweet length analysis
    short_tweets = [t for t in tweets if len(t.get("text", "")) <= 280]
    medium_tweets = [t for t in tweets if 280 < len(t.get("text", "")) <= 500]
    long_tweets = [t for t in tweets if len(t.get("text", "")) > 500]

    def avg_score(tweet_list):
        if not tweet_list:
            return 0
        return round(sum(t["engagement_score"] for t in tweet_list) / len(tweet_list), 2)

    length_analysis = {
        "short": {"count": len(short_tweets), "avg_score": avg_score(short_tweets)},
        "medium": {"count": len(medium_tweets), "avg_score": avg_score(medium_tweets)},
        "long": {"count": len(long_tweets), "avg_score": avg_score(long_tweets)},
    }

    # Question vs statement analysis
    question_tweets = [t for t in tweets if "?" in t.get("text", "")]
    statement_tweets = [t for t in tweets if "?" not in t.get("text", "")]

    question_analysis = {
        "question_tweets": {"count": len(question_tweets), "avg_score": avg_score(question_tweets)},
        "statement_tweets": {"count": len(statement_tweets), "avg_score": avg_score(statement_tweets)},
    }

    # Hashtag analysis
    hashtag_engagement = {}
    for tweet in tweets:
        hashtags = re.findall(r'#(\w+)', tweet.get("text", ""))
        score = tweet["engagement_score"]
        for tag in hashtags:
            tag_lower = tag.lower()
            if tag_lower not in hashtag_engagement:
                hashtag_engagement[tag_lower] = {"total_score": 0, "count": 0, "original": tag}
            hashtag_engagement[tag_lower]["total_score"] += score
            hashtag_engagement[tag_lower]["count"] += 1

    top_hashtags = sorted(
        [
            {"tag": f"#{v['original']}", "count": v["count"],
             "avg_score": round(v["total_score"] / v["count"], 2)}
            for v in hashtag_engagement.values()
            if v["count"] >= 2
        ],
        key=lambda x: x["avg_score"], reverse=True
    )[:15]

    # Overall stats
    total_likes = sum(_safe_int(t.get("like_count", 0)) for t in tweets)
    total_rts = sum(_safe_int(t.get("retweet_count", 0)) for t in tweets)
    total_replies = sum(_safe_int(t.get("reply_count", 0)) for t in tweets)
    avg_engagement = avg_score(tweets)

    # Posting time analysis (hour distribution)
    hour_engagement = {}
    for tweet in tweets:
        created = tweet.get("created_at")
        if created and hasattr(created, 'hour'):
            hour = created.hour
            if hour not in hour_engagement:
                hour_engagement[hour] = {"total_score": 0, "count": 0}
            hour_engagement[hour]["total_score"] += tweet["engagement_score"]
            hour_engagement[hour]["count"] += 1

    best_hours = sorted(
        [{"hour": h, "avg_score": round(d["total_score"] / d["count"], 2), "tweet_count": d["count"]}
         for h, d in hour_engagement.items() if d["count"] >= 3],
        key=lambda x: x["avg_score"], reverse=True
    )[:5]

    return {
        "total_tweets": len(tweets),
        "total_likes": total_likes,
        "total_retweets": total_rts,
        "total_replies": total_replies,
        "avg_engagement_score": avg_engagement,
        "top_tweets": top_tweets,
        # ALL tweet texts for comprehensive style training
        "all_original_tweets": sorted_originals,
        "all_retweets": retweet_tweets,
        "original_count": len(original_tweets),
        "retweet_count": len(retweet_tweets),
        "top_keywords": [{"keyword": kw, "avg_score": sc} for kw, sc in top_keywords],
        "most_used_keywords": [{"keyword": kw, "count": cnt} for kw, cnt in most_used],
        "length_analysis": length_analysis,
        "question_analysis": question_analysis,
        "top_hashtags": top_hashtags,
        "best_hours": best_hours,
    }


def generate_ai_analysis(analysis_data: dict, ai_client, ai_model: str,
                          ai_provider: str, username: str) -> str:
    """
    Use AI to generate a human-readable analysis report from the data.
    This report becomes part of the training context for MiniMax.
    """
    top_tweets_text = ""
    for i, t in enumerate(analysis_data.get("top_tweets", [])[:15], 1):
        top_tweets_text += f"\n{i}. [{t['engagement_score']} puan | ❤️{t['like_count']} 🔁{t['retweet_count']} 💬{t['reply_count']}]\n\"{t['text'][:300]}\"\n"

    keywords_text = ", ".join([f"{k['keyword']}({k['avg_score']})" for k in analysis_data.get("top_keywords", [])[:15]])

    length_data = analysis_data.get("length_analysis", {})
    question_data = analysis_data.get("question_analysis", {})

    prompt = f"""@{username} hesabının son {analysis_data['total_tweets']} tweet'ini analiz ettim.

## GENEL İSTATİSTİKLER:
- Toplam: {analysis_data['total_tweets']} tweet
- Toplam Like: {analysis_data['total_likes']:,} | RT: {analysis_data['total_retweets']:,} | Reply: {analysis_data['total_replies']:,}
- Ortalama Engagement Skoru: {analysis_data['avg_engagement_score']}

## EN İYİ PERFORMANS GÖSTEREN TWEET'LER:
{top_tweets_text}

## UZUNLUK ANALİZİ:
- Kısa (≤280): {length_data.get('short', {}).get('count', 0)} tweet, ort. skor: {length_data.get('short', {}).get('avg_score', 0)}
- Orta (281-500): {length_data.get('medium', {}).get('count', 0)} tweet, ort. skor: {length_data.get('medium', {}).get('avg_score', 0)}
- Uzun (>500): {length_data.get('long', {}).get('count', 0)} tweet, ort. skor: {length_data.get('long', {}).get('avg_score', 0)}

## SORU vs BEYANI:
- Soru içeren: {question_data.get('question_tweets', {}).get('count', 0)} tweet, ort. skor: {question_data.get('question_tweets', {}).get('avg_score', 0)}
- Beyan: {question_data.get('statement_tweets', {}).get('count', 0)} tweet, ort. skor: {question_data.get('statement_tweets', {}).get('avg_score', 0)}

## EN ETKİLEŞİM ÇEKEN KELİMELER:
{keywords_text}

---

Bu verilere dayanarak detaylı bir analiz raporu yaz. Şunları kapsamalı:

1. **Genel Yazım Tarzı**: Bu hesap nasıl yazıyor? Ton, dil, yaklaşım
2. **Ne İşe Yarıyor**: Hangi tarz tweet'ler en çok etkileşim alıyor? Neden?
3. **Hook Kalıpları**: En iyi tweet'lerin açılış cümleleri nasıl? Ortak kalıplar neler?
4. **Kelime Stratejisi**: Hangi kelimeler/konular etkileşim çekiyor?
5. **Uzunluk Stratejisi**: Kısa mı uzun mu daha iyi performans gösteriyor?
6. **Soru Kullanımı**: Sorularla biten tweet'ler daha mı iyi?
7. **Tavsiyeler**: Bu hesabın tarzını taklit etmek isteyen biri ne yapmalı?

Raporu Türkçe yaz. Spesifik örnekler ver. Genel klişeler değil, VERİYE DAYALI analiz yap."""

    system = """Sen bir Twitter/X içerik analisti ve strateji uzmanısın.
Tweet verilerini analiz edip, etkileşim kalıplarını tespit ediyorsun.
Raporların veriye dayalı, spesifik ve uygulanabilir olmalı."""

    try:
        if ai_provider == "anthropic":
            response = ai_client.messages.create(
                model=ai_model,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.content[0].text.strip()
        else:
            response = ai_client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
            return text
    except Exception as e:
        return f"AI analiz hatası: {e}"


def save_tweet_analysis(username: str, analysis: dict, ai_report: str = "",
                        session_state=None):
    """Save tweet analysis to JSON file AND session_state (for Streamlit Cloud persistence)."""
    data = {
        "username": username,
        "analyzed_at": datetime.datetime.now().isoformat(),
        "analysis": analysis,
        "ai_report": ai_report,
    }

    # Save to session_state (persists during Streamlit session)
    if session_state is not None:
        if "tweet_analyses" not in session_state:
            session_state["tweet_analyses"] = {}
        session_state["tweet_analyses"][username.lower()] = data

    # Also save to file (persists locally or if committed to repo)
    try:
        ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
        path = ANALYSES_DIR / f"{username.lower()}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass  # File save may fail on read-only systems, session_state is primary


def load_tweet_analysis(username: str, session_state=None) -> dict | None:
    """Load tweet analysis — checks session_state first, then files."""
    # Check session_state first
    if session_state is not None:
        analyses = session_state.get("tweet_analyses", {})
        if username.lower() in analyses:
            return analyses[username.lower()]

    # Fall back to file
    path = ANALYSES_DIR / f"{username.lower()}.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Also populate session_state for future reads
            if session_state is not None:
                if "tweet_analyses" not in session_state:
                    session_state["tweet_analyses"] = {}
                session_state["tweet_analyses"][username.lower()] = data
            return data
        except Exception:
            pass
    return None


def _auto_import_export_files():
    """Auto-import any export JSON files found in data/ folder into tweet_analyses/."""
    imported = 0
    for path in DATA_DIR.glob("tweet_analyses_export*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("type") != "tweet_analyses_export":
                continue
            analyses = data.get("analyses", {})
            if not analyses:
                continue
            ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
            for username, analysis_data in analyses.items():
                dest = ANALYSES_DIR / f"{username.lower()}.json"
                if not dest.exists():
                    with open(dest, "w", encoding="utf-8") as f:
                        json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
                    imported += 1
        except Exception:
            continue
    return imported


def load_all_analyses(session_state=None) -> list[dict]:
    """Load all analyses — merges session_state and file system.
    Also auto-imports any export files found in data/ folder."""
    # Auto-import export files from data/ folder (only writes missing ones)
    _auto_import_export_files()

    analyses_map = {}

    # Load from files first
    if ANALYSES_DIR.exists():
        for path in ANALYSES_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                key = data.get("username", path.stem).lower()
                analyses_map[key] = data
            except Exception:
                continue

    # Overlay with session_state (more recent)
    if session_state is not None:
        for key, data in session_state.get("tweet_analyses", {}).items():
            analyses_map[key] = data

    # Also sync session_state with everything found
    if session_state is not None and analyses_map:
        if "tweet_analyses" not in session_state:
            session_state["tweet_analyses"] = {}
        session_state["tweet_analyses"].update(analyses_map)

    analyses = list(analyses_map.values())
    return sorted(analyses, key=lambda x: x.get("analyzed_at", ""), reverse=True)


def delete_tweet_analysis(username: str, session_state=None) -> bool:
    """Delete a saved analysis from both session_state and file."""
    deleted = False

    # Remove from session_state
    if session_state is not None:
        analyses = session_state.get("tweet_analyses", {})
        if username.lower() in analyses:
            del analyses[username.lower()]
            deleted = True

    # Remove file
    path = ANALYSES_DIR / f"{username.lower()}.json"
    if path.exists():
        try:
            path.unlink()
            deleted = True
        except Exception:
            pass

    return deleted


def export_all_analyses(session_state=None) -> str:
    """Export all analyses as a single JSON string for download."""
    analyses = load_all_analyses(session_state)
    export_data = {
        "type": "tweet_analyses_export",
        "exported_at": datetime.datetime.now().isoformat(),
        "analyses": {a["username"].lower(): a for a in analyses},
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2, default=str)


def import_analyses_from_json(json_str: str, session_state=None) -> int:
    """Import analyses from a JSON string. Returns count of imported analyses."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return 0

    analyses = data.get("analyses", {})
    if not analyses:
        return 0

    count = 0
    for username, analysis_data in analyses.items():
        # Save to session_state
        if session_state is not None:
            if "tweet_analyses" not in session_state:
                session_state["tweet_analyses"] = {}
            session_state["tweet_analyses"][username.lower()] = analysis_data

        # Save to file
        try:
            ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
            path = ANALYSES_DIR / f"{username.lower()}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass

        count += 1

    return count


def _extract_writing_dna(tweets: list[dict]) -> dict:
    """Extract writing style patterns (DNA) from a list of tweets."""
    if not tweets:
        return {}

    texts = [t.get("text", "") for t in tweets if t.get("text", "")]

    # Hook patterns — first lines of tweets
    hooks = []
    for text in texts:
        first_line = text.split("\n")[0].strip()
        if len(first_line) > 15:
            hooks.append(first_line)

    # Common sentence starters
    starters = Counter()
    for text in texts:
        sentences = re.split(r'[.!?\n]+', text)
        for s in sentences:
            s = s.strip()
            if len(s) > 10:
                words = s.split()[:3]
                if words:
                    starters[" ".join(words).lower()] += 1

    # Average paragraph structure
    para_counts = []
    for text in texts:
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        para_counts.append(len(paras))

    avg_paras = sum(para_counts) / len(para_counts) if para_counts else 1

    # Character traits: lowercase preference, emoji usage, question ending
    lowercase_starts = sum(1 for t in texts if t and t[0].islower())
    question_endings = sum(1 for t in texts if t.rstrip().endswith("?"))
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
                               r'\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF]')
    emoji_tweets = sum(1 for t in texts if emoji_pattern.search(t))

    return {
        "hooks": hooks[:30],
        "top_starters": starters.most_common(20),
        "avg_paragraphs": round(avg_paras, 1),
        "lowercase_pct": round(lowercase_starts / len(texts) * 100) if texts else 0,
        "question_pct": round(question_endings / len(texts) * 100) if texts else 0,
        "emoji_pct": round(emoji_tweets / len(texts) * 100) if texts else 0,
        "total_analyzed": len(texts),
    }


def build_training_context(analyses: list[dict], max_examples: int = 20) -> str:
    """
    Build optimized training context string from saved analyses.
    This gets injected into the system prompt for MiniMax/AI.

    Strategy:
    - Top 15 high-engagement tweets for STRATEGY training (what works)
    - 30 sampled tweets across engagement levels for STYLE training
    - Writing DNA analysis (patterns, hooks, starters)
    - Keeps total context under ~20K chars to avoid token limits
    """
    if not analyses:
        return ""

    context_parts = []

    for analysis_data in analyses[:5]:  # Max 5 accounts
        username = analysis_data.get("username", "unknown")
        analysis = analysis_data.get("analysis", {})
        ai_report = analysis_data.get("ai_report", "")

        all_originals = analysis.get("all_original_tweets", [])
        top_tweets = analysis.get("top_tweets", [])

        # --- WRITING DNA: Pattern analysis from ALL tweets ---
        if all_originals:
            dna = _extract_writing_dna(all_originals)

            dna_text = f"### @{username} - YAZIM DNA'SI ({dna['total_analyzed']} tweet analizi):\n"
            dna_text += f"- Küçük harfle başlama: %{dna['lowercase_pct']}\n"
            dna_text += f"- Soru ile bitirme: %{dna['question_pct']}\n"
            dna_text += f"- Emoji kullanımı: %{dna['emoji_pct']}\n"
            dna_text += f"- Ortalama paragraf sayısı: {dna['avg_paragraphs']}\n"

            if dna["top_starters"]:
                starter_text = ", ".join(
                    [f'"{s}" ({c}x)' for s, c in dna["top_starters"][:15]]
                )
                dna_text += f"- Sık kullanılan cümle başlangıçları: {starter_text}\n"

            context_parts.append(dna_text)

            # --- HOOK PATTERNS: First lines of top tweets ---
            top_hooks = []
            sorted_by_score = sorted(all_originals,
                                     key=lambda t: t.get("engagement_score", 0),
                                     reverse=True)
            for t in sorted_by_score[:20]:
                first_line = t.get("text", "").split("\n")[0].strip()
                if len(first_line) > 20:
                    score = t.get("engagement_score", 0)
                    top_hooks.append(f'- "{first_line[:200]}" [skor:{score:,.0f}]')

            if top_hooks:
                context_parts.append(
                    f"### @{username} - EN İYİ HOOK'LAR (ilk satırlar):\n"
                    + "\n".join(top_hooks[:15])
                )

        # --- ENGAGEMENT STRATEGY: Top 15 performing tweets (full text) ---
        strategy_tweets = []
        if all_originals:
            sorted_orig = sorted(all_originals,
                                 key=lambda t: t.get("engagement_score", 0),
                                 reverse=True)
            strategy_tweets = [t for t in sorted_orig[:15]
                               if not t.get("text", "").startswith("RT @")]
        elif top_tweets:
            strategy_tweets = [t for t in top_tweets[:15]
                               if not t.get("text", "").startswith("RT @")]

        if strategy_tweets:
            examples = []
            for t in strategy_tweets:
                text = t.get("text", "")[:500]
                score = t.get("engagement_score", 0)
                likes = t.get("like_count", 0)
                rts = t.get("retweet_count", 0)
                replies = t.get("reply_count", 0)
                examples.append(
                    f'[Skor:{score:,.0f} | ❤️{likes:,} 🔁{rts:,} 💬{replies:,}]\n"{text}"'
                )

            context_parts.append(
                f"### @{username} - EN ÇOK ETKİLEŞİM ALAN TWEET'LER "
                f"(bu yapıları ve hook'ları referans al):\n\n"
                + "\n---\n".join(examples)
            )

        # --- STYLE TRAINING: Sampled tweets across engagement levels ---
        if all_originals:
            # Smart sampling: pick from different engagement tiers
            sorted_all = sorted(all_originals,
                                key=lambda t: t.get("engagement_score", 0),
                                reverse=True)
            # Filter meaningful tweets
            meaningful = [t for t in sorted_all
                          if len(t.get("text", "")) > 40
                          and not t.get("text", "").startswith("RT @")]

            sampled = []
            n = len(meaningful)
            if n > 0:
                # Take from top 25%, middle 50%, bottom 25%
                top_tier = meaningful[:max(n // 4, 1)]
                mid_tier = meaningful[n // 4:3 * n // 4]
                low_tier = meaningful[3 * n // 4:]

                import random
                random.seed(42)  # Deterministic sampling
                sampled.extend(top_tier[:8])  # 8 from top
                if mid_tier:
                    sampled.extend(random.sample(mid_tier, min(15, len(mid_tier))))
                if low_tier:
                    sampled.extend(random.sample(low_tier, min(7, len(low_tier))))

            if sampled:
                style_texts = []
                for t in sampled:
                    text = t.get("text", "").strip()[:400]
                    style_texts.append(f'"{text}"')

                context_parts.append(
                    f"### @{username} - YAZIM TARZI ÖRNEKLERİ "
                    f"({len(sampled)} tweet, farklı seviyelerden):\n"
                    f"Bu tweet'lerin TONUNU, CÜMLE YAPISINI, KELİME SEÇİMİNİ "
                    f"ve YAZIM TARZINI model al:\n\n"
                    + "\n---\n".join(style_texts)
                )

        # Top keywords
        top_kw = analysis.get("top_keywords", [])[:10]
        if top_kw:
            kw_text = ", ".join(
                [f"{k['keyword']}(skor:{k['avg_score']})" for k in top_kw]
            )
            context_parts.append(
                f"### @{username} - Etkileşim Çeken Kelimeler: {kw_text}"
            )

        # Most used keywords (writing DNA)
        most_used = analysis.get("most_used_keywords", [])[:15]
        if most_used:
            mu_text = ", ".join(
                [f"{k['keyword']}({k['count']}x)" for k in most_used]
            )
            context_parts.append(
                f"### @{username} - En Sık Kullanılan Kelimeler (Yazım DNA'sı): {mu_text}"
            )

        # AI report (trimmed)
        if ai_report:
            report_lines = ai_report.split("\n")
            short_report = "\n".join(report_lines[:30])
            context_parts.append(
                f"### @{username} - Tarz Analizi:\n{short_report}"
            )

    if not context_parts:
        return ""

    return f"""## EĞİTİM VERİSİ — YAZIM TARZI + ETKİLEŞİM ANALİZİ:

Aşağıdaki veriler gerçek Twitter hesaplarının tweet'lerinden elde edilmiştir.
Yazım DNA'sı TÜM tweet'lerden çıkarılmış, örnekler akıllı örnekleme ile seçilmiştir.

### NASIL KULLANACAKSIN:
1. YAZIM DNA'SI: Küçük/büyük harf tercihi, cümle başlangıçları, paragraf yapısı,
   emoji kullanımı ve soru sorma alışkanlıklarını AYNEN uygula.
2. HOOK STRATEJİSİ: En iyi hook'ları (ilk satırlar) incele ve benzer yapıda yaz.
3. YÜKSEK ETKİLEŞİM: En çok etkileşim alan tweet'lerin yapısını, tonunu ve
   konulara yaklaşımını referans al.
4. STİL ÖRNEKLERİ: Farklı engagement seviyelerindeki tweet'lerdeki tonu,
   kelime seçimini ve akışı model al.
5. BİREBİR KOPYALAMA: Tweet'leri kopyalama ama aynı RUHU, TONU ve YAKLAŞIMI koru.

{chr(10).join(context_parts)}

KRİTİK: Yukarıdaki yazım DNA'sını ve stil örneklerini içselleştir. Bu kişi gibi YAZ —
aynı kelimeler, aynı akış, aynı samimiyet, aynı cümle yapısı. Yüksek engagement alan
tweet'lerin hook tarzını, paragraf yapısını ve kapanış biçimini yeni tweet'lere uygula.
"""
