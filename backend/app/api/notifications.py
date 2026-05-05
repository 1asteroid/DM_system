from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import NotificationResponse
from ..services.services import NotificationService as NotificationServiceClass

router = APIRouter(prefix="/notifications", tags=["notifications"])
notification_service = NotificationServiceClass()


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user notifications"""
    return await notification_service.get_list(current_user, db)


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark notification as read"""
    return await notification_service.mark_read(notification_id, current_user, db)


@router.post("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read"""
    return await notification_service.mark_all_read(current_user, db)


