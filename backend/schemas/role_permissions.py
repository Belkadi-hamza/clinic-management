from pydantic import BaseModel
from typing import Optional

class RolePermissionBase(BaseModel):
    role_id: int
    module_id: int
    can_create: Optional[bool] = False
    can_read: Optional[bool] = False
    can_update: Optional[bool] = False
    can_delete: Optional[bool] = False
    can_export: Optional[bool] = False
    can_manage_users: Optional[bool] = False

class RolePermissionCreate(RolePermissionBase):
    pass

class RolePermissionUpdate(BaseModel):
    can_create: Optional[bool] = None
    can_read: Optional[bool] = None
    can_update: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_export: Optional[bool] = None
    can_manage_users: Optional[bool] = None

class RolePermissionResponse(RolePermissionBase):
    id: int
    created_at: Optional[str]
    status: str

    class Config:
        from_attributes = True