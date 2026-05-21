import logging
import os
import random
import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
try:
    import joblib
except Exception:  # pragma: no cover - optional
    joblib = None
try:
    import numpy as np
except Exception:  # pragma: no cover - optional
    np = None

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse as StarletteFileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from ..core.config import settings
from ..core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from ..models.models import (
    AIAnalysis, DiplomaFile, DiplomaStage, DiplomaTopic, FileComment,
    Meeting, MeetingAttendee, Message, Notification, NotificationType, RiskAssessment,
    StageStatus, StudentProfile, SupervisorProfile, Task,
    TopicStatus, User, UserRole,
)
from ..schemas.schemas import (
    AIAnalysisResponse, CatalogListResponse, CatalogTopicCreateRequest, CatalogTopicResponse,
    ChangePasswordRequest, ConversationContactResponse,
    DashboardStats, FileCommentCreate,
    FileResponse, GroupMessageCreate, SupervisorGroupMessageCreate, LoginRequest, MeetingCreateRequest, MeetingResponse,
    MeetingUpdateRequest, MessageCreateRequest, MessageResponse,
    NotificationResponse, RefreshRequest, RegisterRequest, UserCreateRequest,
    RiskAssessmentResponse, RiskListItem,
    StageCreateRequest, StageReviewRequest, StageUpdateRequest,
    TaskCreateRequest, TaskResponse, TaskUpdateRequest, TextAnalysisRequest,
    TokenResponse, TopicAssignSupervisorRequest, TopicCreateRequest, TopicProposeRequest,
    TopicDetailResponse, TopicListResponse, TopicRejectRequest,
    TopicResponse, TopicStatItem, TopicUpdateRequest, UserResponse,
)


async def _send_tg_notification(telegram_id: str, title: str, body: str, bot_token: str):
    """Telegram orqali bildirishnoma yuborish."""
    text = f"{title}"
    if body:
        text += f"\n\n{body}"
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url, json={
                "chat_id": telegram_id,
                "text": text,
            })
            if resp.status >= 400:
                logger.warning("Telegram send failed for %s: %s %s", telegram_id, resp.status, await resp.text())
    except Exception as e:
        logger.warning("Telegram notification failed for %s: %s", telegram_id, e)


async def _notify(user_id: int | None, ntype: NotificationType, title: str, body: str, db: AsyncSession):
    """Foydalanuvchiga bildirishnoma qo'shish va agar Telegram bog'langan bo'lsa yuborish."""
    if not user_id:
        return

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    sent_to_tg = False
    if user and user.telegram_id and settings.BOT_TOKEN:
        await _send_tg_notification(user.telegram_id, title, body, settings.BOT_TOKEN)
        sent_to_tg = True

    db.add(Notification(user_id=user_id, type=ntype, title=title, body=body, sent_to_tg=sent_to_tg))



class AuthService:
    async def _load_user_for_response(self, user_id: int, db: AsyncSession) -> User:
        res = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.student_profile).selectinload(StudentProfile.group),
                selectinload(User.supervisor_profile),
            )
        )
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        return user

    def _user_response(self, user: User) -> UserResponse:
        student = user.student_profile
        supervisor = user.supervisor_profile
        return UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            kafedra_id=user.kafedra_id,
            telegram_id=user.telegram_id,
            avatar_url=user.avatar_url,
            group_id=student.group_id if student else None,
            group_name=student.group.name if student and student.group else None,
            student_id=student.student_id if student else None,
            academic_rank=supervisor.academic_rank if supervisor else None,
            supervisor_profile_id=supervisor.id if supervisor else None,
        )

    async def register(self, data: RegisterRequest, db: AsyncSession) -> TokenResponse:
        res = await db.execute(select(User).where(User.email == data.email))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Bu email allaqachon ro'yxatdan o'tgan")
        user = User(
            full_name=data.full_name, email=data.email,
            password_hash=hash_password(data.password), role=data.role,
        )
        db.add(user)
        await db.flush()
        if data.role == UserRole.STUDENT:
            profile = StudentProfile(
                user_id=user.id,
                group_id=data.group_id,
                student_id=data.student_id
            )
            db.add(profile)
        elif data.role == UserRole.SUPERVISOR:
            profile = SupervisorProfile(
                user_id=user.id,
                academic_rank=data.academic_rank
            )
            db.add(profile)
        await db.flush()
        user = await self._load_user_for_response(user.id, db)
        return self._tokens(user)

    async def create_user(self, data: "UserCreateRequest", admin_user: User, db: AsyncSession) -> UserResponse:
        """Admin tomonidan yangi user yaratish"""
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Faqat adminlar user yarata oladi")
        
        res = await db.execute(select(User).where(User.email == data.email))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Bu email allaqachon ro'yxatdan o'tgan")
        
        if data.role == UserRole.STUDENT and not data.kafedra_id:
            raise HTTPException(status_code=400, detail="Talabalar uchun kafedra ko'rsatilishi kerak")
        
        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            kafedra_id=data.kafedra_id,
        )
        db.add(user)
        await db.flush()
        
        if data.role == UserRole.STUDENT:
            profile = StudentProfile(
                user_id=user.id,
                group_id=data.group_id,
                student_id=data.student_id
            )
            db.add(profile)
        elif data.role == UserRole.SUPERVISOR:
            profile = SupervisorProfile(
                user_id=user.id,
                academic_rank=data.academic_rank
            )
            db.add(profile)
        
        await db.commit()
        user = await self._load_user_for_response(user.id, db)
        return self._user_response(user)

    async def login(self, data: LoginRequest, db: AsyncSession) -> TokenResponse:
        res = await db.execute(select(User).where(User.email == data.email))
        user = res.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Email yoki parol noto'g'ri")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Hisob faol emas")
        user = await self._load_user_for_response(user.id, db)
        return self._tokens(user)

    async def refresh(self, data: RefreshRequest, db: AsyncSession) -> TokenResponse:
        payload = decode_token(data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Refresh token yaroqsiz")
        res = await db.execute(select(User).where(User.id == int(payload["sub"])))
        user = res.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
        user = await self._load_user_for_response(user.id, db)
        return self._tokens(user)

    async def change_password(self, data: ChangePasswordRequest, user: User, db: AsyncSession):
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Eski parol noto'g'ri")
        user.password_hash = hash_password(data.new_password)
        await db.flush()
        return {"message": "Parol o'zgartirildi"}

    async def update_profile(self, data, user: User, db: AsyncSession):
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone is not None:
            user.phone = data.phone
        user.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(user)
        return self._user_response(user)

    async def save_telegram_id(self, telegram_id: str | None, user: User, db: AsyncSession):
        if not telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id ko'rsatilmagan")
        user.telegram_id = str(telegram_id)
        user.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return {"ok": True, "telegram_id": user.telegram_id}

    def _tokens(self, user: User) -> TokenResponse:
        d = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(d),
            refresh_token=create_refresh_token(d),
            user=self._user_response(user),
        )



