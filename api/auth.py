from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.user_repo import create_user, get_user_by_id, get_user_by_username
from schemas.user import UserCreate, UserResponse
from services.auth_service import hash_password, verify_password
from utils.security import COOKIE_NAME, create_access_token, require_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, session: AsyncSession = Depends(get_db)):
    user_id = require_auth(request)
    user = await get_user_by_id(session, user_id)
    return user

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, session: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(session, user.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    
    hashed = hash_password(user.password)
    new_user = await create_user(session, user.username, hashed)
    return new_user

@router.post("/login")
async def login(user: UserCreate, response: Response, session: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(session, user.username)
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(db_user.id)})
    response.set_cookie(key=COOKIE_NAME, value=token, httponly=True, secure=True, samesite="lax", max_age=3600)
    return {"message": "Logged in"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, httponly=True, secure=True, samesite="lax")
    return {"message": "Logged out"}
