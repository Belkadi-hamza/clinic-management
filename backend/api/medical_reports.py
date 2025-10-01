from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import logging

from ..db import get_db
from ..schemas.medical_reports import (
    MedicalReportCreate, MedicalReportUpdate, MedicalReportResponse, MedicalReportWithDetails,
    MedicalReportSearch, ReportTemplateCreate, ReportTemplateUpdate, ReportTemplateResponse,
    ReportTemplateSearch, ReportCategoryCreate, ReportCategoryUpdate, ReportCategoryResponse,
    ReportCategoryTree, ReportCategorySearch, LabTestResultCreate, LabTestResultUpdate,
    LabTestResultResponse, LabTestResultSearch, ReportStats, LabStats, TrendAnalysis,
    BulkReportCreate, BulkLabResultCreate, ReportGenerationRequest, ReportStatusChange,
    ReportReview, LabResultImport
)
from ..crud.medical_reports import (
    get_medical_reports, get_medical_report_by_id, get_medical_report_by_code,
    get_reports_by_patient, get_reports_by_doctor, get_reports_by_type,
    get_reports_by_date_range, get_pending_review_reports, search_medical_reports,
    create_medical_report, create_bulk_medical_reports, update_medical_report,
    delete_medical_report, finalize_medical_report, review_medical_report,
    deliver_medical_report, archive_medical_report,
    get_report_templates, get_report_template_by_id, get_template_by_type,
    search_report_templates, create_report_template, update_report_template,
    delete_report_template, generate_report_from_template,
    get_report_categories, get_report_category_by_id, get_root_categories,
    get_sub_categories, get_category_tree, search_report_categories,
    create_report_category, update_report_category, delete_report_category,
    get_lab_test_results, get_lab_test_result_by_id, get_results_by_report,
    get_abnormal_results, search_lab_test_results, create_lab_test_result,
    create_bulk_lab_results, import_lab_results, update_lab_test_result,
    delete_lab_test_result, verify_lab_result,
    get_report_stats, get_lab_stats, get_trend_analysis
)
from ..deps import get_current_user, require_permission, require_doctor_or_above, require_admin_or_super

router = APIRouter()

logger = logging.getLogger(__name__)

# Medical Report Endpoints
@router.get("/reports/", response_model=List[MedicalReportResponse])
def read_medical_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical reports"""
    require_permission(current_user, "medical_records", "read")
    reports = get_medical_reports(db, skip=skip, limit=limit)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
            
            # Calculate patient age
            if report.patient.date_of_birth:
                today = date.today()
                age = today.year - report.patient.date_of_birth.year
                if today.month < report.patient.date_of_birth.month or (
                    today.month == report.patient.date_of_birth.month and 
                    today.day < report.patient.date_of_birth.day
                ):
                    age -= 1
                enhanced_data.patient_age = age
            
            enhanced_data.patient_gender = report.patient.gender
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.reviewer:
            enhanced_data.reviewer_name = f"{report.reviewer.first_name} {report.reviewer.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.get("/reports/search", response_model=List[MedicalReportResponse])
def search_medical_reports_endpoint(
    patient_name: Optional[str] = Query(None),
    doctor_name: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    is_confidential: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search medical reports with filters"""
    require_permission(current_user, "medical_records", "read")
    
    search_criteria = MedicalReportSearch(
        patient_name=patient_name,
        doctor_name=doctor_name,
        report_type=report_type,
        date_from=date_from,
        date_to=date_to,
        status=status,
        is_confidential=is_confidential
    )
    
    reports = search_medical_reports(db, search_criteria, skip=skip, limit=limit)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.get("/reports/{report_id}", response_model=MedicalReportWithDetails)
