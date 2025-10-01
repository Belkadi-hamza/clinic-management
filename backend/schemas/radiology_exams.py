from pydantic import BaseModel
from typing import Optional

class RadiologyExamBase(BaseModel):
    exam_code: str
    exam_name: str
    category: Optional[str] = None
    exam_type: Optional[str] = None
    is_favorite: Optional[bool] = False

class RadiologyExamCreate(RadiologyExamBase):
    created_by: int

class RadiologyExamUpdate(BaseModel):
    exam_name: Optional[str] = None
    category: Optional[str] = None
    exam_type: Optional[str] = None
    is_favorite: Optional[bool] = None
    updated_by: Optional[int] = None

class RadiologyExamResponse(RadiologyExamBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True