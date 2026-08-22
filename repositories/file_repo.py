from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.file import File


async def get_file_by_id(session: AsyncSession, file_id: int) -> File | None:
    return await session.get(File, file_id)

async def get_files_by_owner(session: AsyncSession, owner_id: int) -> list[File]:
    stmt = select(File).where(File.owner_id == owner_id)
    return list(await session.scalars(stmt))

async def get_public_files(session: AsyncSession) -> list[File]:
    stmt = select(File).where(File.visibility == "public")
    return list(await session.scalars(stmt))

async def get_all_files(session: AsyncSession) -> list[tuple[File, str, str | None]]:
    from sqlalchemy.orm import aliased

    from models.user import User
    Modifier = aliased(User)
    stmt = (
        select(File, User.username, Modifier.username)
        .join(User, File.owner_id == User.id)
        .outerjoin(Modifier, File.last_modified_by_id == Modifier.id)
    )
    return list(await session.execute(stmt))

async def create_file(session: AsyncSession, owner_id: int, original_filename: str, storage_name: str, size: int, content_type: str, checksum: str | None = None) -> File:
    file = File(
        owner_id=owner_id,
        original_filename=original_filename,
        storage_name=storage_name,
        size=size,
        content_type=content_type,
        checksum=checksum
    )
    session.add(file)
    await session.commit()
    await session.refresh(file)
    return file

async def delete_file(session: AsyncSession, file: File) -> None:
    await session.delete(file)
    await session.commit()

async def update_file(session: AsyncSession, file: File) -> File:
    await session.commit()
    await session.refresh(file)
    return file
