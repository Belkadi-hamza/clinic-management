from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import logging
import json

from ..models.medical_reports import MedicalReport, ReportTemplate, ReportCategory, LabTestResult
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..models.patient_visits import PatientVisit
from ..schemas.medical_reports import (
    MedicalReportCreate, MedicalReportUpdate, ReportTemplateCreate, ReportTemplateUpdate,
    ReportCategoryCreate, ReportCategoryUpdate, LabTestResultCreate, LabTestResultUpdate,
    MedicalReportSearch, ReportTemplateSearch, ReportCategorySearch, LabTestResultSearch,
    ReportStatusChange, ReportReview, LabResultImport
)

logger = logging.getLogger(__name__)

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

def get_reports_by_type(db: Session, report_type: str):
    """Get all reports of a specific type"""
    return db.query(MedicalReport).filter(
        MedicalReport.report_type == report_type,
        MedicalReport.deleted_at == None
    ).order_by(MedicalReport.report_date.desc()).all()

def get_reports_by_date_range(db: Session, start_date: date, end_date: date):
    """Get reports within a date range"""
    return db.query(MedicalReport).filter(
        MedicalReport.report_date >= start_date,
        MedicalReport.report_date <= end_date,
        MedicalReport.deleted_at == None
    ).order_by(MedicalReport.report_date.asc()).all()

def get_pending_review_reports(db: Session):
    """Get reports pending review"""
    return db.query(MedicalReport).filter(
        MedicalReport.status == 'finalized',
        MedicalReport.reviewed_by_id == None,
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
        query = query.join(Doctor, MedicalReport.doctor_id == Doctor.id).filter(
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
    
    if search.is_confidential is not None:
        query = query.filter(MedicalReport.is_confidential == search.is_confidential)
    
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

def create_bulk_medical_reports(db: Session, reports: List[MedicalReportCreate], user_id: int):
    """Create multiple medical reports"""
    created_reports = []
    
    for report_data in reports:
        report = MedicalReportCreate(**report_data.dict())
        try:
            db_report = create_medical_report(db, report, user_id)
            created_reports.append(db_report)
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            continue
    
    return created_reports

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
    
    # Check if report has lab results
    lab_results = db.query(LabTestResult).filter(
        LabTestResult.report_id == report_id,
        LabTestResult.deleted_at == None
    ).first()
    
    if lab_results:
        raise ValueError("Cannot delete report that has lab results")
    
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

def review_medical_report(db: Session, report_id: int, review: ReportReview, user_id: int):
    """Review a medical report"""
    db_report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()
    
    if not db_report:
        return None
    
    if db_report.status != 'finalized':
        raise ValueError("Only finalized reports can be reviewed")
    
    db_report.status = 'reviewed'
    db_report.reviewed_by_id = review.reviewed_by_id
    db_report.review_date = date.today()
    db_report.review_notes = review.review_notes
    db_report.updated_by = user_id
    
    db.commit()
    db.refresh(db_report)
    return db_report

def deliver_medical_report(db: Session, report_id: int, user_id: int):
    """Mark report as delivered to patient"""
    db_report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()
    
    if not db_report:
        return None
    
    if db_report.status not in ['finalized', 'reviewed']:
        raise ValueError("Only finalized or reviewed reports can be delivered")
    
    db_report.status = 'delivered'
    db_report.updated_by = user_id
    db.commit()
    db.refresh(db_report)
    return db_report

def archive_medical_report(db: Session, report_id: int, user_id: int):
    """Archive a medical report"""
    db_report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.deleted_at == None
    ).first()
    
    if not db_report:
        return None
    
    db_report.status = 'archived'
    db_report.updated_by = user_id
    db.commit()
    db.refresh(db_report)
    return db_report

# Report Template CRUD operations
def generate_template_code(db: Session):
    """Generate unique report template code"""
    prefix = "RTMP"
    
    # Find the highest number
    max_template = db.query(ReportTemplate).order_by(ReportTemplate.id.desc()).first()
    next_num = (max_template.id + 1) if max_template else 1
    
    return f"{prefix}{next_num:04d}"

def get_report_templates(db: Session, skip: int = 0, limit: int = 100):
    """Get all report templates"""
    return db.query(ReportTemplate).filter(ReportTemplate.deleted_at == None)\
        .order_by(ReportTemplate.template_name.asc())\
        .offset(skip).limit(limit).all()

def get_report_template_by_id(db: Session, template_id: int):
    """Get report template by ID"""
    return db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.deleted_at == None
    ).first()

