from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.permission_repo import get_incoming_requests
from schemas.permission import (
    AccessRequestResponse,
    IncomingAccessRequestResponse,
    PermissionResponse,
)
from services.permission_service import approve_request, reject_request, request_access
from utils.security import require_auth

router = APIRouter(prefix="/api", tags=["permissions"])

@router.post("/files/{file_id}/access-requests", response_model=AccessRequestResponse)
async def create_access_request(file_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    return await request_access(session, user_id, file_id)

@router.get("/access-requests", response_model=list[IncomingAccessRequestResponse])
async def get_my_incoming_requests(request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    return await get_incoming_requests(session, user_id)

@router.post("/access-requests/{request_id}/approve", response_model=PermissionResponse)
async def approve_access_request(request_id: int, request: Request, level: str = "read", session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    if level not in ["read", "modify"]:
        raise HTTPException(status_code=400, detail="Invalid level")
    return await approve_request(session, request_id, user_id, level)

@router.delete("/access-requests/{request_id}/reject")
async def reject_access_request(request_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    await reject_request(session, request_id, user_id)
    return {"message": "Rejected"}
