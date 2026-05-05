from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import TextAnalysisRequest, AIAnalysisResponse
from ..services.services import AIAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])
ai_analysis_service = AIAnalysisService()


@router.post("/text", response_model=AIAnalysisResponse, status_code=201)
async def analyze_text(
    data: TextAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze text content quality"""
    return await ai_analysis_service.analyze_text(data, current_user, db)


@router.get("/topic/{topic_id}", response_model=list[AIAnalysisResponse])
async def get_analyses(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get text quality analyses for topic"""
    return await ai_analysis_service.get_text_quality_analyses(topic_id, db)

