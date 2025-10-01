from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import logging

from ..db import get_db
from ..schemas.medical_certificates import (
    MedicalCertificateCreate, MedicalCertificateUpdate, MedicalCertificateResponse, MedicalCertificateWithDetails,
    MedicalCertificateSearch, CertificateTemplateCreate, CertificateTemplateUpdate, CertificateTemplateResponse,
    CertificateTemplateSearch, MedicalReportCreate, MedicalReportUpdate, MedicalReportResponse, MedicalReportWithDetails,
    MedicalReportSearch, CertificateStats, ReportStats, CertificateVerification,
    BulkCertificateCreate, BulkReportCreate, CertificateGenerationRequest, StatusChangeRequest
)
from ..crud.medical_certificates import (
    get_medical_certificates, get_medical_certificate_by_id, get_medical_certificate_by_code,
    get_certificates_by_patient, get_certificates_by_doctor, get_certificates_by_visit,
    get_certificates_by_date_range, search_medical_certificates, create_medical_certificate,
    create_bulk_medical_certificates, update_medical_certificate, delete_medical_certificate,
    issue_certificate, cancel_certificate, verify_certificate,
    get_certificate_templates, get_certificate_template_by_id, get_template_by_type,
    search_certificate_templates, create_certificate_template, update_certificate_template,
    delete_certificate_template, generate_certificate_from_template,
    get_medical_reports, get_medical_report_by_id, get_medical_report_by_code,
    get_reports_by_patient, get_reports_by_doctor, search_medical_reports,
    create_medical_report, update_medical_report, delete_medical_report, finalize_medical_report,
    get_certificate_stats, get_report_stats, get_expired_certificates, update_expired_certificates
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouter()

logger = logging.getLogger(__name__)

# Medical Certificate Endpoints
@router.get("/certificates/", response_model=List[MedicalCertificateResponse])
def read_medical_certificates(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical certificates"""
    require_permission(current_user, "patients", "read")
    certificates = get_medical_certificates(db, skip=skip, limit=limit)
    
    enhanced_certificates = []
    for certificate in certificates:
        enhanced_data = MedicalCertificateResponse.from_orm(certificate)
        
        # Add related information
        if certificate.patient:
            enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
            enhanced_data.patient_code = certificate.patient.patient_code
            
            # Calculate patient age
            if certificate.patient.date_of_birth:
                today = date.today()
                age = today.year - certificate.patient.date_of_birth.year
                if today.month < certificate.patient.date_of_birth.month or (
                    today.month == certificate.patient.date_of_birth.month and 
                    today.day < certificate.patient.date_of_birth.day
                ):
                    age -= 1
                enhanced_data.patient_age = age
            
            enhanced_data.patient_gender = certificate.patient.gender
        
        if certificate.issuing_doctor:
            enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        
        if certificate.visit:
            enhanced_data.visit_date = certificate.visit.visit_date
        
        enhanced_certificates.append(enhanced_data)
    
    return enhanced_certificates

@router.get("/certificates/{certificate_id}", response_model=MedicalCertificateWithDetails)
def read_medical_certificate(
    certificate_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical certificate by ID with details"""
    require_permission(current_user, "patients", "read")
    certificate = get_medical_certificate_by_id(db, certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Medical certificate not found")
    
    enhanced_data = MedicalCertificateWithDetails.from_orm(certificate)
    
    # Add related information
    if certificate.patient:
        enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
        enhanced_data.patient_code = certificate.patient.patient_code
        enhanced_data.patient_details = {
            "id": certificate.patient.id,
            "code": certificate.patient.patient_code,
            "name": f"{certificate.patient.first_name} {certificate.patient.last_name}",
            "date_of_birth": certificate.patient.date_of_birth,
            "gender": certificate.patient.gender,
            "contact_info": certificate.patient.mobile_phone or certificate.patient.email
        }
        
        # Calculate patient age
        if certificate.patient.date_of_birth:
            today = date.today()
            age = today.year - certificate.patient.date_of_birth.year
            if today.month < certificate.patient.date_of_birth.month or (
                today.month == certificate.patient.date_of_birth.month and 
                today.day < certificate.patient.date_of_birth.day
            ):
                age -= 1
            enhanced_data.patient_age = age
        
        enhanced_data.patient_gender = certificate.patient.gender
    
    if certificate.issuing_doctor:
        enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        enhanced_data.doctor_details = {
            "id": certificate.issuing_doctor.id,
            "name": f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}",
            "specialization": certificate.issuing_doctor.specialization,
            "license_number": certificate.issuing_doctor.license_number
        }
    
    if certificate.visit:
        enhanced_data.visit_date = certificate.visit.visit_date
        enhanced_data.visit_details = {
            "id": certificate.visit.id,
            "visit_date": certificate.visit.visit_date,
            "chief_complaint": certificate.visit.chief_complaint,
            "diagnosis": certificate.visit.diagnosis
        }
    
    return enhanced_data

@router.get("/patients/{patient_id}/certificates", response_model=List[MedicalCertificateResponse])
def read_certificates_by_patient(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for a specific patient"""
    require_permission(current_user, "patients", "read")
    certificates = get_certificates_by_patient(db, patient_id)
    
    enhanced_certificates = []
    for certificate in certificates:
        enhanced_data = MedicalCertificateResponse.from_orm(certificate)
        
        # Add related information
        if certificate.patient:
            enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
            enhanced_data.patient_code = certificate.patient.patient_code
        
        if certificate.issuing_doctor:
            enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        
        if certificate.visit:
            enhanced_data.visit_date = certificate.visit.visit_date
        
        enhanced_certificates.append(enhanced_data)
    
    return enhanced_certificates

@router.get("/doctors/{doctor_id}/certificates", response_model=List[MedicalCertificateResponse])
def read_certificates_by_doctor(
    doctor_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificates issued by a specific doctor"""
    require_permission(current_user, "patients", "read")
    certificates = get_certificates_by_doctor(db, doctor_id)
    
    enhanced_certificates = []
    for certificate in certificates:
        enhanced_data = MedicalCertificateResponse.from_orm(certificate)
        
        # Add related information
        if certificate.patient:
            enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
            enhanced_data.patient_code = certificate.patient.patient_code
        
        if certificate.issuing_doctor:
            enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        
        if certificate.visit:
            enhanced_data.visit_date = certificate.visit.visit_date
        
        enhanced_certificates.append(enhanced_data)
    
    return enhanced_certificates

@router.post("/certificates/", response_model=MedicalCertificateResponse)
def create_medical_certificate_endpoint(
    certificate: MedicalCertificateCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new medical certificate"""
    require_permission(current_user, "patients", "create")
    
    # Validate patient exists
    from ..crud.patients import get_patient_by_id
    patient = get_patient_by_id(db, certificate.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Validate doctor exists
    from ..crud.doctors import get_doctor_by_id
    doctor = get_doctor_by_id(db, certificate.issuing_doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Validate visit if provided
    if certificate.visit_id:
        from ..crud.patients import get_patient_visit_by_id
        visit = get_patient_visit_by_id(db, certificate.visit_id)
        if not visit:
            raise HTTPException(status_code=404, detail="Patient visit not found")
    
    db_certificate = create_medical_certificate(db, certificate, current_user.id)
    
    enhanced_data = MedicalCertificateResponse.from_orm(db_certificate)
    
    # Add related information
    if db_certificate.patient:
        enhanced_data.patient_name = f"{db_certificate.patient.first_name} {db_certificate.patient.last_name}"
        enhanced_data.patient_code = db_certificate.patient.patient_code
    
    if db_certificate.issuing_doctor:
        enhanced_data.doctor_name = f"{db_certificate.issuing_doctor.first_name} {db_certificate.issuing_doctor.last_name}"
    
    if db_certificate.visit:
        enhanced_data.visit_date = db_certificate.visit.visit_date
    
    return enhanced_data

@router.post("/certificates/bulk", response_model=List[MedicalCertificateResponse])
def create_bulk_medical_certificates_endpoint(
    bulk_certificate: BulkCertificateCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple medical certificates"""
    require_permission(current_user, "patients", "create")
    certificates = create_bulk_medical_certificates(db, bulk_certificate.certificates, current_user.id)
    
    enhanced_certificates = []
    for certificate in certificates:
        enhanced_data = MedicalCertificateResponse.from_orm(certificate)
        
        # Add related information
        if certificate.patient:
            enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
            enhanced_data.patient_code = certificate.patient.patient_code
        
        if certificate.issuing_doctor:
            enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        
        if certificate.visit:
            enhanced_data.visit_date = certificate.visit.visit_date
        
        enhanced_certificates.append(enhanced_data)
    
    return enhanced_certificates

@router.put("/certificates/{certificate_id}", response_model=MedicalCertificateResponse)
def update_medical_certificate_endpoint(
    certificate_id: int,
    certificate: MedicalCertificateUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medical certificate"""
    require_permission(current_user, "patients", "update")
    db_certificate = update_medical_certificate(db, certificate_id, certificate, current_user.id)
    if not db_certificate:
        raise HTTPException(status_code=404, detail="Medical certificate not found")
    
    enhanced_data = MedicalCertificateResponse.from_orm(db_certificate)
    
    # Add related information
    if db_certificate.patient:
        enhanced_data.patient_name = f"{db_certificate.patient.first_name} {db_certificate.patient.last_name}"
        enhanced_data.patient_code = db_certificate.patient.patient_code
    
    if db_certificate.issuing_doctor:
        enhanced_data.doctor_name = f"{db_certificate.issuing_doctor.first_name} {db_certificate.issuing_doctor.last_name}"
    
    if db_certificate.visit:
        enhanced_data.visit_date = db_certificate.visit.visit_date
    
    return enhanced_data

@router.delete("/certificates/{certificate_id}")
def delete_medical_certificate_endpoint(
    certificate_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete medical certificate"""
    require_permission(current_user, "patients", "delete")
    db_certificate = delete_medical_certificate(db, certificate_id, current_user.id)
    if not db_certificate:
        raise HTTPException(status_code=404, detail="Medical certificate not found")
    return {"message": "Medical certificate deleted successfully"}

@router.post("/certificates/{certificate_id}/issue")
def issue_medical_certificate_endpoint(
    certificate_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Issue a medical certificate"""
    require_permission(current_user, "patients", "update")
    try:
        db_certificate = issue_certificate(db, certificate_id, current_user.id)
        if not db_certificate:
            raise HTTPException(status_code=404, detail="Medical certificate not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Medical certificate issued successfully"}

@router.post("/certificates/{certificate_id}/cancel")
def cancel_medical_certificate_endpoint(
    certificate_id: int,
    status_change: StatusChangeRequest,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a medical certificate"""
    require_permission(current_user, "patients", "update")
    try:
        db_certificate = cancel_certificate(db, certificate_id, status_change, current_user.id)
        if not db_certificate:
            raise HTTPException(status_code=404, detail="Medical certificate not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Medical certificate cancelled successfully"}

@router.get("/certificates/verify/{certificate_code}", response_model=CertificateVerification)
def verify_medical_certificate_endpoint(
    certificate_code: str,
    db: Session = Depends(get_db)
):
    """Verify a medical certificate"""
    verification = verify_certificate(db, certificate_code)
    return verification

@router.post("/certificates/search/", response_model=List[MedicalCertificateResponse])
def search_medical_certificates_endpoint(
    search: MedicalCertificateSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search medical certificates with filters"""
    require_permission(current_user, "patients", "read")
    certificates = search_medical_certificates(db, search, skip=skip, limit=limit)
    
    enhanced_certificates = []
    for certificate in certificates:
        enhanced_data = MedicalCertificateResponse.from_orm(certificate)
        
        # Add related information
        if certificate.patient:
            enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
            enhanced_data.patient_code = certificate.patient.patient_code
        
        if certificate.issuing_doctor:
            enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        
        if certificate.visit:
            enhanced_data.visit_date = certificate.visit.visit_date
        
        enhanced_certificates.append(enhanced_data)
    
    return enhanced_certificates

# Certificate Template Endpoints
@router.get("/templates/", response_model=List[CertificateTemplateResponse])
def read_certificate_templates(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificate templates"""
    require_permission(current_user, "patients", "read")
    templates = get_certificate_templates(db, skip=skip, limit=limit)
    return templates

@router.get("/templates/{template_id}", response_model=CertificateTemplateResponse)
def read_certificate_template(
    template_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get certificate template by ID"""
    require_permission(current_user, "patients", "read")
    template = get_certificate_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Certificate template not found")
    return template

@router.get("/templates/type/{certificate_type}")
def read_template_by_type(
    certificate_type: str,
    is_default: bool = Query(True),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template by certificate type"""
    require_permission(current_user, "patients", "read")
    template = get_template_by_type(db, certificate_type, is_default)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found for this certificate type")
    return template

@router.post("/templates/", response_model=CertificateTemplateResponse)
def create_certificate_template_endpoint(
    template: CertificateTemplateCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new certificate template"""
    require_permission(current_user, "patients", "create")
    db_template = create_certificate_template(db, template, current_user.id)
    return db_template

@router.put("/templates/{template_id}", response_model=CertificateTemplateResponse)
def update_certificate_template_endpoint(
    template_id: int,
    template: CertificateTemplateUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update certificate template"""
    require_permission(current_user, "patients", "update")
    db_template = update_certificate_template(db, template_id, template, current_user.id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Certificate template not found")
    return db_template

@router.delete("/templates/{template_id}")
def delete_certificate_template_endpoint(
    template_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete certificate template"""
    require_permission(current_user, "patients", "delete")
    try:
        db_template = delete_certificate_template(db, template_id, current_user.id)
        if not db_template:
            raise HTTPException(status_code=404, detail="Certificate template not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Certificate template deleted successfully"}

@router.post("/templates/search/", response_model=List[CertificateTemplateResponse])
def search_certificate_templates_endpoint(
    search: CertificateTemplateSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search certificate templates with filters"""
    require_permission(current_user, "patients", "read")
    templates = search_certificate_templates(db, search, skip=skip, limit=limit)
    return templates

@router.post("/templates/generate-certificate")
def generate_certificate_from_template_endpoint(
    generation_request: CertificateGenerationRequest,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a certificate using a template"""
    require_permission(current_user, "patients", "create")
    try:
        certificate = generate_certificate_from_template(
            db, 
            generation_request.template_id,
            generation_request.patient_id,
            generation_request.issuing_doctor_id,
            generation_request.variables,
            current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "message": "Certificate generated successfully",
        "certificate_code": certificate.certificate_code,
        "certificate_id": certificate.id
    }

# Medical Report Endpoints
@router.get("/reports/", response_model=List[MedicalReportResponse])
def read_medical_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical reports"""
    require_permission(current_user, "patients", "read")
    reports = get_medical_reports(db, skip=skip, limit=limit)
    
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
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical report by ID with details"""
    require_permission(current_user, "patients", "read")
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
            "gender": report.patient.gender
        }
    
    if report.doctor:
        enhanced_data.doctor_name = f"{report.doctor.first_name} {report.doctor.last_name}"
        enhanced_data.doctor_details = {
            "id": report.doctor.id,
            "name": f"{report.doctor.first_name} {report.doctor.last_name}",
            "specialization": report.doctor.specialization
        }
    
    if report.visit:
        enhanced_data.visit_date = report.visit.visit_date
        enhanced_data.visit_details = {
            "id": report.visit.id,
            "visit_date": report.visit.visit_date,
            "chief_complaint": report.visit.chief_complaint
        }
    
    return enhanced_data

@router.post("/reports/", response_model=MedicalReportResponse)
def create_medical_report_endpoint(
    report: MedicalReportCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new medical report"""
    require_permission(current_user, "patients", "create")
    
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
        from ..crud.patients import get_patient_visit_by_id
        visit = get_patient_visit_by_id(db, report.visit_id)
        if not visit:
            raise HTTPException(status_code=404, detail="Patient visit not found")
    
    db_report = create_medical_report(db, report, current_user.id)
    
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
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple medical reports"""
    require_permission(current_user, "patients", "create")
    reports = []
    for report_data in bulk_report.reports:
        report = MedicalReportCreate(**report_data.dict())
        db_report = create_medical_report(db, report, current_user.id)
        reports.append(db_report)
    
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

@router.post("/reports/{report_id}/finalize")
def finalize_medical_report_endpoint(
    report_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize a medical report"""
    require_permission(current_user, "patients", "update")
    try:
        db_report = finalize_medical_report(db, report_id, current_user.id)
        if not db_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Medical report finalized successfully"}

# Statistics and Reports
@router.get("/stats/certificates", response_model=CertificateStats)
def get_certificate_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get certificate statistics"""
    require_permission(current_user, "patients", "read")
    stats = get_certificate_stats(db, start_date, end_date)
    return CertificateStats(**stats)

@router.get("/stats/reports", response_model=ReportStats)
def get_report_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical report statistics"""
    require_permission(current_user, "patients", "read")
    stats = get_report_stats(db, start_date, end_date)
    return ReportStats(**stats)

@router.get("/reports/expired-certificates")
def get_expired_certificates_endpoint(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expired certificates"""
    require_permission(current_user, "patients", "read")
    expired_certificates = get_expired_certificates(db)
    
    enhanced_certificates = []
    for certificate in expired_certificates:
        enhanced_data = MedicalCertificateResponse.from_orm(certificate)
        
        # Add related information
        if certificate.patient:
            enhanced_data.patient_name = f"{certificate.patient.first_name} {certificate.patient.last_name}"
            enhanced_data.patient_code = certificate.patient.patient_code
        
        if certificate.issuing_doctor:
            enhanced_data.doctor_name = f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}"
        
        enhanced_certificates.append(enhanced_data)
    
    return enhanced_certificates

@router.post("/maintenance/update-expired-certificates")
def update_expired_certificates_endpoint(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update status of expired certificates"""
    require_permission(current_user, "system", "update")
    updated_count = update_expired_certificates(db)
    return {"message": f"Updated {updated_count} expired certificates"}