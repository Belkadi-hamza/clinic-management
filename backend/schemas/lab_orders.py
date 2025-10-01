from pydantic import BaseModel
from typing import Optional
from datetime import date

class LabOrderBase(BaseModel):
    visit_id: int
    test_id: int
    ordering_doctor_id: int
    order_date: date
    laboratory_name: Optional[str] = None
    clinical_notes: Optional[str] = None
    results: Optional[str] = None
    result_date: Optional[date] = None
    is_abnormal: Optional[bool] = None

class LabOrderCreate(LabOrderBase):
    created_by: int

class LabOrderUpdate(BaseModel):
    laboratory_name: Optional[str] = None
    clinical_notes: Optional[str] = None
    results: Optional[str] = None
    result_date: Optional[date] = None
    is_abnormal: Optional[bool] = None
    updated_by: Optional[int] = None

class LabOrderResponse(LabOrderBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True