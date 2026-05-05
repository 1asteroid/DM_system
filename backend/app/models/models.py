from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float,
                        ForeignKey, Integer, String, Text)
from sqlalchemy.orm import relationship

from ..core.database import Base


# ── ENUMLAR ──────────────────────────────────────────────────────────────────

class UserRole(str, PyEnum):
    ADMIN        = "admin"
    KAFEDRA_HEAD = "kafedra_head"
    SUPERVISOR   = "supervisor"
    STUDENT      = "student"


class TopicStatus(str, PyEnum):
    DRAFT    = "draft"
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StageStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED   = "submitted"
    APPROVED    = "approved"
    REJECTED    = "rejected"


class MeetingStatus(str, PyEnum):
    PLANNED   = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationType(str, PyEnum):
    DEADLINE_REMINDER = "deadline_reminder"
    NEW_TASK          = "new_task"
    FILE_UPLOADED     = "file_uploaded"
    COMMENT_ADDED     = "comment_added"
    MEETING_SCHEDULED = "meeting_scheduled"
    STATUS_CHANGED    = "status_changed"


# ── TASHKILOT ─────────────────────────────────────────────────────────────────

class Faculty(Base):
    __tablename__ = "faculties"
    id         = Column(Integer, primary_key=True)
    name       = Column(String(200), nullable=False)
    short_name = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    kafedras   = relationship("Kafedra", back_populates="faculty")


class Kafedra(Base):
    __tablename__ = "kafedras"
    id         = Column(Integer, primary_key=True)
    name       = Column(String(200), nullable=False)
    short_name = Column(String(50))
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    faculty    = relationship("Faculty", back_populates="kafedras")
    users      = relationship("User", back_populates="kafedra")
    directions = relationship("Direction", back_populates="kafedra")


class Direction(Base):
    __tablename__ = "directions"
    id         = Column(Integer, primary_key=True)
    name       = Column(String(200), nullable=False)
    code       = Column(String(20))
    kafedra_id = Column(Integer, ForeignKey("kafedras.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    kafedra    = relationship("Kafedra", back_populates="directions")
    groups     = relationship("Group", back_populates="direction")


class Group(Base):
    __tablename__ = "groups"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(50), nullable=False)
    year         = Column(Integer)
    direction_id = Column(Integer, ForeignKey("directions.id"))
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    direction    = relationship("Direction", back_populates="groups")
    students     = relationship("StudentProfile", back_populates="group")


# ── FOYDALANUVCHILAR ──────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    full_name     = Column(String(200), nullable=False)
    email         = Column(String(150), unique=True, nullable=False, index=True)
    phone         = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), nullable=False)
    telegram_id   = Column(String(50), unique=True, nullable=True)
    is_active     = Column(Boolean, default=True)
    avatar_url    = Column(String(300))
    kafedra_id    = Column(Integer, ForeignKey("kafedras.id"), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    kafedra            = relationship("Kafedra", back_populates="users")
    student_profile    = relationship("StudentProfile", back_populates="user", uselist=False)
    supervisor_profile = relationship("SupervisorProfile", back_populates="user", uselist=False)
    notifications      = relationship("Notification", back_populates="user")
    sent_messages      = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), unique=True)
    group_id   = Column(Integer, ForeignKey("groups.id"))
    student_id = Column(String(20), unique=True)
    course     = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user          = relationship("User", back_populates="student_profile")
    group         = relationship("Group", back_populates="students")
    diploma_topic = relationship("DiplomaTopic", back_populates="student", uselist=False)


class SupervisorProfile(Base):
    __tablename__ = "supervisor_profiles"
    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id"), unique=True)
    academic_rank = Column(String(100))
    max_students  = Column(Integer, default=5)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user           = relationship("User", back_populates="supervisor_profile")
    diploma_topics = relationship("DiplomaTopic", back_populates="supervisor")


# ── DIPLOM MAVZUSI ────────────────────────────────────────────────────────────

class DiplomaTopic(Base):
    __tablename__ = "diploma_topics"
    id                 = Column(Integer, primary_key=True, index=True)
    title              = Column(String(500), nullable=False)
    title_en           = Column(String(500))
    description        = Column(Text)
    status             = Column(Enum(TopicStatus), default=TopicStatus.DRAFT, nullable=False)
    academic_year      = Column(String(10), nullable=False)
    progress           = Column(Float, default=0.0)
    student_id         = Column(Integer, ForeignKey("student_profiles.id"), unique=True, nullable=True)
    supervisor_id      = Column(Integer, ForeignKey("supervisor_profiles.id"), nullable=True)
    reviewer_id        = Column(Integer, ForeignKey("users.id"), nullable=True)
    reject_reason      = Column(Text)
    approved_at        = Column(DateTime(timezone=True))
    defense_date       = Column(DateTime(timezone=True))
    # Catalog / template fields
    is_template        = Column(Boolean, default=False)
    selection_deadline = Column(DateTime(timezone=True), nullable=True)
    created_by_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    student    = relationship("StudentProfile", back_populates="diploma_topic")
    supervisor = relationship("SupervisorProfile", back_populates="diploma_topics")
    stages     = relationship("DiplomaStage", back_populates="topic",
                              order_by="DiplomaStage.order", cascade="all, delete-orphan")
    files      = relationship("DiplomaFile", back_populates="topic")
    meetings   = relationship("Meeting", back_populates="topic")
    tasks      = relationship("Task", back_populates="topic")
    ai_analyses     = relationship("AIAnalysis",     back_populates="topic", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="topic", uselist=False, cascade="all, delete-orphan")


