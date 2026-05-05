from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User, TopicStatus
from ..schemas.schemas import (
    CatalogListResponse,
    CatalogTopicCreateRequest,
    CatalogTopicResponse,
    TopicApproveRequest,
    TopicAssignSupervisorRequest,
    TopicCreateRequest,
    TopicDetailResponse,
    TopicListResponse,
    TopicProposeRequest,
    TopicRejectRequest,
    TopicResponse,
    TopicUpdateRequest,
)
from ..services.services import TopicService as TopicServiceClass

router = APIRouter(prefix="/topics", tags=["topics"])
topic_service = TopicServiceClass()


@router.get("", response_model=TopicListResponse)
async def list_topics(
    search: str = Query(None),
    status: TopicStatus = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all topics with pagination and search"""
    return await topic_service.get_list(
        user=current_user,
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        search=search,
    )


@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(
    data: TopicCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new topic"""
    return await topic_service.create(data, current_user, db)


@router.post("/propose", response_model=TopicResponse, status_code=201)
async def propose_topic(
    data: TopicProposeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Propose a new topic"""
    return await topic_service.propose(data, current_user, db)


@router.get("/catalog", response_model=CatalogListResponse)
async def list_catalog(
    include_taken: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    academic_year: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get catalog of topics"""
    return await topic_service.get_catalog(db, include_taken, page, page_size, academic_year)


@router.post("/catalog", response_model=CatalogTopicResponse, status_code=201)
async def create_catalog_topic(
    data: CatalogTopicCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new catalog topic"""
    return await topic_service.create_catalog(data, current_user, db)


@router.post("/catalog/{topic_id}/select", response_model=CatalogTopicResponse)
async def select_catalog_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Select a catalog topic"""
    return await topic_service.select_topic(topic_id, current_user, db)


@router.post("/auto-assign")
async def auto_assign_topics(
    academic_year: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Automatically assign topics to students"""
    return await topic_service.auto_assign(academic_year, current_user, db)


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get topic details"""
    return await topic_service.get_one(topic_id, current_user, db)


@router.patch("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    data: TopicUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update topic"""
    return await topic_service.update(topic_id, data, current_user, db)


@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete topic"""
    return await topic_service.delete(topic_id, current_user, db)


@router.post("/{topic_id}/submit", response_model=TopicResponse)
async def submit_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit topic for approval"""
    return await topic_service.submit(topic_id, current_user, db)


@router.post("/{topic_id}/approve", response_model=TopicResponse)
async def approve_topic(
    topic_id: int,
    data: TopicApproveRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve topic (admin/kafedra_head only), optional supervisor assignment"""
    return await topic_service.approve(topic_id, current_user, db, data.supervisor_id if data else None)


@router.post("/{topic_id}/reject", response_model=TopicResponse)
async def reject_topic(
    topic_id: int,
    data: TopicRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject topic"""
    return await topic_service.reject(topic_id, data, current_user, db)


@router.post("/{topic_id}/assign-supervisor", response_model=TopicResponse)
async def assign_supervisor(
    topic_id: int,
    data: TopicAssignSupervisorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign supervisor to topic"""
    return await topic_service.assign_supervisor(topic_id, data, current_user, db)