def get_template_by_type(db: Session, report_type: str, is_default: bool = True):
    """Get template by report type"""
    query = db.query(ReportTemplate).filter(
        ReportTemplate.report_type == report_type,
        ReportTemplate.deleted_at == None,
        ReportTemplate.is_active == True
    )
    
    if is_default:
        query = query.filter(ReportTemplate.is_default == True)
    
    return query.first()

def search_report_templates(db: Session, search: ReportTemplateSearch, skip: int = 0, limit: int = 100):
    """Search report templates with filters"""
    query = db.query(ReportTemplate).filter(ReportTemplate.deleted_at == None)
    
    if search.template_name:
        query = query.filter(ReportTemplate.template_name.ilike(f"%{search.template_name}%"))
    
    if search.report_type:
        query = query.filter(ReportTemplate.report_type == search.report_type)
    
    if search.is_active is not None:
        query = query.filter(ReportTemplate.is_active == search.is_active)
    
    if search.is_default is not None:
        query = query.filter(ReportTemplate.is_default == search.is_default)
    
    return query.order_by(ReportTemplate.template_name.asc())\
        .offset(skip).limit(limit).all()

def create_report_template(db: Session, template: ReportTemplateCreate, user_id: int):
    """Create new report template"""
    template_code = generate_template_code(db)
    
    # If this is set as default, unset other defaults for the same report type
    if template.is_default:
        db.query(ReportTemplate).filter(
            ReportTemplate.report_type == template.report_type,
            ReportTemplate.is_default == True,
            ReportTemplate.deleted_at == None
        ).update({'is_default': False})
    
    db_template = ReportTemplate(**template.dict(), template_code=template_code, created_by=user_id)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def update_report_template(db: Session, template_id: int, template: ReportTemplateUpdate, user_id: int):
    """Update report template"""
    db_template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.deleted_at == None
    ).first()
    
    if not db_template:
        return None
    
    # If this is set as default, unset other defaults for the same report type
    if template.is_default and (template.is_default != db_template.is_default):
        db.query(ReportTemplate).filter(
            ReportTemplate.report_type == db_template.report_type,
            ReportTemplate.is_default == True,
            ReportTemplate.deleted_at == None,
            ReportTemplate.id != template_id
        ).update({'is_default': False})
    
    for key, value in template.dict(exclude_unset=True).items():
        setattr(db_template, key, value)
    
    db_template.updated_by = user_id
    db.commit()
    db.refresh(db_template)
    return db_template

def delete_report_template(db: Session, template_id: int, user_id: int):
    """Soft delete report template"""
    db_template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.deleted_at == None
    ).first()
    
    if not db_template:
        return None
    
    # Check if template is being used by reports
    reports_using_template = db.query(MedicalReport).filter(
        MedicalReport.template_used == db_template.template_name,
        MedicalReport.deleted_at == None
    ).first()
    
    if reports_using_template:
        raise ValueError("Cannot delete template that is being used by reports")
    
    db_template.deleted_at = func.now()
    db_template.deleted_by = user_id
    db.commit()
    return db_template

def generate_report_from_template(db: Session, template_id: int, patient_id: int, doctor_id: int, variables: Dict[str, Any], user_id: int):
    """Generate a report using a template"""
    template = get_report_template_by_id(db, template_id)
    if not template:
        raise ValueError("Template not found")
    
    # Get patient and doctor details
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    
    if not patient or not doctor:
        raise ValueError("Patient or doctor not found")
    
    # Create report using template
    report_data = MedicalReportCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        report_date=date.today(),
        report_type=template.report_type,
        title=f"{template.report_type.replace('_', ' ').title()} Report",
        content=template.content,  # This would be processed with variables
        template_used=template.template_name,
        additional_notes="Generated from template"
    )
    
    # Apply variables to report fields
    if 'findings' in variables:
        report_data.findings = variables['findings']
    if 'diagnosis' in variables:
        report_data.diagnosis = variables['diagnosis']
    if 'recommendations' in variables:
        report_data.recommendations = variables['recommendations']
    
    report = create_medical_report(db, report_data, user_id)
    return report

# Report Category CRUD operations
def generate_category_code(db: Session):
    """Generate unique report category code"""
    prefix = "RCAT"
    
    # Find the highest number
    max_category = db.query(ReportCategory).order_by(ReportCategory.id.desc()).first()
    next_num = (max_category.id + 1) if max_category else 1
    
    return f"{prefix}{next_num:04d}"

