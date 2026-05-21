"""
Available supervisors endpoint
Mavzu olmagan yoki joy bor supervisorlarni olish
"""


from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User, UserRole, DiplomaTopic, SupervisorProfile

router = APIRouter(prefix="/supervisors", tags=["supervisors"])


@router.get("/available")
async def get_available_supervisors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get supervisors with available capacity
    - Har supervisor maksimal 5 ta student qabul qila oladi
    - To'lgan supervisorlar chiqmaydi
    """

    supervisor_count_subquery = (
        select(
            DiplomaTopic.supervisor_id,
            func.count(DiplomaTopic.id).label("student_count")
        )
        .where(DiplomaTopic.status.in_(["approved", "submitted"]))
        .group_by(DiplomaTopic.supervisor_id)
    ).subquery()

    result = await db.execute(
        select(User).where(
            User.role == UserRole.SUPERVISOR,
            User.is_active == True
        ).options(
            selectinload(User.supervisor_profile)
        )
    )
    supervisors = result.scalars().all()

    count_result = await db.execute(
        select(supervisor_count_subquery)
    )
    count_map = {}
    for row in count_result:
        if row.supervisor_id:
            count_map[row.supervisor_id] = row.student_count

    available = []
    for sup in supervisors:
        if sup.supervisor_profile:
            student_count = count_map.get(sup.supervisor_profile.id, 0)
            max_students = sup.supervisor_profile.max_students or 5

            if student_count < max_students:
                available.append({
                    "id": sup.id,
                    "full_name": sup.full_name,
                    "email": sup.email,
                    "academic_rank": sup.supervisor_profile.academic_rank,
                    "current_students": student_count,
                    "max_students": max_students,
                    "available_slots": max_students - student_count
                })

    return {
        "total": len(available),
        "supervisors": available
    }


@router.get("/{supervisor_id}/info")
async def get_supervisor_info(
    supervisor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get supervisor information with students count"""

    result = await db.execute(
        select(User).where(
            User.id == supervisor_id,
            User.role == UserRole.SUPERVISOR
        ).options(
            selectinload(User.supervisor_profile)
        )
    )
    supervisor = result.scalar_one_or_none()

    if not supervisor:
        return {"error": "Supervisor topilmadi"}

    count_result = await db.execute(
        select(func.count(DiplomaTopic.id)).where(
            DiplomaTopic.supervisor_id == supervisor.supervisor_profile.id,
            DiplomaTopic.status.in_(["approved", "submitted"])
        )
    )
    student_count = count_result.scalar() or 0

    return {
        "id": supervisor.id,
        "full_name": supervisor.full_name,
        "email": supervisor.email,
        "academic_rank": supervisor.supervisor_profile.academic_rank,
        "current_students": student_count,
        "max_students": supervisor.supervisor_profile.max_students or 5,
        "available_slots": (supervisor.supervisor_profile.max_students or 5) - student_count
    }

