from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.models import User
from ..schemas.schemas import FileCommentCreate
from ..services.services import FileService as FileServiceClass

router = APIRouter(prefix="/topics", tags=["files"])
file_service = FileServiceClass()


@router.get("/{topic_id}/files")
async def list_files(
    topic_id: int,
    stage_id: int = Query(None),  # Agar stage_id bo'lsa, o'quvchi fayllarini qaytarish
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get files for topic: supervisor materials (stage_id=null) or student submissions per stage"""
    if stage_id:
        # O'quvchi fayllarini stage bo'yicha
        return await file_service.get_stage_student_files(stage_id, db)
    else:
        # Rahbar umumiy fayllarini
        return await file_service.get_list(topic_id, db)


@router.post("/{topic_id}/files")
async def upload_file(
    topic_id: int,
    file: UploadFile = File(...),
    stage_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload file"""
    return await file_service.upload(topic_id, stage_id, file, current_user, db)


@router.delete("/{topic_id}/files/{file_id}")
async def delete_file(
    topic_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete file"""
    return await file_service.delete(file_id, current_user, db)


@router.get("/{topic_id}/files/{file_id}/download")
async def download_file(
    topic_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download file"""
    return await file_service.download(file_id, db)


@router.post("/{topic_id}/files/{file_id}/comments")
async def add_comment(
    topic_id: int,
    file_id: int,
    data: FileCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add comment to file"""
    return await file_service.add_comment(file_id, data, current_user, db)