def get_report_categories(db: Session, skip: int = 0, limit: int = 100):
    """Get all report categories"""
    return db.query(ReportCategory).filter(ReportCategory.deleted_at == None)\
        .order_by(ReportCategory.sort_order.asc(), ReportCategory.category_name.asc())\
        .offset(skip).limit(limit).all()

def get_report_category_by_id(db: Session, category_id: int):
    """Get report category by ID"""
    return db.query(ReportCategory).filter(
        ReportCategory.id == category_id,
        ReportCategory.deleted_at == None
    ).first()

def get_root_categories(db: Session, report_type: str = None):
    """Get all root categories (no parent)"""
    query = db.query(ReportCategory).filter(
        ReportCategory.parent_category_id == None,
        ReportCategory.deleted_at == None
    )
    
    if report_type:
        query = query.filter(ReportCategory.report_type == report_type)
    
    return query.order_by(ReportCategory.sort_order.asc(), ReportCategory.category_name.asc()).all()

def get_sub_categories(db: Session, parent_category_id: int):
    """Get all sub-categories for a parent category"""
    return db.query(ReportCategory).filter(
        ReportCategory.parent_category_id == parent_category_id,
        ReportCategory.deleted_at == None
    ).order_by(ReportCategory.sort_order.asc(), ReportCategory.category_name.asc()).all()

def get_category_tree(db: Session, report_type: str = None):
    """Get complete category hierarchy"""
    root_categories = get_root_categories(db, report_type)
    tree = []
    
    for category in root_categories:
        tree.append(_build_category_tree(db, category))
    
    return tree

def _build_category_tree(db: Session, category: ReportCategory):
    """Recursively build category tree"""
    sub_categories = get_sub_categories(db, category.id)
    
    # Count reports in this category (this would need a category-reports relationship)
    report_count = 0  # Implement based on your relationship
    
    tree_node = {
        'category': category,
        'report_count': report_count,
        'sub_categories': []
    }
    
    for sub_category in sub_categories:
        tree_node['sub_categories'].append(_build_category_tree(db, sub_category))
    
    return tree_node

def search_report_categories(db: Session, search: ReportCategorySearch, skip: int = 0, limit: int = 100):
    """Search report categories with filters"""
    query = db.query(ReportCategory).filter(ReportCategory.deleted_at == None)
    
    if search.category_name:
        query = query.filter(ReportCategory.category_name.ilike(f"%{search.category_name}%"))
    
    if search.report_type:
        query = query.filter(ReportCategory.report_type == search.report_type)
    
    if search.parent_category_id is not None:
        if search.parent_category_id == 0:  # Special case for root categories
            query = query.filter(ReportCategory.parent_category_id == None)
        else:
            query = query.filter(ReportCategory.parent_category_id == search.parent_category_id)
    
    if search.is_active is not None:
        query = query.filter(ReportCategory.is_active == search.is_active)
    
    return query.order_by(ReportCategory.sort_order.asc(), ReportCategory.category_name.asc())\
        .offset(skip).limit(limit).all()

def create_report_category(db: Session, category: ReportCategoryCreate, user_id: int):
    """Create new report category"""
    category_code = generate_category_code(db)
    db_category = ReportCategory(**category.dict(), category_code=category_code, created_by=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_report_category(db: Session, category_id: int, category: ReportCategoryUpdate, user_id: int):
    """Update report category"""
    db_category = db.query(ReportCategory).filter(
        ReportCategory.id == category_id,
        ReportCategory.deleted_at == None
    ).first()
    
    if not db_category:
        return None
    
    # Prevent circular reference
    if category.parent_category_id == category_id:
        raise ValueError("Category cannot be its own parent")
    
    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)
    
    db_category.updated_by = user_id
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_report_category(db: Session, category_id: int, user_id: int):
    """Soft delete report category"""
    db_category = db.query(ReportCategory).filter(
        ReportCategory.id == category_id,
        ReportCategory.deleted_at == None
    ).first()
    
    if not db_category:
        return None
    
    # Check if category has sub-categories
    sub_categories = get_sub_categories(db, category_id)
    if sub_categories:
        raise ValueError("Cannot delete category with sub-categories")
    
    # Check if category has reports (implement based on your relationship)
    # reports = db.query(MedicalReport).filter(MedicalReport.category_id == category_id).first()
    # if reports:
    #     raise ValueError("Cannot delete category with associated reports")
    
    db_category.deleted_at = func.now()
    db_category.deleted_by = user_id
    db.commit()
    return db_category

