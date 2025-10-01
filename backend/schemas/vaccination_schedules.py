from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class VaccinationScheduleBase(BaseModel):
    patient_id: int
    vaccine_id: int
    dose_number: int
    scheduled_date: date
    administering_doctor_id: Optional[int] = None
    lot_number: Optional[str] = None
    batch_number: Optional[str] = None
    expiration_date: Optional[date] = None
    administration_site: Optional[str] = None
    route: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('scheduled_date')
    def scheduled_date_cannot_be_in_past(cls, v):
        if v < date.today():
            raise ValueError('Scheduled date cannot be in the past')
        return v

    @field_validator('dose_number')
    def validate_dose_number(cls, v):
        if v < 1:
            raise ValueError('Dose number must be at least 1')
        return v

class VaccinationScheduleCreate(VaccinationScheduleBase):
    pass

class VaccinationScheduleUpdate(BaseModel):
    scheduled_date: Optional[date] = None
    administered_date: Optional[date] = None
    is_administered: Optional[bool] = None
    administering_doctor_id: Optional[int] = None
    lot_number: Optional[str] = None
    batch_number: Optional[str] = None
    expiration_date: Optional[date] = None
    administration_site: Optional[str] = None
    route: Optional[str] = None
    adverse_reactions: Optional[str] = None
    notes: Optional[str] = None

class VaccinationScheduleAdminister(BaseModel):
    administered_date: date
    administering_doctor_id: int
    lot_number: str
    batch_number: Optional[str] = None
    expiration_date: date
    administration_site: str
    route: str
    adverse_reactions: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('administered_date')
    def administered_date_cannot_be_future(cls, v):
        if v > date.today():
            raise ValueError('Administered date cannot be in the future')
        return v

class VaccinationScheduleResponse(BaseModel):
    id: int
    schedule_code: str
    patient_id: int
    vaccine_id: int
    dose_number: int
    scheduled_date: date
    administered_date: Optional[date] = None
    is_administered: bool
    administering_doctor_id: Optional[int] = None
    lot_number: Optional[str] = None
    batch_number: Optional[str] = None
    expiration_date: Optional[date] = None
    administration_site: Optional[str] = None
    route: Optional[str] = None
    adverse_reactions: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    vaccine_name: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_code: Optional[str] = None
    vaccine_code: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    
    class Config:
        from_attributes = True

class VaccinationScheduleWithDetails(VaccinationScheduleResponse):
    patient_details: Optional[dict] = None
    vaccine_details: Optional[dict] = None
    doctor_details: Optional[dict] = None

class VaccinationScheduleSearch(BaseModel):
    patient_name: Optional[str] = None
    vaccine_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_administered: Optional[bool] = None
    dose_number: Optional[int] = None
    doctor_name: Optional[str] = None

class VaccinationStats(BaseModel):
    total_schedules: int
    administered_count: int
    pending_count: int
    upcoming_count: int
    overdue_count: int
    completion_rate: float

class PatientVaccinationStatus(BaseModel):
    vaccine_id: int
    vaccine_name: str
    total_doses_required: int
    doses_administered: int
    next_dose_number: Optional[int] = None
    next_scheduled_date: Optional[date] = None
    is_complete: bool
    last_administered_date: Optional[date] = None
    completion_percentage: float

class VaccinationDueAlert(BaseModel):
    patient_id: int
    patient_name: str
    vaccine_name: str
    dose_number: int
    scheduled_date: date
    days_until_due: int
    contact_info: Optional[str] = None

class VaccinationCalendarEvent(BaseModel):
    id: int
    schedule_code: str
    patient_name: str
    vaccine_name: str
    dose_number: int
    scheduled_date: date
    is_administered: bool
    patient_id: int
    vaccine_id: int

class BulkVaccinationScheduleCreate(BaseModel):
    patient_id: int
    schedules: List[dict]  # List of {vaccine_id, dose_number, scheduled_date}

class VaccinationReport(BaseModel):
    period: str
    total_administered: int
    by_vaccine: List[dict]
    by_month: List[dict]
    completion_rates: List[dict]