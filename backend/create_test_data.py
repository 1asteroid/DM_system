#!/usr/bin/env python3
"""
Create test users for development
Test o'quvchi, o'qituvchi va admin users
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.models import User, UserRole, StudentProfile, SupervisorProfile
from sqlalchemy import select


async def create_test_users():
    """Create test users"""
    print("🔧 Test users yaratilmoqda...\n")

    await init_db()  # Init database

    async with SessionLocal() as session:
        # Check existing users
        result = await session.execute(select(User).where(User.role == UserRole.STUDENT))
        if result.scalar_one_or_none():
            print("⚠️  Test users allaqachon mavjud. Qaytish.")
            return

        # 1. Admin User
        admin = User(
            full_name="Admin Foydalanuvchi",
            email="admin@diplom.uz",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        print("✅ Admin created: admin@diplom.uz / admin123")

        # 2. Kafedra Head
        kafedra_head = User(
            full_name="Kafedra Mudiri",
            email="kafedra@diplom.uz",
            password_hash=hash_password("kafedra123"),
            role=UserRole.KAFEDRA_HEAD,
            is_active=True,
        )
        session.add(kafedra_head)
        print("✅ Kafedra Head created: kafedra@diplom.uz / kafedra123")

        # 3. Supervisors
        supervisors = [
            {
                "name": "Prof. Abdullayev",
                "email": "supervisor1@diplom.uz",
                "password": "supervisor123",
                "rank": "Professor"
            },
            {
                "name": "Doc. Karimova",
                "email": "supervisor2@diplom.uz",
                "password": "supervisor456",
                "rank": "Docent"
            },
            {
                "name": "Doc. Sharifov",
                "email": "supervisor3@diplom.uz",
                "password": "supervisor789",
                "rank": "Docent"
            },
        ]

        for sup_data in supervisors:
            sup = User(
                full_name=sup_data["name"],
                email=sup_data["email"],
                password_hash=hash_password(sup_data["password"]),
                role=UserRole.SUPERVISOR,
                is_active=True,
            )
            session.add(sup)
            await session.flush()

            # Create supervisor profile
            sup_profile = SupervisorProfile(
                user_id=sup.id,
                academic_rank=sup_data["rank"],
                max_students=5
            )
            session.add(sup_profile)
            print(f"✅ Supervisor created: {sup_data['email']} / {sup_data['password']}")

        # 4. Students (5 ta)
        students = [
            {"name": "Olimov Alisher", "email": "student01@diplom.uz", "password": "student123", "id": "STU001"},
            {"name": "Kobilov Karim", "email": "student02@diplom.uz", "password": "student456", "id": "STU002"},
            {"name": "Normatova Nozima", "email": "student03@diplom.uz", "password": "student789", "id": "STU003"},
            {"name": "Rahimova Rayhona", "email": "student04@diplom.uz", "password": "student101", "id": "STU004"},
            {"name": "Sobirjonov Sobir", "email": "student05@diplom.uz", "password": "student202", "id": "STU005"},
        ]

        for std_data in students:
            std = User(
                full_name=std_data["name"],
                email=std_data["email"],
                password_hash=hash_password(std_data["password"]),
                role=UserRole.STUDENT,
                is_active=True,
            )
            session.add(std)
            await session.flush()

            # Create student profile
            std_profile = StudentProfile(
                user_id=std.id,
                student_id=std_data["id"],
                group_id=1
            )
            session.add(std_profile)
            print(f"✅ Student created: {std_data['email']} / {std_data['password']}")

        await session.commit()

        print("\n" + "="*60)
        print("✨ BARCHA TEST USERS MUVAFFAQIYATLI YARATILDI!")
        print("="*60)
        print("\n📋 Test credentials:\n")
        print("ADMIN:")
        print("  Email: admin@diplom.uz")
        print("  Password: admin123\n")
        print("KAFEDRA MUDIRI:")
        print("  Email: kafedra@diplom.uz")
        print("  Password: kafedra123\n")
        print("SUPERVISORS:")
        for sup in supervisors:
            print(f"  {sup['email']} / {sup['password']}")
        print("\nSTUDENTS:")
        for std in students:
            print(f"  {std['email']} / {std['password']}")


if __name__ == "__main__":
    asyncio.run(create_test_users())

