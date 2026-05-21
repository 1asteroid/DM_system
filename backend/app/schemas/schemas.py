from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from ..models.models import UserRole, TopicStatus, StageStatus, MeetingStatus, NotificationType


# ═══════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.STUDENT
    # Student fields
    group_id: int | None = None
    student_id: str | None = None
    # Supervisor fields
    academic_rank: str | None = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if len(v) < 8:
            raise ValueError("Parol kamida 8 ta belgi bo'lishi kerak")
        return v


class UserCreateRequest(BaseModel):
    """Admin tomonidan user yaratish uchun schema (kafedra_id bilan)"""
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole
    kafedra_id: int | None = None
    # Student fields
    group_id: int | None = None
    student_id: str | None = None
    # Supervisor fields
    academic_rank: str | None = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if len(v) < 8:
            raise ValueError("Parol kamida 8 ta belgi bo'lishi kerak")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=200)
    phone: str | None = Field(None, max_length=20)


class TelegramLinkRequest(BaseModel):
    telegram_id: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    kafedra_id: int | None = None
    telegram_id: str | None = None
    avatar_url: str | None = None
    # Student info
    group_id: int | None = None
    group_name: str | None = None
    student_id: str | None = None
    # Supervisor info
    academic_rank: str | None = None
    supervisor_profile_id: int | None = None
    model_config = {"from_attributes": True}


class SupervisorStudentResponse(BaseModel):
    student_id: int
    student_name: str
    student_email: str | None = None
    topic_id: int
    topic_title: str
    status: TopicStatus
    progress: float = 0.0
    stages_total: int = 0
    stages_approved: int = 0
    stages_submitted: int = 0
    stages_rejected: int = 0


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ═══════════════════════════════════════════════
# KAFEDRA & GROUP SCHEMAS
# ═══════════════════════════════════════════════

class KafedraResponse(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: int
    name: str
    year: int | None = None
    direction_id: int | None = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# TOPIC SCHEMAS
# ═══════════════════════════════════════════════

class TopicCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    title_en: str | None = None
    description: str | None = None
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    supervisor_user_id: int | None = None  # user.id of the supervisor
    defense_date: datetime | None = None


class TopicProposeRequest(BaseModel):
    """Used by students to suggest a custom topic (pending approval)."""
    title: str = Field(..., min_length=5, max_length=500)
    title_en: str | None = None
    description: str | None = None
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    supervisor_user_id: int  # required — student must choose a supervisor
    defense_date: datetime | None = None


class TopicUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=500)
    title_en: str | None = None
    description: str | None = None
    defense_date: datetime | None = None


class TopicRejectRequest(BaseModel):
    reason: str = Field(..., min_length=5)


class TopicAssignSupervisorRequest(BaseModel):
    supervisor_id: int


class TopicApproveRequest(BaseModel):
    supervisor_id: int | None = None


# ═══════════════════════════════════════════════
# CATALOG SCHEMAS
# ═══════════════════════════════════════════════

class CatalogTopicCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    title_en: str | None = None
    description: str | None = None
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    supervisor_user_id: int  # user.id of the supervisor
    selection_deadline: datetime
    defense_date: datetime | None = None


class CatalogTopicResponse(BaseModel):
    id: int
    title: str
    title_en: str | None
    description: str | None
    academic_year: str
    supervisor_id: int | None
    selection_deadline: datetime | None
    defense_date: datetime | None
    is_taken: bool
    created_at: datetime


class CatalogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CatalogTopicResponse]


class StageShort(BaseModel):
    id: int
    name: str
    order: int
    status: StageStatus
    weight: float
    deadline: datetime | None = None
    submitted_at: datetime | None = None
    comment: str | None = None
    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: int
    title: str
    title_en: str | None
    description: str | None
    status: TopicStatus
    academic_year: str
    progress: float
    supervisor_id: int | None = None
    student_id: int | None = None
    student_name: str | None = None
    defense_date: datetime | None
    approved_at: datetime | None
    reject_reason: str | None
    created_at: datetime
    updated_at: datetime
    stages_submitted: int = 0   # stages waiting for supervisor review
    model_config = {"from_attributes": True}


class TopicDetailResponse(TopicResponse):
    stages: list[StageShort] = []
    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TopicResponse]


# ═══════════════════════════════════════════════
# STAGE SCHEMAS
# ═══════════════════════════════════════════════

class StageCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    order: int = Field(..., ge=1)
    weight: float = Field(10.0, ge=0, le=100)
    deadline: datetime | None = None


class StageUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    weight: float | None = None
    deadline: datetime | None = None


class StageReviewRequest(BaseModel):
    approved: bool
    comment: str | None = None


class StageResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    description: str | None
    order: int
    status: StageStatus
    weight: float
    deadline: datetime | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    comment: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# FILE SCHEMAS
# ═══════════════════════════════════════════════

class FileResponse(BaseModel):
    id: int
    topic_id: int
    stage_id: int | None
    file_name: str
    file_size: int | None
    file_type: str | None
    version: int
    is_final: bool
    plagiat_score: float | None
    created_at: datetime
    file_url: str | None = None
    model_config = {"from_attributes": True}


class FileCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class FileCommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# TASK SCHEMAS
# ═══════════════════════════════════════════════

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str | None = None
    deadline: datetime | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    is_done: bool | None = None


class TaskResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    description: str | None
    deadline: datetime | None
    is_done: bool
    done_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# MEETING SCHEMAS
# ═══════════════════════════════════════════════

class MeetingCreateRequest(BaseModel):
    title: str
    reason: str | None = None
    topic_id: int | None = None
    scheduled_at: datetime
    duration_min: int = Field(30, ge=10, le=180)
    location: str | None = None
    attendee_ids: list[int] = Field(default_factory=list)


class MeetingUpdateRequest(BaseModel):
    title: str | None = None
    reason: str | None = None
    scheduled_at: datetime | None = None
    duration_min: int | None = None
    location: str | None = None
    status: MeetingStatus | None = None
    notes: str | None = None


class MeetingAttendeeInfo(BaseModel):
    user_id: int
    full_name: str
    model_config = {"from_attributes": True}


class MeetingResponse(BaseModel):
    id: int
    title: str
    reason: str | None
    topic_id: int | None
    scheduled_at: datetime
    duration_min: int
    location: str | None
    status: MeetingStatus
    notes: str | None
    created_by: int | None
    created_at: datetime
    attendees: list[MeetingAttendeeInfo] = []
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# MESSAGE SCHEMAS
# ═══════════════════════════════════════════════

class MessageCreateRequest(BaseModel):
    receiver_id: int
    content: str = Field(..., min_length=1)
    topic_id: int | None = None


class GroupMessageCreate(BaseModel):
    topic_id: int
    content: str = Field(..., min_length=1)


class SupervisorGroupMessageCreate(BaseModel):
    supervisor_user_id: int
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: str | None = None
    receiver_id: int | None  # None for group (topic) messages
    topic_id: int | None
    content: str
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ConversationContactResponse(BaseModel):
    user_id: int
    full_name: str
    last_message: str
    last_message_at: datetime
    unread_count: int


# ═══════════════════════════════════════════════
# AI ANALYSIS SCHEMAS
# ═══════════════════════════════════════════════

class TextAnalysisRequest(BaseModel):
    topic_id: int
    content: str = Field(..., min_length=10)


class AIAnalysisResponse(BaseModel):
    id: int
    topic_id: int
    file_id: int | None
    analysis_type: str
    score: float
    result: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# RISK ASSESSMENT SCHEMAS
# ═══════════════════════════════════════════════

class RiskAssessmentResponse(BaseModel):
    id: int
    topic_id: int
    risk_score: float
    risk_level: str
    factors: str
    recommendation: str | None
    assessed_at: datetime
    model_config = {"from_attributes": True}


class RiskListItem(BaseModel):
    id: int
    topic_id: int
    topic_title: str
    topic_status: str
    topic_progress: float
    risk_score: float
    risk_level: str
    factors: str
    recommendation: str | None
    assessed_at: str


# ═══════════════════════════════════════════════
# NOTIFICATION SCHEMAS
# ═══════════════════════════════════════════════

class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    title: str
    body: str | None
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# REPORT SCHEMAS
# ═══════════════════════════════════════════════

class TopicStatItem(BaseModel):
    status: str
    count: int


class DashboardStats(BaseModel):
    total_topics: int
    approved: int
    pending: int
    rejected: int
    draft: int
    avg_progress: float
    topics_by_status: list[TopicStatItem]


# ═══════════════════════════════════════════════
# COMMON
# ═══════════════════════════════════════════════

class MessageOnly(BaseModel):
    message: str
