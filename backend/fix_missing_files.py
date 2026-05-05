"""
Database'dagi orphan file references ni tekshirish va tuzatish
- Fayl disk'da mavjud bo'lmasa: database'dan o'chirish
- Fayl mavjud bo'lsa va analiz qilingan bo'lsa: saqlash
"""
import asyncio
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.models import DiplomaFile, AIAnalysis
from app.core.config import settings

# Database connection
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


async def fix_missing_files():
    """
    1. Barcha DiplomaFile recordlarni tekshirish
    2. Agar file disk'da yo'q bo'lsa - database'dan o'chirish
    3. Bog'langan AIAnalysis recordlarini ham o'chirish
    """
    async with AsyncSessionLocal() as db:
        # 1. Barcha file recordlarni olish
        result = await db.execute(select(DiplomaFile))
        all_files = result.scalars().all()
        
        print(f"📊 Jami {len(all_files)} ta file record topildi\n")
        
        orphan_count = 0
        valid_count = 0
        
        for file_record in all_files:
            file_path = Path(UPLOADS_DIR) / file_record.file_path
            
            if not file_path.exists():
                print(f"❌ File topilmadi: {file_record.file_path}")
                print(f"   ID: {file_record.id} | Topic: {file_record.topic_id}")
                
                # 2. Bog'langan AIAnalysis recordlarini topish va o'chirish
                analyses = await db.execute(
                    select(AIAnalysis).where(AIAnalysis.file_id == file_record.id)
                )
                related_analyses = analyses.scalars().all()
                
                if related_analyses:
                    print(f"   → {len(related_analyses)} ta analysis record o'chirilmoqda")
                    for analysis in related_analyses:
                        await db.delete(analysis)
                
                # 3. File recordni o'chirish
                await db.delete(file_record)
                orphan_count += 1
                print()
            else:
                valid_count += 1
        
        # Commit changes
        if orphan_count > 0:
            await db.commit()
            print(f"\n✅ {orphan_count} ta orphan file record o'chirildi")
        
        print(f"✅ {valid_count} ta haqiqiy file saqlandi")
        
        # 4. Verification - check if remaining files exist
        result = await db.execute(select(DiplomaFile))
        remaining = result.scalars().all()
        
        print(f"\n📊 Verification: {len(remaining)} ta file record qoldi")
        
        missing_after = 0
        for f in remaining:
            if not (Path(UPLOADS_DIR) / f.file_path).exists():
                missing_after += 1
                print(f"⚠️  Hali qolgan: {f.file_path}")
        
        if missing_after == 0:
            print("✅ Barcha qolgan file recordlar valid!")


async def main():
    try:
        await fix_missing_files()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