def read_medical_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical report by ID with details"""
    require_permission(current_user, "medical_records", "read")
    report = get_medical_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    enhanced_data = MedicalReportWithDetails.from_orm(report)
    
    # Add related information
    if report.patient:
        enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
        enhanced_data.patient_code = report.patient.patient_code
        enhanced_data.patient_details = {
            "id": report.patient.id,
            "code": report.patient.patient_code,
            "name": f"{report.patient.first_name} {report.patient.last_name}",
            "date_of_birth": report.patient.date_of_birth,
            "gender": report.patient.gender,
            "contact_info": report.patient.mobile_phone or report.patient.email
        }
        
        # Calculate patient age
        if report.patient.date_of_birth:
            today = date.today()
            age = today.year - report.patient.date_of_birth.year
            if today.month < report.patient.date_of_birth.month or (
                today.month == report.patient.date_of_birth.month and 
                today.day < report.patient.date_of_birth.day
            ):
                age -= 1
            enhanced_data.patient_age = age
        
        enhanced_data.patient_gender = report.patient.gender
    
    if report.doctor:
        enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        enhanced_data.doctor_details = {
            "id": report.doctor.id,
            "name": f"{report.doctor.first_name} {report.doctor.last_name}",
            "specialization": report.doctor.specialization,
            "license_number": report.doctor.license_number
        }
    
    if report.reviewer:
        enhanced_data.reviewer_name = f"{report.reviewer.first_name} {report.reviewer.last_name}"
        enhanced_data.reviewer_details = {
            "id": report.reviewer.id,
            "name": f"{report.reviewer.first_name} {report.reviewer.last_name}",
            "specialization": report.reviewer.specialization
        }
    
    if report.visit:
        enhanced_data.visit_date = report.visit.visit_date
        enhanced_data.visit_details = {
            "id": report.visit.id,
            "visit_date": report.visit.visit_date,
            "chief_complaint": report.visit.chief_complaint,
            "diagnosis": report.visit.diagnosis
        }
    
    # Add lab results
    lab_results = get_results_by_report(db, report_id)
    enhanced_data.lab_results = [
        LabTestResultResponse.from_orm(result) for result in lab_results
    ]
    
    return enhanced_data

@router.get("/reports/code/{report_code}", response_model=MedicalReportWithDetails)
def read_medical_report_by_code(
    report_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical report by code"""
    require_permission(current_user, "medical_records", "read")
    report = get_medical_report_by_code(db, report_code)
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    return read_medical_report(report.id, current_user, db)

