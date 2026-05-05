from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import StageCreateRequest, StageUpdateRequest, StageReviewRequest
from ..services.services import StageService as StageServiceClass

router = APIRouter(prefix="/topics", tags=["stages"])
stage_service = StageServiceClass()


@router.get("/{topic_id}/stages")
async def list_stages(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get stages for topic"""
    return await stage_service.get_list(topic_id, db)


@router.post("/{topic_id}/stages", status_code=201)
async def create_stage(
    topic_id: int,
    data: StageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create stage for topic"""
    return await stage_service.create(topic_id, data, current_user, db)


@router.patch("/{topic_id}/stages/{stage_id}")
async def update_stage(
    topic_id: int,
    stage_id: int,
    data: StageUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update stage"""
    return await stage_service.update(stage_id, data, current_user, db)


@router.delete("/{topic_id}/stages/{stage_id}")
async def delete_stage(
    topic_id: int,
    stage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete stage"""
    return await stage_service.delete(stage_id, current_user, db)


@router.post("/{topic_id}/stages/{stage_id}/start", status_code=200)
async def start_stage(
    topic_id: int,
    stage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start stage"""
    return await stage_service.start(stage_id, current_user, db)


@router.post("/{topic_id}/stages/{stage_id}/submit", status_code=200)
async def submit_stage(
    topic_id: int,
    stage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit stage"""
    return await stage_service.submit(stage_id, current_user, db)


@router.post("/{topic_id}/stages/{stage_id}/review", status_code=200)
async def review_stage(
    topic_id: int,
    stage_id: int,
    data: StageReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review stage"""
    return await stage_service.review(stage_id, data, current_user, db)
