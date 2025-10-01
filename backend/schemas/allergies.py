from pydantic import BaseModel
from typing import Optional

class AllergyBase(BaseModel):
    allergy_name: str
    allergy_type: str
    description: Optional[str] = None

class AllergyCreate(AllergyBase):
    created_by: int

class AllergyUpdate(BaseModel):
    allergy_name: Optional[str] = None
    allergy_type: Optional[str] = None
    description: Optional[str] = None
    updated_by: Optional[int] = None

class AllergyResponse(AllergyBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True