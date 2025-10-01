from pydantic import BaseModel
from typing import Optional
from datetime import date

class PatientDiagnosisBase(BaseModel):
    visit_id: int
    condition_id: int
    diagnosis_date: date
    diagnosing_doctor_id: int
    certainty_level: Optional[str] = None
    notes: Optional[str] = None

class PatientDiagnosisCreate(PatientDiagnosisBase):
    created_by: int

class PatientDiagnosisUpdate(BaseModel):
    diagnosis_date: Optional[date] = None
    diagnosing_doctor_id: Optional[int] = None
    certainty_level: Optional[str] = None
    notes: Optional[str] = None

class PatientDiagnosisResponse(PatientDiagnosisBase):
    id: int
    created_by: int
    created_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True