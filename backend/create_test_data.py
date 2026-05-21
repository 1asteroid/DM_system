import argparse
import asyncio
import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.models import (
    AIAnalysis,
    AuditLog,
    DiplomaFile,
    DiplomaStage,
    DiplomaTopic,
    Direction,
    Faculty,
    FileComment,
    Group,
    Kafedra,
    Meeting,
    MeetingAttendee,
    MeetingStatus,
    Message,
    Notification,
    NotificationType,
    RiskAssessment,
    StageStatus,
    StudentProfile,
    SupervisorProfile,
    Task,
    TopicStatus,
    User,
    UserRole,
)

MALE_FIRST_NAMES = [
    "Aziz", "Jasur", "Temur", "Sardor", "Bekzod", "Diyor", "Shahzod", "Oybek", "Akmal", "Umar",
    "Ali", "Bakhrom", "Dilshod", "Farhod", "Habib", "Ismail", "Javohir", "Karim", "Lazar", "Muzaffar",
]
FEMALE_FIRST_NAMES = [
    "Madina", "Aziza", "Dilnoza", "Shahnoza", "Nilufar", "Malika", "Nodira", "Zarina", "Gulnoza", "Sabina",
    "Amina", "Darina", "Elena", "Feroza", "Gulnar", "Hulkar", "Irina", "Julia", "Kamila", "Lydia",
]
MALE_LAST_NAMES = [
    "Karimov", "Rakhimov", "Aliyev", "Yuldashev", "Tursunov", "Saidov", "Abdullayev", "Nazarov", "Mamatov", "Islomov",
    "Azimov", "Berdiyev", "Chotilov", "Dostiyev", "Ergashov", "Fayzullayev", "Gavlov", "Hushmandov", "Ikramov", "Jalilayev",
]
FEMALE_LAST_NAMES = [
    "Rasulova", "Qodirova", "Ergasheva", "Ortiqova", "Asqarova", "Hakimova", "Normatova", "Shermatova", "Hamroyeva", "Xolmatova",
    "Azimova", "Berdiyeva", "Chotilyeva", "Dostiyeva", "Ergasheva", "Fayzullayeva", "Gavlova", "Hushmandova", "Ikramova", "Jalilayeva",
]

TOPIC_TITLES = [
    "Talabalar uchun adaptiv ta'lim monitoring platformasi",
    "Diplom jarayonida risklarni bashoratlash uchun ML modul",
    "Ilmiy rahbar va talaba o'rtasida aqlli kommunikatsiya tizimi",
    "Hujjatlar sifatini baholash va avtomatik tavsiya tizimi",
    "Bitiruv ishlarida progress analytics va dashboard",
    "Universitet uchun raqamli ilmiy workflow arxitekturasi",
    "Mavzu tanlash jarayonini optimallashtirish algoritmlari",
    "Matn sifatini NLP asosida baholash va indikatorlash",
    "Plagiat monitoring va hisobot generatsiyasi",
    "Kafedra kesimida diplom ishlarida KPI monitoring",
]

STAGE_TEMPLATES = [
    ("Mavzu tasdiqlash", 15.0),
    ("Adabiyotlar tahlili", 20.0),
    ("Amaliy qism", 30.0),
    ("Natijalar va xulosa", 20.0),
    ("Himoyaga tayyorlash", 15.0),
]


def _random_male_name() -> str:
    return f"{random.choice(MALE_FIRST_NAMES)} {random.choice(MALE_LAST_NAMES)}"

def _random_female_name() -> str:
    return f"{random.choice(FEMALE_FIRST_NAMES)} {random.choice(FEMALE_LAST_NAMES)}"

def _random_name(male: bool | None = None) -> str:
    if male is None:
        male = random.choice([True, False])
    return _random_male_name() if male else _random_female_name()


def _slugify(full_name: str) -> str:
    return "".join(ch.lower() for ch in full_name if ch.isalnum())


def _pick_status() -> TopicStatus:
    r = random.random()
    if r < 0.62:
        return TopicStatus.APPROVED
    if r < 0.82:
        return TopicStatus.PENDING
    if r < 0.94:
        return TopicStatus.DRAFT
    return TopicStatus.REJECTED


