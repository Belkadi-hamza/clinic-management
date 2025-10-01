from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# Base schemas
class SymptomBase(BaseModel):
    symptom_code: str
    symptom_name: str
    description: Optional[str] = None

class VisitSymptomBase(BaseModel):
    symptom_id: int
    severity: Optional[str] = None
    duration_days: Optional[int] = None
    notes: Optional[str] = None

# Create schemas
class SymptomCreate(SymptomBase):
    @field_validator('symptom_code')
    def validate_symptom_code(cls, v):
        if not v.strip():
            raise ValueError('Symptom code cannot be empty')
        if len(v) > 20:
            raise ValueError('Symptom code cannot exceed 20 characters')
        return v.upper()

    @field_validator('symptom_name')
    def validate_symptom_name(cls, v):
        if not v.strip():
            raise ValueError('Symptom name cannot be empty')
        return v

class VisitSymptomCreate(VisitSymptomBase):
    visit_id: int

# Update schemas
class SymptomUpdate(BaseModel):
    symptom_code: Optional[str] = None
    symptom_name: Optional[str] = None
    description: Optional[str] = None

    @field_validator('symptom_code')
    def validate_symptom_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Symptom code cannot be empty')
            if len(v) > 20:
                raise ValueError('Symptom code cannot exceed 20 characters')
            return v.upper()
        return v

    @field_validator('symptom_name')
    def validate_symptom_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Symptom name cannot be empty')
        return v

class VisitSymptomUpdate(BaseModel):
    severity: Optional[str] = None
    duration_days: Optional[int] = None
    notes: Optional[str] = None

# Response schemas
class SymptomResponse(SymptomBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True

class VisitSymptomResponse(VisitSymptomBase):
    id: int
    visit_id: int
    symptom_name: str
    symptom_code: str
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

class SymptomWithUsageResponse(SymptomResponse):
    usage_count: int = 0

# List responses
class SymptomListResponse(BaseModel):
    symptoms: List[SymptomResponse]
    total: int

class VisitSymptomListResponse(BaseModel):
    visit_symptoms: List[VisitSymptomResponse]
    total: int