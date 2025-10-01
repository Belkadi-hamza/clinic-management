from pydantic import BaseModel
from typing import Optional

class ModuleBase(BaseModel):
    name: str
    description: Optional[str] = None

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ModuleResponse(ModuleBase):
    id: int
    created_at: Optional[str]

    class Config:
        from_attributes = True