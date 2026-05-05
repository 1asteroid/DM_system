from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import (
    MessageResponse,
    MessageCreateRequest,
    ConversationContactResponse,
    GroupMessageCreate,
    SupervisorGroupMessageCreate,
)
from ..services.services import MessageService as MessageServiceClass

router = APIRouter(prefix="/messages", tags=["messages"])
message_service = MessageServiceClass()


@router.get("/contacts", response_model=list[ConversationContactResponse])
async def get_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of message contacts"""
    return await message_service.get_contacts(current_user, db)


@router.get("/conversation/{user_id}", response_model=list[MessageResponse])
async def get_conversation(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation with specific user"""
    return await message_service.get_conversation(user_id, current_user, db)


@router.post("", response_model=MessageResponse, status_code=201)
async def send_message(
    data: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send message"""
    return await message_service.send(data, current_user, db)


@router.get("/group/{topic_id}", response_model=list[MessageResponse])
async def get_group_messages(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get group messages for topic"""
    return await message_service.get_group_messages(topic_id, current_user, db)


@router.post("/group", response_model=MessageResponse, status_code=201)
async def send_group_message(
    data: GroupMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send group message to topic"""
    return await message_service.send_group_message(data, current_user, db)


@router.get("/supervisor-group/{supervisor_user_id}", response_model=list[MessageResponse])
async def get_supervisor_group_messages(
    supervisor_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get supervisor group messages"""
    return await message_service.get_supervisor_group_messages(supervisor_user_id, current_user, db)


@router.post("/supervisor-group", response_model=MessageResponse, status_code=201)
async def send_supervisor_group_message(
    data: SupervisorGroupMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send message to supervisor group"""
    return await message_service.send_supervisor_group_message(data, current_user, db)

