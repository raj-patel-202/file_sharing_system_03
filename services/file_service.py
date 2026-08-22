from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.file_repo import delete_file, get_file_by_id, update_file
from utils.storage import delete_file as delete_storage_file


async def update_file_visibility(session: AsyncSession, file_id: int, user_id: int, visibility: str):
    file = await get_file_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if file.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can modify visibility")
    
    file.visibility = visibility
    await update_file(session, file)
    return file

async def remove_file(session: AsyncSession, file_id: int, user_id: int):
    file = await get_file_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if file.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete file")
    
    storage_name = file.storage_name
    await delete_file(session, file)
    try:
        delete_storage_file(storage_name)
    except Exception as e:
        import logging
        logging.warning(f"Failed to delete physical file {storage_name}: {e}")
