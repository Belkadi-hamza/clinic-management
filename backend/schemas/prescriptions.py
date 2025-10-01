from pydantic import BaseModel
from typing import Optional

class PrescriptionBase(BaseModel):
    visit_id: int
    medication_id: int
    prescribing_doctor_id: int
    dosage_instructions: str
    quantity_prescribed: Optional[int] = None
    duration_days: Optional[int] = None
    is_free: Optional[bool] = False
    refills_allowed: Optional[int] = 0

class PrescriptionCreate(PrescriptionBase):
    created_by: int

class PrescriptionUpdate(BaseModel):
    dosage_instructions: Optional[str] = None
    quantity_prescribed: Optional[int] = None
    duration_days: Optional[int] = None
    is_free: Optional[bool] = None
    refills_allowed: Optional[int] = None

class PrescriptionResponse(PrescriptionBase):
    id: int
    created_by: int
    created_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True