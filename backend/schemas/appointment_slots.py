from pydantic import BaseModel
from typing import Optional
from datetime import time

class AppointmentSlotBase(BaseModel):
    slot_index: int
    slot_time: time
    is_available: Optional[bool] = True

class AppointmentSlotCreate(AppointmentSlotBase):
    created_by: int

class AppointmentSlotUpdate(BaseModel):
    slot_index: Optional[int] = None
    slot_time: Optional[time] = None
    is_available: Optional[bool] = None
    updated_by: Optional[int] = None

class AppointmentSlotResponse(AppointmentSlotBase):
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[int]

    class Config:
        from_attributes = True