@router.get("/patients/{patient_id}/reports", response_model=List[MedicalReportResponse])
def read_reports_by_patient(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for a specific patient"""
    require_permission(current_user, "medical_records", "read")
    reports = get_reports_by_patient(db, patient_id)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.get("/doctors/{doctor_id}/reports", response_model=List[MedicalReportResponse])
def read_reports_by_doctor(
    doctor_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports created by a specific doctor"""
    require_permission(current_user, "medical_records", "read")
    reports = get_reports_by_doctor(db, doctor_id)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.get("/reports/type/{report_type}", response_model=List[MedicalReportResponse])
def read_reports_by_type(
    report_type: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports of a specific type"""
    require_permission(current_user, "medical_records", "read")
    reports = get_reports_by_type(db, report_type)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.get("/reports/date-range", response_model=List[MedicalReportResponse])
def read_reports_by_date_range(
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reports within a date range"""
    require_permission(current_user, "medical_records", "read")
    reports = get_reports_by_date_range(db, start_date, end_date)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.get("/reports/pending-review", response_model=List[MedicalReportResponse])
def read_pending_review_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reports pending review"""
    require_permission(current_user, "medical_records", "read")
    reports = get_pending_review_reports(db)
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.post("/reports/", response_model=MedicalReportResponse)
def create_medical_report_endpoint(
    report: MedicalReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new medical report"""
    require_permission(current_user, "medical_records", "create")
    
    # Validate patient exists
    from ..crud.patients import get_patient_by_id
    patient = get_patient_by_id(db, report.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Validate doctor exists
    from ..crud.doctors import get_doctor_by_id
    doctor = get_doctor_by_id(db, report.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Validate visit if provided
    if report.visit_id:
        from ..crud.patient_visits import get_patient_visit_by_id
        visit = get_patient_visit_by_id(db, report.visit_id)
        if not visit:
            raise HTTPException(status_code=404, detail="Patient visit not found")
    
    # Validate reviewer if provided
    if report.reviewed_by_id:
        reviewer = get_doctor_by_id(db, report.reviewed_by_id)
        if not reviewer:
            raise HTTPException(status_code=404, detail="Reviewer doctor not found")
    
    db_report = create_medical_report(db, report, current_user["id"])
    
    enhanced_data = MedicalReportResponse.from_orm(db_report)
    
    # Add related information
    if db_report.patient:
        enhanced_data.patient_name = f"{db_report.patient.first_name} {db_report.patient.last_name}"
        enhanced_data.patient_code = db_report.patient.patient_code
    
    if db_report.doctor:
        enhanced_data.doctor_name = f"{db_report.doctor.first_name} {db_report.doctor.last_name}"
    
    if db_report.visit:
        enhanced_data.visit_date = db_report.visit.visit_date
    
    return enhanced_data

@router.post("/reports/bulk", response_model=List[MedicalReportResponse])
def create_bulk_medical_reports_endpoint(
    bulk_report: BulkReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple medical reports"""
    require_permission(current_user, "medical_records", "create")
    reports = create_bulk_medical_reports(db, bulk_report.reports, current_user["id"])
    
    enhanced_reports = []
    for report in reports:
        enhanced_data = MedicalReportResponse.from_orm(report)
        
        # Add related information
        if report.patient:
            enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
            enhanced_data.patient_code = report.patient.patient_code
        
        if report.doctor:
            enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        
        if report.visit:
            enhanced_data.visit_date = report.visit.visit_date
        
        enhanced_reports.append(enhanced_data)
    
    return enhanced_reports

@router.put("/reports/{report_id}", response_model=MedicalReportResponse)
def update_medical_report_endpoint(
    report_id: int,
    report: MedicalReportUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medical report"""
    require_permission(current_user, "medical_records", "update")
    db_report = update_medical_report(db, report_id, report, current_user["id"])
    if not db_report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    enhanced_data = MedicalReportResponse.from_orm(db_report)
    
    # Add related information
    if db_report.patient:
        enhanced_data.patient_name = f"{db_report.patient.first_name} {db_report.patient.last_name}"
        enhanced_data.patient_code = db_report.patient.patient_code
    
    if db_report.doctor:
        enhanced_data.doctor_name = f"{db_report.doctor.first_name} {db_report.doctor.last_name}"
    
    if db_report.reviewer:
        enhanced_data.reviewer_name = f"{db_report.reviewer.first_name} {db_report.reviewer.last_name}"
    
    if db_report.visit:
        enhanced_data.visit_date = db_report.visit.visit_date
    
    return enhanced_data

@router.delete("/reports/{report_id}")
def delete_medical_report_endpoint(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete medical report"""
    require_permission(current_user, "medical_records", "delete")
    try:
        db_report = delete_medical_report(db, report_id, current_user["id"])
        if not db_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Medical report deleted successfully"}

@router.post("/reports/{report_id}/finalize", response_model=MedicalReportResponse)
def finalize_medical_report_endpoint(
    report_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Finalize a medical report"""
    try:
        db_report = finalize_medical_report(db, report_id, current_user["id"])
        if not db_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = MedicalReportResponse.from_orm(db_report)
    
    # Add related information
    if db_report.patient:
        enhanced_data.patient_name = f"{db_report.patient.first_name} {db_report.patient.last_name}"
        enhanced_data.patient_code = db_report.patient.patient_code
    
    if db_report.doctor:
        enhanced_data.doctor_name = f"{db_report.doctor.first_name} {db_report.doctor.last_name}"
    
    return enhanced_data

@router.post("/reports/{report_id}/review", response_model=MedicalReportResponse)
def review_medical_report_endpoint(
    report_id: int,
    review: ReportReview,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Review a medical report"""
    try:
        db_report = review_medical_report(db, report_id, review, current_user["id"])
        if not db_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = MedicalReportResponse.from_orm(db_report)
    
    # Add related information
    if db_report.patient:
        enhanced_data.patient_name = f"{db_report.patient.first_name} {db_report.patient.last_name}"
        enhanced_data.patient_code = db_report.patient.patient_code
    
    if db_report.doctor:
        enhanced_data.doctor_name = f"{db_report.doctor.first_name} {db_report.doctor.last_name}"
    
    if db_report.reviewer:
        enhanced_data.reviewer_name = f"{db_report.reviewer.first_name} {db_report.reviewer.last_name}"
    
    return enhanced_data

@router.post("/reports/{report_id}/deliver", response_model=MedicalReportResponse)
def deliver_medical_report_endpoint(
    report_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Mark report as delivered to patient"""
    try:
        db_report = deliver_medical_report(db, report_id, current_user["id"])
        if not db_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = MedicalReportResponse.from_orm(db_report)
    
    # Add related information
    if db_report.patient:
        enhanced_data.patient_name = f"{db_report.patient.first_name} {db_report.patient.last_name}"
        enhanced_data.patient_code = db_report.patient.patient_code
    
    if db_report.doctor:
        enhanced_data.doctor_name = f"{db_report.doctor.first_name} {db_report.doctor.last_name}"
    
    return enhanced_data

@router.post("/reports/{report_id}/archive", response_model=MedicalReportResponse)
def archive_medical_report_endpoint(
    report_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Archive a medical report"""
    try:
        db_report = archive_medical_report(db, report_id, current_user["id"])
        if not db_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = MedicalReportResponse.from_orm(db_report)
    
    # Add related information
    if db_report.patient:
        enhanced_data.patient_name = f"{db_report.patient.first_name} {db_report.patient.last_name}"
        enhanced_data.patient_code = db_report.patient.patient_code
    
    if db_report.doctor:
        enhanced_data.doctor_name = f"{db_report.doctor.first_name} {db_report.doctor.last_name}"
    
    return enhanced_data

# Report Template Endpoints
@router.get("/templates/", response_model=List[ReportTemplateResponse])
def read_report_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all report templates"""
    require_permission(current_user, "medical_records", "read")
    templates = get_report_templates(db, skip=skip, limit=limit)
    return [ReportTemplateResponse.from_orm(template) for template in templates]

@router.get("/templates/search", response_model=List[ReportTemplateResponse])
def search_report_templates_endpoint(
    template_name: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_default: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search report templates with filters"""
    require_permission(current_user, "medical_records", "read")
    
    search_criteria = ReportTemplateSearch(
        template_name=template_name,
        report_type=report_type,
        is_active=is_active,
        is_default=is_default
    )
    
    templates = search_report_templates(db, search_criteria, skip=skip, limit=limit)
    return [ReportTemplateResponse.from_orm(template) for template in templates]

@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
def read_report_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get report template by ID"""
    require_permission(current_user, "medical_records", "read")
    template = get_report_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")
    
    return ReportTemplateResponse.from_orm(template)

@router.get("/templates/type/{report_type}/default", response_model=ReportTemplateResponse)
def read_default_template_by_type(
    report_type: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get default template for a report type"""
    require_permission(current_user, "medical_records", "read")
    template = get_template_by_type(db, report_type, is_default=True)
    if not template:
        raise HTTPException(status_code=404, detail="Default template not found for this report type")
    
    return ReportTemplateResponse.from_orm(template)

@router.post("/templates/", response_model=ReportTemplateResponse)
def create_report_template_endpoint(
    template: ReportTemplateCreate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Create new report template"""
    db_template = create_report_template(db, template, current_user["id"])
    return ReportTemplateResponse.from_orm(db_template)

@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
def update_report_template_endpoint(
    template_id: int,
    template: ReportTemplateUpdate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Update report template"""
    db_template = update_report_template(db, template_id, template, current_user["id"])
    if not db_template:
        raise HTTPException(status_code=404, detail="Report template not found")
    
    return ReportTemplateResponse.from_orm(db_template)

@router.delete("/templates/{template_id}")
def delete_report_template_endpoint(
    template_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Delete report template"""
    try:
        db_template = delete_report_template(db, template_id, current_user["id"])
        if not db_template:
            raise HTTPException(status_code=404, detail="Report template not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Report template deleted successfully"}

@router.post("/templates/generate-report", response_model=MedicalReportResponse)
def generate_report_from_template_endpoint(
    request: ReportGenerationRequest,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Generate a report using a template"""
    try:
        report = generate_report_from_template(
            db, 
            request.template_id, 
            request.patient_id, 
            request.doctor_id, 
            request.variables, 
            current_user["id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = MedicalReportResponse.from_orm(report)
    
    # Add related information
    if report.patient:
        enhanced_data.patient_name = f"{report.patient.first_name} {report.patient.last_name}"
        enhanced_data.patient_code = report.patient.patient_code
    
    if report.doctor:
        enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
    
    return enhanced_data

# Report Category Endpoints
@router.get("/categories/", response_model=List[ReportCategoryResponse])
def read_report_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all report categories"""
    require_permission(current_user, "medical_records", "read")
    categories = get_report_categories(db, skip=skip, limit=limit)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = ReportCategoryResponse.from_orm(category)
        
        # Add sub-category count
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Add report count (placeholder - implement based on your relationship)
        enhanced_data.report_count = 0
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

@router.get("/categories/tree", response_model=List[ReportCategoryTree])
def read_category_tree(
    report_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete category hierarchy"""
    require_permission(current_user, "medical_records", "read")
    category_tree = get_category_tree(db, report_type)
    return category_tree

@router.get("/categories/root", response_model=List[ReportCategoryResponse])
def read_root_categories(
    report_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all root categories"""
    require_permission(current_user, "medical_records", "read")
    categories = get_root_categories(db, report_type)
    return [ReportCategoryResponse.from_orm(category) for category in categories]

@router.get("/categories/{category_id}/subcategories", response_model=List[ReportCategoryResponse])
def read_sub_categories(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sub-categories for a parent category"""
    require_permission(current_user, "medical_records", "read")
    categories = get_sub_categories(db, category_id)
    return [ReportCategoryResponse.from_orm(category) for category in categories]

@router.get("/categories/search", response_model=List[ReportCategoryResponse])
def search_report_categories_endpoint(
    category_name: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    parent_category_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search report categories with filters"""
    require_permission(current_user, "medical_records", "read")
    
    search_criteria = ReportCategorySearch(
        category_name=category_name,
        report_type=report_type,
        parent_category_id=parent_category_id,
        is_active=is_active
    )
    
    categories = search_report_categories(db, search_criteria, skip=skip, limit=limit)
    return [ReportCategoryResponse.from_orm(category) for category in categories]

@router.get("/categories/{category_id}", response_model=ReportCategoryResponse)
def read_report_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get report category by ID"""
    require_permission(current_user, "medical_records", "read")
    category = get_report_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Report category not found")
    
    enhanced_data = ReportCategoryResponse.from_orm(category)
    
    # Add sub-category count
    sub_categories = get_sub_categories(db, category_id)
    enhanced_data.sub_category_count = len(sub_categories)
    
    # Add parent category name if exists
    if category.parent_category:
        enhanced_data.parent_category_name = category.parent_category.category_name
    
    return enhanced_data

@router.post("/categories/", response_model=ReportCategoryResponse)
def create_report_category_endpoint(
    category: ReportCategoryCreate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Create new report category"""
    # Validate parent category if provided
    if category.parent_category_id:
        parent_category = get_report_category_by_id(db, category.parent_category_id)
        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    db_category = create_report_category(db, category, current_user["id"])
    return ReportCategoryResponse.from_orm(db_category)

@router.put("/categories/{category_id}", response_model=ReportCategoryResponse)
def update_report_category_endpoint(
    category_id: int,
    category: ReportCategoryUpdate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Update report category"""
    try:
        db_category = update_report_category(db, category_id, category, current_user["id"])
        if not db_category:
            raise HTTPException(status_code=404, detail="Report category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return ReportCategoryResponse.from_orm(db_category)

@router.delete("/categories/{category_id}")
def delete_report_category_endpoint(
    category_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Delete report category"""
    try:
        db_category = delete_report_category(db, category_id, current_user["id"])
        if not db_category:
            raise HTTPException(status_code=404, detail="Report category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Report category deleted successfully"}

# Lab Test Result Endpoints
@router.get("/lab-results/", response_model=List[LabTestResultResponse])
def read_lab_test_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all lab test results"""
    require_permission(current_user, "lab_tests", "read")
    results = get_lab_test_results(db, skip=skip, limit=limit)
    
    enhanced_results = []
    for result in results:
        enhanced_data = LabTestResultResponse.from_orm(result)
        
        # Add related information
        if result.report and result.report.patient:
            enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
        
        if result.report:
            enhanced_data.report_title = result.report.title
        
        enhanced_results.append(enhanced_data)
    
    return enhanced_results

@router.get("/lab-results/search", response_model=List[LabTestResultResponse])
def search_lab_test_results_endpoint(
    test_name: Optional[str] = Query(None),
    patient_name: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    flag: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search lab test results with filters"""
    require_permission(current_user, "lab_tests", "read")
    
    search_criteria = LabTestResultSearch(
        test_name=test_name,
        patient_name=patient_name,
        date_from=date_from,
        date_to=date_to,
        flag=flag
    )
    
    results = search_lab_test_results(db, search_criteria, skip=skip, limit=limit)
    
    enhanced_results = []
    for result in results:
        enhanced_data = LabTestResultResponse.from_orm(result)
        
        # Add related information
        if result.report and result.report.patient:
            enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
        
        if result.report:
            enhanced_data.report_title = result.report.title
        
        enhanced_results.append(enhanced_data)
    
    return enhanced_results

@router.get("/lab-results/{result_id}", response_model=LabTestResultResponse)
def read_lab_test_result(
    result_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get lab test result by ID"""
    require_permission(current_user, "lab_tests", "read")
    result = get_lab_test_result_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lab test result not found")
    
    enhanced_data = LabTestResultResponse.from_orm(result)
    
    # Add related information
    if result.report and result.report.patient:
        enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
    
    if result.report:
        enhanced_data.report_title = result.report.title
    
    return enhanced_data

@router.get("/reports/{report_id}/lab-results", response_model=List[LabTestResultResponse])
def read_results_by_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all lab results for a specific report"""
    require_permission(current_user, "lab_tests", "read")
    results = get_results_by_report(db, report_id)
    
    enhanced_results = []
    for result in results:
        enhanced_data = LabTestResultResponse.from_orm(result)
        
        # Add related information
        if result.report and result.report.patient:
            enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
        
        if result.report:
            enhanced_data.report_title = result.report.title
        
        enhanced_results.append(enhanced_data)
    
    return enhanced_results

@router.get("/lab-results/abnormal", response_model=List[LabTestResultResponse])
def read_abnormal_results(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all abnormal lab results"""
    require_permission(current_user, "lab_tests", "read")
    results = get_abnormal_results(db)
    
    enhanced_results = []
    for result in results:
        enhanced_data = LabTestResultResponse.from_orm(result)
        
        # Add related information
        if result.report and result.report.patient:
            enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
        
        if result.report:
            enhanced_data.report_title = result.report.title
        
        enhanced_results.append(enhanced_data)
    
    return enhanced_results

@router.post("/lab-results/", response_model=LabTestResultResponse)
def create_lab_test_result_endpoint(
    result: LabTestResultCreate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Create new lab test result"""
    # Validate report exists
    report = get_medical_report_by_id(db, result.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    db_result = create_lab_test_result(db, result, current_user["id"])
    
    enhanced_data = LabTestResultResponse.from_orm(db_result)
    
    # Add related information
    if db_result.report and db_result.report.patient:
        enhanced_data.patient_name = f"{db_result.report.patient.first_name} {db_result.report.patient.last_name}"
    
    if db_result.report:
        enhanced_data.report_title = db_result.report.title
    
    return enhanced_data

@router.post("/lab-results/bulk", response_model=List[LabTestResultResponse])
def create_bulk_lab_results_endpoint(
    bulk_results: BulkLabResultCreate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Create multiple lab test results"""
    results = create_bulk_lab_results(db, bulk_results.results, current_user["id"])
    
    enhanced_results = []
    for result in results:
        enhanced_data = LabTestResultResponse.from_orm(result)
        
        # Add related information
        if result.report and result.report.patient:
            enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
        
        if result.report:
            enhanced_data.report_title = result.report.title
        
        enhanced_results.append(enhanced_data)
    
    return enhanced_results

@router.post("/lab-results/import", response_model=List[LabTestResultResponse])
def import_lab_results_endpoint(
    import_data: LabResultImport,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Import multiple lab results"""
    # Validate report exists
    report = get_medical_report_by_id(db, import_data.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    results = import_lab_results(db, import_data, current_user["id"])
    
    enhanced_results = []
    for result in results:
        enhanced_data = LabTestResultResponse.from_orm(result)
        
        # Add related information
        if result.report and result.report.patient:
            enhanced_data.patient_name = f"{result.report.patient.first_name} {result.report.patient.last_name}"
        
        if result.report:
            enhanced_data.report_title = result.report.title
        
        enhanced_results.append(enhanced_data)
    
    return enhanced_results

@router.put("/lab-results/{result_id}", response_model=LabTestResultResponse)
def update_lab_test_result_endpoint(
    result_id: int,
    result: LabTestResultUpdate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Update lab test result"""
    db_result = update_lab_test_result(db, result_id, result, current_user["id"])
    if not db_result:
        raise HTTPException(status_code=404, detail="Lab test result not found")
    
    enhanced_data = LabTestResultResponse.from_orm(db_result)
    
    # Add related information
    if db_result.report and db_result.report.patient:
        enhanced_data.patient_name = f"{db_result.report.patient.first_name} {db_result.report.patient.last_name}"
    
    if db_result.report:
        enhanced_data.report_title = db_result.report.title
    
    return enhanced_data

@router.delete("/lab-results/{result_id}")
def delete_lab_test_result_endpoint(
    result_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Delete lab test result"""
    db_result = delete_lab_test_result(db, result_id, current_user["id"])
    if not db_result:
        raise HTTPException(status_code=404, detail="Lab test result not found")
    
    return {"message": "Lab test result deleted successfully"}

@router.post("/lab-results/{result_id}/verify", response_model=LabTestResultResponse)
def verify_lab_result_endpoint(
    result_id: int,
    verified_by: str,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Verify a lab test result"""
    db_result = verify_lab_result(db, result_id, verified_by, current_user["id"])
    if not db_result:
        raise HTTPException(status_code=404, detail="Lab test result not found")
    
    enhanced_data = LabTestResultResponse.from_orm(db_result)
    
    # Add related information
    if db_result.report and db_result.report.patient:
        enhanced_data.patient_name = f"{db_result.report.patient.first_name} {db_result.report.patient.last_name}"
    
    if db_result.report:
        enhanced_data.report_title = db_result.report.title
    
    return enhanced_data

# Statistics and Analytics Endpoints
@router.get("/stats/reports", response_model=ReportStats)
def get_report_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical report statistics"""
    require_permission(current_user, "reports", "read")
    stats = get_report_stats(db, start_date, end_date)
    return ReportStats(**stats)

@router.get("/stats/lab", response_model=LabStats)
def get_lab_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get lab test statistics"""
    require_permission(current_user, "reports", "read")
    stats = get_lab_stats(db, start_date, end_date)
    return LabStats(**stats)

@router.get("/stats/trends", response_model=List[TrendAnalysis])
def get_trend_analysis_endpoint(
    months: int = Query(12, ge=1, le=36),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trend analysis for reports and lab results"""
    require_permission(current_user, "reports", "read")
    trends = get_trend_analysis(db, months)
    return [TrendAnalysis(**trend) for trend in trends]

# Dashboard Endpoints
@router.get("/dashboard/summary")
def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary for medical reports"""
    require_permission(current_user, "medical_records", "read")
    
    # Get recent reports (last 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    recent_reports = get_reports_by_date_range(db, start_date, end_date)
    
    # Get pending review reports
    pending_review = get_pending_review_reports(db)
    
    # Get abnormal results
    abnormal_results = get_abnormal_results(db)
    
    # Get report statistics for the current month
    month_start = date.today().replace(day=1)
    month_stats = get_report_stats(db, month_start, end_date)
    
    return {
        "recent_reports_count": len(recent_reports),
        "pending_review_count": len(pending_review),
        "abnormal_results_count": len(abnormal_results),
        "monthly_stats": month_stats,
        "recent_reports": [
            {
                "id": report.id,
                "report_code": report.report_code,
                "title": report.title,
                "patient_name": f"{report.patient.first_name} {report.patient.last_name}" if report.patient else "Unknown",
                "report_date": report.report_date,
                "status": report.status
            }
            for report in recent_reports[:10]  # Limit to 10 recent reports
        ]
    }

# Export Endpoints
@router.get("/reports/{report_id}/export")
def export_medical_report(
    report_id: int,
    format: str = Query("pdf", regex="^(pdf|html|json)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export medical report in different formats"""
    require_permission(current_user, "medical_records", "export")
    
    report = get_medical_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    # This would typically generate and return the report in the requested format
    # For now, return a placeholder response
    return {
        "message": f"Report exported in {format.upper()} format",
        "report_id": report_id,
        "report_code": report.report_code,
        "format": format,
        "download_url": f"/api/reports/{report_id}/download/{format}"  # Placeholder
    }

@router.get("/reports/export/bulk")
def bulk_export_reports(
    report_ids: List[int] = Query(...),
    format: str = Query("pdf", regex="^(pdf|zip)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk export multiple medical reports"""
    require_permission(current_user, "medical_records", "export")
    
    reports = []
    for report_id in report_ids:
        report = get_medical_report_by_id(db, report_id)
        if report:
            reports.append(report)
    
    if not reports:
        raise HTTPException(status_code=404, detail="No valid reports found")
    
    # This would typically generate and return a zip file containing all reports
    return {
        "message": f"Exported {len(reports)} reports in {format.upper()} format",
        "report_count": len(reports),
        "format": format,
        "download_url": f"/api/reports/export/bulk/download"  # Placeholder
    }