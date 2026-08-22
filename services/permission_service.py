from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.permission import AccessRequest, Permission
from repositories.file_repo import get_file_by_id
from repositories.permission_repo import (
    create_access_request,
    create_permission,
    delete_access_request,
    get_access_request,
    get_access_request_by_user_and_file,
)


async def request_access(session: AsyncSession, user_id: int, file_id: int) -> AccessRequest:
    file = await get_file_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    if file.owner_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You own this file")
        
    existing = await get_access_request_by_user_and_file(session, user_id, file_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request already pending")
        
    return await create_access_request(session, user_id, file_id)

async def approve_request(session: AsyncSession, request_id: int, owner_id: int, level: str = "read") -> Permission:
    req = await get_access_request(session, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        
    file = await get_file_by_id(session, req.file_id)
    if not file or file.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    from repositories.permission_repo import get_permission
    existing_perm = await get_permission(session, req.user_id, req.file_id)
    
    if existing_perm:
        existing_perm.level = level
        await session.commit()
        await session.refresh(existing_perm)
        perm = existing_perm
    else:
        perm = await create_permission(session, req.user_id, req.file_id, level)
        
    await delete_access_request(session, req)
    return perm

async def reject_request(session: AsyncSession, request_id: int, owner_id: int):
    req = await get_access_request(session, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        
    file = await get_file_by_id(session, req.file_id)
    if not file or file.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    await delete_access_request(session, req)
