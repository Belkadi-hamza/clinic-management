from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging
import json

from ..models.medical_certificates import MedicalCertificate, CertificateTemplate, MedicalReport
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..models.patient_visits import PatientVisit
from ..schemas.medical_certificates import (
    MedicalCertificateCreate, MedicalCertificateUpdate, CertificateTemplateCreate, 
    CertificateTemplateUpdate, MedicalReportCreate, MedicalReportUpdate,
    MedicalCertificateSearch, CertificateTemplateSearch, MedicalReportSearch,
    StatusChangeRequest
)

logger = logging.getLogger(__name__)

# Medical Certificate CRUD operations
def generate_certificate_code(db: Session):
    """Generate unique medical certificate code"""
    from datetime import datetime
    prefix = "MCERT"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(MedicalCertificate).filter(
        MedicalCertificate.certificate_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.certificate_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_medical_certificates(db: Session, skip: int = 0, limit: int = 100):
    """Get all medical certificates"""
    return db.query(MedicalCertificate).filter(MedicalCertificate.deleted_at == None)\
        .order_by(MedicalCertificate.issue_date.desc())\
        .offset(skip).limit(limit).all()

def get_medical_certificate_by_id(db: Session, certificate_id: int):
    """Get medical certificate by ID"""
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.id == certificate_id,
        MedicalCertificate.deleted_at == None
    ).first()

def get_medical_certificate_by_code(db: Session, certificate_code: str):
    """Get medical certificate by code"""
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.certificate_code == certificate_code,
        MedicalCertificate.deleted_at == None
    ).first()

def get_certificates_by_patient(db: Session, patient_id: int):
    """Get all certificates for a specific patient"""
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.patient_id == patient_id,
        MedicalCertificate.deleted_at == None
    ).order_by(MedicalCertificate.issue_date.desc()).all()

def get_certificates_by_doctor(db: Session, doctor_id: int):
    """Get all certificates issued by a specific doctor"""
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.issuing_doctor_id == doctor_id,
        MedicalCertificate.deleted_at == None
    ).order_by(MedicalCertificate.issue_date.desc()).all()

def get_certificates_by_visit(db: Session, visit_id: int):
    """Get all certificates for a specific visit"""
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.visit_id == visit_id,
        MedicalCertificate.deleted_at == None
    ).order_by(MedicalCertificate.issue_date.desc()).all()

def get_certificates_by_date_range(db: Session, start_date: date, end_date: date):
    """Get certificates within a date range"""
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.issue_date >= start_date,
        MedicalCertificate.issue_date <= end_date,
        MedicalCertificate.deleted_at == None
    ).order_by(MedicalCertificate.issue_date.asc()).all()