# Lab Test Result CRUD operations
def generate_result_code(db: Session):
    """Generate unique lab test result code"""
    from datetime import datetime
    prefix = "RES"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(LabTestResult).filter(
        LabTestResult.result_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.result_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_lab_test_results(db: Session, skip: int = 0, limit: int = 100):
    """Get all lab test results"""
    return db.query(LabTestResult).filter(LabTestResult.deleted_at == None)\
        .order_by(LabTestResult.created_at.desc())\
        .offset(skip).limit(limit).all()

def get_lab_test_result_by_id(db: Session, result_id: int):
    """Get lab test result by ID"""
    return db.query(LabTestResult).filter(
        LabTestResult.id == result_id,
        LabTestResult.deleted_at == None
    ).first()

def get_results_by_report(db: Session, report_id: int):
    """Get all lab results for a specific report"""
    return db.query(LabTestResult).filter(
        LabTestResult.report_id == report_id,
        LabTestResult.deleted_at == None
    ).order_by(LabTestResult.test_name.asc()).all()

def get_abnormal_results(db: Session):
    """Get all abnormal lab results"""
    return db.query(LabTestResult).filter(
        LabTestResult.flag != 'normal',
        LabTestResult.deleted_at == None
    ).order_by(LabTestResult.created_at.desc()).all()

def search_lab_test_results(db: Session, search: LabTestResultSearch, skip: int = 0, limit: int = 100):
    """Search lab test results with filters"""
    query = db.query(LabTestResult).filter(LabTestResult.deleted_at == None)
    
    if search.test_name:
        query = query.filter(LabTestResult.test_name.ilike(f"%{search.test_name}%"))
    
    if search.patient_name:
        query = query.join(MedicalReport).join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.date_from:
        query = query.filter(LabTestResult.created_at >= search.date_from)
    
    if search.date_to:
        query = query.filter(LabTestResult.created_at <= search.date_to)
    
    if search.flag:
        query = query.filter(LabTestResult.flag == search.flag)
    
    return query.order_by(LabTestResult.created_at.desc())\
        .offset(skip).limit(limit).all()

def create_lab_test_result(db: Session, result: LabTestResultCreate, user_id: int):
    """Create new lab test result"""
    result_code = generate_result_code(db)
    db_result = LabTestResult(**result.dict(), result_code=result_code, created_by=user_id)
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def create_bulk_lab_results(db: Session, results: List[LabTestResultCreate], user_id: int):
    """Create multiple lab test results"""
    created_results = []
    
    for result_data in results:
        result = LabTestResultCreate(**result_data.dict())
        try:
            db_result = create_lab_test_result(db, result, user_id)
            created_results.append(db_result)
        except Exception as e:
            logger.error(f"Failed to create lab result: {e}")
            continue
    
    return created_results

def import_lab_results(db: Session, import_data: LabResultImport, user_id: int):
    """Import multiple lab results"""
    imported_results = []
    
    for result_data in import_data.results:
        result = LabTestResultCreate(
            report_id=import_data.report_id,
            test_name=result_data.get('test_name'),
            test_code=result_data.get('test_code'),
            result_value=result_data.get('result_value'),
            numeric_value=result_data.get('numeric_value'),
            unit=result_data.get('unit'),
            normal_range=result_data.get('normal_range'),
            flag=result_data.get('flag'),
            notes=result_data.get('notes'),
            performed_by=result_data.get('performed_by'),
            performed_date=result_data.get('performed_date'),
            verified_by=result_data.get('verified_by')
        )
        
        try:
            db_result = create_lab_test_result(db, result, user_id)
            imported_results.append(db_result)
        except Exception as e:
            logger.error(f"Failed to import lab result: {e}")
            continue
    
    return imported_results

def update_lab_test_result(db: Session, result_id: int, result: LabTestResultUpdate, user_id: int):
    """Update lab test result"""
    db_result = db.query(LabTestResult).filter(
        LabTestResult.id == result_id,
        LabTestResult.deleted_at == None
    ).first()
    
    if not db_result:
        return None
    
    for key, value in result.dict(exclude_unset=True).items():
        setattr(db_result, key, value)
    
    db_result.updated_by = user_id
    db.commit()
    db.refresh(db_result)
    return db_result

def delete_lab_test_result(db: Session, result_id: int, user_id: int):
    """Soft delete lab test result"""
    db_result = db.query(LabTestResult).filter(
        LabTestResult.id == result_id,
        LabTestResult.deleted_at == None
    ).first()
    
    if not db_result:
        return None
    
    db_result.deleted_at = func.now()
    db_result.deleted_by = user_id
    db.commit()
    return db_result

def verify_lab_result(db: Session, result_id: int, verified_by: str, user_id: int):
    """Verify a lab test result"""
    db_result = db.query(LabTestResult).filter(
        LabTestResult.id == result_id,
        LabTestResult.deleted_at == None
    ).first()
    
    if not db_result:
        return None
    
    db_result.verified_by = verified_by
    db_result.verified_date = date.today()
    db_result.updated_by = user_id
    
    db.commit()
    db.refresh(db_result)
    return db_result

# Statistics and Reports
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
    
    # Abnormal results count
    abnormal_results_count = db.query(LabTestResult).filter(
        LabTestResult.flag != 'normal',
        LabTestResult.deleted_at == None
    ).count()
    
    # Pending review count
    pending_review_count = db.query(MedicalReport).filter(
        MedicalReport.status == 'finalized',
        MedicalReport.reviewed_by_id == None,
        MedicalReport.deleted_at == None
    ).count()
    
    return {
        "total_reports": total_reports,
        "by_type": [{"type": report_type, "count": count} for report_type, count in by_type],
        "by_status": [{"status": status, "count": count} for status, count in by_status],
        "by_month": [{"year": int(year), "month": int(month), "count": count} for year, month, count in by_month],
        "abnormal_results_count": abnormal_results_count,
        "pending_review_count": pending_review_count
    }

def get_lab_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get lab test statistics"""
    query = db.query(LabTestResult).filter(LabTestResult.deleted_at == None)
    
    if start_date:
        query = query.filter(LabTestResult.created_at >= start_date)
    if end_date:
        query = query.filter(LabTestResult.created_at <= end_date)
    
    total_tests = query.count()
    abnormal_tests = query.filter(LabTestResult.flag != 'normal').count()
    critical_tests = query.filter(LabTestResult.flag == 'critical').count()
    
    # Tests by type
    by_test_type = db.query(
        LabTestResult.test_name,
        func.count(LabTestResult.id).label('count')
    ).filter(
        LabTestResult.deleted_at == None
    ).group_by(LabTestResult.test_name).all()
    
    # Tests by flag
    by_flag = db.query(
        LabTestResult.flag,
        func.count(LabTestResult.id).label('count')
    ).filter(
        LabTestResult.deleted_at == None
    ).group_by(LabTestResult.flag).all()
    
    return {
        "total_tests": total_tests,
        "abnormal_tests": abnormal_tests,
        "critical_tests": critical_tests,
        "by_test_type": [{"test_type": test_type, "count": count} for test_type, count in by_test_type],
        "by_flag": [{"flag": flag, "count": count} for flag, count in by_flag]
    }

def get_trend_analysis(db: Session, months: int = 12):
    """Get trend analysis for reports and lab results"""
    end_date = date.today()
    start_date = end_date - timedelta(days=months*30)
    
    # Report trends
    report_trends = db.query(
        extract('year', MedicalReport.report_date).label('year'),
        extract('month', MedicalReport.report_date).label('month'),
        func.count(MedicalReport.id).label('total_reports')
    ).filter(
        MedicalReport.deleted_at == None,
        MedicalReport.report_date >= start_date,
        MedicalReport.report_date <= end_date
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Abnormal result trends
    abnormal_trends = db.query(
        extract('year', LabTestResult.created_at).label('year'),
        extract('month', LabTestResult.created_at).label('month'),
        func.count(LabTestResult.id).label('abnormal_count')
    ).filter(
        LabTestResult.deleted_at == None,
        LabTestResult.flag != 'normal',
        LabTestResult.created_at >= start_date,
        LabTestResult.created_at <= end_date
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Calculate average tests per report
    total_reports = len(report_trends)
    total_tests = db.query(LabTestResult).filter(
        LabTestResult.deleted_at == None,
        LabTestResult.created_at >= start_date,
        LabTestResult.created_at <= end_date
    ).count()
    
    average_tests_per_report = total_tests / total_reports if total_reports > 0 else 0
    
    trends = []
    for report_trend in report_trends:
        period = f"{int(report_trend.year)}-{int(report_trend.month):02d}"
        abnormal_count = next(
            (trend.abnormal_count for trend in abnormal_trends 
             if int(trend.year) == int(report_trend.year) and int(trend.month) == int(report_trend.month)),
            0
        )
        
        trends.append({
            "period": period,
            "total_reports": report_trend.total_reports,
            "abnormal_count": abnormal_count,
            "average_tests_per_report": round(average_tests_per_report, 2)
        })
    
    return trends