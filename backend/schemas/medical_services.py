from pydantic import BaseModel
from typing import Optional

class MedicalServiceBase(BaseModel):
    service_code: str
    service_name: str
    description: Optional[str] = None
    standard_price: float
    is_active: Optional[bool] = True

class MedicalServiceCreate(MedicalServiceBase):
    created_by: int

class MedicalServiceUpdate(BaseModel):
    service_name: Optional[str] = None
    description: Optional[str] = None
    standard_price: Optional[float] = None
    is_active: Optional[bool] = None
    updated_by: Optional[int] = None

class MedicalServiceResponse(MedicalServiceBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True