from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, date

class StaffBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None
    mobile_phone: Optional[str] = None
    home_phone: Optional[str] = None
    fax: Optional[str] = None
    city: Optional[str] = None
    line: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    profile_image: Optional[str] = None
    hire_date: Optional[date] = None
    doctor_code: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    is_doctor: Optional[bool] = None

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None
    mobile_phone: Optional[str] = None
    home_phone: Optional[str] = None
    fax: Optional[str] = None
    city: Optional[str] = None
    line: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    profile_image: Optional[str] = None
    hire_date: Optional[date] = None
    doctor_code: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    is_doctor: Optional[bool] = None

class StaffResponse(StaffBase):
    id: int
    created_at: datetime
    status: str
    
    model_config = ConfigDict(from_attributes=True)