class TopicService:
    @staticmethod
    def _naive(dt):
        """Strip timezone info so datetimes match TIMESTAMP WITHOUT TIME ZONE columns."""
        if dt is None:
            return None
        return dt.replace(tzinfo=None) if dt.tzinfo else dt

    @staticmethod
    def _supervisor_assignment_active(topic: DiplomaTopic) -> bool:
        return topic.status == TopicStatus.APPROVED and topic.supervisor_id is not None

    async def create(self, data: TopicCreateRequest, user: User, db: AsyncSession) -> TopicResponse:
        """Admin / kafedra_head creates an official topic (not tied to a student yet)."""
        if user.role not in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            raise HTTPException(status_code=403, detail="Faqat admin va kafedra mudiri mavzu qo'sha oladi")
        supervisor_profile_id = None
        if data.supervisor_user_id:
            res = await db.execute(
                select(User)
                .where(User.id == data.supervisor_user_id, User.role == UserRole.SUPERVISOR)
                .options(selectinload(User.supervisor_profile))
            )
            sup_user = res.scalar_one_or_none()
            if not sup_user or not sup_user.supervisor_profile:
                raise HTTPException(status_code=404, detail="Rahbar topilmadi")
            supervisor_profile_id = sup_user.supervisor_profile.id
        topic = DiplomaTopic(
            title=data.title, title_en=data.title_en, description=data.description,
            academic_year=data.academic_year,
            supervisor_id=supervisor_profile_id,
            defense_date=self._naive(data.defense_date),
            status=TopicStatus.APPROVED,
            created_by_id=user.id,
        )
        db.add(topic)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def propose(self, data: TopicProposeRequest, user: User, db: AsyncSession) -> TopicResponse:
        """Student proposes a custom topic with a desired supervisor. Requires admin/kafedra approval."""
        if user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Faqat talabalar mavzu tavsiya qila oladi")
        student = user.student_profile
        if not student:
            raise HTTPException(status_code=400, detail="Talaba profili topilmadi")
        active_res = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.student_id == student.id,
                DiplomaTopic.status != TopicStatus.REJECTED,
            )
        )
        if active_res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Sizda allaqon faol diplom mavzusi mavjud")
        old_rejected_res = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.student_id == student.id,
                DiplomaTopic.status == TopicStatus.REJECTED,
            )
        )
        old_rejected = old_rejected_res.scalar_one_or_none()
        if old_rejected:
            await db.delete(old_rejected)
            await db.flush()
        res = await db.execute(
            select(User)
            .where(User.id == data.supervisor_user_id, User.role == UserRole.SUPERVISOR)
            .options(selectinload(User.supervisor_profile))
        )
        sup_user = res.scalar_one_or_none()
        if not sup_user or not sup_user.supervisor_profile:
            raise HTTPException(status_code=404, detail="Rahbar topilmadi")
        topic = DiplomaTopic(
            title=data.title, title_en=data.title_en, description=data.description,
            academic_year=data.academic_year, student_id=student.id,
            supervisor_id=sup_user.supervisor_profile.id,
            defense_date=self._naive(data.defense_date),
            status=TopicStatus.PENDING,
        )
        db.add(topic)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def get_list(self, user: User, db: AsyncSession,
                       page=1, page_size=20, status=None, search=None) -> TopicListResponse:
        from sqlalchemy.orm import joinedload
        
        q = select(DiplomaTopic)
        if user.role == UserRole.STUDENT:
            if not user.student_profile:
                return TopicListResponse(total=0, page=page, page_size=page_size, items=[])
            q = q.where(DiplomaTopic.student_id == user.student_profile.id)
        elif user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile:
                return TopicListResponse(total=0, page=page, page_size=page_size, items=[])
            q = q.where(
                DiplomaTopic.supervisor_id == user.supervisor_profile.id,
                DiplomaTopic.status == TopicStatus.APPROVED,
            )
        elif user.role == UserRole.KAFEDRA_HEAD:
            from ..models.models import StudentProfile as SP
            q = q.join(SP, DiplomaTopic.student_id == SP.id).join(
                User, SP.user_id == User.id
            ).where(User.kafedra_id == user.kafedra_id)
        if status:
            q = q.where(DiplomaTopic.status == status)
        if search:
            q = q.where(or_(DiplomaTopic.title.ilike(f"%{search}%"), DiplomaTopic.title_en.ilike(f"%{search}%")))
        
        q = q.options(joinedload(DiplomaTopic.student).joinedload(StudentProfile.user))
        
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size).order_by(DiplomaTopic.created_at.desc())
        items = (await db.execute(q)).scalars().all()
        topic_ids = [t.id for t in items]
        submitted_counts: dict[int, int] = {}
        if topic_ids:
            cnt_res = await db.execute(
                select(DiplomaStage.topic_id, func.count().label("cnt"))
                .where(DiplomaStage.topic_id.in_(topic_ids), DiplomaStage.status == StageStatus.SUBMITTED)
                .group_by(DiplomaStage.topic_id)
            )
            for row in cnt_res.all():
                submitted_counts[row.topic_id] = row.cnt
        result = []
        for t in items:
            r = TopicResponse.model_validate(t)
            r.stages_submitted = submitted_counts.get(t.id, 0)
            if t.student and t.student.user:
                r.student_name = t.student.user.full_name
            result.append(r)
        return TopicListResponse(total=total, page=page, page_size=page_size, items=result)

    async def get_one(self, topic_id: int, user: User, db: AsyncSession) -> TopicDetailResponse:
        topic = await self._get_or_404(topic_id, db, with_stages=True)
        self._check_access(topic, user)
        return TopicDetailResponse.model_validate(topic)

    async def update(self, topic_id: int, data: TopicUpdateRequest, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        self._check_owner_or_admin(topic, user)
        if topic.status == TopicStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Tasdiqlangan mavzuni o'zgartirish mumkin emas")
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(topic, k, v)
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def delete(self, topic_id: int, user: User, db: AsyncSession):
        topic = await self._get_or_404(topic_id, db)
        self._check_owner_or_admin(topic, user)
        if topic.status not in (TopicStatus.DRAFT, TopicStatus.REJECTED):
            raise HTTPException(status_code=400, detail="Faqat draft/rejected mavzuni o'chirish mumkin")
        await db.delete(topic)
        return {"message": "Mavzu o'chirildi"}

    async def submit(self, topic_id: int, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        self._check_owner_or_admin(topic, user)
        if topic.status != TopicStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Faqat draft holatdagi mavzuni yuborish mumkin")
        if not topic.supervisor_id:
            raise HTTPException(status_code=400, detail="Avval ilmiy rahbar tayinlanishi kerak")
        topic.status = TopicStatus.PENDING
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        heads_res = await db.execute(
            select(User).where(User.role == UserRole.KAFEDRA_HEAD, User.is_active == True)  # noqa: E712
        )
        for head in heads_res.scalars().all():
            await _notify(head.id, NotificationType.STATUS_CHANGED,
                          "Yangi mavzu tasdiqlash kutmoqda",
                          f"'{topic.title}' mavzusi ko'rib chiqish uchun yuborildi.", db)
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def approve(
        self,
        topic_id: int,
        user: User,
        db: AsyncSession,
        supervisor_user_id: int | None = None,
    ) -> TopicResponse:
        if user.role not in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            raise HTTPException(status_code=403, detail="Faqat admin yoki kafedra mudiri tasdiqlashi mumkin")

        topic = await self._get_or_404(topic_id, db)
        if topic.status != TopicStatus.PENDING:
            raise HTTPException(status_code=400, detail="Faqat pending holatdagi mavzuni tasdiqlash mumkin")

        if supervisor_user_id is not None:
            sup_res = await db.execute(
                select(User)
                .where(User.id == supervisor_user_id, User.role == UserRole.SUPERVISOR)
                .options(selectinload(User.supervisor_profile))
            )
            sup_user = sup_res.scalar_one_or_none()
            if not sup_user or not sup_user.supervisor_profile:
                raise HTTPException(status_code=404, detail="Rahbar topilmadi")
            topic.supervisor_id = sup_user.supervisor_profile.id

        topic.status = TopicStatus.APPROVED
        topic.approved_at = datetime.now(timezone.utc)
        topic.updated_at = datetime.now(timezone.utc)

        await self._notify_student(topic, NotificationType.STATUS_CHANGED,
                                   "Mavzungiz tasdiqlandi",
                                   f"'{topic.title}' mavzusi admin/kafedra mudiri tomonidan tasdiqlandi.", db)

        if topic.supervisor_id:
            sup_res = await db.execute(
                select(SupervisorProfile).where(SupervisorProfile.id == topic.supervisor_id)
            )
            sup = sup_res.scalar_one_or_none()
            if sup:
                await _notify(sup.user_id, NotificationType.STATUS_CHANGED,
                              "Yangi o'quvchi biriktirildi",
                              f"Sizga '{topic.title}' mavzusi bo'yicha yangi o'quvchi biriktirildi.", db)

        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def reject(self, topic_id: int, data: TopicRejectRequest, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        topic.status = TopicStatus.REJECTED
        topic.reject_reason = data.reason
        topic.updated_at = datetime.now(timezone.utc)
        await self._notify_student(topic, NotificationType.STATUS_CHANGED,
                                   "Mavzungiz rad etildi",
                                   f"'{topic.title}' mavzusi rad etildi. Sabab: {data.reason}", db)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def assign_supervisor(self, topic_id: int, data: TopicAssignSupervisorRequest,
                                 user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        res = await db.execute(
            select(User)
            .where(User.id == data.supervisor_id, User.role == UserRole.SUPERVISOR)
            .options(selectinload(User.supervisor_profile))
        )
        sup_user = res.scalar_one_or_none()
        if not sup_user or not sup_user.supervisor_profile:
            raise HTTPException(status_code=404, detail="Rahbar topilmadi")
        topic.supervisor_id = sup_user.supervisor_profile.id
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def get_list_with_rejected(self, user: User, db: AsyncSession,
                                      page=1, page_size=20, status=None, search=None) -> TopicListResponse:
        q = select(DiplomaTopic)
        if user.role == UserRole.STUDENT:
            if not user.student_profile:
                return TopicListResponse(total=0, page=page, page_size=page_size, items=[])
            q = q.where(DiplomaTopic.student_id == user.student_profile.id)
        elif user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile:
                return TopicListResponse(total=0, page=page, page_size=page_size, items=[])
            q = q.where(DiplomaTopic.supervisor_id == user.supervisor_profile.id)
        if status:
            q = q.where(DiplomaTopic.status == status)
        if search:
            q = q.where(or_(DiplomaTopic.title.ilike(f"%{search}%"), DiplomaTopic.title_en.ilike(f"%{search}%")))
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size).order_by(DiplomaTopic.created_at.desc())
        items = (await db.execute(q)).scalars().all()
        topic_ids = [t.id for t in items]
        submitted_counts: dict[int, int] = {}
        if topic_ids:
            cnt_res = await db.execute(
                select(DiplomaStage.topic_id, func.count().label("cnt"))
                .where(DiplomaStage.topic_id.in_(topic_ids), DiplomaStage.status == StageStatus.SUBMITTED)
                .group_by(DiplomaStage.topic_id)
            )
            for row in cnt_res.all():
                submitted_counts[row.topic_id] = row.cnt
        result = []
        for t in items:
            r = TopicResponse.model_validate(t)
            r.stages_submitted = submitted_counts.get(t.id, 0)
            result.append(r)
        return TopicListResponse(total=total, page=page, page_size=page_size, items=result)

    async def get_one_with_rejected(self, topic_id: int, user: User, db: AsyncSession) -> TopicDetailResponse:
        topic = await self._get_or_404(topic_id, db, with_stages=True)
        if user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            return TopicDetailResponse.model_validate(topic)
        if user.role == UserRole.STUDENT and topic.student_id == user.student_profile.id:
            return TopicDetailResponse.model_validate(topic)
        if user.role == UserRole.SUPERVISOR and topic.supervisor_id == user.supervisor_profile.id:
            return TopicDetailResponse.model_validate(topic)
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    async def update_with_rejected(self, topic_id: int, data: TopicUpdateRequest, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        if user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            pass
        elif user.role == UserRole.STUDENT and topic.student_id == user.student_profile.id:
            pass
        elif user.role == UserRole.SUPERVISOR and topic.supervisor_id == user.supervisor_profile.id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        if topic.status == TopicStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Tasdiqlangan mavzuni o'zgartirish mumkin emas")
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(topic, k, v)
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def delete_with_rejected(self, topic_id: int, user: User, db: AsyncSession):
        topic = await self._get_or_404(topic_id, db)
        if user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            pass
        elif user.role == UserRole.STUDENT and topic.student_id == user.student_profile.id:
            pass
        elif user.role == UserRole.SUPERVISOR and topic.supervisor_id == user.supervisor_profile.id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        if topic.status not in (TopicStatus.DRAFT, TopicStatus.REJECTED):
            raise HTTPException(status_code=400, detail="Faqat draft/rejected mavzuni o'chirish mumkin")
        await db.delete(topic)
        return {"message": "Mavzu o'chirildi"}

    async def submit_with_rejected(self, topic_id: int, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        if user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Faqat talabalar mavzu yuborishi mumkin")
        if topic.status != TopicStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Faqat draft holatdagi mavzuni yuborish mumkin")
        topic.status = TopicStatus.PENDING
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        heads_res = await db.execute(
            select(User).where(User.role == UserRole.KAFEDRA_HEAD, User.is_active == True)  # noqa: E712
        )
        for head in heads_res.scalars().all():
            await _notify(head.id, NotificationType.STATUS_CHANGED,
                          "Yangi mavzu tasdiqlash kutmoqda",
                          f"'{topic.title}' mavzusi ko'rib chiqish uchun yuborildi.", db)
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def approve_with_rejected(self, topic_id: int, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        if topic.status != TopicStatus.PENDING:
            raise HTTPException(status_code=400, detail="Faqat pending holatdagi mavzuni tasdiqlash mumkin")
        topic.status = TopicStatus.APPROVED
        topic.approved_at = datetime.now(timezone.utc)
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await self._notify_student(topic, NotificationType.STATUS_CHANGED,
                                   "Mavzungiz tasdiqlandi",
                                   f"'{topic.title}' mavzusi kafedra mudiri tomonidan tasdiqlandi.", db)
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def reject_with_rejected(self, topic_id: int, data: TopicRejectRequest, user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        topic.status = TopicStatus.REJECTED
        topic.reject_reason = data.reason
        topic.updated_at = datetime.now(timezone.utc)
        await self._notify_student(topic, NotificationType.STATUS_CHANGED,
                                   "Mavzungiz rad etildi",
                                   f"'{topic.title}' mavzusi rad etildi. Sabab: {data.reason}", db)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def assign_supervisor_with_rejected(self, topic_id: int, data: TopicAssignSupervisorRequest,
                                 user: User, db: AsyncSession) -> TopicResponse:
        topic = await self._get_or_404(topic_id, db)
        res = await db.execute(
            select(User)
            .where(User.id == data.supervisor_id, User.role == UserRole.SUPERVISOR)
            .options(selectinload(User.supervisor_profile))
        )
        sup_user = res.scalar_one_or_none()
        if not sup_user or not sup_user.supervisor_profile:
            raise HTTPException(status_code=404, detail="Rahbar topilmadi")
        topic.supervisor_id = sup_user.supervisor_profile.id
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(topic)
        return TopicResponse.model_validate(topic)

    async def _get_or_404(self, topic_id, db, with_stages=False):
        q = select(DiplomaTopic).where(DiplomaTopic.id == topic_id)
        if with_stages:
            q = q.options(selectinload(DiplomaTopic.stages))
        q = q.options(
            selectinload(DiplomaTopic.student).selectinload(StudentProfile.user),
            selectinload(DiplomaTopic.supervisor).selectinload(SupervisorProfile.user)
        )
        res = await db.execute(q)
        topic = res.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail=f"Mavzu #{topic_id} topilmadi")
        return topic

    def _check_access(self, topic, user):
        if user.role == UserRole.ADMIN:
            return
        if user.role == UserRole.KAFEDRA_HEAD:
            if not user.kafedra_id:
                raise HTTPException(status_code=403, detail="Kafedra mudiriga kafedra ko'rsatilmagan")
            if not topic.student or not topic.student.user or topic.student.user.kafedra_id != user.kafedra_id:
                raise HTTPException(status_code=403, detail="Ruxsat yo'q")
            return
        if user.role == UserRole.STUDENT and (not user.student_profile or topic.student_id != user.student_profile.id):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        if user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile:
                raise HTTPException(status_code=403, detail="Ruxsat yo'q")
            if topic.supervisor_id != user.supervisor_profile.id or topic.status != TopicStatus.APPROVED:
                raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    def _check_owner_or_admin(self, topic, user):
        if user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD): return
        if user.role == UserRole.STUDENT and user.student_profile and topic.student_id == user.student_profile.id: return
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    async def _notify_student(self, topic, ntype: NotificationType, title: str, body: str, db: AsyncSession):
        if not topic.student_id:
            return
        sp_res = await db.execute(select(StudentProfile).where(StudentProfile.id == topic.student_id))
        sp = sp_res.scalar_one_or_none()
        if sp:
            await _notify(sp.user_id, ntype, title, body, db)


    async def create_catalog(self, data: CatalogTopicCreateRequest, user: User,
                              db: AsyncSession) -> CatalogTopicResponse:
        """Kafedra mudiri yoki admin katalog (shablon) mavzu yaratadi."""
        if user.role not in (UserRole.KAFEDRA_HEAD, UserRole.ADMIN):
            raise HTTPException(status_code=403, detail="Faqat kafedra mudiri katalog mavzu yarata oladi")
        res = await db.execute(
            select(User)
            .where(User.id == data.supervisor_user_id, User.role == UserRole.SUPERVISOR)
            .options(selectinload(User.supervisor_profile))
        )
        sup_user = res.scalar_one_or_none()
        if not sup_user or not sup_user.supervisor_profile:
            raise HTTPException(status_code=404, detail="Rahbar topilmadi")
        topic = DiplomaTopic(
            title=data.title, title_en=data.title_en, description=data.description,
            academic_year=data.academic_year,
            supervisor_id=sup_user.supervisor_profile.id,
            defense_date=self._naive(data.defense_date),
            status=TopicStatus.APPROVED,
            is_template=True,
            selection_deadline=self._naive(data.selection_deadline),
            created_by_id=user.id,
        )
        db.add(topic)
        await db.flush()
        await db.refresh(topic)
        return self._to_catalog_response(topic)

    async def get_catalog(self, db: AsyncSession, include_taken: bool = False,
                           page: int = 1, page_size: int = 20,
                           academic_year: str | None = None) -> CatalogListResponse:
        """Katalog mavzularini qaytaradi (barcha foydalanuvchilar uchun)."""
        q = select(DiplomaTopic).where(DiplomaTopic.is_template == True)  # noqa: E712
        if not include_taken:
            q = q.where(DiplomaTopic.student_id == None)  # noqa: E711
        if academic_year:
            q = q.where(DiplomaTopic.academic_year == academic_year)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size).order_by(DiplomaTopic.selection_deadline.asc())
        items = (await db.execute(q)).scalars().all()
        return CatalogListResponse(
            total=total, page=page, page_size=page_size,
            items=[self._to_catalog_response(t) for t in items],
        )

    async def select_topic(self, topic_id: int, user: User, db: AsyncSession) -> CatalogTopicResponse:
        """Talaba katalog mavzusini tanlaydi."""
        if user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Faqat talabalar mavzu tanlashi mumkin")
        student = user.student_profile
        if not student:
            raise HTTPException(status_code=400, detail="Talaba profili topilmadi")
        active_res = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.student_id == student.id,
                DiplomaTopic.status != TopicStatus.REJECTED,
            )
        )
        if active_res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Sizda allaqon faol diplom mavzusi mavjud")
        old_rej_res = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.student_id == student.id,
                DiplomaTopic.status == TopicStatus.REJECTED,
            )
        )
        old_rej = old_rej_res.scalar_one_or_none()
        if old_rej:
            old_rej.student_id = None
            await db.flush()
        topic = await self._get_or_404(topic_id, db)
        if not topic.is_template:
            raise HTTPException(status_code=400, detail="Bu katalog mavzu emas")
        if topic.student_id is not None:
            raise HTTPException(status_code=409, detail="Bu mavzu allaqon tanlangan")
        if topic.selection_deadline and datetime.now(timezone.utc) > topic.selection_deadline:
            raise HTTPException(status_code=400, detail="Mavzu tanlash muddati o'tib ketdi")
        topic.student_id = student.id
        topic.is_template = False  # Katalogdan olib tashlash
        topic.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(topic)
        return self._to_catalog_response(topic)

    async def auto_assign(self, academic_year: str, user: User, db: AsyncSession) -> dict:
        """Muddat o'tgandan so'ng mavzu tanlamagan talablarga avtomatik mavzu va rahbar tayinlash."""
        if user.role not in (UserRole.KAFEDRA_HEAD, UserRole.ADMIN):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        subq = select(DiplomaTopic.student_id).where(DiplomaTopic.student_id != None)  # noqa: E711
        students_res = await db.execute(
            select(StudentProfile).where(StudentProfile.id.not_in(subq))
        )
        unassigned = students_res.scalars().all()
        if not unassigned:
            return {"assigned": 0, "message": "Barcha talabalar mavzu tanlagan"}
        topics_res = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.is_template == True,  # noqa: E712
                DiplomaTopic.student_id == None,  # noqa: E711
                DiplomaTopic.academic_year == academic_year,
            ).order_by(DiplomaTopic.id)
        )
        available = list(topics_res.scalars().all())
        sups_res = await db.execute(
            select(SupervisorProfile).options(selectinload(SupervisorProfile.diploma_topics))
        )
        all_sups = sups_res.scalars().all()
        sups_with_cap = sorted(
            [s for s in all_sups
             if len([t for t in s.diploma_topics if t.student_id is not None]) < s.max_students],
            key=lambda s: len([t for t in s.diploma_topics if t.student_id is not None]),
        )
        assigned_count = 0
        topic_idx = 0
        sup_idx = 0
        for student in unassigned:
            if topic_idx < len(available):
                topic = available[topic_idx]
                topic.student_id = student.id
                if not topic.supervisor_id and sups_with_cap:
                    topic.supervisor_id = sups_with_cap[sup_idx % len(sups_with_cap)].id
                    sup_idx += 1
                topic.updated_at = datetime.now(timezone.utc)
                topic_idx += 1
            elif sups_with_cap:
                sup = sups_with_cap[sup_idx % len(sups_with_cap)]
                new_topic = DiplomaTopic(
                    title=f"Diplom ishi — {student.id}",
                    academic_year=academic_year,
                    status=TopicStatus.APPROVED,
                    is_template=False,
                    student_id=student.id,
                    supervisor_id=sup.id,
                    created_by_id=user.id,
                )
                db.add(new_topic)
                sup_idx += 1
            else:
                break
            assigned_count += 1
        await db.flush()
        return {"assigned": assigned_count, "message": f"{assigned_count} ta talabaga mavzu tayinlandi"}

    def _to_catalog_response(self, topic: DiplomaTopic) -> CatalogTopicResponse:
        return CatalogTopicResponse(
            id=topic.id, title=topic.title, title_en=topic.title_en,
            description=topic.description, academic_year=topic.academic_year,
            supervisor_id=topic.supervisor_id, selection_deadline=topic.selection_deadline,
            defense_date=topic.defense_date, is_taken=topic.student_id is not None,
            created_at=topic.created_at,
        )



