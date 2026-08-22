from pydantic import BaseModel


class AccessRequestCreate(BaseModel):
    file_id: int

class AccessRequestResponse(BaseModel):
    id: int
    user_id: int
    file_id: int
    status: str

    model_config = {"from_attributes": True}

class IncomingAccessRequestResponse(BaseModel):
    id: int
    user_id: int
    username: str
    file_id: int
    filename: str
    status: str

class PermissionCreate(BaseModel):
    user_id: int
    level: str = "read"

class PermissionResponse(BaseModel):
    id: int
    user_id: int
    file_id: int
    level: str

    model_config = {"from_attributes": True}
