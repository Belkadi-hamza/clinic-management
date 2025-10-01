from pydantic import BaseModel
from typing import Optional, Any

class AuditLogBase(BaseModel):
    table_name: str
    record_id: int
    action: str
    old_values: Optional[Any] = None
    new_values: Optional[Any] = None
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    created_at: Optional[str]

    class Config:
        from_attributes = True