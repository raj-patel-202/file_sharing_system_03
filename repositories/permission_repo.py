from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.permission import AccessRequest, Permission


async def get_permission(session: AsyncSession, user_id: int, file_id: int) -> Permission | None:
    stmt = select(Permission).where(Permission.user_id == user_id, Permission.file_id == file_id)
    perms = (await session.scalars(stmt)).all()
    if not perms:
        return None
    for p in perms:
        if p.level == "modify":
            return p
    return perms[0]

async def create_access_request(session: AsyncSession, user_id: int, file_id: int) -> AccessRequest:
    req = AccessRequest(user_id=user_id, file_id=file_id)
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req
    
async def create_permission(session: AsyncSession, user_id: int, file_id: int, level: str) -> Permission:
    perm = Permission(user_id=user_id, file_id=file_id, level=level)
    session.add(perm)
    await session.commit()
    await session.refresh(perm)
    return perm
    
async def delete_permission(session: AsyncSession, perm: Permission) -> None:
    await session.delete(perm)
    await session.commit()

async def get_access_request(session: AsyncSession, request_id: int) -> AccessRequest | None:
    return await session.get(AccessRequest, request_id)

async def get_access_request_by_user_and_file(session: AsyncSession, user_id: int, file_id: int) -> AccessRequest | None:
    stmt = select(AccessRequest).where(AccessRequest.user_id == user_id, AccessRequest.file_id == file_id)
    return (await session.scalars(stmt)).one_or_none()

async def get_incoming_requests(session: AsyncSession, owner_id: int) -> list[dict]:
    from models.file import File
    from models.user import User
    stmt = (
        select(AccessRequest, User, File)
        .join(User, AccessRequest.user_id == User.id)
        .join(File, AccessRequest.file_id == File.id)
        .where(File.owner_id == owner_id)
        .where(AccessRequest.status == "pending")
    )
    result = await session.execute(stmt)
    requests = []
    for req, user, file in result:
        requests.append({
            "id": req.id,
            "user_id": user.id,
            "username": user.username,
            "file_id": file.id,
            "filename": file.original_filename,
            "status": req.status
        })
    return requests

async def delete_access_request(session: AsyncSession, req: AccessRequest) -> None:
    await session.delete(req)
    await session.commit()
