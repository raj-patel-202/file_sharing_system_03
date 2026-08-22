from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.upload_repo import create_upload_session, get_upload_session
from schemas.file import UploadSessionCreate, UploadSessionResponse
from services.upload_service import complete_upload, process_chunk
from utils.security import require_auth

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

@router.post("", response_model=UploadSessionResponse)
async def init_upload(data: UploadSessionCreate, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    
    if data.target_file_id:
        from repositories.file_repo import get_file_by_id
        from repositories.permission_repo import get_permission
        file = await get_file_by_id(session, data.target_file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != user_id:
            perm = await get_permission(session, user_id, file.id)
            if not perm or perm.level != "modify":
                raise HTTPException(status_code=403, detail="Not authorized to modify this file")
                
    return await create_upload_session(session, user_id, data.original_filename, data.total_size, data.visibility, data.target_file_id)

@router.get("/sessions", response_model=list[UploadSessionResponse])
async def list_upload_sessions(request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    from repositories.upload_repo import get_upload_sessions_by_user
    return await get_upload_sessions_by_user(session, user_id)

@router.delete("/{session_id}")
async def cancel_upload_session(session_id: str, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    upload_session = await get_upload_session(session, session_id)
    if not upload_session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    if upload_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from repositories.upload_repo import delete_upload_session
    await delete_upload_session(session, upload_session)
    
    import os

    from utils.storage import get_part_path
    part_path = get_part_path(session_id)
    if os.path.exists(part_path):
        try:
            os.remove(part_path)
        except Exception:
            pass
            
    return {"status": "cancelled"}

@router.get("/{session_id}/status", response_model=UploadSessionResponse)
async def get_upload_status(session_id: str, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    upload_session = await get_upload_session(session, session_id)
    if not upload_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if upload_session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return upload_session

@router.patch("/{session_id}/chunks")
async def upload_chunk(session_id: str, request: Request, offset: int = Form(...), chunk: UploadFile = Form(...), session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    data = await chunk.read()
    await process_chunk(session, session_id, user_id, offset, data)
    
    upload_session = await get_upload_session(session, session_id)
    if upload_session.committed_size == upload_session.total_size:
        file = await complete_upload(session, session_id, user_id)
        return {"status": "complete", "file_id": file.id}
        
    return {"status": "in_progress", "committed_size": upload_session.committed_size}
