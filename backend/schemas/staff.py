from pydantic import BaseModel, EmailStr
from typing import Optional

class StaffBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    position: Optional[str] = None
    department: Optional[str] = None
    mobile_phone: Optional[str] = None
    home_phone: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    position: Optional[str] = None
    department: Optional[str] = None
    mobile_phone: Optional[str] = None
    home_phone: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None

class StaffResponse(StaffBase):
    id: int
    created_at: str
    status: str

    class Config:
        from_attributes = True