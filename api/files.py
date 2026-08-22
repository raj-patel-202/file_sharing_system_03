from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.file_repo import get_all_files, get_file_by_id
from repositories.permission_repo import (
    get_access_request_by_user_and_file,
    get_permission,
)
from schemas.file import FileResponse, FileVisibilityUpdate
from services.file_service import remove_file, update_file_visibility
from utils.security import require_auth
from utils.storage import get_upload_path

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("", response_model=list[FileResponse])
async def list_files(request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    files_with_user = await get_all_files(session)
    result = []
    for f, username, modifier_username in files_with_user:
        f_resp = FileResponse.model_validate(f)
        f_resp.owner_username = username
        f_resp.last_modified_by_username = modifier_username
        if f.owner_id == user_id:
            f_resp.access_status = "owner"
        elif f.visibility == "public":
            perm = await get_permission(session, user_id, f.id)
            if perm and perm.level == "modify":
                f_resp.access_status = "granted_modify"
            else:
                req = await get_access_request_by_user_and_file(session, user_id, f.id)
                if req:
                    f_resp.access_status = "granted_read_pending_modify"
                else:
                    f_resp.access_status = "granted_read"
        else:
            perm = await get_permission(session, user_id, f.id)
            if perm:
                if perm.level == "modify":
                    f_resp.access_status = "granted_modify"
                else:
                    req = await get_access_request_by_user_and_file(session, user_id, f.id)
                    if req:
                        f_resp.access_status = "granted_read_pending_modify"
                    else:
                        f_resp.access_status = "granted_read"
            else:
                req = await get_access_request_by_user_and_file(session, user_id, f.id)
                if req:
                    f_resp.access_status = "pending"
                else:
                    f_resp.access_status = "none"
        result.append(f_resp)
    return result

@router.get("/{file_id}", response_model=FileResponse)
async def get_file(file_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    file = await get_file_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    if file.visibility != "public" and file.owner_id != user_id:
        perm = await get_permission(session, user_id, file.id)
        if not perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    return file

@router.get("/{file_id}/download")
async def download_file(file_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    file = await get_file_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        
    if file.visibility != "public" and file.owner_id != user_id:
        perm = await get_permission(session, user_id, file.id)
        if not perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    path = get_upload_path(file.storage_name)
    return FastAPIFileResponse(path, filename=file.original_filename)

@router.patch("/{file_id}", response_model=FileResponse)
async def update_file_metadata(file_id: int, update: FileVisibilityUpdate, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    return await update_file_visibility(session, file_id, user_id, update.visibility)

@router.delete("/{file_id}")
async def delete_file_endpoint(file_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    await remove_file(session, file_id, user_id)
    return {"message": "Deleted"}
