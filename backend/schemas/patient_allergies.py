from pydantic import BaseModel
from typing import Optional
from datetime import date

class PatientAllergyBase(BaseModel):
    patient_id: int
    allergy_id: int
    severity: Optional[str] = None
    reaction_description: Optional[str] = None
    diagnosed_date: Optional[date] = None

class PatientAllergyCreate(PatientAllergyBase):
    created_by: int

class PatientAllergyUpdate(BaseModel):
    severity: Optional[str] = None
    reaction_description: Optional[str] = None
    diagnosed_date: Optional[date] = None

class PatientAllergyResponse(PatientAllergyBase):
    id: int
    created_by: int
    created_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True