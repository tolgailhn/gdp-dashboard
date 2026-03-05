"""
Analytics API - Tweet analizi ve stil oğrenme
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AnalyzeRequest(BaseModel):
    username: str
    tweet_count: int = 50


class StyleDNA(BaseModel):
    avg_length: float
    emoji_usage: float
    hashtag_usage: float
    top_topics: list[str]
    tone: str
    sample_patterns: list[str]


class AnalyzeResponse(BaseModel):
    username: str
    tweets_analyzed: int
    style_dna: StyleDNA
    engagement_avg: float


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_account(request: AnalyzeRequest):
    """Hesap tweet'lerini analiz et, stil DNA cikar"""
    from backend.modules.tweet_analyzer import TweetAnalyzer

    try:
        analyzer = TweetAnalyzer()
        result = await analyzer.analyze(
            username=request.username,
            count=request.tweet_count,
        )
        return AnalyzeResponse(
            username=request.username,
            tweets_analyzed=result.get("tweets_analyzed", 0),
            style_dna=StyleDNA(**result.get("style_dna", {})),
            engagement_avg=result.get("engagement_avg", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
