from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# Base schemas
class VisitSymptomBase(BaseModel):
    symptom_id: int
    severity: Optional[str] = None
    duration_days: Optional[int] = None
    notes: Optional[str] = None

# Create schemas
class VisitSymptomCreate(VisitSymptomBase):
    visit_id: int

    @field_validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = ['mild', 'moderate', 'severe', 'very_severe', 'critical']
            if v.lower() not in valid_severities:
                raise ValueError(f'Severity must be one of: {", ".join(valid_severities)}')
            return v.lower()
        return v

    @field_validator('duration_days')
    def validate_duration_days(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Duration days cannot be negative')
            if v > 3650:  # 10 years
                raise ValueError('Duration days cannot exceed 3650 days (10 years)')
        return v

    @field_validator('notes')
    def validate_notes(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Notes cannot exceed 1000 characters')
        return v

# Update schemas
class VisitSymptomUpdate(BaseModel):
    severity: Optional[str] = None
    duration_days: Optional[int] = None
    notes: Optional[str] = None

    @field_validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = ['mild', 'moderate', 'severe', 'very_severe', 'critical']
            if v.lower() not in valid_severities:
                raise ValueError(f'Severity must be one of: {", ".join(valid_severities)}')
            return v.lower()
        return v

    @field_validator('duration_days')
    def validate_duration_days(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Duration days cannot be negative')
            if v > 3650:
                raise ValueError('Duration days cannot exceed 3650 days (10 years)')
        return v

    @field_validator('notes')
    def validate_notes(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Notes cannot exceed 1000 characters')
        return v

# Response schemas
class VisitSymptomResponse(VisitSymptomBase):
    id: int
    visit_id: int
    symptom_name: str
    symptom_code: str
    created_at: datetime
    status: str
    created_by_username: Optional[str] = None

    class Config:
        from_attributes = True

class VisitSymptomDetailResponse(VisitSymptomResponse):
    patient_name: str
    patient_code: str
    visit_date: datetime
    doctor_name: str

    class Config:
        from_attributes = True

# Bulk operations
class VisitSymptomBulkCreate(BaseModel):
    visit_id: int
    symptoms: List[VisitSymptomBase]

class VisitSymptomBulkCreateResponse(BaseModel):
    created: List[VisitSymptomResponse]
    errors: List[dict]
    total_created: int
    total_errors: int

# Analysis schemas
class SymptomAnalysisResponse(BaseModel):
    symptom_id: int
    symptom_code: str
    symptom_name: str
    occurrence_count: int
    average_duration: Optional[float]
    severity_distribution: dict
    most_common_patient_age_group: Optional[str]

class VisitSymptomsSummaryResponse(BaseModel):
    visit_id: int
    total_symptoms: int
    symptoms_by_severity: dict
    symptoms_list: List[VisitSymptomResponse]

# List responses
class VisitSymptomListResponse(BaseModel):
    visit_symptoms: List[VisitSymptomResponse]
    total: int

class VisitSymptomDetailedListResponse(BaseModel):
    visit_symptoms: List[VisitSymptomDetailResponse]
    total: int