# ── BOSQICHLAR ────────────────────────────────────────────────────────────────

class DiplomaStage(Base):
    __tablename__ = "diploma_stages"
    id           = Column(Integer, primary_key=True)
    topic_id     = Column(Integer, ForeignKey("diploma_topics.id"))
    name         = Column(String(200), nullable=False)
    description  = Column(Text)
    order        = Column(Integer, nullable=False)
    status       = Column(Enum(StageStatus), default=StageStatus.NOT_STARTED)
    weight       = Column(Float, default=10.0)
    deadline     = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    reviewed_at  = Column(DateTime(timezone=True))
    comment      = Column(Text)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    topic = relationship("DiplomaTopic", back_populates="stages")
    files = relationship("DiplomaFile", back_populates="stage")


# ── FAYLLAR ───────────────────────────────────────────────────────────────────

class DiplomaFile(Base):
    __tablename__ = "diploma_files"
    id            = Column(Integer, primary_key=True)
    topic_id      = Column(Integer, ForeignKey("diploma_topics.id"))
    stage_id      = Column(Integer, ForeignKey("diploma_stages.id"), nullable=True)
    uploaded_by   = Column(Integer, ForeignKey("users.id"))
    file_name     = Column(String(300), nullable=False)
    file_path     = Column(String(500), nullable=False)
    file_size     = Column(Integer)
    file_type     = Column(String(50))
    version       = Column(Integer, default=1)
    is_final      = Column(Boolean, default=False)
    plagiat_score = Column(Float)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    topic    = relationship("DiplomaTopic", back_populates="files")
    stage    = relationship("DiplomaStage", back_populates="files")
    comments = relationship("FileComment", back_populates="file")


class FileComment(Base):
    __tablename__ = "file_comments"
    id         = Column(Integer, primary_key=True)
    file_id    = Column(Integer, ForeignKey("diploma_files.id"))
    author_id  = Column(Integer, ForeignKey("users.id"))
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    file       = relationship("DiplomaFile", back_populates="comments")
    author     = relationship("User")


# ── VAZIFALAR ─────────────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True)
    topic_id    = Column(Integer, ForeignKey("diploma_topics.id"))
    created_by  = Column(Integer, ForeignKey("users.id"))
    title       = Column(String(300), nullable=False)
    description = Column(Text)
    deadline    = Column(DateTime(timezone=True))
    is_done     = Column(Boolean, default=False)
    done_at     = Column(DateTime(timezone=True))
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    topic       = relationship("DiplomaTopic", back_populates="tasks")
    creator     = relationship("User")


# ── UCHRASHUVLAR ──────────────────────────────────────────────────────────────

class Meeting(Base):
    __tablename__ = "meetings"
    id           = Column(Integer, primary_key=True)
    title        = Column(String(300), nullable=False)
    reason       = Column(Text)
    topic_id     = Column(Integer, ForeignKey("diploma_topics.id"), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_min = Column(Integer, default=30)
    location     = Column(String(200))
    status       = Column(Enum(MeetingStatus), default=MeetingStatus.PLANNED)
    notes        = Column(Text)
    created_by   = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    topic        = relationship("DiplomaTopic", back_populates="meetings")
    attendees    = relationship("MeetingAttendee", back_populates="meeting", cascade="all, delete-orphan")
    creator      = relationship("User", foreign_keys=[created_by])


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"
    id         = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting    = relationship("Meeting", back_populates="attendees")
    user       = relationship("User")


# ── AI TAHLIL ─────────────────────────────────────────────────────────────────

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id            = Column(Integer, primary_key=True)
    topic_id      = Column(Integer, ForeignKey("diploma_topics.id"))
    file_id       = Column(Integer, ForeignKey("diploma_files.id"), nullable=True)
    analysis_type = Column(String(50))   # 'text_quality' | 'plagiarism'
    score         = Column(Float, default=0.0)
    result        = Column(Text)         # JSON string
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    topic = relationship("DiplomaTopic", back_populates="ai_analyses")
    file  = relationship("DiplomaFile")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id             = Column(Integer, primary_key=True)
    topic_id       = Column(Integer, ForeignKey("diploma_topics.id"), unique=True)
    risk_score     = Column(Float, default=0.0)
    risk_level     = Column(String(20), default="low")  # low|medium|high|critical
    factors        = Column(Text)    # JSON string
    recommendation = Column(Text)
    assessed_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    topic = relationship("DiplomaTopic", back_populates="risk_assessment", uselist=False)


# ── XABARLAR ──────────────────────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True)
    sender_id   = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    topic_id    = Column(Integer, nullable=True)  # No FK — allows virtual supervisor-group IDs (>1_000_000)
    content     = Column(Text, nullable=False)
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sender      = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver    = relationship("User", foreign_keys=[receiver_id])


# ── BILDIRISHNOMALAR ──────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    type       = Column(Enum(NotificationType), nullable=False)
    title      = Column(String(200), nullable=False)
    body       = Column(Text)
    is_read    = Column(Boolean, default=False)
    sent_to_tg = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user       = relationship("User", back_populates="notifications")


# ── AUDIT LOG ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    action     = Column(String(100), nullable=False)
    entity     = Column(String(50))
    entity_id  = Column(Integer)
    old_value  = Column(Text)
    new_value  = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
