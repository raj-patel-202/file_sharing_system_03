from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FileVisibilityUpdate(BaseModel):
    visibility: Literal["public", "private"]

class FileResponse(BaseModel):
    id: int
    owner_id: int
    original_filename: str
    size: int
    content_type: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    access_status: str | None = None
    owner_username: str | None = None
    last_modified_by_id: int | None = None
    last_modified_by_username: str | None = None

    model_config = {"from_attributes": True}

class UploadSessionCreate(BaseModel):
    original_filename: str
    total_size: int = Field(gt=0)
    visibility: Literal["public", "private"] = "private"
    target_file_id: int | None = None

class UploadSessionResponse(BaseModel):
    id: str
    original_filename: str
    total_size: int
    committed_size: int
    visibility: str
    target_file_id: int | None = None

    model_config = {"from_attributes": True}
