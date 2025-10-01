from pydantic import BaseModel
from typing import Optional
from datetime import date

class RadiologyOrderBase(BaseModel):
    visit_id: int
    exam_id: int
    ordering_doctor_id: int
    order_date: date
    imaging_center: Optional[str] = None
    clinical_notes: Optional[str] = None
    radiology_report: Optional[str] = None
    findings: Optional[str] = None
    conclusion: Optional[str] = None
    report_date: Optional[date] = None

class RadiologyOrderCreate(RadiologyOrderBase):
    created_by: int

class RadiologyOrderUpdate(BaseModel):
    imaging_center: Optional[str] = None
    clinical_notes: Optional[str] = None
    radiology_report: Optional[str] = None
    findings: Optional[str] = None
    conclusion: Optional[str] = None
    report_date: Optional[date] = None
    updated_by: Optional[int] = None

class RadiologyOrderResponse(RadiologyOrderBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True