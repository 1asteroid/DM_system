"""
Cleanup script: Mavzu katalogidan duplicate topiclarni fix qilish
- is_template=True bo'lgan lekin student_id null bo'lmagan topiclarni o'chirish
- yoki is_template=False qilish
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.models import DiplomaTopic
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def cleanup_duplicate_topics():
    """
    Har bir talaba uchun:
    - 1 ta real topic (is_template=False, student_id=X)
    - 0 ta template (is_template=True bo'lmasligi kerak)
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.is_template == True,
                DiplomaTopic.student_id != None,
            )
        )
        wrong_templates = result.scalars().all()
        
        print(f"Found {len(wrong_templates)} wrong template topics (is_template=True but has student_id)")
        
        for topic in wrong_templates:
            print(f"  - Topic {topic.id} ('{topic.title[:30]}...'): "
                  f"is_template=True, student_id={topic.student_id} → "
                  f"Fixing: is_template=False")
            topic.is_template = False
        
        if wrong_templates:
            await db.commit()
            print(f"✅ Fixed {len(wrong_templates)} topics")
        else:
            print("✅ No duplicates found - database is clean!")
        
        result = await db.execute(
            select(DiplomaTopic).where(
                DiplomaTopic.student_id != None,
                DiplomaTopic.status != "rejected",
            )
        )
        all_student_topics = result.scalars().all()
        
        from collections import defaultdict
        by_student = defaultdict(list)
        for topic in all_student_topics:
            by_student[topic.student_id].append(topic)
        
        issues = {sid: topics for sid, topics in by_student.items() if len(topics) > 1}
        
        if issues:
            print(f"\n⚠️  WARNING: {len(issues)} talaba bir nechta active mavzusi bor:")
            for student_id, topics in issues.items():
                print(f"  Student {student_id}:")
                for t in topics:
                    print(f"    - Topic {t.id}: is_template={t.is_template}, status={t.status}")
        else:
            print("\n✅ Verification passed: Each student has max 1 active topic")


async def main():
    try:
        await cleanup_duplicate_topics()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
