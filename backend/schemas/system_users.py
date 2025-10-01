from pydantic import BaseModel
from typing import Optional

class SystemUserBase(BaseModel):
    staff_id: int
    username: str
    role_id: int
    is_active: Optional[bool] = True
    must_change_password: Optional[bool] = False

class SystemUserCreate(SystemUserBase):
    password: str

class SystemUserUpdate(BaseModel):
    username: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    must_change_password: Optional[bool] = None
    password: Optional[str] = None

class SystemUserResponse(SystemUserBase):
    id: int
    last_login: Optional[str]
    login_attempts: Optional[int]
    locked_until: Optional[str]
    created_at: Optional[str]
    status: str

    class Config:
        from_attributes = True