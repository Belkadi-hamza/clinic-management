from pydantic import BaseModel
from typing import Optional

class MedicalConditionBase(BaseModel):
    condition_code: str
    condition_name: str
    category: Optional[str] = None
    icd_code: Optional[str] = None
    description: Optional[str] = None
    general_information: Optional[str] = None
    diagnostic_criteria: Optional[str] = None
    treatment_guidelines: Optional[str] = None
    is_favorite: Optional[bool] = False

class MedicalConditionCreate(MedicalConditionBase):
    created_by: int

class MedicalConditionUpdate(BaseModel):
    condition_name: Optional[str] = None
    category: Optional[str] = None
    icd_code: Optional[str] = None
    description: Optional[str] = None
    general_information: Optional[str] = None
    diagnostic_criteria: Optional[str] = None
    treatment_guidelines: Optional[str] = None
    is_favorite: Optional[bool] = None
    updated_by: Optional[int] = None

class MedicalConditionResponse(MedicalConditionBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True