from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

Base = declarative_base()

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    from .security import hash_password
    from ..models.models import StudentProfile, User, UserRole

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == "student01@diplom.uz"))
        if existing.scalar_one_or_none() is None:
            user = User(
                full_name="Demo Student",
                email="student01@diplom.uz",
                password_hash=hash_password("student123"),
                role=UserRole.STUDENT,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            session.add(StudentProfile(user_id=user.id, student_id="STU001"))
            await session.commit()
