"""
Scanner API - AI konu tarama
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ScanRequest(BaseModel):
    time_range: str = "24h"  # 1h, 6h, 24h, 7d
    category: str = "all"


class AITopic(BaseModel):
    title: str
    summary: str
    category: str
    engagement_score: float
    source_tweets: list[dict]
    media_urls: list[str] = []


class ScanResponse(BaseModel):
    topics: list[AITopic]
    total_tweets_scanned: int


@router.post("/scan", response_model=ScanResponse)
async def scan_topics(request: ScanRequest):
    """AI konularini tara"""
    from backend.modules.twitter_scanner import TwitterScanner

    try:
        scanner = TwitterScanner()
        topics = await scanner.scan(
            time_range=request.time_range,
            category=request.category,
        )
        return ScanResponse(
            topics=[AITopic(
                title=t.title,
                summary=t.summary,
                category=t.category,
                engagement_score=t.engagement_score,
                source_tweets=t.source_tweets,
                media_urls=getattr(t, "media_urls", []),
            ) for t in topics],
            total_tweets_scanned=scanner.total_scanned,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
