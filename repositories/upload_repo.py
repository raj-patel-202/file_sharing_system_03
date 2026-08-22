from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.upload_session import UploadSession


async def get_upload_session(session: AsyncSession, session_id: str) -> UploadSession | None:
    return await session.get(UploadSession, session_id)

async def get_upload_sessions_by_user(session: AsyncSession, user_id: int) -> list[UploadSession]:
    stmt = select(UploadSession).where(UploadSession.user_id == user_id)
    return list(await session.scalars(stmt))

async def create_upload_session(session: AsyncSession, user_id: int, original_filename: str, total_size: int, visibility: str = "private", target_file_id: int | None = None) -> UploadSession:
    sess = UploadSession(
        user_id=user_id,
        original_filename=original_filename,
        total_size=total_size,
        visibility=visibility,
        target_file_id=target_file_id
    )
    session.add(sess)
    await session.commit()
    await session.refresh(sess)
    return sess

async def update_upload_session(session: AsyncSession, upload_session: UploadSession) -> UploadSession:
    await session.commit()
    await session.refresh(upload_session)
    return upload_session

async def delete_upload_session(session: AsyncSession, upload_session: UploadSession) -> None:
    await session.delete(upload_session)
    await session.commit()
