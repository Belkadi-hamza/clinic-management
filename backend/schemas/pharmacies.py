from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

# Base schemas
class PharmacyBase(BaseModel):
    pharmacy_code: str
    pharmacy_name: str
    owner_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool = True

# Create schemas
class PharmacyCreate(PharmacyBase):
    @field_validator('pharmacy_code')
    def validate_pharmacy_code(cls, v):
        if not v.strip():
            raise ValueError('Pharmacy code cannot be empty')
        if len(v) > 20:
            raise ValueError('Pharmacy code cannot exceed 20 characters')
        return v.upper()

    @field_validator('pharmacy_name')
    def validate_pharmacy_name(cls, v):
        if not v.strip():
            raise ValueError('Pharmacy name cannot be empty')
        return v

    @field_validator('phone', 'mobile')
    def validate_phone_numbers(cls, v):
        if v is not None:
            # Remove any non-digit characters
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v

    @field_validator('email')
    def validate_email_domain(cls, v):
        if v is not None:
            # Basic email validation is handled by EmailStr
            # You can add additional domain validation here if needed
            pass
        return v

# Update schemas
class PharmacyUpdate(BaseModel):
    pharmacy_code: Optional[str] = None
    pharmacy_name: Optional[str] = None
    owner_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

    @field_validator('pharmacy_code')
    def validate_pharmacy_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Pharmacy code cannot be empty')
            if len(v) > 20:
                raise ValueError('Pharmacy code cannot exceed 20 characters')
            return v.upper()
        return v

    @field_validator('pharmacy_name')
    def validate_pharmacy_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Pharmacy name cannot be empty')
        return v

    @field_validator('phone', 'mobile')
    def validate_phone_numbers(cls, v):
        if v is not None:
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v

# Response schemas
class PharmacyResponse(PharmacyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    status: str
    created_by_username: Optional[str] = None
    updated_by_username: Optional[str] = None

    class Config:
        from_attributes = True

class PharmacySimpleResponse(BaseModel):
    id: int
    pharmacy_code: str
    pharmacy_name: str
    city: Optional[str]
    phone: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

# List responses
class PharmacyListResponse(BaseModel):
    pharmacies: List[PharmacyResponse]
    total: int
    active_count: int
    inactive_count: int

class PharmacySearchResponse(BaseModel):
    pharmacies: List[PharmacySimpleResponse]
    total: int

# Statistics
class PharmacyStatsResponse(BaseModel):
    total_pharmacies: int
    active_pharmacies: int
    inactive_pharmacies: int
    pharmacies_by_city: List[dict]
    recently_added: List[PharmacySimpleResponse]