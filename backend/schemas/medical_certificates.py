from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class CertificateType(str, Enum):
    sick_leave = "sick_leave"
    fitness = "fitness"
    pregnancy = "pregnancy"
    vaccination = "vaccination"
    dental = "dental"
    other = "other"

class CertificateStatus(str, Enum):
    draft = "draft"
    issued = "issued"
    cancelled = "cancelled"
    expired = "expired"

class ReportType(str, Enum):
    lab = "lab"
    radiology = "radiology"
    clinical = "clinical"
    surgical = "surgical"
    discharge = "discharge"
    other = "other"

class ReportStatus(str, Enum):
    draft = "draft"
    finalized = "finalized"
    delivered = "delivered"
    archived = "archived"

# Medical Certificate Schemas
class MedicalCertificateBase(BaseModel):
    patient_id: int
    issuing_doctor_id: int
    visit_id: Optional[int] = None
    issue_date: date
    certificate_type: CertificateType
    title: str
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    work_resumption_date: Optional[date] = None
    accident_date: Optional[date] = None
    diagnosis: Optional[str] = None
    medical_findings: Optional[str] = None
    restrictions: Optional[str] = None
    recommendations: Optional[str] = None
    treatment_plan: Optional[str] = None
    is_work_related: bool = False
    is_confidential: bool = False
    status: CertificateStatus = CertificateStatus.draft
    template_used: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('issue_date')
    def issue_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Issue date cannot be in the future')
        return v

    @field_validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('End date cannot be before start date')
        return v

    @field_validator('work_resumption_date')
    def work_resumption_after_start(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('Work resumption date cannot be before start date')
        return v

    @field_validator('duration_days')
    def duration_days_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duration days must be positive')
        return v

    @field_validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class MedicalCertificateCreate(MedicalCertificateBase):
    pass

class MedicalCertificateUpdate(BaseModel):
    visit_id: Optional[int] = None
    issue_date: Optional[date] = None
    certificate_type: Optional[CertificateType] = None
    title: Optional[str] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    work_resumption_date: Optional[date] = None
    accident_date: Optional[date] = None
    diagnosis: Optional[str] = None
    medical_findings: Optional[str] = None
    restrictions: Optional[str] = None
    recommendations: Optional[str] = None
    treatment_plan: Optional[str] = None
    is_work_related: Optional[bool] = None
    is_confidential: Optional[bool] = None
    status: Optional[CertificateStatus] = None
    template_used: Optional[str] = None
    notes: Optional[str] = None

class MedicalCertificateResponse(MedicalCertificateBase):
    id: int
    certificate_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    doctor_name: Optional[str] = None
    visit_date: Optional[date] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    
    class Config:
        from_attributes = True

class MedicalCertificateWithDetails(MedicalCertificateResponse):
    patient_details: Optional[dict] = None
    doctor_details: Optional[dict] = None
    visit_details: Optional[dict] = None

# Certificate Template Schemas
class CertificateTemplateBase(BaseModel):
    template_name: str
    certificate_type: CertificateType
    content: str
    variables: Optional[str] = None
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    clinic_email: Optional[str] = None
    doctor_signature_line: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    version: str = '1.0'

    @field_validator('template_name')
    def template_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()

    @field_validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

class CertificateTemplateCreate(CertificateTemplateBase):
    pass

class CertificateTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    certificate_type: Optional[CertificateType] = None
    content: Optional[str] = None
    variables: Optional[str] = None
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    clinic_email: Optional[str] = None
    doctor_signature_line: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    version: Optional[str] = None

class CertificateTemplateResponse(CertificateTemplateBase):
    id: int
    template_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Medical Report Schemas
class MedicalReportBase(BaseModel):
    patient_id: int
    doctor_id: int
    visit_id: Optional[int] = None
    report_date: date
    report_type: ReportType
    title: str
    content: str
    findings: Optional[str] = None
    diagnosis: Optional[str] = None
    recommendations: Optional[str] = None
    medications: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    is_confidential: bool = True
    status: ReportStatus = ReportStatus.draft
    template_used: Optional[str] = None
    additional_notes: Optional[str] = None

    @field_validator('report_date')
    def report_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Report date cannot be in the future')
        return v

    @field_validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

class MedicalReportCreate(MedicalReportBase):
    pass

class MedicalReportUpdate(BaseModel):
    visit_id: Optional[int] = None
    report_date: Optional[date] = None
    report_type: Optional[ReportType] = None
    title: Optional[str] = None
    content: Optional[str] = None
    findings: Optional[str] = None
    diagnosis: Optional[str] = None
    recommendations: Optional[str] = None
    medications: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    is_confidential: Optional[bool] = None
    status: Optional[ReportStatus] = None
    template_used: Optional[str] = None
    additional_notes: Optional[str] = None

class MedicalReportResponse(MedicalReportBase):
    id: int
    report_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    doctor_name: Optional[str] = None
    visit_date: Optional[date] = None
    
    class Config:
        from_attributes = True

class MedicalReportWithDetails(MedicalReportResponse):
    patient_details: Optional[dict] = None
    doctor_details: Optional[dict] = None
    visit_details: Optional[dict] = None

# Search and Filter Schemas
class MedicalCertificateSearch(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    certificate_type: Optional[CertificateType] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[CertificateStatus] = None
    is_work_related: Optional[bool] = None

class CertificateTemplateSearch(BaseModel):
    template_name: Optional[str] = None
    certificate_type: Optional[CertificateType] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class MedicalReportSearch(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[ReportStatus] = None

# Statistics and Reports
class CertificateStats(BaseModel):
    total_certificates: int
    by_type: List[dict]
    by_status: List[dict]
    by_month: List[dict]
    work_related_count: int

class ReportStats(BaseModel):
    total_reports: int
    by_type: List[dict]
    by_status: List[dict]
    by_month: List[dict]

class CertificateVerification(BaseModel):
    certificate_code: str
    is_valid: bool
    status: str
    patient_name: str
    doctor_name: str
    issue_date: date
    certificate_type: str

# Bulk Operations
class BulkCertificateCreate(BaseModel):
    certificates: List[MedicalCertificateCreate]

class BulkReportCreate(BaseModel):
    reports: List[MedicalReportCreate]

# Certificate Generation
class CertificateGenerationRequest(BaseModel):
    template_id: int
    patient_id: int
    issuing_doctor_id: int
    visit_id: Optional[int] = None
    variables: dict  # Dynamic variables for template

class ReportGenerationRequest(BaseModel):
    template_id: int
    patient_id: int
    doctor_id: int
    visit_id: Optional[int] = None
    variables: dict

# Status Change
class StatusChangeRequest(BaseModel):
    status: CertificateStatus
    cancellation_reason: Optional[str] = None

    @field_validator('cancellation_reason')
    def cancellation_reason_required(cls, v, values):
        if values.get('status') == CertificateStatus.cancelled and not v:
            raise ValueError('Cancellation reason is required when cancelling a certificate')
        return v