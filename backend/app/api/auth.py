from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TelegramLinkRequest,
    TokenResponse,
    UserResponse,
)
from ..services.services import AuthService
auth_service = AuthService()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(data, db)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh(data, db)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    student = current_user.student_profile
    supervisor = current_user.supervisor_profile
    return UserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        telegram_id=current_user.telegram_id,
        avatar_url=current_user.avatar_url,
        group_id=student.group_id if student else None,
        group_name=student.group.name if student and student.group else None,
        student_id=student.student_id if student else None,
        academic_rank=supervisor.academic_rank if supervisor else None,
        supervisor_profile_id=supervisor.id if supervisor else None,
    )


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.change_password(data, current_user, db)


@router.patch("/profile")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.update_profile(data, current_user, db)


@router.post("/telegram")
async def save_telegram_id(
    data: TelegramLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.save_telegram_id(data.telegram_id, current_user, db)
