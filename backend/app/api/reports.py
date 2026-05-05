from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import DashboardStats
from ..services.services import ReportService as ReportServiceClass

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])
report_service = ReportServiceClass()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics"""
    try:
        return await report_service.dashboard(current_user, db)
    except Exception as e:
        logger.exception("Dashboard error")
        # Return empty stats on error
        return DashboardStats(
            total_topics=0,
            approved=0,
            pending=0,
            rejected=0,
            draft=0,
            avg_progress=0.0,
            topics_by_status=[]
        )


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics data"""
    try:
        return await report_service.advanced_analytics(db)
    except Exception as e:
        logger.exception("Analytics error")
        # Return basic empty analytics on error
        return {
            'total_topics': 0,
            'total_students': 0,
            'total_supervisors': 0,
            'avg_progress': 0.0,
            'topics_by_status': [],
            'risk_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'supervisor_stats': [],
            'overdue_stages_count': 0,
            'submitted_stages_count': 0,
        }

