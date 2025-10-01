from pydantic import BaseModel
from typing import Optional

class MedicationBase(BaseModel):
    medication_code: str
    generic_name: str
    brand_name: Optional[str] = None
    pharmaceutical_form: Optional[str] = None
    dosage_strength: Optional[str] = None
    manufacturer: Optional[str] = None
    unit_price: Optional[float] = None
    is_active: Optional[bool] = True

class MedicationCreate(MedicationBase):
    created_by: int

class MedicationUpdate(BaseModel):
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    pharmaceutical_form: Optional[str] = None
    dosage_strength: Optional[str] = None
    manufacturer: Optional[str] = None
    unit_price: Optional[float] = None
    is_active: Optional[bool] = None
    updated_by: Optional[int] = None

class MedicationResponse(MedicationBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True