def _risk_bucket(topic_status: TopicStatus) -> tuple[str, float, int]:
    if topic_status == TopicStatus.REJECTED:
        return "critical", random.uniform(0.80, 0.98), random.randint(8, 18)
    if topic_status == TopicStatus.DRAFT:
        return "medium", random.uniform(0.40, 0.68), random.randint(15, 55)
    if topic_status == TopicStatus.PENDING:
        return random.choice([("medium", random.uniform(0.40, 0.70), random.randint(25, 70)),
                              ("high", random.uniform(0.70, 0.88), random.randint(20, 60))])
    return random.choice([("low", random.uniform(0.08, 0.35), random.randint(65, 96)),
                          ("medium", random.uniform(0.35, 0.62), random.randint(45, 82))])


def _stage_statuses(topic_status: TopicStatus) -> list[StageStatus]:
    if topic_status == TopicStatus.REJECTED:
        return [StageStatus.APPROVED, StageStatus.SUBMITTED, StageStatus.REJECTED, StageStatus.NOT_STARTED, StageStatus.NOT_STARTED]
    if topic_status == TopicStatus.DRAFT:
        return [StageStatus.IN_PROGRESS, StageStatus.NOT_STARTED, StageStatus.NOT_STARTED, StageStatus.NOT_STARTED, StageStatus.NOT_STARTED]
    if topic_status == TopicStatus.PENDING:
        return [StageStatus.APPROVED, StageStatus.SUBMITTED, StageStatus.IN_PROGRESS, StageStatus.NOT_STARTED, StageStatus.NOT_STARTED]
    approved_count = random.randint(2, 5)
    statuses = [StageStatus.APPROVED] * approved_count + [StageStatus.IN_PROGRESS] + [StageStatus.NOT_STARTED] * 5
    return statuses[:5]


def _write_upload_file(
    upload_dir: Path,
    topic_id: int,
    stage_order: int | None,
    ext: str,
    content: str,
    is_supervisor: bool = True,
) -> tuple[str, int, str]:
    """Create and save a file. 
    
    Args:
        is_supervisor: True = supervisor provided file, False = student submitted file
    """
    fname = f"{uuid.uuid4().hex}.{ext}"
    full_path = upload_dir / fname
    full_path.write_text(content, encoding="utf-8")
    
    file_type_label = "supervisor" if is_supervisor else "student"
    if stage_order:
        display = f"{100000 + topic_id}_stage{stage_order}_{file_type_label}.{ext}"
    else:
        display = f"{100000 + topic_id}_topic_{file_type_label}.{ext}"
    
    return fname, full_path.stat().st_size, display


async def _reset_all(session):
    """Clear existing domain data in dependency-safe order."""
    for model in [
        AuditLog,
        Message,
        Notification,
        MeetingAttendee,
        Meeting,
        FileComment,
        DiplomaFile,
        DiplomaStage,
        Task,
        AIAnalysis,
        RiskAssessment,
        DiplomaTopic,
        StudentProfile,
        SupervisorProfile,
        User,
        Group,
        Direction,
        Kafedra,
        Faculty,
    ]:
        await session.execute(delete(model))
    await session.commit()