class StageService:
    async def create(self, topic_id: int, data: StageCreateRequest, user: User, db: AsyncSession):
        topic = await self._get_topic(topic_id, db)
        if topic.status != TopicStatus.APPROVED or not topic.supervisor_id:
            raise HTTPException(
                status_code=400,
                detail="Bosqich qo'shish uchun mavzu tasdiqlangan va ilmiy rahbar biriktirilgan bo'lishi kerak",
            )
        if user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile or topic.supervisor_id != user.supervisor_profile.id:
                raise HTTPException(status_code=403, detail="Faqat o'z o'quvchilari mavzulariga bosqich qo'sha olishingiz mumkin")
        else:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q. Faqat ilmiy rahbar o'z mavzulariga bosqich qo'sha oladi")

        existing_count_res = await db.execute(
            select(func.count(DiplomaStage.id)).where(DiplomaStage.topic_id == topic_id)
        )
        existing_count = existing_count_res.scalar_one()

        initial_status = StageStatus.NOT_STARTED
        stage = DiplomaStage(
            topic_id=topic_id,
            name=data.name,
            description=data.description,
            order=data.order,
            weight=data.weight,
            deadline=data.deadline,
            status=initial_status,
        )
        db.add(stage)
        await db.flush()
        await db.refresh(stage)
        await self._recalc_progress(topic_id, db)
        return stage

    async def get_list(self, topic_id: int, db: AsyncSession):
        res = await db.execute(
            select(DiplomaStage).where(DiplomaStage.topic_id == topic_id)
            .order_by(DiplomaStage.order)
        )
        return res.scalars().all()

    async def update(self, stage_id: int, data: StageUpdateRequest, user: User, db: AsyncSession):
        stage = await self._get_or_404(stage_id, db)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(stage, k, v)
        await db.flush()
        await db.refresh(stage)
        return stage

    async def submit(self, stage_id: int, user: User, db: AsyncSession):
        stage = await self._get_or_404(stage_id, db)
        if stage.status not in (StageStatus.NOT_STARTED, StageStatus.IN_PROGRESS, StageStatus.REJECTED):
            raise HTTPException(status_code=400, detail="Bu bosqich allaqon yuborilgan yoki tasdiqlangan")
        if user.role == UserRole.STUDENT:
            blocking_res = await db.execute(
                select(DiplomaStage).where(
                    DiplomaStage.topic_id == stage.topic_id,
                    DiplomaStage.order < stage.order,
                    DiplomaStage.status != StageStatus.APPROVED,
                ).limit(1)
            )
            blocking = blocking_res.scalar_one_or_none()
            if blocking:
                raise HTTPException(
                    status_code=400,
                    detail=f"{blocking.order}-bosqich hali tasdiqlanmagan. Avval uni tugatish kerak."
                )
        stage.status = StageStatus.SUBMITTED
        stage.submitted_at = datetime.now(timezone.utc)
        await db.flush()
        topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == stage.topic_id))
        topic = topic_res.scalar_one_or_none()
        if topic and topic.supervisor_id:
            sup_res = await db.execute(
                select(SupervisorProfile).where(SupervisorProfile.id == topic.supervisor_id)
            )
            sup = sup_res.scalar_one_or_none()
            if sup:
                await _notify(sup.user_id, NotificationType.STATUS_CHANGED,
                              "Bosqich ko'rib chiqishga yuborildi",
                              f"'{stage.name}' bosqichi talaba tomonidan yuborildi.", db)
        return stage

    async def review(self, stage_id: int, data: StageReviewRequest, user: User, db: AsyncSession):
        """Review and approve/reject stage (supervisor or kafedra head only)"""
        if user.role not in (UserRole.SUPERVISOR, UserRole.KAFEDRA_HEAD, UserRole.ADMIN):
            raise HTTPException(status_code=403, detail="Faqat ilmiy rahbar yoki kafedra mudiri bosqichni ko'rib chiqishi mumkin")
        
        stage = await self._get_or_404(stage_id, db)
        
        topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == stage.topic_id))
        topic = topic_res.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="Mavzu topilmadi")
        
        if user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile or topic.supervisor_id != user.supervisor_profile.id:
                raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        elif user.role == UserRole.KAFEDRA_HEAD:
            if not user.kafedra_id:
                raise HTTPException(status_code=403, detail="Kafedra mudiriga kafedra ko'rsatilmagan")
            if not topic.student or not topic.student.user or topic.student.user.kafedra_id != user.kafedra_id:
                raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        
        stage.status = StageStatus.APPROVED if data.approved else StageStatus.REJECTED
        stage.reviewed_at = datetime.now(timezone.utc)
        stage.comment = data.comment

        if data.approved:
            next_stage_res = await db.execute(
                select(DiplomaStage)
                .where(
                    DiplomaStage.topic_id == stage.topic_id,
                    DiplomaStage.order > stage.order,
                )
                .order_by(DiplomaStage.order)
                .limit(1)
            )
            next_stage = next_stage_res.scalar_one_or_none()
            if next_stage and next_stage.status == StageStatus.NOT_STARTED:
                next_stage.status = StageStatus.IN_PROGRESS

        topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == stage.topic_id))
        topic = topic_res.scalar_one_or_none()
        if topic and topic.student_id:
            sp_res = await db.execute(select(StudentProfile).where(StudentProfile.id == topic.student_id))
            sp = sp_res.scalar_one_or_none()
            if sp:
                if data.approved:
                    await _notify(sp.user_id, NotificationType.STATUS_CHANGED,
                                  f"{stage.name} tasdiqlandi",
                                  f"'{stage.name}' bosqichi ilmiy rahbar tomonidan tasdiqlandi.", db)
                else:
                    default_comment = "Izoh yo'q"
                    await _notify(sp.user_id, NotificationType.STATUS_CHANGED,
                                  f"{stage.name} qaytarildi",
                                  f"'{stage.name}' bosqichi qaytarildi. Izoh: {data.comment or default_comment}", db)
        await db.flush()
        await self._recalc_progress(stage.topic_id, db)
        return stage

    async def start(self, stage_id: int, user: User, db: AsyncSession):
        """Talaba bosqichni 'jarayonda' deb belgilaydi."""
        stage = await self._get_or_404(stage_id, db)
        if stage.status != StageStatus.NOT_STARTED:
            raise HTTPException(status_code=400, detail="Faqat boshlanmagan bosqichni boshlash mumkin")

        blocking_res = await db.execute(
            select(DiplomaStage).where(
                DiplomaStage.topic_id == stage.topic_id,
                DiplomaStage.order < stage.order,
                DiplomaStage.status != StageStatus.APPROVED,
            ).limit(1)
        )
        if blocking_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Avvalgi bosqich tasdiqlanmaguncha keyingisini boshlab bo'lmaydi")

        stage.status = StageStatus.IN_PROGRESS
        await db.flush()
        return stage

    async def delete(self, stage_id: int, user: User, db: AsyncSession):
        stage = await self._get_or_404(stage_id, db)
        topic_id = stage.topic_id
        await db.delete(stage)
        await self._recalc_progress(topic_id, db)
        return {"message": "Bosqich o'chirildi"}

    async def _recalc_progress(self, topic_id: int, db: AsyncSession):
        res = await db.execute(select(DiplomaStage).where(DiplomaStage.topic_id == topic_id))
        stages = res.scalars().all()
        if not stages: return
        total_weight = sum(s.weight for s in stages)
        done_weight = sum(s.weight for s in stages if s.status == StageStatus.APPROVED)
        progress = (done_weight / total_weight * 100) if total_weight else 0
        topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == topic_id))
        topic = topic_res.scalar_one_or_none()
        if topic:
            topic.progress = round(progress, 1)
            topic.updated_at = datetime.now(timezone.utc)
            await db.flush()

    async def _get_or_404(self, stage_id, db):
        res = await db.execute(select(DiplomaStage).where(DiplomaStage.id == stage_id))
        stage = res.scalar_one_or_none()
        if not stage:
            raise HTTPException(status_code=404, detail="Bosqich topilmadi")
        return stage

    async def _get_topic(self, topic_id, db):
        res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == topic_id))
        topic = res.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="Mavzu topilmadi")
        return topic



