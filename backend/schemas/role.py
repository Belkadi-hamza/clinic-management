from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    created_at: Optional[datetime] = None
    status: str

    model_config = ConfigDict(from_attributes=True)