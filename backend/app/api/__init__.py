from fastapi import APIRouter

from ..core.database import get_db
from ..core.dependencies import get_current_user
from .auth import router as auth_router
from .topics import router as topics_router
from .stages import router as stages_router
from .files import router as files_router
from .tasks import router as tasks_router
from .reports import router as reports_router
from .users import router as users_router
from .meetings import router as meetings_router
from .messages import router as messages_router
from .analysis import router as analysis_router
from .risk import router as risk_router
from .notifications import router as notifications_router
from .websocket import router as websocket_router
from .supervisors import router as supervisors_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(topics_router)
api_router.include_router(stages_router)
api_router.include_router(files_router)
api_router.include_router(tasks_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
api_router.include_router(meetings_router)
api_router.include_router(messages_router)
api_router.include_router(analysis_router)
api_router.include_router(risk_router)
api_router.include_router(notifications_router)
api_router.include_router(supervisors_router)

# WebSocket router (not prefixed)
app_router = APIRouter()
app_router.include_router(websocket_router)