async def create_realistic_data(
    students_kafedra_1: int = 42,
    students_kafedra_2: int = 45,
    supervisors_per_kafedra: int = 8,
    reset: bool = False,
    force: bool = False,
) -> None:
    random.seed(42)
    print("[seed] Initializing database...")
    await init_db()

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    async with SessionLocal() as session:
        existing_users = (await session.execute(
            select(func.count(User.id)).where(User.email != "student01@diplom.uz")
        )).scalar_one()
        if existing_users and not (reset or force):
            print(
                f"[seed] Found {existing_users} existing users. "
                "Use --reset to recreate or --force to append."
            )
            return

        if reset:
            print("[seed] Resetting current data...")
            await _reset_all(session)

        print("[seed] Creating organization structure...")
        faculty = Faculty(name="Axborot texnologiyalari fakulteti", short_name="ATF")
        session.add(faculty)
        await session.flush()

        kafedra_defs = [
            ("Dasturiy injiniring", "DI", students_kafedra_1),
            ("Sun'iy intellekt va data analytics", "SI", students_kafedra_2),
        ]

        kafedras: list[Kafedra] = []
        groups_by_kafedra: dict[int, list[Group]] = {}
        for idx, (k_name, k_short, _) in enumerate(kafedra_defs, start=1):
            kaf = Kafedra(name=k_name, short_name=k_short, faculty_id=faculty.id)
            session.add(kaf)
            await session.flush()
            kafedras.append(kaf)

            direction = Direction(
                name=f"{k_name} yo'nalishi",
                code=f"{idx:02d}01",
                kafedra_id=kaf.id,
            )
            session.add(direction)
            await session.flush()

            g1 = Group(name=f"{k_short}-401", year=2024, direction_id=direction.id)
            g2 = Group(name=f"{k_short}-402", year=2024, direction_id=direction.id)
            session.add_all([g1, g2])
            await session.flush()
            groups_by_kafedra[kaf.id] = [g1, g2]

        print("[seed] Creating users (admin, heads, supervisors, students)...")
        default_password = "Test12345!"
        users_created = 0

        admin = User(
            full_name="Bosh Administrator",
            email="admin@diplom.uz",
            phone="+998901111111",
            password_hash=hash_password(default_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.flush()
        users_created += 1

        heads: list[User] = []
        for idx, kaf in enumerate(kafedras, start=1):
            head = User(
                full_name=f"{_random_name()}",
                email=f"kafedra.head{idx}@diplom.uz",
                phone=f"+99890{idx}23456{idx}",
                password_hash=hash_password(default_password),
                role=UserRole.KAFEDRA_HEAD,
                is_active=True,
                kafedra_id=kaf.id,
            )
            session.add(head)
            heads.append(head)
            users_created += 1

        supervisor_profiles_by_kafedra: dict[int, list[SupervisorProfile]] = {k.id: [] for k in kafedras}
        supervisor_users_by_kafedra: dict[int, list[User]] = {k.id: [] for k in kafedras}
        for idx, kaf in enumerate(kafedras, start=1):
            for s in range(supervisors_per_kafedra):
                name = _random_name()
                email = f"sup.{idx}.{s+1}@diplom.uz"
                sup_user = User(
                    full_name=name,
                    email=email,
                    phone=f"+99893{idx}{s:02d}7788",
                    password_hash=hash_password(default_password),
                    role=UserRole.SUPERVISOR,
                    is_active=True,
                    kafedra_id=kaf.id,
                )
                session.add(sup_user)
                await session.flush()

                sup_profile = SupervisorProfile(
                    user_id=sup_user.id,
                    academic_rank=random.choice(["Assistant", "Senior Lecturer", "Docent", "Professor"]),
                    max_students=max(8, int((students_kafedra_1 + students_kafedra_2) / (2 * supervisors_per_kafedra)) + 3),
                )
                session.add(sup_profile)
                await session.flush()
                supervisor_profiles_by_kafedra[kaf.id].append(sup_profile)
                supervisor_users_by_kafedra[kaf.id].append(sup_user)
                users_created += 1

        students_by_kafedra: dict[int, list[tuple[User, StudentProfile]]] = {k.id: [] for k in kafedras}
        student_seq = 1
        for kaf, (_, _, student_count) in zip(kafedras, kafedra_defs):
            groups = groups_by_kafedra[kaf.id]
            for s in range(student_count):
                name = _random_name()
                email = f"student.{kaf.short_name.lower()}.{s+1}@diplom.uz"
                user = User(
                    full_name=name,
                    email=email,
                    phone=f"+99895{kaf.id}{s:03d}22",
                    password_hash=hash_password(default_password),
                    role=UserRole.STUDENT,
                    is_active=True,
                    kafedra_id=kaf.id,
                )
                session.add(user)
                await session.flush()

                profile = StudentProfile(
                    user_id=user.id,
                    group_id=groups[s % len(groups)].id,
                    student_id=f"STU{student_seq:04d}",
                    course=4,
                )
                session.add(profile)
                students_by_kafedra[kaf.id].append((user, profile))
                users_created += 1
                student_seq += 1

        await session.flush()
        print(f"[seed] Users created: {users_created}")

        print("[seed] Creating topics, stages, tasks, meetings, files, analyses...")
        topic_count = 0
        active_topic_count = 0
        draft_topic_count = 0
        pending_topic_count = 0
        rejected_topic_count = 0
        file_count = 0
        message_count = 0
        notification_count = 0

        now = datetime.now(timezone.utc)
        academic_year = "2025/2026"

        for kaf in kafedras:
            students = students_by_kafedra[kaf.id]
            sup_profiles = supervisor_profiles_by_kafedra[kaf.id]
            sup_users = supervisor_users_by_kafedra[kaf.id]

            for idx, (student_user, student_profile) in enumerate(students):
                topic_status = _pick_status()
                is_active_topic = topic_status == TopicStatus.APPROVED
                risk_level, risk_score, progress = _risk_bucket(topic_status)

                created_at = now - timedelta(days=random.randint(20, 180))
                defense_date = created_at + timedelta(days=random.randint(120, 260))

                assigned_sup_profile = None
                assigned_sup_user = None
                if is_active_topic:
                    assigned_sup_profile = sup_profiles[idx % len(sup_profiles)]
                    assigned_sup_user = sup_users[idx % len(sup_users)]

                topic = DiplomaTopic(
                    title=f"{random.choice(TOPIC_TITLES)} #{idx + 1}",
                    title_en="Diploma research project",
                    description="Realistik demo ma'lumotlar asosida yaratilgan diplom mavzusi.",
                    status=topic_status,
                    academic_year=academic_year,
                    progress=float(progress if is_active_topic else 0.0),
                    student_id=student_profile.id,
                    supervisor_id=assigned_sup_profile.id if assigned_sup_profile else None,
                    reviewer_id=random.choice(heads).id,
                    reject_reason="Tadqiqot maqsadi aniq emas" if topic_status == TopicStatus.REJECTED else None,
                    approved_at=created_at + timedelta(days=10) if topic_status == TopicStatus.APPROVED else None,
                    defense_date=defense_date,
                    is_template=False,
                    created_by_id=random.choice(heads).id,
                    created_at=created_at,
                    updated_at=now - timedelta(days=random.randint(0, 7)),
                )
                session.add(topic)
                await session.flush()
                topic_count += 1

                if topic_status == TopicStatus.APPROVED:
                    active_topic_count += 1
                elif topic_status == TopicStatus.DRAFT:
                    draft_topic_count += 1
                elif topic_status == TopicStatus.PENDING:
                    pending_topic_count += 1
                else:
                    rejected_topic_count += 1

                if topic_status != TopicStatus.APPROVED:
                    ext = random.choice(["pdf", "docx", "txt"])
                    body = (
                        f"Mavzu: {topic.title}\n"
                        f"Talaba: {student_user.full_name}\n"
                        f"Holat: {topic_status.value}\n"
                        "Bu qoralama / ko'rib chiqilayotgan mavzu uchun biriktirilgan namunaviy fayl."
                    )
                    stored_name, fsize, display_name = _write_upload_file(upload_dir, topic.id, None, ext, body)
                    session.add(DiplomaFile(
                        topic_id=topic.id,
                        stage_id=None,
                        uploaded_by=student_user.id,
                        file_name=display_name,
                        file_path=stored_name,
                        file_size=fsize,
                        file_type=ext,
                        version=1,
                        is_final=False,
                        plagiat_score=round(random.uniform(4, 28), 2),
                        created_at=created_at + timedelta(days=2),
                    ))
                    file_count += 1

                    session.add(Message(
                        sender_id=student_user.id,
                        receiver_id=random.choice(heads).id,
                        topic_id=topic.id,
                        content="Mavzu qoralama holatda. Iltimos, ko'rib chiqing.",
                        is_read=random.random() < 0.5,
                        created_at=now - timedelta(days=random.randint(0, 8)),
                    ))
                    message_count += 1

                    session.add(Notification(
                        user_id=student_user.id,
                        type=NotificationType.STATUS_CHANGED,
                        title="Qoralama mavzu yaratildi",
                        body="Sizning mavzuyingiz qoralama holatda saqlandi.",
                        is_read=False,
                        sent_to_tg=random.random() < 0.5,
                        created_at=now - timedelta(hours=random.randint(1, 72)),
                    ))
                    notification_count += 1
                    continue

                stage_statuses = _stage_statuses(topic_status)
                stages: list[DiplomaStage] = []
                for order, ((stage_name, weight), st_status) in enumerate(zip(STAGE_TEMPLATES, stage_statuses), start=1):
                    deadline = created_at + timedelta(days=order * 30)
                    stage = DiplomaStage(
                        topic_id=topic.id,
                        name=stage_name,
                        description=f"{stage_name} bo'yicha ishlar",
                        order=order,
                        status=st_status,
                        weight=weight,
                        deadline=deadline,
                        submitted_at=deadline - timedelta(days=random.randint(1, 6)) if st_status in (StageStatus.SUBMITTED, StageStatus.APPROVED, StageStatus.REJECTED) else None,
                        reviewed_at=deadline - timedelta(days=random.randint(0, 2)) if st_status in (StageStatus.APPROVED, StageStatus.REJECTED) else None,
                        comment="Qayta ishlab chiqing" if st_status == StageStatus.REJECTED else None,
                        created_at=created_at,
                    )
                    session.add(stage)
                    stages.append(stage)

                for t in range(random.randint(4, 8)):
                    done = random.random() < (0.70 if topic_status == TopicStatus.APPROVED else 0.35)
                    task = Task(
                        topic_id=topic.id,
                        created_by=assigned_sup_user.id,
                        title=f"Vazifa #{t+1}: {random.choice(['hisobot', 'kod', 'tahlil', 'test'])}",
                        description="Nazorat uchun topshiriq.",
                        deadline=created_at + timedelta(days=20 + t * 8),
                        is_done=done,
                        done_at=created_at + timedelta(days=18 + t * 8) if done else None,
                        created_at=created_at,
                    )
                    session.add(task)

                for m in range(random.randint(1, 4)):
                    mt_status = random.choice([MeetingStatus.PLANNED, MeetingStatus.COMPLETED, MeetingStatus.CANCELLED])
                    meeting_time = now + timedelta(days=random.randint(-20, 25), hours=random.randint(8, 17))
                    meeting = Meeting(
                        title=f"Progress uchrashuv #{m+1}",
                        reason="Diplom mavzusi bo'yicha holatni ko'rib chiqish",
                        topic_id=topic.id,
                        scheduled_at=meeting_time,
                        duration_min=random.choice([30, 45, 60]),
                        location=random.choice(["Zoom", "Google Meet", "Kafedra 204-xona"]),
                        status=mt_status,
                        notes="Muhokama qilindi" if mt_status == MeetingStatus.COMPLETED else None,
                        created_by=assigned_sup_user.id,
                        created_at=created_at,
                    )
                    session.add(meeting)
                    await session.flush()
                    session.add(MeetingAttendee(meeting_id=meeting.id, user_id=student_user.id))
                    session.add(MeetingAttendee(meeting_id=meeting.id, user_id=assigned_sup_user.id))

                await session.flush()

                exts = ["pdf", "docx", "txt"]

                for sp_fidx in range(random.randint(5, 6)):
                    ext = random.choice(exts)
                    body = (
                        f"[SUPERVISOR MATERIAL]\n"
                        f"Mavzu: {topic.title}\n"
                        f"Rahbar: {assigned_sup_user.full_name}\n"
                        f"Navi: {'Adabiyot' if sp_fidx == 0 else 'Qo\'llanma'} #{sp_fidx}\n"
                        "Bu rahbar tarafidan talabaga butun diplom jarayoni uchun yuboriladigan material."
                    )
                    stored_name, fsize, display_name = _write_upload_file(
                        upload_dir, topic.id, None, ext, body, is_supervisor=True
                    )
                    session.add(DiplomaFile(
                        topic_id=topic.id,
                        stage_id=None,  # STAGE'GA BOG'LIQ EMAS - UMUMIY
                        uploaded_by=assigned_sup_user.id,
                        file_name=display_name,
                        file_path=stored_name,
                        file_size=fsize,
                        file_type=ext,
                        version=1,
                        is_final=False,
                        plagiat_score=None,
                        created_at=created_at + timedelta(days=2),
                    ))
                    file_count += 1

                for stage in stages:
                    if stage.status in (StageStatus.APPROVED, StageStatus.SUBMITTED, StageStatus.IN_PROGRESS):
                        ext = random.choice(exts)
                        body = (
                            f"[STUDENT WORK]\n"
                            f"Mavzu: {topic.title}\n"
                            f"Bosqich: {stage.name}\n"
                            f"Talaba: {student_user.full_name}\n"
                            "Bu talaba tarafidan stage uchun yuklagan o'z ishlari."
                        )
                        stored_name, fsize, display_name = _write_upload_file(
                            upload_dir, topic.id, stage.order, ext, body, is_supervisor=False
                        )
                        session.add(DiplomaFile(
                            topic_id=topic.id,
                            stage_id=stage.id,  # STAGE'GA BOG'LIQ
                            uploaded_by=student_user.id,
                            file_name=display_name,
                            file_path=stored_name,
                            file_size=fsize,
                            file_type=ext,
                            version=1,
                            is_final=stage.status == StageStatus.APPROVED,
                            plagiat_score=round(random.uniform(4, 28), 2) if stage.status == StageStatus.APPROVED else None,
                            created_at=created_at + timedelta(days=stage.order * 20 + random.randint(1, 5)),
                        ))
                        file_count += 1

                session.add(AIAnalysis(
                    topic_id=topic.id,
                    analysis_type="text_quality",
                    score=round(random.uniform(62, 96), 2),
                    result=json.dumps({
                        "clarity": round(random.uniform(0.60, 0.96), 2),
                        "structure": round(random.uniform(0.58, 0.95), 2),
                        "terminology": round(random.uniform(0.55, 0.93), 2),
                    }),
                    created_at=now - timedelta(days=random.randint(1, 10)),
                ))
                session.add(AIAnalysis(
                    topic_id=topic.id,
                    analysis_type="plagiarism",
                    score=round(random.uniform(3, 24), 2),
                    result=json.dumps({"similarity_percent": round(random.uniform(3, 24), 2)}),
                    created_at=now - timedelta(days=random.randint(1, 10)),
                ))

                session.add(RiskAssessment(
                    topic_id=topic.id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    factors=json.dumps({
                        "progress_gap": round(random.uniform(0, 35), 2),
                        "task_completion_rate": round(random.uniform(0.2, 1.0), 2),
                        "meeting_frequency": round(random.uniform(0.1, 1.0), 2),
                    }),
                    recommendation="Haftalik nazoratni kuchaytirish" if risk_level in {"high", "critical"} else "Reja asosida davom etish",
                    assessed_at=now - timedelta(days=random.randint(0, 5)),
                ))

                for mi in range(random.randint(2, 5)):
                    session.add(Message(
                        sender_id=student_user.id if mi % 2 == 0 else assigned_sup_user.id,
                        receiver_id=assigned_sup_user.id if mi % 2 == 0 else student_user.id,
                        topic_id=topic.id,
                        content=random.choice([
                            "Ustoz, bugungi natijalar tayyor.",
                            "Ilova bo'limini qayta ko'rib chiqdim.",
                            "Deadline bo'yicha savolim bor.",
                            "Himoya slaydlarini yangiladim.",
                        ]),
                        is_read=mi % 3 != 0,
                        created_at=now - timedelta(days=random.randint(0, 14)),
                    ))
                    message_count += 1

                for noti_user_id, title, body in [
                    (student_user.id, "Yangi topshiriq", "Rahbar tomonidan yangi topshiriq qo'shildi"),
                    (assigned_sup_user.id, "Talaba fayl yukladi", "Talaba yangi fayl yubordi"),
                ]:
                    session.add(Notification(
                        user_id=noti_user_id,
                        type=NotificationType.NEW_TASK,
                        title=title,
                        body=body,
                        is_read=False,
                        sent_to_tg=random.random() < 0.5,
                        created_at=now - timedelta(hours=random.randint(1, 72)),
                    ))
                    notification_count += 1

                if topic_count % 20 == 0:
                    await session.commit()
                    print(f"[seed] Progress: {topic_count} topics committed...")

        await session.commit()

        print("\n[seed] COMPLETED")
        print(f"  users_total_created: {users_created}")
        print(f"  topics: {topic_count}")
        print(f"  approved_topics: {active_topic_count}")
        print(f"  draft_topics: {draft_topic_count}")
        print(f"  pending_topics: {pending_topic_count}")
        print(f"  rejected_topics: {rejected_topic_count}")
        print(f"  files: {file_count}")
        print(f"  messages: {message_count}")
        print(f"  notifications: {notification_count}")
        print(f"  upload_dir: {upload_dir}")
        print("  default_password: Test12345!")
        print("  admin_login: admin@diplom.uz")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create realistic test data for Diplom Monitoring")
    parser.add_argument("--students-k1", type=int, default=42, help="Students for kafedra #1")
    parser.add_argument("--students-k2", type=int, default=45, help="Students for kafedra #2")
    parser.add_argument("--supervisors-per-kafedra", type=int, default=8, help="Supervisors per kafedra")
    parser.add_argument("--reset", action="store_true", help="Delete existing domain data before seeding")
    parser.add_argument("--force", action="store_true", help="Append data even if users already exist")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    await create_realistic_data(
        students_kafedra_1=args.students_k1,
        students_kafedra_2=args.students_k2,
        supervisors_per_kafedra=args.supervisors_per_kafedra,
        reset=args.reset,
        force=args.force,
    )


if __name__ == "__main__":
    asyncio.run(_main())

