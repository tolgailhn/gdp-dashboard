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


def pull_user_tweets(twikit_client, username: str, count: int = 500,
                     progress_callback=None) -> list[dict]:
    """
    Pull last N tweets from a user via Twikit.
    Returns list of tweet dicts with engagement data.
    """
    if not twikit_client or not twikit_client.is_authenticated:
        raise ValueError("Twikit client not authenticated")

    all_tweets = []
    batch_size = min(count, 100)
    batches_needed = (count + batch_size - 1) // batch_size

    for batch_num in range(batches_needed):
        if progress_callback:
            fetched = len(all_tweets)
            progress_callback(f"@{username}: {fetched}/{count} tweet çekildi...")

        tweets = twikit_client.get_user_tweets(username, count=batch_size)
        if not tweets:
            break

        all_tweets.extend(tweets)

        if len(tweets) < batch_size:
            break

    if progress_callback:
        progress_callback(f"@{username}: {len(all_tweets)} tweet çekildi. Analiz yapılıyor...")

    return all_tweets[:count]


def calculate_engagement_score(tweet: dict) -> float:
    """
    Calculate weighted engagement score based on X algorithm weights.
    RT = 20x, Reply = 13.5x, Like = 1x, Bookmark ≈ 10x
    """
    rt = tweet.get("retweet_count", 0) or 0
    reply = tweet.get("reply_count", 0) or 0
    like = tweet.get("like_count", 0) or 0
    impressions = tweet.get("impression_count", 0) or 0

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
    """
    if not tweets:
        return {"error": "No tweets to analyze"}

    # Calculate engagement scores
    for tweet in tweets:
        tweet["engagement_score"] = calculate_engagement_score(tweet)

    # Sort by engagement score
    sorted_tweets = sorted(tweets, key=lambda t: t["engagement_score"], reverse=True)

    # Top performing tweets
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
    total_likes = sum(t.get("like_count", 0) or 0 for t in tweets)
    total_rts = sum(t.get("retweet_count", 0) or 0 for t in tweets)
    total_replies = sum(t.get("reply_count", 0) or 0 for t in tweets)
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


def save_tweet_analysis(username: str, analysis: dict, ai_report: str = ""):
    """Save tweet analysis to JSON file."""
    ANALYSES_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "username": username,
        "analyzed_at": datetime.datetime.now().isoformat(),
        "analysis": analysis,
        "ai_report": ai_report,
    }

    path = ANALYSES_DIR / f"{username.lower()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_tweet_analysis(username: str) -> dict | None:
    """Load tweet analysis for a specific username."""
    path = ANALYSES_DIR / f"{username.lower()}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_all_analyses() -> list[dict]:
    """Load all saved tweet analyses."""
    if not ANALYSES_DIR.exists():
        return []

    analyses = []
    for path in ANALYSES_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                analyses.append(json.load(f))
        except Exception:
            continue

    return sorted(analyses, key=lambda x: x.get("analyzed_at", ""), reverse=True)


def delete_tweet_analysis(username: str) -> bool:
    """Delete a saved analysis."""
    path = ANALYSES_DIR / f"{username.lower()}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def build_training_context(analyses: list[dict], max_examples: int = 20) -> str:
    """
    Build training context string from saved analyses.
    This gets injected into the system prompt for MiniMax/AI.
    """
    if not analyses:
        return ""

    context_parts = []

    for analysis_data in analyses[:5]:  # Max 5 accounts
        username = analysis_data.get("username", "unknown")
        analysis = analysis_data.get("analysis", {})
        ai_report = analysis_data.get("ai_report", "")

        # Top performing examples
        top_tweets = analysis.get("top_tweets", [])[:max_examples // max(len(analyses), 1)]

        if top_tweets:
            examples = []
            for t in top_tweets:
                examples.append(
                    f'- "{t["text"][:400]}" '
                    f'[Skor:{t["engagement_score"]} | ❤️{t["like_count"]} 🔁{t["retweet_count"]} 💬{t["reply_count"]}]'
                )

            context_parts.append(f"""### @{username} - En İyi Performans Gösteren Tweet'ler:
{chr(10).join(examples)}""")

        # Top keywords
        top_kw = analysis.get("top_keywords", [])[:10]
        if top_kw:
            kw_text = ", ".join([f"{k['keyword']}(skor:{k['avg_score']})" for k in top_kw])
            context_parts.append(f"### @{username} - Etkileşim Çeken Kelimeler: {kw_text}")

        # AI report (trimmed)
        if ai_report:
            # Only include key insights, not the full report
            report_lines = ai_report.split("\n")
            short_report = "\n".join(report_lines[:30])
            context_parts.append(f"### @{username} - Tarz Analizi:\n{short_report}")

    if not context_parts:
        return ""

    return f"""## EĞİTİM VERİSİ — GERÇEK ETKİLEŞİM ANALİZİ:

Aşağıdaki veriler gerçek Twitter hesaplarının tweet analizlerinden elde edilmiştir.
Bu örneklerin TARZINI, TONUNU ve YAPILARINI referans al.
Birebir kopyalama ama aynı kalıpları ve yaklaşımları kullan.

{chr(10).join(context_parts)}

KRİTİK: Bu örneklerdeki yazım tarzını, hook kalıplarını, cümle yapısını ve kelime tercihlerini model al.
Yüksek engagement alan tweet'lerin ortak özelliklerini yeni tweet'lere uygula.
"""
