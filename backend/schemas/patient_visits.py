from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class PatientVisitBase(BaseModel):
    visit_code: str
    patient_id: int
    doctor_id: int
    visit_date: date
    visit_time: Optional[time] = None
    visit_type: Optional[str] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    clinical_notes: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    blood_glucose: Optional[float] = None
    temperature: Optional[float] = None
    status: Optional[str] = "completed"

class PatientVisitCreate(PatientVisitBase):
    created_by: int

class PatientVisitUpdate(BaseModel):
    visit_date: Optional[date] = None
    visit_time: Optional[time] = None
    visit_type: Optional[str] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    clinical_notes: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    blood_glucose: Optional[float] = None
    temperature: Optional[float] = None
    status: Optional[str] = None
    updated_by: Optional[int] = None

class PatientVisitResponse(PatientVisitBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True