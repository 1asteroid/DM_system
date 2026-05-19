from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User, UserRole, SupervisorProfile, StudentProfile, DiplomaTopic, TopicStatus, DiplomaStage, StageStatus
from ..schemas.schemas import UserResponse, SupervisorStudentResponse, UserCreateRequest
from ..services.services import AuthService

router = APIRouter(prefix="/users", tags=["users"])
auth_service = AuthService()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new user (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Faqat adminlar user yarata oladi")
    
    return await auth_service.create_user(data, current_user, db)


@router.get("", response_model=list[UserResponse])
async def list_users(
    role: UserRole = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of active users"""
    query = select(User).where(User.is_active == True)

    if role:
        query = query.where(User.role == role)

    result = await db.execute(query)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/supervisors", response_model=list[UserResponse])
async def list_supervisors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of supervisors"""
    query = select(User).where(
        (User.role == UserRole.SUPERVISOR) & (User.is_active == True)
    )
    result = await db.execute(query)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/supervisor/my-students", response_model=list[SupervisorStudentResponse])
async def get_my_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get my student list (for supervisors). Only approved topic assignments are visible."""
    if current_user.role != UserRole.SUPERVISOR or not current_user.supervisor_profile:
        return []

    topic_res = await db.execute(
        select(DiplomaTopic)
        .options(selectinload(DiplomaTopic.student).selectinload(StudentProfile.user))
        .where(
            DiplomaTopic.supervisor_id == current_user.supervisor_profile.id,
            DiplomaTopic.status == TopicStatus.APPROVED,
            DiplomaTopic.student_id.isnot(None),
        )
        .order_by(DiplomaTopic.updated_at.desc())
    )
    topics = topic_res.scalars().all()
    topic_ids = [t.id for t in topics]

    stage_totals: dict[int, int] = {}
    stage_approved: dict[int, int] = {}
    stage_submitted: dict[int, int] = {}
    stage_rejected: dict[int, int] = {}
    if topic_ids:
        stage_res = await db.execute(
            select(DiplomaStage.topic_id, DiplomaStage.status).where(DiplomaStage.topic_id.in_(topic_ids))
        )
        for topic_id, status in stage_res.all():
            stage_totals[topic_id] = stage_totals.get(topic_id, 0) + 1
            if status == StageStatus.APPROVED:
                stage_approved[topic_id] = stage_approved.get(topic_id, 0) + 1
            elif status == StageStatus.SUBMITTED:
                stage_submitted[topic_id] = stage_submitted.get(topic_id, 0) + 1
            elif status == StageStatus.REJECTED:
                stage_rejected[topic_id] = stage_rejected.get(topic_id, 0) + 1

    items: list[SupervisorStudentResponse] = []
    for topic in topics:
        student = topic.student.user if topic.student and topic.student.user else None
        if not student:
            continue
        items.append(SupervisorStudentResponse(
            student_id=student.id,
            student_name=student.full_name,
            student_email=student.email,
            topic_id=topic.id,
            topic_title=topic.title,
            status=topic.status,
            progress=float(topic.progress or 0),
            stages_total=stage_totals.get(topic.id, 0),
            stages_approved=stage_approved.get(topic.id, 0),
            stages_submitted=stage_submitted.get(topic.id, 0),
            stages_rejected=stage_rejected.get(topic.id, 0),
        ))
    return items


@router.get("/my-supervisor", response_model=UserResponse)
async def get_my_supervisor(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get my supervisor (for students). Only approved topic assignment is visible."""
    if current_user.role != UserRole.STUDENT:
        return None

    result = await db.execute(
        select(User).join(
            SupervisorProfile, User.id == SupervisorProfile.user_id
        ).join(
            DiplomaTopic, DiplomaTopic.supervisor_id == SupervisorProfile.id
        ).where(
            DiplomaTopic.student_id == current_user.student_profile.id,
            DiplomaTopic.status == TopicStatus.APPROVED,
        )
    )
    user = result.scalar_one_or_none()
    return UserResponse.model_validate(user) if user else None


@router.get("/search", response_model=list[UserResponse])
async def search_users(
    q: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search users by name or email"""
    if not q or len(q) < 2:
        return []

    query = select(User).where(
        (User.is_active == True) & (
            (User.full_name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )
    ).limit(10)

    result = await db.execute(query)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate user (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise PermissionError("Only admins can deactivate users")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    user.is_active = False
    await db.commit()
    return UserResponse.model_validate(user)