def search_medical_certificates(db: Session, search: MedicalCertificateSearch, skip: int = 0, limit: int = 100):
    """Search medical certificates with filters"""
    query = db.query(MedicalCertificate).filter(MedicalCertificate.deleted_at == None)
    
    if search.patient_name:
        query = query.join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.doctor_name:
        query = query.join(Doctor).filter(
            or_(
                Doctor.first_name.ilike(f"%{search.doctor_name}%"),
                Doctor.last_name.ilike(f"%{search.doctor_name}%")
            )
        )
    
    if search.certificate_type:
        query = query.filter(MedicalCertificate.certificate_type == search.certificate_type)
    
    if search.date_from:
        query = query.filter(MedicalCertificate.issue_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(MedicalCertificate.issue_date <= search.date_to)
    
    if search.status:
        query = query.filter(MedicalCertificate.status == search.status)
    
    if search.is_work_related is not None:
        query = query.filter(MedicalCertificate.is_work_related == search.is_work_related)
    
    return query.order_by(MedicalCertificate.issue_date.desc())\
        .offset(skip).limit(limit).all()

def create_medical_certificate(db: Session, certificate: MedicalCertificateCreate, user_id: int):
    """Create new medical certificate"""
    certificate_code = generate_certificate_code(db)
    
    # Calculate end date if duration_days is provided
    if certificate.duration_days and certificate.start_date and not certificate.end_date:
        certificate_dict = certificate.dict()
        certificate_dict['end_date'] = certificate.start_date + timedelta(days=certificate.duration_days)
    else:
        certificate_dict = certificate.dict()
    
    db_certificate = MedicalCertificate(**certificate_dict, certificate_code=certificate_code, created_by=user_id)
    db.add(db_certificate)
    db.commit()
    db.refresh(db_certificate)
    return db_certificate

def create_bulk_medical_certificates(db: Session, certificates: List[MedicalCertificateCreate], user_id: int):
    """Create multiple medical certificates"""
    created_certificates = []
    
    for certificate_data in certificates:
        certificate = MedicalCertificateCreate(**certificate_data.dict())
        try:
            db_certificate = create_medical_certificate(db, certificate, user_id)
            created_certificates.append(db_certificate)
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            continue
    
    return created_certificates

def update_medical_certificate(db: Session, certificate_id: int, certificate: MedicalCertificateUpdate, user_id: int):
    """Update medical certificate"""
    db_certificate = db.query(MedicalCertificate).filter(
        MedicalCertificate.id == certificate_id,
        MedicalCertificate.deleted_at == None
    ).first()
    
    if not db_certificate:
        return None
    
    # Recalculate end date if duration_days or start_date changes
    certificate_dict = certificate.dict(exclude_unset=True)
    
    if ('duration_days' in certificate_dict or 'start_date' in certificate_dict) and not certificate_dict.get('end_date'):
        duration = certificate_dict.get('duration_days', db_certificate.duration_days)
        start_date = certificate_dict.get('start_date', db_certificate.start_date)
        
        if duration and start_date:
            certificate_dict['end_date'] = start_date + timedelta(days=duration)
    
    for key, value in certificate_dict.items():
        setattr(db_certificate, key, value)
    
    db_certificate.updated_by = user_id
    db.commit()
    db.refresh(db_certificate)
    return db_certificate

def delete_medical_certificate(db: Session, certificate_id: int, user_id: int):
    """Soft delete medical certificate"""
    db_certificate = db.query(MedicalCertificate).filter(
        MedicalCertificate.id == certificate_id,
        MedicalCertificate.deleted_at == None
    ).first()
    
    if not db_certificate:
        return None
    
    db_certificate.deleted_at = func.now()
    db_certificate.deleted_by = user_id
    db.commit()
    return db_certificate

def issue_certificate(db: Session, certificate_id: int, user_id: int):
    """Issue a certificate (change status from draft to issued)"""
    db_certificate = db.query(MedicalCertificate).filter(
        MedicalCertificate.id == certificate_id,
        MedicalCertificate.deleted_at == None
    ).first()
    
    if not db_certificate:
        return None
    
    if db_certificate.status != 'draft':
        raise ValueError("Only draft certificates can be issued")
    
    db_certificate.status = 'issued'
    db_certificate.updated_by = user_id
    db.commit()
    db.refresh(db_certificate)
    return db_certificate

def cancel_certificate(db: Session, certificate_id: int, status_change: StatusChangeRequest, user_id: int):
    """Cancel a certificate"""
    db_certificate = db.query(MedicalCertificate).filter(
        MedicalCertificate.id == certificate_id,
        MedicalCertificate.deleted_at == None
    ).first()
    
    if not db_certificate:
        return None
    
    if db_certificate.status == 'cancelled':
        raise ValueError("Certificate is already cancelled")
    
    db_certificate.status = status_change.status
    db_certificate.cancellation_reason = status_change.cancellation_reason
    db_certificate.updated_by = user_id
    
    db.commit()
    db.refresh(db_certificate)
    return db_certificate

def verify_certificate(db: Session, certificate_code: str):
    """Verify a certificate's validity"""
    certificate = get_medical_certificate_by_code(db, certificate_code)
    
    if not certificate:
        return {
            "certificate_code": certificate_code,
            "is_valid": False,
            "status": "not_found",
            "patient_name": None,
            "doctor_name": None,
            "issue_date": None,
            "certificate_type": None
        }
    
    # Calculate patient age
    patient_age = None
    if certificate.patient and certificate.patient.date_of_birth:
        today = date.today()
        age = today.year - certificate.patient.date_of_birth.year
        if today.month < certificate.patient.date_of_birth.month or (
            today.month == certificate.patient.date_of_birth.month and 
            today.day < certificate.patient.date_of_birth.day
        ):
            age -= 1
        patient_age = age
    
    return {
        "certificate_code": certificate.certificate_code,
        "is_valid": certificate.status == 'issued',
        "status": certificate.status,
        "patient_name": f"{certificate.patient.first_name} {certificate.patient.last_name}" if certificate.patient else None,
        "patient_age": patient_age,
        "patient_gender": certificate.patient.gender if certificate.patient else None,
        "doctor_name": f"{certificate.issuing_doctor.first_name} {certificate.issuing_doctor.last_name}" if certificate.issuing_doctor else None,
        "issue_date": certificate.issue_date,
        "certificate_type": certificate.certificate_type,
        "duration_days": certificate.duration_days,
        "start_date": certificate.start_date,
        "end_date": certificate.end_date,
        "diagnosis": certificate.diagnosis
    }

# Certificate Template CRUD operations
def generate_template_code(db: Session):
    """Generate unique certificate template code"""
    prefix = "TEMP"
    
    # Find the highest number
    max_template = db.query(CertificateTemplate).order_by(CertificateTemplate.id.desc()).first()
    next_num = (max_template.id + 1) if max_template else 1
    
    return f"{prefix}{next_num:04d}"

def get_certificate_templates(db: Session, skip: int = 0, limit: int = 100):
    """Get all certificate templates"""
    return db.query(CertificateTemplate).filter(CertificateTemplate.deleted_at == None)\
        .order_by(CertificateTemplate.template_name.asc())\
        .offset(skip).limit(limit).all()

def get_certificate_template_by_id(db: Session, template_id: int):
    """Get certificate template by ID"""
    return db.query(CertificateTemplate).filter(
        CertificateTemplate.id == template_id,
        CertificateTemplate.deleted_at == None
    ).first()

def get_template_by_type(db: Session, certificate_type: str, is_default: bool = True):
    """Get template by certificate type"""
    query = db.query(CertificateTemplate).filter(
        CertificateTemplate.certificate_type == certificate_type,
        CertificateTemplate.deleted_at == None,
        CertificateTemplate.is_active == True
    )
    
    if is_default:
        query = query.filter(CertificateTemplate.is_default == True)
    
    return query.first()

def search_certificate_templates(db: Session, search: CertificateTemplateSearch, skip: int = 0, limit: int = 100):
    """Search certificate templates with filters"""
    query = db.query(CertificateTemplate).filter(CertificateTemplate.deleted_at == None)
    
    if search.template_name:
        query = query.filter(CertificateTemplate.template_name.ilike(f"%{search.template_name}%"))
    
    if search.certificate_type:
        query = query.filter(CertificateTemplate.certificate_type == search.certificate_type)
    
    if search.is_active is not None:
        query = query.filter(CertificateTemplate.is_active == search.is_active)
    
    if search.is_default is not None:
        query = query.filter(CertificateTemplate.is_default == search.is_default)
    
    return query.order_by(CertificateTemplate.template_name.asc())\
        .offset(skip).limit(limit).all()

def create_certificate_template(db: Session, template: CertificateTemplateCreate, user_id: int):
    """Create new certificate template"""
    template_code = generate_template_code(db)
    
    # If this is set as default, unset other defaults for the same certificate type
    if template.is_default:
        db.query(CertificateTemplate).filter(
            CertificateTemplate.certificate_type == template.certificate_type,
            CertificateTemplate.is_default == True,
            CertificateTemplate.deleted_at == None
        ).update({'is_default': False})
    
    db_template = CertificateTemplate(**template.dict(), template_code=template_code, created_by=user_id)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def update_certificate_template(db: Session, template_id: int, template: CertificateTemplateUpdate, user_id: int):
    """Update certificate template"""
    db_template = db.query(CertificateTemplate).filter(
        CertificateTemplate.id == template_id,
        CertificateTemplate.deleted_at == None
    ).first()
    
    if not db_template:
        return None
    
    # If this is set as default, unset other defaults for the same certificate type
    if template.is_default and (template.is_default != db_template.is_default):
        db.query(CertificateTemplate).filter(
            CertificateTemplate.certificate_type == db_template.certificate_type,
            CertificateTemplate.is_default == True,
            CertificateTemplate.deleted_at == None,
            CertificateTemplate.id != template_id
        ).update({'is_default': False})
    
    for key, value in template.dict(exclude_unset=True).items():
        setattr(db_template, key, value)
    
    db_template.updated_by = user_id
    db.commit()
    db.refresh(db_template)
    return db_template

def delete_certificate_template(db: Session, template_id: int, user_id: int):
    """Soft delete certificate template"""
    db_template = db.query(CertificateTemplate).filter(
        CertificateTemplate.id == template_id,
        CertificateTemplate.deleted_at == None
    ).first()
    
    if not db_template:
        return None
    
    # Check if template is being used by certificates
    certificates_using_template = db.query(MedicalCertificate).filter(
        MedicalCertificate.template_used == db_template.template_name,
        MedicalCertificate.deleted_at == None
    ).first()
    
    if certificates_using_template:
        raise ValueError("Cannot delete template that is being used by certificates")
    
    db_template.deleted_at = func.now()
    db_template.deleted_by = user_id
    db.commit()
    return db_template

def generate_certificate_from_template(db: Session, template_id: int, patient_id: int, doctor_id: int, variables: dict, user_id: int):
    """Generate a certificate using a template"""
    template = get_certificate_template_by_id(db, template_id)
    if not template:
        raise ValueError("Template not found")
    
    # Get patient and doctor details
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    
    if not patient or not doctor:
        raise ValueError("Patient or doctor not found")
    
    # Create certificate using template
    certificate_data = MedicalCertificateCreate(
        patient_id=patient_id,
        issuing_doctor_id=doctor_id,
        issue_date=date.today(),
        certificate_type=template.certificate_type,
        title=f"{template.certificate_type.replace('_', ' ').title()} Certificate",
        template_used=template.template_name,
        notes="Generated from template"
    )
    
    # Apply variables to certificate fields
    if 'duration_days' in variables:
        certificate_data.duration_days = variables['duration_days']
    if 'diagnosis' in variables:
        certificate_data.diagnosis = variables['diagnosis']
    if 'recommendations' in variables:
        certificate_data.recommendations = variables['recommendations']
    
    certificate = create_medical_certificate(db, certificate_data, user_id)
    return certificate

# Medical Report CRUD operations
def generate_report_code(db: Session):
    """Generate unique medical report code"""
    from datetime import datetime
    prefix = "REP"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(MedicalReport).filter(
        MedicalReport.report_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.report_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_medical_reports(db: Session, skip: int = 0, limit: int = 100):
    """Get all medical reports"""
    return db.query(MedicalReport).filter(MedicalReport.deleted_at == None)\
        .order_by(MedicalReport.report_date.desc())\
        .offset(skip).limit(limit).all()

def get_medical_report_by_id(db: Session, report_id: int):
    """Get medical report by ID"""
    return db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()

def get_medical_report_by_code(db: Session, report_code: str):
    """Get medical report by code"""
    return db.query(MedicalReport).filter(
        MedicalReport.report_code == report_code,
        MedicalReport.deleted_at == None
    ).first()

def get_reports_by_patient(db: Session, patient_id: int):
    """Get all reports for a specific patient"""
    return db.query(MedicalReport).filter(
        MedicalReport.patient_id == patient_id,
        MedicalReport.deleted_at == None
    ).order_by(MedicalReport.report_date.desc()).all()

def get_reports_by_doctor(db: Session, doctor_id: int):
    """Get all reports created by a specific doctor"""
    return db.query(MedicalReport).filter(
        MedicalReport.doctor_id == doctor_id,
        MedicalReport.deleted_at == None
    ).order_by(MedicalReport.report_date.desc()).all()

def search_medical_reports(db: Session, search: MedicalReportSearch, skip: int = 0, limit: int = 100):
    """Search medical reports with filters"""
    query = db.query(MedicalReport).filter(MedicalReport.deleted_at == None)
    
    if search.patient_name:
        query = query.join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.doctor_name:
        query = query.join(Doctor).filter(
            or_(
                Doctor.first_name.ilike(f"%{search.doctor_name}%"),
                Doctor.last_name.ilike(f"%{search.doctor_name}%")
            )
        )
    
    if search.report_type:
        query = query.filter(MedicalReport.report_type == search.report_type)
    
    if search.date_from:
        query = query.filter(MedicalReport.report_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(MedicalReport.report_date <= search.date_to)
    
    if search.status:
        query = query.filter(MedicalReport.status == search.status)
    
    return query.order_by(MedicalReport.report_date.desc())\
        .offset(skip).limit(limit).all()

def create_medical_report(db: Session, report: MedicalReportCreate, user_id: int):
    """Create new medical report"""
    report_code = generate_report_code(db)
    db_report = MedicalReport(**report.dict(), report_code=report_code, created_by=user_id)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def update_medical_report(db: Session, report_id: int, report: MedicalReportUpdate, user_id: int):
    """Update medical report"""
    db_report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()
    
    if not db_report:
        return None
    
    for key, value in report.dict(exclude_unset=True).items():
        setattr(db_report, key, value)
    
    db_report.updated_by = user_id
    db.commit()
    db.refresh(db_report)
    return db_report

def delete_medical_report(db: Session, report_id: int, user_id: int):
    """Soft delete medical report"""
    db_report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()
    
    if not db_report:
        return None
    
    db_report.deleted_at = func.now()
    db_report.deleted_by = user_id
    db.commit()
    return db_report

def finalize_medical_report(db: Session, report_id: int, user_id: int):
    """Finalize a medical report"""
    db_report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()
    
    if not db_report:
        return None
    
    if db_report.status != 'draft':
        raise ValueError("Only draft reports can be finalized")
    
    db_report.status = 'finalized'
    db_report.updated_by = user_id
    db.commit()
    db.refresh(db_report)
    return db_report

# Statistics and Reports
def get_certificate_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get certificate statistics"""
    query = db.query(MedicalCertificate).filter(MedicalCertificate.deleted_at == None)
    
    if start_date:
        query = query.filter(MedicalCertificate.issue_date >= start_date)
    if end_date:
        query = query.filter(MedicalCertificate.issue_date <= end_date)
    
    total_certificates = query.count()
    
    # Certificates by type
    by_type = db.query(
        MedicalCertificate.certificate_type,
        func.count(MedicalCertificate.id).label('count')
    ).filter(
        MedicalCertificate.deleted_at == None
    ).group_by(MedicalCertificate.certificate_type).all()
    
    # Certificates by status
    by_status = db.query(
        MedicalCertificate.status,
        func.count(MedicalCertificate.id).label('count')
    ).filter(
        MedicalCertificate.deleted_at == None
    ).group_by(MedicalCertificate.status).all()
    
    # Certificates by month
    by_month = db.query(
        extract('year', MedicalCertificate.issue_date).label('year'),
        extract('month', MedicalCertificate.issue_date).label('month'),
        func.count(MedicalCertificate.id).label('count')
    ).filter(
        MedicalCertificate.deleted_at == None
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Work-related certificates count
    work_related_count = query.filter(MedicalCertificate.is_work_related == True).count()
    
    return {
        "total_certificates": total_certificates,
        "by_type": [{"type": cert_type, "count": count} for cert_type, count in by_type],
        "by_status": [{"status": status, "count": count} for status, count in by_status],
        "by_month": [{"year": int(year), "month": int(month), "count": count} for year, month, count in by_month],
        "work_related_count": work_related_count
    }

def get_report_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get medical report statistics"""
    query = db.query(MedicalReport).filter(MedicalReport.deleted_at == None)
    
    if start_date:
        query = query.filter(MedicalReport.report_date >= start_date)
    if end_date:
        query = query.filter(MedicalReport.report_date <= end_date)
    
    total_reports = query.count()
    
    # Reports by type
    by_type = db.query(
        MedicalReport.report_type,
        func.count(MedicalReport.id).label('count')
    ).filter(
        MedicalReport.deleted_at == None
    ).group_by(MedicalReport.report_type).all()
    
    # Reports by status
    by_status = db.query(
        MedicalReport.status,
        func.count(MedicalReport.id).label('count')
    ).filter(
        MedicalReport.deleted_at == None
    ).group_by(MedicalReport.status).all()
    
    # Reports by month
    by_month = db.query(
        extract('year', MedicalReport.report_date).label('year'),
        extract('month', MedicalReport.report_date).label('month'),
        func.count(MedicalReport.id).label('count')
    ).filter(
        MedicalReport.deleted_at == None
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    return {
        "total_reports": total_reports,
        "by_type": [{"type": report_type, "count": count} for report_type, count in by_type],
        "by_status": [{"status": status, "count": count} for status, count in by_status],
        "by_month": [{"year": int(year), "month": int(month), "count": count} for year, month, count in by_month]
    }

def get_expired_certificates(db: Session):
    """Get certificates that have expired (end_date passed)"""
    today = date.today()
    return db.query(MedicalCertificate).filter(
        MedicalCertificate.end_date < today,
        MedicalCertificate.status == 'issued',
        MedicalCertificate.deleted_at == None
    ).order_by(MedicalCertificate.end_date.asc()).all()

def update_expired_certificates(db: Session):
    """Update status of expired certificates"""
    today = date.today()
    expired_certificates = db.query(MedicalCertificate).filter(
        MedicalCertificate.end_date < today,
        MedicalCertificate.status == 'issued',
        MedicalCertificate.deleted_at == None
    ).all()
    
    for certificate in expired_certificates:
        certificate.status = 'expired'
    
    db.commit()
    return len(expired_certificates)