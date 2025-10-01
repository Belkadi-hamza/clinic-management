from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# Base schemas
class DoctorSpecialtyBase(BaseModel):
    specialty: str

# Create schemas
class DoctorSpecialtyCreate(DoctorSpecialtyBase):
    doctor_id: int

    @field_validator('specialty')
    def validate_specialty(cls, v):
        if not v.strip():
            raise ValueError('Specialty cannot be empty')
        if len(v) > 100:
            raise ValueError('Specialty cannot exceed 100 characters')
        return v.strip()

# Update schemas
class DoctorSpecialtyUpdate(BaseModel):
    specialty: Optional[str] = None

    @field_validator('specialty')
    def validate_specialty(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Specialty cannot be empty')
            if len(v) > 100:
                raise ValueError('Specialty cannot exceed 100 characters')
            return v.strip()
        return v

# Response schemas
class DoctorSpecialtyResponse(DoctorSpecialtyBase):
    id: int
    doctor_id: int
    created_at: datetime
    status: str
    created_by_username: Optional[str] = None

    class Config:
        from_attributes = True

class DoctorSpecialtyWithDoctorResponse(DoctorSpecialtyResponse):
    doctor_name: str
    doctor_code: str

    class Config:
        from_attributes = True

# Bulk operations
class DoctorSpecialtyBulkCreate(BaseModel):
    doctor_id: int
    specialties: List[str]

class DoctorSpecialtyBulkCreateResponse(BaseModel):
    created: List[DoctorSpecialtyResponse]
    errors: List[dict]
    total_created: int
    total_errors: int

# Analysis and statistics
class SpecialtyStatsResponse(BaseModel):
    specialty: str
    doctor_count: int
    percentage: float

class DoctorSpecialtySummaryResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    specialties: List[str]
    total_specialties: int

# List responses
class DoctorSpecialtyListResponse(BaseModel):
    doctor_specialties: List[DoctorSpecialtyResponse]
    total: int

class DoctorSpecialtyDetailedListResponse(BaseModel):
    doctor_specialties: List[DoctorSpecialtyWithDoctorResponse]
    total: int

# Search and filter
class SpecialtySearchResponse(BaseModel):
    specialties: List[str]
    total: int