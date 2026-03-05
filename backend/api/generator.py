"""
Generator API - Tweet/thread uretimi
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    style: str = "default"
    length: str = "medium"  # short, medium, long
    thread: bool = False
    research_context: str = ""
    media_urls: list[str] = []


class GenerateResponse(BaseModel):
    text: str
    thread_parts: list[str] = []
    hook_type: str = ""


class ResearchRequest(BaseModel):
    topic: str
    depth: str = "normal"  # quick, normal, deep


class ResearchResponse(BaseModel):
    summary: str
    key_points: list[str]
    sources: list[dict]
    media_urls: list[str] = []


@router.post("/tweet", response_model=GenerateResponse)
async def generate_tweet(request: GenerateRequest):
    """Tweet uret"""
    from backend.modules.content_generator import ContentGenerator

    try:
        generator = ContentGenerator()
        result = generator.generate(
            topic=request.topic,
            style=request.style,
            length=request.length,
            is_thread=request.thread,
            research_context=request.research_context,
            media_urls=request.media_urls,
        )
        return GenerateResponse(
            text=result.get("text", ""),
            thread_parts=result.get("thread_parts", []),
            hook_type=result.get("hook_type", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research", response_model=ResearchResponse)
async def research_topic(request: ResearchRequest):
    """Konu hakkinda derin arastirma yap"""
    from backend.modules.deep_research import DeepResearcher

    try:
        researcher = DeepResearcher()
        result = await researcher.research(
            topic=request.topic,
            depth=request.depth,
        )
        return ResearchResponse(
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            sources=result.get("sources", []),
            media_urls=result.get("media_urls", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
