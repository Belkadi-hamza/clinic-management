from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, time
from enum import Enum

class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class AppointmentType(str, Enum):
    consultation = "consultation"
    follow_up = "follow_up"
    emergency = "emergency"
    routine_checkup = "routine_checkup"

class AppointmentSlotBase(BaseModel):
    slot_index: int
    slot_time: str
    is_available: bool = True

class AppointmentSlotCreate(AppointmentSlotBase):
    pass

class AppointmentSlotUpdate(BaseModel):
    slot_index: Optional[int] = None
    slot_time: Optional[str] = None
    is_available: Optional[bool] = None

class AppointmentSlotResponse(AppointmentSlotBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: str
    slot_id: Optional[int] = None
    appointment_type: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.scheduled
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('appointment_date')
    def appointment_date_cannot_be_in_past(cls, v):
        if v < date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    slot_id: Optional[int] = None
    appointment_type: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('appointment_date')
    def appointment_date_cannot_be_in_past(cls, v):
        if v and v < date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

class AppointmentResponse(BaseModel):
    id: int
    appointment_code: str
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: str
    slot_id: Optional[int]
    appointment_type: Optional[str]
    status: AppointmentStatus
    reason_for_visit: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: Optional[str]
    
    # Related data
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_code: Optional[str] = None
    doctor_code: Optional[str] = None
    
    class Config:
        from_attributes = True

class AppointmentWithDetails(AppointmentResponse):
    patient_details: Optional[dict] = None
    doctor_details: Optional[dict] = None
    slot_details: Optional[dict] = None

class AppointmentCalendar(BaseModel):
    date: date
    appointments: List[AppointmentResponse]

class TimeSlot(BaseModel):
    time: str
    available: bool
    slot_id: Optional[int]

class DailySchedule(BaseModel):
    date: date
    slots: List[TimeSlot]

class AppointmentStats(BaseModel):
    total: int
    scheduled: int
    confirmed: int
    completed: int
    cancelled: int
    no_show: int

class AppointmentSearch(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[AppointmentStatus] = None