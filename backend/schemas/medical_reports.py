from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class ReportType(str, Enum):
    lab = "lab"
    radiology = "radiology"
    clinical = "clinical"
    surgical = "surgical"
    discharge = "discharge"
    pathology = "pathology"
    imaging = "imaging"
    other = "other"

class ReportStatus(str, Enum):
    draft = "draft"
    finalized = "finalized"
    reviewed = "reviewed"
    delivered = "delivered"
    archived = "archived"

class ResultFlag(str, Enum):
    normal = "normal"
    low = "low"
    high = "high"
    critical = "critical"
    abnormal = "abnormal"

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
    test_results: Optional[Dict[str, Any]] = None
    normal_range: Optional[str] = None
    abnormal_notes: Optional[str] = None
    imaging_findings: Optional[str] = None
    impression: Optional[str] = None
    technique: Optional[str] = None
    comparison: Optional[str] = None
    clinical_history: Optional[str] = None
    is_confidential: bool = True
    status: ReportStatus = ReportStatus.draft
    reviewed_by_id: Optional[int] = None
    review_notes: Optional[str] = None
    template_used: Optional[str] = None
    additional_notes: Optional[str] = None
    attachment_urls: Optional[List[str]] = None

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

    @field_validator('reviewed_by_id')
    def review_date_required_with_reviewer(cls, v, values):
        if v and not values.get('review_date'):
            raise ValueError('Review date is required when reviewer is specified')
        return v

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
    test_results: Optional[Dict[str, Any]] = None
    normal_range: Optional[str] = None
    abnormal_notes: Optional[str] = None
    imaging_findings: Optional[str] = None
    impression: Optional[str] = None
    technique: Optional[str] = None
    comparison: Optional[str] = None
    clinical_history: Optional[str] = None
    is_confidential: Optional[bool] = None
    status: Optional[ReportStatus] = None
    reviewed_by_id: Optional[int] = None
    review_date: Optional[date] = None
    review_notes: Optional[str] = None
    template_used: Optional[str] = None
    additional_notes: Optional[str] = None
    attachment_urls: Optional[List[str]] = None

class MedicalReportResponse(MedicalReportBase):
    id: int
    report_code: str
    review_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    doctor_name: Optional[str] = None
    reviewer_name: Optional[str] = None
    visit_date: Optional[date] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    
    class Config:
        from_attributes = True

class MedicalReportWithDetails(MedicalReportResponse):
    patient_details: Optional[dict] = None
    doctor_details: Optional[dict] = None
    reviewer_details: Optional[dict] = None
    visit_details: Optional[dict] = None
    lab_results: List['LabTestResultResponse'] = []

# Report Template Schemas
class ReportTemplateBase(BaseModel):
    template_name: str
    report_type: ReportType
    content: str
    variables: Optional[Dict[str, Any]] = None
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    styles: Optional[str] = None
    sections: Optional[Dict[str, Any]] = None
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

class ReportTemplateCreate(ReportTemplateBase):
    pass

class ReportTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    header_content: Optional[str] = None
    footer_content: Optional[str] = None
    styles: Optional[str] = None
    sections: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    version: Optional[str] = None

class ReportTemplateResponse(ReportTemplateBase):
    id: int
    template_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Report Category Schemas
class ReportCategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None
    report_type: ReportType
    parent_category_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0

    @field_validator('category_name')
    def category_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()

class ReportCategoryCreate(ReportCategoryBase):
    pass

class ReportCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None
    report_type: Optional[ReportType] = None
    parent_category_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class ReportCategoryResponse(ReportCategoryBase):
    id: int
    category_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    parent_category_name: Optional[str] = None
    sub_category_count: int = 0
    report_count: int = 0
    
    class Config:
        from_attributes = True

class ReportCategoryTree(ReportCategoryResponse):
    sub_categories: List['ReportCategoryTree'] = []

# Lab Test Result Schemas
class LabTestResultBase(BaseModel):
    report_id: int
    test_name: str
    test_code: Optional[str] = None
    result_value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    flag: Optional[ResultFlag] = None
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    performed_date: Optional[date] = None
    verified_by: Optional[str] = None

    @field_validator('test_name')
    def test_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Test name cannot be empty')
        return v.strip()

    @field_validator('performed_date')
    def performed_date_not_future(cls, v):
        if v and v > date.today():
            raise ValueError('Performed date cannot be in the future')
        return v

    @field_validator('verified_by')
    def verified_date_required_with_verifier(cls, v, values):
        if v and not values.get('verified_date'):
            raise ValueError('Verified date is required when verifier is specified')
        return v

class LabTestResultCreate(LabTestResultBase):
    pass

class LabTestResultUpdate(BaseModel):
    test_name: Optional[str] = None
    test_code: Optional[str] = None
    result_value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    flag: Optional[ResultFlag] = None
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    performed_date: Optional[date] = None
    verified_by: Optional[str] = None
    verified_date: Optional[date] = None

class LabTestResultResponse(LabTestResultBase):
    id: int
    result_code: str
    verified_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    report_title: Optional[str] = None
    patient_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Search and Filter Schemas
class MedicalReportSearch(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[ReportStatus] = None
    is_confidential: Optional[bool] = None

class ReportTemplateSearch(BaseModel):
    template_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class ReportCategorySearch(BaseModel):
    category_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    parent_category_id: Optional[int] = None
    is_active: Optional[bool] = None

class LabTestResultSearch(BaseModel):
    test_name: Optional[str] = None
    patient_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    flag: Optional[ResultFlag] = None

# Statistics and Reports
class ReportStats(BaseModel):
    total_reports: int
    by_type: List[dict]
    by_status: List[dict]
    by_month: List[dict]
    abnormal_results_count: int
    pending_review_count: int

class LabStats(BaseModel):
    total_tests: int
    abnormal_tests: int
    critical_tests: int
    by_test_type: List[dict]
    by_flag: List[dict]

class TrendAnalysis(BaseModel):
    period: str
    total_reports: int
    abnormal_count: int
    average_tests_per_report: float

# Bulk Operations
class BulkReportCreate(BaseModel):
    reports: List[MedicalReportCreate]

class BulkLabResultCreate(BaseModel):
    results: List[LabTestResultCreate]

# Report Generation
class ReportGenerationRequest(BaseModel):
    template_id: int
    patient_id: int
    doctor_id: int
    visit_id: Optional[int] = None
    variables: Dict[str, Any]

# Status Change
class ReportStatusChange(BaseModel):
    status: ReportStatus
    review_notes: Optional[str] = None

class ReportReview(BaseModel):
    reviewed_by_id: int
    review_notes: Optional[str] = None

    @field_validator('reviewed_by_id')
    def reviewer_required(cls, v):
        if not v:
            raise ValueError('Reviewer ID is required')
        return v

# Lab Result Import
class LabResultImport(BaseModel):
    report_id: int
    results: List[Dict[str, Any]]
    import_source: Optional[str] = None

    @field_validator('results')
    def results_not_empty(cls, v):
        if not v:
            raise ValueError('Results cannot be empty')
        return v