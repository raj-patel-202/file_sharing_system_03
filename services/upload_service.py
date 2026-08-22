import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.file import File
from repositories.file_repo import create_file
from repositories.upload_repo import (
    delete_upload_session,
    get_upload_session,
    update_upload_session,
)
from utils.storage import finalize_upload, write_chunk


async def process_chunk(session: AsyncSession, session_id: str, user_id: int, offset: int, chunk: bytes):
    upload_session = await get_upload_session(session, session_id)
    if not upload_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    if upload_session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    if offset != upload_session.committed_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Expected offset {upload_session.committed_size}, got {offset}")
    
    chunk_size = len(chunk)
    if upload_session.committed_size + chunk_size > upload_session.total_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Chunk exceeds total size")
    
    # Write to disk
    await write_chunk(session_id, chunk, offset)
    
    upload_session.committed_size += chunk_size
    await update_upload_session(session, upload_session)
    
    return upload_session

async def complete_upload(session: AsyncSession, session_id: str, user_id: int):
    upload_session = await get_upload_session(session, session_id)
    if not upload_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    if upload_session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    if upload_session.committed_size != upload_session.total_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload not complete")
    
    storage_name = f"{uuid.uuid4().hex}"
    
    # Finalize on disk
    await finalize_upload(session_id, storage_name)
    
    import os
    if upload_session.target_file_id:
        file = await session.get(File, upload_session.target_file_id)
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target file not found")
        
        from utils.storage import get_upload_path
        old_path = get_upload_path(file.storage_name)
        
        file.storage_name = storage_name
        file.size = upload_session.total_size
        file.content_type = "application/octet-stream"
        file.last_modified_by_id = user_id
        file.original_filename = upload_session.original_filename
        file.visibility = upload_session.visibility
        
        await session.delete(upload_session)
        await session.commit()
        await session.refresh(file)
        
        if os.path.exists(old_path):
            os.remove(old_path)
        return file
    else:
        # Create file record
        file = await create_file(
            session=session,
            owner_id=user_id,
            original_filename=upload_session.original_filename,
            storage_name=storage_name,
            size=upload_session.total_size,
            content_type="application/octet-stream"
        )
        file.visibility = upload_session.visibility
        await session.commit()
        
        await delete_upload_session(session, upload_session)
        
        return file
