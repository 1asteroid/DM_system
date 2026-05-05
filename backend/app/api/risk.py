from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import RiskAssessmentResponse
from ..services.services import RiskService as RiskServiceClass

router = APIRouter(prefix="/risk", tags=["risk"])
risk_service = RiskServiceClass()


@router.get("/assessments", response_model=list[dict])
async def list_risks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of risk assessments

    - SUPERVISOR: o'z o'quvchilari mavzularining risk'ini ko'radi
    - STUDENT: o'zining risk'ini ko'radi
    - ADMIN/KAFEDRA_HEAD: barcha risk'larni ko'radi
    """
    return await risk_service.get_all_risks(current_user, db)


@router.get("/assessment/{topic_id}", response_model=RiskAssessmentResponse)
async def get_risk(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get risk assessment for topic

    - SUPERVISOR: faqat o'z o'quvchilari mavzulariga ruxsat
    - STUDENT: faqat o'z mavzusiga ruxsat
    - ADMIN/KAFEDRA_HEAD: barcha mavzularga ruxsat
    """
    result = await risk_service.get_risk(topic_id, current_user, db)
    if not result:
        raise HTTPException(status_code=404, detail="Risk assessment topilmadi")
    return result


@router.post("/assess/{topic_id}", response_model=RiskAssessmentResponse, status_code=201)
async def assess_risk(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create risk assessment for topic"""
    return await risk_service.assess_risk(topic_id, db)

