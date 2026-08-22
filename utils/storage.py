import os

import aiofiles

from core.config import settings


def get_upload_path(storage_name: str) -> str:
    return os.path.join(settings.upload_dir, storage_name)

def get_part_path(session_id: str) -> str:
    return os.path.join(settings.upload_dir, f"{session_id}.part")

async def write_chunk(session_id: str, chunk_data: bytes, offset: int):
    os.makedirs(settings.upload_dir, exist_ok=True)
    part_path = get_part_path(session_id)
    async with aiofiles.open(part_path, "ab" if offset > 0 else "wb") as f:
        # Seek to offset
        await f.seek(offset)
        await f.write(chunk_data)

async def finalize_upload(session_id: str, storage_name: str):
    part_path = get_part_path(session_id)
    final_path = get_upload_path(storage_name)
    if os.path.exists(part_path):
        os.rename(part_path, final_path)

def delete_file(storage_name: str):
    path = get_upload_path(storage_name)
    if os.path.exists(path):
        os.remove(path)
