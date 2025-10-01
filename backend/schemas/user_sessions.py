from pydantic import BaseModel
from typing import Optional

class UserSessionBase(BaseModel):
    user_id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: str

class UserSessionCreate(UserSessionBase):
    pass

class UserSessionUpdate(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: Optional[str] = None

class UserSessionResponse(UserSessionBase):
    id: int
    created_at: Optional[str]

    class Config:
        from_attributes = True