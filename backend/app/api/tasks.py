from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import TaskCreateRequest, TaskUpdateRequest, TaskResponse
from ..services.services import TaskService as TaskServiceClass

router = APIRouter(prefix="/topics", tags=["tasks"])
task_service = TaskServiceClass()


@router.get("/{topic_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get tasks for topic"""
    return await task_service.get_list(topic_id, db)


@router.post("/{topic_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    topic_id: int,
    data: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create task for topic"""
    return await task_service.create(topic_id, data, current_user, db)


@router.patch("/{topic_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    topic_id: int,
    task_id: int,
    data: TaskUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task"""
    return await task_service.update(task_id, data, current_user, db)


@router.delete("/{topic_id}/tasks/{task_id}")
async def delete_task(
    topic_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete task"""
    return await task_service.delete(task_id, db)