class FileService:
    async def upload(self, topic_id: int, stage_id: int | None,
                      file: UploadFile, user: User, db: AsyncSession) -> FileResponse:
        content = await file.read()
        stage = None

        max_bytes = 20 * 1024 * 1024 if stage_id else settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            limit_label = "20MB" if stage_id else f"{settings.MAX_FILE_SIZE_MB}MB"
            raise HTTPException(status_code=413, detail=f"Fayl hajmi {limit_label} dan oshmasligi kerak")

        if stage_id:
            stage_res = await db.execute(select(DiplomaStage).where(DiplomaStage.id == stage_id))
            stage = stage_res.scalar_one_or_none()
            if not stage:
                raise HTTPException(status_code=404, detail="Bosqich topilmadi")
            if stage.status == StageStatus.APPROVED:
                raise HTTPException(status_code=400,
                                    detail="Bu bosqich tasdiqlangan — fayl yuklash mumkin emas")
            if stage.status == StageStatus.SUBMITTED:
                raise HTTPException(status_code=400,
                                    detail="Bosqich allaqon ko'rib chiqishga yuborilgan")
            if stage.status == StageStatus.APPROVED:
                raise HTTPException(status_code=400,
                                    detail="Bu bosqich tasdiqlangan — fayl yuklash mumkin emas")

            if stage.status == StageStatus.NOT_STARTED:
                stage.status = StageStatus.IN_PROGRESS

            old_res = await db.execute(
                select(DiplomaFile).where(
                    DiplomaFile.topic_id == topic_id,
                    DiplomaFile.stage_id == stage_id,
                )
            )
            for old_f in old_res.scalars().all():
                try:
                    raw = old_f.file_path if os.path.isabs(old_f.file_path) else os.path.join(settings.UPLOAD_DIR, old_f.file_path)
                    if os.path.exists(raw):
                        os.remove(raw)
                except OSError:
                    pass
                await db.delete(old_f)
            await db.flush()

        ver_res = await db.execute(
            select(func.max(DiplomaFile.version))
            .where(DiplomaFile.topic_id == topic_id, DiplomaFile.stage_id == stage_id)
        )
        last_version = ver_res.scalar_one_or_none() or 0

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        original_name = file.filename or "file"
        ext = os.path.splitext(original_name)[1].lower()
        base_name = os.path.splitext(original_name)[0]

        fname = f"{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(settings.UPLOAD_DIR, fname)

        unique_code = str(random.randint(100000, 999999))
        display_name = f"{unique_code}_{base_name}{ext}"

        with open(fpath, "wb") as fh:
            fh.write(content)

        db_file = DiplomaFile(
            topic_id=topic_id, stage_id=stage_id, uploaded_by=user.id,
            file_name=display_name, file_path=fname,
            file_size=len(content), file_type=ext.lstrip("."),
            version=last_version + 1,
        )
        db.add(db_file)
        await db.flush()

        if stage_id:
            assert stage is not None
            stage.status = StageStatus.SUBMITTED
            stage.submitted_at = datetime.now(timezone.utc)
            await db.flush()
            topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == topic_id))
            topic = topic_res.scalar_one_or_none()
            if topic and topic.supervisor_id:
                sup_res = await db.execute(
                    select(SupervisorProfile).where(SupervisorProfile.id == topic.supervisor_id)
                )
                sup = sup_res.scalar_one_or_none()
                if sup:
                    await _notify(sup.user_id, NotificationType.FILE_UPLOADED,
                                  "Bosqich fayli yuklandi",
                                  f"'{stage.name}' bosqichi uchun fayl yuklandi va ko'rib chiqishga yuborildi.", db)

        await db.refresh(db_file)
        resp = FileResponse.model_validate(db_file)
        resp.file_url = f"/uploads/{fname}"
        return resp

    async def get_list(self, topic_id: int, db: AsyncSession) -> list[FileResponse]:
        """Get topic-level supervisor files (stage_id IS NULL, uploaded_by IS supervisor)"""
        sup_prof_res = await db.execute(select(SupervisorProfile))
        supervisor_user_ids = {sp.user_id for sp in sup_prof_res.scalars().all()}

        res = await db.execute(
            select(DiplomaFile).where(
                DiplomaFile.topic_id == topic_id,
                DiplomaFile.stage_id == None  # TOPIC LEVEL FILES ONLY
            )
            .order_by(DiplomaFile.created_at.desc())
        )
        
        result = []
        for f in res.scalars().all():
            if f.uploaded_by in supervisor_user_ids:
                r = FileResponse.model_validate(f)
                fname_only = os.path.basename(f.file_path)
                r.file_url = f"/uploads/{fname_only}"
                result.append(r)
        
        return result

    async def get_stage_student_files(self, stage_id: int, db: AsyncSession) -> list[FileResponse]:
        """Get student-submitted files for a specific stage (stage_id = {stage_id}, uploaded_by IS student)"""
        stage_res = await db.execute(select(DiplomaStage).where(DiplomaStage.id == stage_id))
        stage = stage_res.scalar_one_or_none()
        if not stage:
            raise HTTPException(status_code=404, detail="Bosqich topilmadi")

        sp_res = await db.execute(select(StudentProfile))
        student_user_ids = {sp.user_id for sp in sp_res.scalars().all()}

        res = await db.execute(
            select(DiplomaFile)
            .where(DiplomaFile.stage_id == stage_id)
            .order_by(DiplomaFile.created_at.desc())
        )
        
        result = []
        for f in res.scalars().all():
            if f.uploaded_by in student_user_ids:
                r = FileResponse.model_validate(f)
                fname_only = os.path.basename(f.file_path)
                r.file_url = f"/uploads/{fname_only}"
                result.append(r)
        
        return result

    async def delete(self, file_id: int, user: User, db: AsyncSession):
        res = await db.execute(select(DiplomaFile).where(DiplomaFile.id == file_id))
        f = res.scalar_one_or_none()
        if not f:
            raise HTTPException(status_code=404, detail="Fayl topilmadi")
        if user.role not in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD) and f.uploaded_by != user.id:
            raise HTTPException(status_code=403, detail="Faqat o'z faylingizni o'chira olasiz")
        full_path = f.file_path if os.path.isabs(f.file_path) else os.path.join(settings.UPLOAD_DIR, f.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        await db.delete(f)
        return {"message": "Fayl o'chirildi"}

    async def download(self, file_id: int, db: AsyncSession):
        res = await db.execute(select(DiplomaFile).where(DiplomaFile.id == file_id))
        f = res.scalar_one_or_none()
        if not f:
            raise HTTPException(status_code=404, detail="Fayl topilmadi")

        full_path = f.file_path if os.path.isabs(f.file_path) else os.path.join(settings.UPLOAD_DIR, f.file_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Fayl diskda topilmadi")

        media_type, _ = mimetypes.guess_type(f.file_name or full_path)
        return StarletteFileResponse(
            path=full_path,
            filename=f.file_name or os.path.basename(full_path),
            media_type=media_type or "application/octet-stream",
        )

    async def add_comment(self, file_id: int, data: FileCommentCreate,
                           user: User, db: AsyncSession):
        res = await db.execute(select(DiplomaFile).where(DiplomaFile.id == file_id))
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Fayl topilmadi")
        comment = FileComment(file_id=file_id, author_id=user.id, content=data.content)
        db.add(comment)
        await db.flush()
        await db.refresh(comment)
        return comment



class TaskService:
    async def create(self, topic_id: int, data: TaskCreateRequest, user: User, db: AsyncSession) -> TaskResponse:
        task = Task(topic_id=topic_id, created_by=user.id,
                    title=data.title, description=data.description, deadline=data.deadline)
        db.add(task)
        await db.flush()
        topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == topic_id))
        topic = topic_res.scalar_one_or_none()
        if topic and topic.student_id:
            sp_res = await db.execute(select(StudentProfile).where(StudentProfile.id == topic.student_id))
            sp = sp_res.scalar_one_or_none()
            if sp:
                await _notify(sp.user_id, NotificationType.NEW_TASK,
                              "Yangi vazifa qo'shildi",
                              f"'{data.title}' nomli yangi vazifa qo'shildi.", db)
                await db.flush()
        await db.refresh(task)
        return TaskResponse.model_validate(task)

    async def get_list(self, topic_id: int, db: AsyncSession) -> list[TaskResponse]:
        res = await db.execute(select(Task).where(Task.topic_id == topic_id).order_by(Task.created_at.desc()))
        return [TaskResponse.model_validate(t) for t in res.scalars().all()]

    async def update(self, task_id: int, data: TaskUpdateRequest, user: User, db: AsyncSession) -> TaskResponse:
        res = await db.execute(select(Task).where(Task.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Vazifa topilmadi")
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(task, k, v)
        if data.is_done is True and not task.done_at:
            task.done_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(task)
        return TaskResponse.model_validate(task)

    async def delete(self, task_id: int, db: AsyncSession):
        res = await db.execute(select(Task).where(Task.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Vazifa topilmadi")
        await db.delete(task)
        return {"message": "Vazifa o'chirildi"}



def _load_meeting(q):
    """Meeting queryga attendees + user ni eager load qiladi."""
    return q.options(
        selectinload(Meeting.attendees).selectinload(MeetingAttendee.user)
    )


class MeetingService:
    async def create(self, data: MeetingCreateRequest, user: User, db: AsyncSession) -> MeetingResponse:
        if not data.title or not data.title.strip():
            raise HTTPException(status_code=400, detail="Uchrashuv nomi kiritilmagan")

        meeting = Meeting(
            title=data.title.strip(),
            reason=data.reason,
            topic_id=data.topic_id,
            scheduled_at=data.scheduled_at,
            duration_min=data.duration_min,
            location=data.location,
            created_by=user.id,
        )
        db.add(meeting)
        await db.flush()

        attendee_ids = list(set(data.attendee_ids))
        for uid in attendee_ids:
            db.add(MeetingAttendee(meeting_id=meeting.id, user_id=uid))
        await db.flush()

        time_str = meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')
        loc_str = f", joy: {meeting.location}" if meeting.location else ""
        reason_str = f"\nSabab: {meeting.reason}" if meeting.reason else ""
        body = f"{time_str}{loc_str}{reason_str}"

        for uid in attendee_ids:
            if uid != user.id:
                await _notify(uid, NotificationType.MEETING_SCHEDULED,
                              f"Yangi uchrashuv: {meeting.title}", body, db)

        res = await db.execute(
            _load_meeting(select(Meeting)).where(Meeting.id == meeting.id)
        )
        return self._to_response(res.scalar_one())

    async def get_supervisor_students(self, user: User, db: AsyncSession) -> list[dict]:
        """Rahbarning barcha talabalarini qaytaradi."""
        if not user.supervisor_profile:
            return []
        res = await db.execute(
            select(StudentProfile, User)
            .join(User, User.id == StudentProfile.user_id)
            .join(DiplomaTopic, DiplomaTopic.student_id == StudentProfile.id, isouter=True)
            .where(DiplomaTopic.supervisor_id == user.supervisor_profile.id)
        )
        return [{"id": u.id, "full_name": u.full_name} for _, u in res.all()]

    async def get_list(self, topic_id: int, db: AsyncSession) -> list[MeetingResponse]:
        res = await db.execute(
            _load_meeting(select(Meeting))
            .where(Meeting.topic_id == topic_id)
            .order_by(Meeting.scheduled_at)
        )
        return [self._to_response(m) for m in res.scalars().all()]

    async def get_all_for_user(self, user: User, db: AsyncSession) -> list[MeetingResponse]:
        base = _load_meeting(select(Meeting))
        if user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            res = await db.execute(base.order_by(Meeting.scheduled_at.desc()))
        elif user.role == UserRole.SUPERVISOR:
            res = await db.execute(
                base.where(Meeting.created_by == user.id)
                .order_by(Meeting.scheduled_at.desc())
            )
        elif user.role == UserRole.STUDENT:
            from sqlalchemy import union
            attendee_ids_q = select(MeetingAttendee.meeting_id).where(
                MeetingAttendee.user_id == user.id
            )
            admin_ids_q = select(Meeting.id).where(
                Meeting.created_by.in_(
                    select(User.id).where(User.role.in_([UserRole.ADMIN, UserRole.KAFEDRA_HEAD]))
                )
            )
            combined = union(attendee_ids_q, admin_ids_q).subquery()
            res = await db.execute(
                base.where(Meeting.id.in_(select(combined)))
                .order_by(Meeting.scheduled_at.desc())
            )
        else:
            return []
        return [self._to_response(m) for m in res.scalars().all()]

    async def update(self, meeting_id: int, data: MeetingUpdateRequest, db: AsyncSession) -> MeetingResponse:
        res = await db.execute(
            _load_meeting(select(Meeting)).where(Meeting.id == meeting_id)
        )
        meeting = res.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Uchrashuv topilmadi")
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(meeting, k, v)
        await db.flush()
        res2 = await db.execute(
            _load_meeting(select(Meeting)).where(Meeting.id == meeting_id)
        )
        return self._to_response(res2.scalar_one())

    async def delete(self, meeting_id: int, db: AsyncSession):
        res = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = res.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Uchrashuv topilmadi")
        await db.delete(meeting)
        return {"message": "Uchrashuv o'chirildi"}

    def _to_response(self, meeting: Meeting) -> MeetingResponse:
        from ..schemas.schemas import MeetingAttendeeInfo
        attendees = [
            MeetingAttendeeInfo(user_id=a.user_id, full_name=a.user.full_name)
            for a in (meeting.attendees or [])
            if a.user
        ]
        data = {
            "id": meeting.id,
            "title": meeting.title,
            "reason": meeting.reason,
            "topic_id": meeting.topic_id,
            "scheduled_at": meeting.scheduled_at,
            "duration_min": meeting.duration_min,
            "location": meeting.location,
            "status": meeting.status,
            "notes": meeting.notes,
            "created_by": meeting.created_by,
            "created_at": meeting.created_at,
            "attendees": attendees,
        }
        return MeetingResponse(**data)



class MessageService:
    async def _safe_ws_send(self, user_id: int, payload: dict):
        """Best-effort WS push; API response should not fail if socket is unavailable."""
        try:
            from ..api.websocket import send_to_user
            await send_to_user(user_id, payload)
        except Exception:
            logger.debug("WS push failed for user_id=%s", user_id)

    async def _broadcast_supervisor_group_message(
        self,
        supervisor_user_id: int,
        payload: dict,
        db: AsyncSession,
    ):
        student_user_ids_res = await db.execute(
            select(StudentProfile.user_id)
            .join(DiplomaTopic, DiplomaTopic.student_id == StudentProfile.id)
            .join(SupervisorProfile, DiplomaTopic.supervisor_id == SupervisorProfile.id)
            .where(SupervisorProfile.user_id == supervisor_user_id)
        )
        recipient_ids = {supervisor_user_id}
        recipient_ids.update(uid for uid in student_user_ids_res.scalars().all() if uid)

        for uid in recipient_ids:
            await self._safe_ws_send(uid, payload)

    async def send(self, data: MessageCreateRequest, user: User, db: AsyncSession) -> MessageResponse:
        msg = Message(sender_id=user.id, receiver_id=data.receiver_id,
                      content=data.content, topic_id=data.topic_id)
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        response = MessageResponse.model_validate(msg)
        payload = {"type": "message", "message": response.model_dump(mode="json")}
        await self._safe_ws_send(data.receiver_id, payload)
        await self._safe_ws_send(user.id, payload)
        return response

    async def get_conversation(self, other_user_id: int, user: User, db: AsyncSession) -> list[MessageResponse]:
        """Return direct chat history between current user and another user in chronological order."""
        res = await db.execute(
            select(Message).where(
                or_(
                    (Message.sender_id == user.id) & (Message.receiver_id == other_user_id),
                    (Message.sender_id == other_user_id) & (Message.receiver_id == user.id),
                )
            ).order_by(Message.created_at)
        )
        msgs = res.scalars().all()

        for m in msgs:
            if m.receiver_id == user.id and not m.is_read:
                m.is_read = True
        await db.flush()

        return [MessageResponse.model_validate(m) for m in msgs]

    async def send_group_message(self, data: GroupMessageCreate, user: User, db: AsyncSession) -> MessageResponse:
        """Send a group message visible to all topic participants (receiver_id=None)."""
        topic_res = await db.execute(
            select(DiplomaTopic).where(DiplomaTopic.id == data.topic_id)
        )
        topic = topic_res.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="Mavzu topilmadi")
        is_participant = (
            (user.role == UserRole.STUDENT and user.student_profile and
             topic.student_id == user.student_profile.id) or
            (user.role == UserRole.SUPERVISOR and user.supervisor_profile and
             topic.supervisor_id == user.supervisor_profile.id) or
            user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD)
        )
        if not is_participant:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        msg = Message(sender_id=user.id, receiver_id=None, topic_id=data.topic_id, content=data.content)
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        return MessageResponse.model_validate(msg)

    async def get_group_messages(self, topic_id: int, user: User, db: AsyncSession) -> list[MessageResponse]:
        """Get all group messages for a topic."""
        topic_res = await db.execute(select(DiplomaTopic).where(DiplomaTopic.id == topic_id))
        topic = topic_res.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="Mavzu topilmadi")
        is_participant = (
            (user.role == UserRole.STUDENT and user.student_profile and
             topic.student_id == user.student_profile.id) or
            (user.role == UserRole.SUPERVISOR and user.supervisor_profile and
             topic.supervisor_id == user.supervisor_profile.id) or
            user.role in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD)
        )
        if not is_participant:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        res = await db.execute(
            select(Message).where(
                Message.topic_id == topic_id,
                Message.receiver_id == None,  # noqa: E711
            ).order_by(Message.created_at)
        )
        return [MessageResponse.model_validate(m) for m in res.scalars().all()]

    async def search_users(self, q: str, user: User, db: AsyncSession) -> list:
        """Search users by name or email for starting a new conversation."""
        result = await db.execute(
            select(User).where(
                or_(User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")),
                User.is_active == True,  # noqa: E712
                User.id != user.id,
            ).limit(20)
        )
        return result.scalars().all()

    async def get_my_supervisor(self, user: User, db: AsyncSession):
        """Return the supervisor info for a student based on their approved topic."""
        if user.role != UserRole.STUDENT or not user.student_profile:
            raise HTTPException(status_code=403, detail="Faqat talabalar uchun")
        topic_res = await db.execute(
            select(DiplomaTopic)
            .where(
                DiplomaTopic.student_id == user.student_profile.id,
                DiplomaTopic.supervisor_id != None,  # noqa: E711
                DiplomaTopic.status == TopicStatus.APPROVED,
            )
            .options(
                selectinload(DiplomaTopic.supervisor).selectinload(SupervisorProfile.user)
            )
            .order_by(DiplomaTopic.updated_at.desc())
            .limit(1)
        )
        topic = topic_res.scalar_one_or_none()
        if not topic or not topic.supervisor or not topic.supervisor.user:
            return None
        sup_user = topic.supervisor.user
        return {
            "user_id": sup_user.id,
            "full_name": sup_user.full_name,
            "email": sup_user.email,
            "phone": sup_user.phone,
            "topic_id": topic.id,
            "topic_title": topic.title,
        }

    _GROUP_OFFSET = 1_000_000

    async def _get_supervisor_virtual_topic_id(self, supervisor_user_id: int, db: AsyncSession) -> int:
        """Returns the virtual topic_id used to store supervisor group messages."""
        res = await db.execute(select(SupervisorProfile).where(SupervisorProfile.user_id == supervisor_user_id))
        sp = res.scalar_one_or_none()
        if not sp:
            raise HTTPException(status_code=404, detail="Rahbar topilmadi")
        return sp.id + self._GROUP_OFFSET

    async def send_supervisor_group_message(
        self, data: SupervisorGroupMessageCreate, user: User, db: AsyncSession
    ) -> MessageResponse:
        """Send a message to the supervisor's group (all his students + himself)."""
        virtual_topic_id = await self._get_supervisor_virtual_topic_id(data.supervisor_user_id, db)
        is_allowed = False
        if user.role == UserRole.SUPERVISOR and user.id == data.supervisor_user_id:
            is_allowed = True
        elif user.role == UserRole.STUDENT and user.student_profile:
            topic_res = await db.execute(
                select(DiplomaTopic).join(SupervisorProfile, DiplomaTopic.supervisor_id == SupervisorProfile.id)
                .where(
                    SupervisorProfile.user_id == data.supervisor_user_id,
                    DiplomaTopic.student_id == user.student_profile.id,
                )
                .limit(1)
            )
            is_allowed = topic_res.scalar_one_or_none() is not None
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        msg = Message(sender_id=user.id, receiver_id=None, topic_id=virtual_topic_id, content=data.content)
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        r = MessageResponse.model_validate(msg)
        r.sender_name = user.full_name

        payload = {
            "type": "supervisor_group_message",
            "supervisor_user_id": data.supervisor_user_id,
            "message": r.model_dump(mode="json"),
        }
        await self._broadcast_supervisor_group_message(data.supervisor_user_id, payload, db)
        return r

    async def get_supervisor_group_messages(
        self, supervisor_user_id: int, user: User, db: AsyncSession
    ) -> list[MessageResponse]:
        """Get messages for the supervisor's group."""
        virtual_topic_id = await self._get_supervisor_virtual_topic_id(supervisor_user_id, db)
        res = await db.execute(
            select(Message).where(
                Message.topic_id == virtual_topic_id,
                Message.receiver_id == None,  # noqa: E711
            ).order_by(Message.created_at)
        )
        msgs = res.scalars().all()
        sender_ids = list({m.sender_id for m in msgs})
        sender_map: dict[int, str] = {}
        if sender_ids:
            users_res = await db.execute(select(User).where(User.id.in_(sender_ids)))
            for u in users_res.scalars().all():
                sender_map[u.id] = u.full_name
        result = []
        for m in msgs:
            r = MessageResponse.model_validate(m)
            r.sender_name = sender_map.get(m.sender_id)
            result.append(r)
        return result

    async def get_contacts(self, user: User, db: AsyncSession) -> list[ConversationContactResponse]:
        res = await db.execute(
            select(Message).where(
                or_(Message.sender_id == user.id, Message.receiver_id == user.id)
            ).order_by(Message.created_at.desc())
        )
        msgs = res.scalars().all()

        seen: set[int] = set()
        partner_ids: list[int] = []
        for m in msgs:
            pid = m.receiver_id if m.sender_id == user.id else m.sender_id
            if pid not in seen:
                seen.add(pid)
                partner_ids.append(pid)

        if not partner_ids:
            return []

        users_res = await db.execute(select(User).where(User.id.in_(partner_ids)))
        users_map: dict[int, User] = {u.id: u for u in users_res.scalars().all()}

        contacts: list[ConversationContactResponse] = []
        for pid in partner_ids:
            partner = users_map.get(pid)
            if not partner:
                continue
            last_msg = next(
                (m for m in msgs
                 if (m.sender_id == user.id and m.receiver_id == pid)
                 or (m.sender_id == pid and m.receiver_id == user.id)),
                None,
            )
            if not last_msg:
                continue
            unread = sum(
                1 for m in msgs
                if m.sender_id == pid and m.receiver_id == user.id and not m.is_read
            )
            contacts.append(ConversationContactResponse(
                user_id=pid,
                full_name=partner.full_name,
                last_message=last_msg.content[:80],
                last_message_at=last_msg.created_at,
                unread_count=unread,
            ))
        return contacts



class NotificationService:
    async def get_list(self, user: User, db: AsyncSession) -> list[NotificationResponse]:
        res = await db.execute(
            select(Notification).where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc()).limit(50)
        )
        return [NotificationResponse.model_validate(n) for n in res.scalars().all()]

    async def mark_read(self, notification_id: int, user: User, db: AsyncSession):
        res = await db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
        )
        n = res.scalar_one_or_none()
        if not n:
            raise HTTPException(status_code=404, detail="Bildirishnoma topilmadi")
        n.is_read = True
        await db.flush()
        return {"message": "O'qildi"}

    async def mark_all_read(self, user: User, db: AsyncSession):
        res = await db.execute(
            select(Notification).where(Notification.user_id == user.id, Notification.is_read == False)
        )
        for n in res.scalars().all():
            n.is_read = True
        await db.flush()
        return {"message": "Hammasi o'qildi"}

    async def create_notification(self, user_id: int, ntype: NotificationType,
                                   title: str, body: str, db: AsyncSession):
        await _notify(user_id, ntype, title, body, db)
        res = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.type == ntype, Notification.title == title)
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def check_deadline_reminders(self, db: AsyncSession, days_warning: int = 3):
        """Deadline eslatmalarini tekshirish va yuborish."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        warning_date = now + timedelta(days=days_warning)

        sent_count = 0

        res = await db.execute(
            select(DiplomaStage)
            .options(selectinload(DiplomaStage.topic).selectinload(DiplomaTopic.student).selectinload(StudentProfile.user))
            .where(
                DiplomaStage.deadline != None,
                DiplomaStage.deadline <= warning_date,
                DiplomaStage.deadline > now,
                DiplomaStage.status != StageStatus.APPROVED,
            )
        )
        stages = res.scalars().all()

        for stage in stages:
            if not stage.topic or not stage.topic.student:
                continue
            user = stage.topic.student.user
            if not user:
                continue

            days_left = (stage.deadline - now).days
            title = f"⏰ Deadline yaqinlashmoqda!"
            body = f"'{stage.name}' bosqichi uchun {days_left} kun qoldi. Mavzu: {stage.topic.title}"

            await _notify(user.id, NotificationType.DEADLINE_REMINDER, title, body, db)

            if stage.topic.supervisor:
                sup_user = stage.topic.supervisor.user
                if sup_user:
                    sup_title = f"⏰ Talaba deadline yaqin"
                    sup_body = f"{user.full_name} - '{stage.name}' bosqichi uchun {days_left} kun qoldi"
                    await _notify(sup_user.id, NotificationType.DEADLINE_REMINDER, sup_title, sup_body, db)

            sent_count += 1

        return {"sent_notifications": sent_count}


class CatalogService:
    """Compatibility wrapper; catalog logic is implemented in TopicService."""

    async def create(self, data: CatalogTopicCreateRequest, user: User, db: AsyncSession):
        return await TopicService().create_catalog(data, user, db)

    async def get_list(
        self,
        user: User,
        db: AsyncSession,
        academic_year: str | None = None,
        available_only: bool = False,
    ):
        return await TopicService().get_catalog(
            db,
            include_taken=not available_only,
            page=1,
            page_size=1000,
            academic_year=academic_year,
        )

    async def update(self, catalog_id: int, data, user: User, db: AsyncSession):
        raise HTTPException(status_code=410, detail="Catalog update endpoint eskirgan")

    async def delete(self, catalog_id: int, user: User, db: AsyncSession):
        raise HTTPException(status_code=410, detail="Catalog delete endpoint eskirgan")

    async def student_select(self, catalog_id: int, data, user: User, db: AsyncSession):
        return await TopicService().select_topic(catalog_id, user, db)

    async def auto_assign(self, academic_year: str, user: User, db: AsyncSession):
        return await TopicService().auto_assign(academic_year, user, db)


class ReportService:
    async def dashboard(self, user: User, db: AsyncSession) -> DashboardStats:
        q = select(DiplomaTopic)
        if user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile:
                return DashboardStats(
                    total_topics=0, approved=0, pending=0, rejected=0, draft=0,
                    avg_progress=0.0, topics_by_status=[]
                )
            q = q.where(DiplomaTopic.supervisor_id == user.supervisor_profile.id)

        res = await db.execute(q)
        topics = res.scalars().all()

        by_status: dict[str, int] = {}
        for t in topics:
            by_status[t.status.value] = by_status.get(t.status.value, 0) + 1

        avg_progress = sum(t.progress for t in topics) / len(topics) if topics else 0
        return DashboardStats(
            total_topics=len(topics),
            approved=by_status.get("approved", 0),
            pending=by_status.get("pending", 0),
            rejected=by_status.get("rejected", 0),
            draft=by_status.get("draft", 0),
            avg_progress=round(avg_progress, 1),
            topics_by_status=[TopicStatItem(status=k, count=v) for k, v in by_status.items()],
        )

    async def advanced_analytics(self, db: AsyncSession) -> dict:
        now = datetime.now(timezone.utc)

        total_topics = (await db.execute(select(func.count(DiplomaTopic.id)))).scalar() or 0
        total_students = (await db.execute(select(func.count(StudentProfile.id)))).scalar() or 0
        total_supervisors = (await db.execute(select(func.count(SupervisorProfile.id)))).scalar() or 0
        avg_progress = round(float((await db.execute(select(func.avg(DiplomaTopic.progress)))).scalar() or 0), 1)

        status_res = await db.execute(
            select(DiplomaTopic.status, func.count(DiplomaTopic.id)).group_by(DiplomaTopic.status)
        )
        topics_by_status = [
            {"status": s.value if hasattr(s, "value") else str(s), "count": c}
            for s, c in status_res.all()
        ]

        risk_scores = (await db.execute(select(RiskAssessment.risk_score))).scalars().all()
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for score in risk_scores:
            s = float(score or 0)
            if s >= 90:
                risk_distribution["critical"] += 1
            elif s >= 80:
                risk_distribution["high"] += 1
            elif s >= 60:
                risk_distribution["medium"] += 1
            else:
                risk_distribution["low"] += 1

        overdue_count = (await db.execute(
            select(func.count(DiplomaStage.id)).where(
                (DiplomaStage.deadline < now) & (DiplomaStage.status.not_in(["approved", "submitted"]))
            )
        )).scalar() or 0

        submitted_count = (await db.execute(
            select(func.count(DiplomaStage.id)).where(DiplomaStage.status == "submitted")
        )).scalar() or 0

        from sqlalchemy import case
        sup_stats_res = await db.execute(
            select(
                User.id,
                User.full_name,
                func.count(DiplomaTopic.id).label("total"),
                func.avg(DiplomaTopic.progress).label("avg_progress"),
                func.sum(case((RiskAssessment.risk_score >= 80, 1), else_=0)).label("high_risk"),
            )
            .join(SupervisorProfile, User.id == SupervisorProfile.user_id)
            .outerjoin(DiplomaTopic, DiplomaTopic.supervisor_id == SupervisorProfile.id)
            .outerjoin(RiskAssessment, RiskAssessment.topic_id == DiplomaTopic.id)
            .group_by(User.id, User.full_name)
            .having(func.count(DiplomaTopic.id) > 0)
        )
        supervisor_stats = [
            {
                "supervisor_id": row.id,
                "supervisor_name": row.full_name,
                "total_students": row.total,
                "avg_progress": round(float(row.avg_progress or 0), 1),
                "high_risk_count": int(row.high_risk or 0),
            }
            for row in sup_stats_res.all()
        ]

        return {
            "total_topics": total_topics,
            "total_students": total_students,
            "total_supervisors": total_supervisors,
            "avg_progress": avg_progress,
            "topics_by_status": topics_by_status,
            "risk_distribution": risk_distribution,
            "supervisor_stats": supervisor_stats,
            "overdue_stages_count": overdue_count,
            "submitted_stages_count": submitted_count,
        }



class AIAnalysisService:
    def _analyze_text_content(self, content: str) -> dict:
        import re
        text = content.strip()
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = len(words)
        unique_words = len(set(words))
        vocab_richness = round(unique_words / max(word_count, 1) * 100, 1)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_count = len(sentences)
        avg_wps = round(word_count / max(sentence_count, 1), 1)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = max(len(paragraphs), 1)
        length_score  = min(25.0, word_count / 3000 * 25)
        vocab_score   = min(25.0, vocab_richness / 2)
        sent_score    = min(25.0, avg_wps / 20 * 25)
        struct_score  = min(25.0, paragraph_count / 5 * 25)
        quality_score = round(length_score + vocab_score + sent_score + struct_score, 1)
        return {
            'word_count': word_count,
            'unique_words': unique_words,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_words_per_sentence': avg_wps,
            'vocab_richness': vocab_richness,
            'quality_score': quality_score,
            'summary': (
                f"Matn {word_count} so'z, {sentence_count} gap, "
                f"{paragraph_count} paragrafdan iborat. "
                f"Sifat ko'rsatkichi: {quality_score}/100."
            ),
        }

    async def analyze_text(
        self, data: TextAnalysisRequest, user: User, db: AsyncSession
    ) -> AIAnalysisResponse:
        import json
        result = self._analyze_text_content(data.content)
        analysis = AIAnalysis(
            topic_id=data.topic_id,
            analysis_type='text_quality',
            score=result['quality_score'],
            result=json.dumps({**result, 'original_content': data.content[:2000]}, ensure_ascii=False),
        )
        db.add(analysis)
        await db.flush()
        await db.refresh(analysis)
        return AIAnalysisResponse.model_validate(analysis)

    async def get_text_quality_analyses(
        self, topic_id: int, db: AsyncSession
    ) -> list[AIAnalysisResponse]:
        res = await db.execute(
            select(AIAnalysis)
            .where(
                (AIAnalysis.topic_id == topic_id) &
                (AIAnalysis.analysis_type == 'text_quality')
            )
            .order_by(AIAnalysis.created_at.desc())
        )
        return [AIAnalysisResponse.model_validate(a) for a in res.scalars().all()]



class RiskService:
    def __init__(self):
        """Initialize RiskService and load ML model if available"""
        model_dir = Path(__file__).parent.parent.parent / "models"
        self.use_ml_model = (model_dir / "risk_rf_model.pkl").exists()
        
        if self.use_ml_model:
            try:
                self.ml_model = joblib.load(model_dir / "risk_rf_model.pkl")
                self.ml_scaler = joblib.load(model_dir / "risk_scaler.pkl")
                logger.info("✓ Random Forest model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load ML model: {e}. Falling back to rule-based.")
                self.use_ml_model = False
        else:
            logger.info("ML model not found. Using rule-based risk assessment.")
    
    @staticmethod
    def _risk_level_from_score(risk_score: float) -> str:
        if risk_score >= 90:
            return 'critical'
        if risk_score >= 80:
            return 'high'
        if risk_score >= 60:
            return 'medium'
        return 'low'

    def _normalized_assessment_level(self, assessment: RiskAssessment) -> str:
        return self._risk_level_from_score(float(assessment.risk_score or 0))

    async def assess_risk(
        self, topic_id: int, db: AsyncSession
    ) -> RiskAssessmentResponse:
        import json
        logger.info(f"assess_risk: Starting for topic_id={topic_id}")

        topic_res = await db.execute(
            select(DiplomaTopic)
            .where(DiplomaTopic.id == topic_id)
            .options(selectinload(DiplomaTopic.stages))
        )
        topic = topic_res.scalar_one_or_none()
        if not topic:
            logger.warning(f"assess_risk: Topic not found: {topic_id}")
            raise HTTPException(status_code=404, detail="Mavzu topilmadi")
        logger.info(f"assess_risk: Found topic: {topic.title}, status={topic.status.value}")

        tasks_res = await db.execute(select(Task).where(Task.topic_id == topic_id))
        tasks = tasks_res.scalars().all()

        meetings_res = await db.execute(select(Meeting).where(Meeting.topic_id == topic_id))
        meetings = meetings_res.scalars().all()

        now = datetime.now(timezone.utc)
        
        def make_aware(dt):
            if dt is None:
                return None
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        created_at = make_aware(topic.created_at)
        defense_date = make_aware(topic.defense_date)
        
        risk_score = 0.0
        risk_level = 'low'
        factors: list[dict] = []
        
        if self.use_ml_model:
            try:
                if defense_date and created_at:
                    total_days = (defense_date - created_at).days
                    passed_days = (now - created_at).days
                    if total_days > 0:
                        expected_progress = min(100.0, (passed_days / total_days) * 100)
                        progress_gap = max(0, expected_progress - topic.progress)
                    else:
                        progress_gap = 0
                else:
                    progress_gap = 0
                
                stages = topic.stages
                if stages:
                    approved_cnt = sum(1 for s in stages if s.status.value == 'approved')
                    stage_completion = approved_cnt / len(stages)
                else:
                    stage_completion = 0
                
                if tasks:
                    done_cnt = sum(1 for t in tasks if t.is_done)
                    task_completion = done_cnt / len(tasks)
                else:
                    task_completion = 0
                
                meeting_count = len(meetings)
                
                days_passed = (now - created_at).days if created_at else 0
                
                status_map = {'draft': 0, 'pending': 1, 'approved': 2, 'rejected': -1}
                status_encoded = status_map.get(topic.status.value, 0)
                
                progress = topic.progress
                
                features = np.array([[
                    progress_gap,           # 0
                    stage_completion,       # 1
                    task_completion,        # 2
                    meeting_count,          # 3
                    days_passed,            # 4
                    status_encoded,         # 5
                    progress,               # 6
                ]])
                
                features_scaled = self.ml_scaler.transform(features)
                
                risk_level_pred = self.ml_model.predict(features_scaled)[0]
                risk_proba = self.ml_model.predict_proba(features_scaled)[0].max()
                risk_score = risk_proba * 100
                risk_level = self._risk_level_from_score(risk_score)

                factors.append({
                    'factor': 'ml_model_prediction',
                    'severity': 'info',
                    'message': f"ML model class: {risk_level_pred}, normalized level: {risk_level} ({risk_score:.1f}% confidence)"
                })
                
                logger.info(f"assess_risk: ML prediction for topic {topic_id}: model_class={risk_level_pred}, normalized_level={risk_level}, score={risk_score:.1f}%")

            except Exception as e:
                logger.warning(f"assess_risk: ML prediction failed: {e}. Falling back to rule-based.")
                self.use_ml_model = False
                risk_score = 0.0
                factors = []
                risk_level = 'low'
        
        if not self.use_ml_model:
            if defense_date and created_at:
                total_days = (defense_date - created_at).days
                passed_days = (now - created_at).days
                if total_days > 0 and passed_days >= 0:
                    expected = min(100.0, passed_days / total_days * 100)
                    gap = expected - topic.progress
                    if gap > 30:
                        risk_score += 35
                        factors.append({'factor': 'progress_lag', 'severity': 'critical',
                                        'message': f"Progress kutilganidan {gap:.0f}% orqada"})
                    elif gap > 15:
                        risk_score += 20
                        factors.append({'factor': 'progress_lag', 'severity': 'high',
                                        'message': f"Progress kutilganidan {gap:.0f}% orqada"})
                    elif gap < -20:
                        risk_score = max(0, risk_score - 15)
                        factors.append({'factor': 'ahead_of_schedule', 'severity': 'positive',
                                        'message': f"Progress rejalashtirilgandan {abs(gap):.0f}% oldinroq"})

            if topic.status.value == 'draft':
                risk_score += 15
                factors.append({'factor': 'not_submitted', 'severity': 'medium',
                                'message': "Mavzu hali tasdiqlanmagan"})
            elif topic.status.value == 'rejected':
                risk_score += 20
                factors.append(
                    {
                        'factor': 'rejected',
                        'severity': 'high',
                        'message': "Mavzu rad etilgan",
                    }
                )

            stages = topic.stages
            if stages:
                approved_cnt = sum(1 for s in stages if s.status.value == 'approved')
                total_cnt = len(stages)
                rate = approved_cnt / total_cnt
                
                overdue_uncompleted = [s for s in stages
                           if s.deadline and make_aware(s.deadline) < now 
                           and s.status.value not in ('approved', 'submitted')]
                
                if rate < 0.25:
                    risk_score += 25
                    factors.append({'factor': 'low_stage_completion', 'severity': 'high',
                                    'message': f"Faqat {approved_cnt}/{total_cnt} bosqich tasdiqlangan"})
                elif rate < 0.5:
                    risk_score += 15
                    factors.append({'factor': 'low_stage_completion', 'severity': 'medium',
                                    'message': f"{approved_cnt}/{total_cnt} bosqich tasdiqlangan"})
                elif rate >= 0.8:
                    risk_score = max(0, risk_score - 10)
                    factors.append({'factor': 'high_stage_completion', 'severity': 'positive',
                                    'message': f"{approved_cnt}/{total_cnt} bosqich tasdiqlangan - yaxshi natiја"})
                
                if overdue_uncompleted:
                    add = min(len(overdue_uncompleted) * 8, 24)
                    risk_score += add
                    factors.append({'factor': 'overdue_stages', 'severity': 'critical',
                                    'message': f"{len(overdue_uncompleted)} ta bosqichning muddati o'tgan"})
            else:
                risk_score += 10
                factors.append({'factor': 'no_stages', 'severity': 'medium',
                                'message': "Bosqichlar aniqlanmagan"})

            if tasks:
                done_cnt = sum(1 for t in tasks if t.is_done)
                task_rate = done_cnt / len(tasks)
                if task_rate < 0.3:
                    risk_score += 10
                    factors.append({'factor': 'low_task_completion', 'severity': 'medium',
                                    'message': f"Vazifalar {task_rate * 100:.0f}% bajarilgan"})
                elif task_rate >= 0.7:
                    risk_score = max(0, risk_score - 5)
                    factors.append({'factor': 'high_task_completion', 'severity': 'positive',
                                    'message': f"Vazifalar {task_rate * 100:.0f}% bajarilgan"})

            if len(meetings) >= 4:
                risk_score = max(0, risk_score - 5)
                factors.append({'factor': 'regular_meetings', 'severity': 'positive',
                                'message': f"Supervisor bilan {len(meetings)} ta uchrashuv o'tkazilgan"})
            elif len(meetings) < 2:
                risk_score += 5
                factors.append({'factor': 'low_meetings', 'severity': 'low',
                                'message': "Kamdan-kam uchrashuv o'tkazilgan"})

            risk_score = max(0, min(100.0, risk_score))
            risk_level = self._risk_level_from_score(risk_score)

        recs: list[str] = []
        factor_names = {f['factor'] for f in factors}
        if 'progress_lag' in factor_names:
            recs.append("Bosqich ishlarini tezlashtirish kerak")
        if 'overdue_stages' in factor_names:
            recs.append("Muddati o'tgan bosqichlarni imkon qadar tezroq tugatish zarur")
        if 'low_stage_completion' in factor_names:
            recs.append("Qolgan bosqichlarni rejalashtirib, supervisor bilan muhokama qiling")
        if 'low_meetings' in factor_names:
            recs.append("Supervisor bilan tez-tez uchrashib boring")
        if 'not_submitted' in factor_names:
            recs.append("Mavzuni imkon qadar tezroq tasdiqlatish kerak")
        recommendation = '; '.join(recs) or "Ishlashda davom eting"

        existing_res = await db.execute(
            select(RiskAssessment).where(RiskAssessment.topic_id == topic_id)
        )
        existing = existing_res.scalar_one_or_none()
        logger.info(f"assess_risk: Risk score={risk_score}, level={risk_level}, factors count={len(factors)}")
        if existing:
            logger.info(f"assess_risk: Updating existing assessment for topic {topic_id}")
            existing.risk_score = risk_score
            existing.risk_level = risk_level
            existing.factors = json.dumps(factors, ensure_ascii=False)
            existing.recommendation = recommendation
            existing.assessed_at = now
            assessment = existing
        else:
            logger.info(f"assess_risk: Creating new assessment for topic {topic_id}")
            assessment = RiskAssessment(
                topic_id=topic_id,
                risk_score=risk_score,
                risk_level=risk_level,
                factors=json.dumps(factors, ensure_ascii=False),
                recommendation=recommendation,
            )
            db.add(assessment)
            await db.flush()
            logger.info(f"assess_risk: Flushed new assessment, id={assessment.id}")
            await db.refresh(assessment)
        logger.info(f"assess_risk: Assessment complete, validating response")
        result = RiskAssessmentResponse.model_validate(assessment)
        logger.info(f"assess_risk: Successfully validated response for topic {topic_id}")
        return result

    async def get_supervisor_risks(self, supervisor_id: int, db: AsyncSession) -> list[dict]:
        """Get risk assessments for a supervisor's students"""
        res = await db.execute(
            select(RiskAssessment, DiplomaTopic)
            .join(DiplomaTopic, RiskAssessment.topic_id == DiplomaTopic.id)
            .where(DiplomaTopic.supervisor_id == supervisor_id)
            .order_by(RiskAssessment.risk_score.desc())
        )
        return [
            {
                'id': a.id,
                'topic_id': a.topic_id,
                'topic_title': t.title,
                'topic_status': t.status.value,
                'topic_progress': t.progress,
                'risk_score': a.risk_score,
                'risk_level': self._normalized_assessment_level(a),
                'factors': a.factors,
                'recommendation': a.recommendation,
                'assessed_at': a.assessed_at.isoformat(),
            }
            for a, t in res.all()
        ]

    async def get_student_risk(self, student_profile_id: int, db: AsyncSession) -> list[dict]:
        """Get a student's own risk assessment"""
        res = await db.execute(
            select(RiskAssessment, DiplomaTopic)
            .join(DiplomaTopic, RiskAssessment.topic_id == DiplomaTopic.id)
            .where(DiplomaTopic.student_id == student_profile_id)
            .order_by(RiskAssessment.assessed_at.desc())
        )
        return [
            {
                'id': a.id,
                'topic_id': a.topic_id,
                'topic_title': t.title,
                'topic_status': t.status.value,
                'topic_progress': t.progress,
                'risk_score': a.risk_score,
                'risk_level': self._normalized_assessment_level(a),
                'factors': a.factors,
                'recommendation': a.recommendation,
                'assessed_at': a.assessed_at.isoformat(),
            }
            for a, t in res.all()
        ]

    async def get_all_risks(self, user: User, db: AsyncSession) -> list[dict]:
        """Get risk assessments
        - SUPERVISOR: o'z o'quvchilari mavzularining risk'ini ko'radi
        - STUDENT: o'zining risk'ini ko'radi
        - ADMIN/KAFEDRA_HEAD: barcha risk'larni ko'radi
        """
        q = (
            select(RiskAssessment, DiplomaTopic)
            .join(DiplomaTopic, RiskAssessment.topic_id == DiplomaTopic.id)
        )

        if user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile:
                return []
            q = q.where(DiplomaTopic.supervisor_id == user.supervisor_profile.id)
        elif user.role == UserRole.STUDENT:
            if not user.student_profile:
                return []
            q = q.where(DiplomaTopic.student_id == user.student_profile.id)
        elif user.role not in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")

        res = await db.execute(
            q.order_by(RiskAssessment.risk_score.desc())
        )
        return [
            {
                'id': a.id,
                'topic_id': a.topic_id,
                'topic_title': t.title,
                'topic_status': t.status.value,
                'topic_progress': t.progress,
                'risk_score': a.risk_score,
                'risk_level': self._normalized_assessment_level(a),
                'factors': a.factors,
                'recommendation': a.recommendation,
                'assessed_at': a.assessed_at.isoformat(),
            }
            for a, t in res.all()
        ]

    async def get_risk(
        self, topic_id: int, user: User, db: AsyncSession
    ) -> RiskAssessmentResponse | None:
        """Get risk assessment for topic
        - SUPERVISOR: faqat o'z o'quvchilari mavzulariga ruxsat
        - STUDENT: faqat o'z mavzusiga ruxsat
        - ADMIN/KAFEDRA_HEAD: barcha mavzularga ruxsat
        """
        topic_res = await db.execute(
            select(DiplomaTopic).where(DiplomaTopic.id == topic_id)
        )
        topic = topic_res.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="Mavzu topilmadi")

        if user.role == UserRole.SUPERVISOR:
            if not user.supervisor_profile or topic.supervisor_id != user.supervisor_profile.id:
                raise HTTPException(status_code=403, detail="Faqat o'z o'quvchilari mavzularining risk'ini ko'rishingiz mumkin")
        elif user.role == UserRole.STUDENT:
            if not user.student_profile or topic.student_id != user.student_profile.id:
                raise HTTPException(status_code=403, detail="Faqat o'z risk'ingizni ko'rishingiz mumkin")
        elif user.role not in (UserRole.ADMIN, UserRole.KAFEDRA_HEAD):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")

        res = await db.execute(
            select(RiskAssessment).where(RiskAssessment.topic_id == topic_id)
        )
        a = res.scalar_one_or_none()
        if not a:
            return None
        out = RiskAssessmentResponse.model_validate(a)
        out.risk_level = self._normalized_assessment_level(a)
        return out

