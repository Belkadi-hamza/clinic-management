from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class VaccineBase(BaseModel):
    vaccine_name: str
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    recommended_age_months: Optional[int] = None
    booster_required: bool = False
    booster_interval_months: Optional[int] = None
    total_doses_required: int = 1
    is_active: bool = True

    @field_validator('total_doses_required')
    def validate_total_doses(cls, v):
        if v < 1:
            raise ValueError('Total doses required must be at least 1')
        return v

    @field_validator('booster_interval_months')
    def validate_booster_interval(cls, v, values):
        if values.get('booster_required') and not v:
            raise ValueError('Booster interval is required when booster is required')
        return v

class VaccineCreate(VaccineBase):
    pass

class VaccineUpdate(BaseModel):
    vaccine_name: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    recommended_age_months: Optional[int] = None
    booster_required: Optional[bool] = None
    booster_interval_months: Optional[int] = None
    total_doses_required: Optional[int] = None
    is_active: Optional[bool] = None

class VaccineResponse(VaccineBase):
    id: int
    vaccine_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

class VaccineInventoryBase(BaseModel):
    vaccine_id: int
    lot_number: str
    batch_number: Optional[str] = None
    expiration_date: date
    quantity_available: int
    quantity_used: int = 0
    reorder_level: int = 10
    unit_cost: Optional[int] = None  # in cents
    supplier: Optional[str] = None
    received_date: date
    storage_temperature: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('quantity_available')
    def validate_quantity_available(cls, v):
        if v < 0:
            raise ValueError('Quantity available cannot be negative')
        return v

    @field_validator('quantity_used')
    def validate_quantity_used(cls, v):
        if v < 0:
            raise ValueError('Quantity used cannot be negative')
        return v

    @field_validator('expiration_date')
    def expiration_date_cannot_be_past(cls, v):
        if v < date.today():
            raise ValueError('Expiration date cannot be in the past')
        return v

class VaccineInventoryCreate(VaccineInventoryBase):
    pass

class VaccineInventoryUpdate(BaseModel):
    quantity_available: Optional[int] = None
    quantity_used: Optional[int] = None
    reorder_level: Optional[int] = None
    unit_cost: Optional[int] = None
    supplier: Optional[str] = None
    storage_temperature: Optional[str] = None
    notes: Optional[str] = None

class VaccineInventoryResponse(VaccineInventoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    vaccine_name: Optional[str] = None
    vaccine_code: Optional[str] = None
    
    class Config:
        from_attributes = True

class VaccinationStats(BaseModel):
    total_vaccines: int
    total_schedules: int
    administered_count: int
    pending_count: int
    upcoming_schedules: int
    expired_vaccines: int
    low_stock_vaccines: int

class PatientVaccinationStatus(BaseModel):
    vaccine_id: int
    vaccine_name: str
    total_doses_required: int
    doses_administered: int
    next_dose_number: Optional[int] = None
    next_scheduled_date: Optional[date] = None
    is_complete: bool
    last_administered_date: Optional[date] = None

class VaccineSchedulePlan(BaseModel):
    vaccine_id: int
    dose_number: int
    recommended_age_months: Optional[int] = None
    scheduled_date: date

class BulkVaccinationSchedule(BaseModel):
    patient_id: int
    schedules: List[VaccineSchedulePlan]

class VaccineSearch(BaseModel):
    vaccine_name: Optional[str] = None
    manufacturer: Optional[str] = None
    is_active: Optional[bool] = None

class VaccinationScheduleSearch(BaseModel):
    patient_name: Optional[str] = None
    vaccine_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_administered: Optional[bool] = None
    dose_number: Optional[int] = None

class InventoryAlert(BaseModel):
    vaccine_id: int
    vaccine_name: str
    lot_number: str
    quantity_available: int
    reorder_level: int
    status: str  # 'low_stock', 'expired', 'out_of_stock'

class VaccinationDueAlert(BaseModel):
    patient_id: int
    patient_name: str
    vaccine_name: str
    dose_number: int
    scheduled_date: date
    days_until_due: int