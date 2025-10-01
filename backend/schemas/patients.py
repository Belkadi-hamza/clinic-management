from pydantic import BaseModel
from typing import Optional
from datetime import date

class PatientBase(BaseModel):
    patient_code: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    blood_type: Optional[str] = None
    place_of_birth: Optional[str] = None
    medical_history: Optional[str] = None

class PatientCreate(PatientBase):
    created_by: int

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    blood_type: Optional[str] = None
    place_of_birth: Optional[str] = None
    medical_history: Optional[str] = None
    updated_by: Optional[int] = None

class PatientResponse(PatientBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True