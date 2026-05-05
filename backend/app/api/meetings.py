from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import MeetingResponse, MeetingCreateRequest, MeetingUpdateRequest
from ..services.services import MeetingService as MeetingServiceClass

router = APIRouter(prefix="/meetings", tags=["meetings"])
meeting_service = MeetingServiceClass()


@router.get("", response_model=list[MeetingResponse])
async def list_all_meetings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of all user meetings"""
    return await meeting_service.get_all_for_user(current_user, db)


@router.get("/topic/{topic_id}", response_model=list[MeetingResponse])
async def list_topic_meetings(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get meetings for specific topic"""
    return await meeting_service.get_list(topic_id, db)


@router.post("", response_model=MeetingResponse, status_code=201)
async def create_meeting(
    data: MeetingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new meeting"""
    return await meeting_service.create(data, current_user, db)


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: int,
    data: MeetingUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update meeting"""
    return await meeting_service.update(meeting_id, data, db)


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete meeting"""
    return await meeting_service.delete(meeting_id, db)

