from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, case
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from ..models.visit_symptoms import VisitSymptom
from ..models.symptoms import Symptom
from ..models.patient_visits import PatientVisit
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..schemas.visit_symptoms import VisitSymptomCreate, VisitSymptomUpdate, VisitSymptomBase

# Visit Symptom CRUD operations
def get_visit_symptoms(
    db: Session, 
    visit_id: int,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[VisitSymptom], int]:
    """Get all symptoms for a specific visit"""
    query = db.query(VisitSymptom).filter(
        VisitSymptom.visit_id == visit_id,
        VisitSymptom.deleted_at == None
    )
    
    total = query.count()
    visit_symptoms = query.order_by(VisitSymptom.created_at.desc()).offset(skip).limit(limit).all()
    return visit_symptoms, total

def get_visit_symptom_by_id(db: Session, visit_symptom_id: int) -> Optional[VisitSymptom]:
    """Get a specific visit symptom by ID"""
    return db.query(VisitSymptom).filter(
        VisitSymptom.id == visit_symptom_id,
        VisitSymptom.deleted_at == None
    ).first()

def get_visit_symptoms_by_symptom_id(db: Session, symptom_id: int) -> List[VisitSymptom]:
    """Get all visit symptoms for a specific symptom"""
    return db.query(VisitSymptom).filter(
        VisitSymptom.symptom_id == symptom_id,
        VisitSymptom.deleted_at == None
    ).all()

def create_visit_symptom(db: Session, visit_symptom: VisitSymptomCreate, user_id: int) -> Tuple[Optional[VisitSymptom], Optional[str]]:
    """Add a symptom to a visit"""
    # Check if symptom exists
    symptom = db.query(Symptom).filter(
        Symptom.id == visit_symptom.symptom_id,
        Symptom.deleted_at == None
    ).first()
    
    if not symptom:
        return None, "Symptom not found"
    
    # Check if visit exists
    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_symptom.visit_id,
        PatientVisit.deleted_at == None
    ).first()
    
    if not visit:
        return None, "Visit not found"
    
    # Check if symptom is already added to this visit
    existing = db.query(VisitSymptom).filter(
        VisitSymptom.visit_id == visit_symptom.visit_id,
        VisitSymptom.symptom_id == visit_symptom.symptom_id,
        VisitSymptom.deleted_at == None
    ).first()
    
    if existing:
        return None, "Symptom already added to this visit"
    
    db_visit_symptom = VisitSymptom(
        visit_id=visit_symptom.visit_id,
        symptom_id=visit_symptom.symptom_id,
        severity=visit_symptom.severity,
        duration_days=visit_symptom.duration_days,
        notes=visit_symptom.notes,
        created_by=user_id
    )
    db.add(db_visit_symptom)
    db.commit()
    db.refresh(db_visit_symptom)
    return db_visit_symptom, None

def update_visit_symptom(db: Session, visit_symptom_id: int, visit_symptom: VisitSymptomUpdate, user_id: int) -> Tuple[Optional[VisitSymptom], Optional[str]]:
    """Update a visit symptom"""
    db_visit_symptom = get_visit_symptom_by_id(db, visit_symptom_id)
    if not db_visit_symptom:
        return None, "Visit symptom not found"
    
    update_data = visit_symptom.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_visit_symptom, key, value)
    
    db.commit()
    db.refresh(db_visit_symptom)
    return db_visit_symptom, None

def delete_visit_symptom(db: Session, visit_symptom_id: int, user_id: int) -> Tuple[Optional[VisitSymptom], Optional[str]]:
    """Remove a symptom from a visit"""
    db_visit_symptom = get_visit_symptom_by_id(db, visit_symptom_id)
    if not db_visit_symptom:
        return None, "Visit symptom not found"
    
    db_visit_symptom.deleted_at = func.now()
    db_visit_symptom.deleted_by = user_id
    db.commit()
    return db_visit_symptom, None

def bulk_create_visit_symptoms(db: Session, bulk_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Bulk add multiple symptoms to a visit"""
    visit_id = bulk_data['visit_id']
    symptoms_data = bulk_data['symptoms']
    
    created = []
    errors = []
    
    # Check if visit exists
    visit = db.query(PatientVisit).filter(
        PatientVisit.id == visit_id,
        PatientVisit.deleted_at == None
    ).first()
    
    if not visit:
        return {
            "created": [],
            "errors": [{"error": "Visit not found"}],
            "total_created": 0,
            "total_errors": 1
        }
    
    for symptom_data in symptoms_data:
        # Check if symptom exists
        symptom = db.query(Symptom).filter(
            Symptom.id == symptom_data.symptom_id,
            Symptom.deleted_at == None
        ).first()
        
        if not symptom:
            errors.append({
                "symptom_id": symptom_data.symptom_id,
                "error": "Symptom not found"
            })
            continue
        
        # Check if symptom is already added to this visit
        existing = db.query(VisitSymptom).filter(
            VisitSymptom.visit_id == visit_id,
            VisitSymptom.symptom_id == symptom_data.symptom_id,
            VisitSymptom.deleted_at == None
        ).first()
        
        if existing:
            errors.append({
                "symptom_id": symptom_data.symptom_id,
                "symptom_name": symptom.symptom_name,
                "error": "Symptom already added to this visit"
            })
            continue
        
        try:
            db_visit_symptom = VisitSymptom(
                visit_id=visit_id,
                symptom_id=symptom_data.symptom_id,
                severity=symptom_data.severity,
                duration_days=symptom_data.duration_days,
                notes=symptom_data.notes,
                created_by=user_id
            )
            db.add(db_visit_symptom)
            created.append(db_visit_symptom)
        except Exception as e:
            errors.append({
                "symptom_id": symptom_data.symptom_id,
                "symptom_name": symptom.symptom_name,
                "error": str(e)
            })
    
    if created:
        db.commit()
        # Refresh all created visit symptoms to get their IDs
        for vs in created:
            db.refresh(vs)
    
    return {
        "created": created,
        "errors": errors,
        "total_created": len(created),
        "total_errors": len(errors)
    }

def get_symptom_analysis(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    """Get symptom analysis for the specified period"""
    start_date = datetime.now() - timedelta(days=days)
    
    analysis = db.query(
        Symptom.id,
        Symptom.symptom_code,
        Symptom.symptom_name,
        func.count(VisitSymptom.id).label('occurrence_count'),
        func.avg(VisitSymptom.duration_days).label('average_duration'),
        func.max(VisitSymptom.severity).label('most_severe')
    ).join(
        VisitSymptom, Symptom.id == VisitSymptom.symptom_id
    ).join(
        PatientVisit, VisitSymptom.visit_id == PatientVisit.id
    ).filter(
        VisitSymptom.deleted_at == None,
        Symptom.deleted_at == None,
        PatientVisit.deleted_at == None,
        PatientVisit.visit_date >= start_date
    ).group_by(
        Symptom.id, Symptom.symptom_code, Symptom.symptom_name
    ).order_by(
        desc('occurrence_count')
    ).all()
    
    result = []
    for item in analysis:
        # Get severity distribution for this symptom
        severity_distribution = db.query(
            VisitSymptom.severity,
            func.count(VisitSymptom.id).label('count')
        ).filter(
            VisitSymptom.symptom_id == item.id,
            VisitSymptom.deleted_at == None,
            VisitSymptom.severity.isnot(None)
        ).group_by(VisitSymptom.severity).all()
        
        severity_dict = {sev: count for sev, count in severity_distribution}
        
        result.append({
            "symptom_id": item.id,
            "symptom_code": item.symptom_code,
            "symptom_name": item.symptom_name,
            "occurrence_count": item.occurrence_count,
            "average_duration": float(item.average_duration) if item.average_duration else None,
            "severity_distribution": severity_dict,
            "most_severe": item.most_severe
        })
    
    return result

def get_visit_symptoms_summary(db: Session, visit_id: int) -> Dict[str, Any]:
    """Get summary of symptoms for a visit"""
    visit_symptoms, total = get_visit_symptoms(db, visit_id)
    
    severity_distribution = {}
    symptoms_list = []
    
    for vs in visit_symptoms:
        severity = vs.severity or 'unknown'
        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        symptoms_list.append({
            "id": vs.id,
            "symptom_id": vs.symptom_id,
            "symptom_name": vs.symptom.symptom_name,
            "symptom_code": vs.symptom.symptom_code,
            "severity": vs.severity,
            "duration_days": vs.duration_days,
            "notes": vs.notes,
            "created_at": vs.created_at
        })
    
    return {
        "visit_id": visit_id,
        "total_symptoms": total,
        "symptoms_by_severity": severity_distribution,
        "symptoms_list": symptoms_list
    }

def search_visit_symptoms(
    db: Session, 
    patient_id: Optional[int] = None,
    symptom_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[VisitSymptom], int]:
    """Search visit symptoms with various filters"""
    query = db.query(VisitSymptom).join(
        PatientVisit, VisitSymptom.visit_id == PatientVisit.id
    ).join(
        Symptom, VisitSymptom.symptom_id == Symptom.id
    ).filter(
        VisitSymptom.deleted_at == None,
        PatientVisit.deleted_at == None,
        Symptom.deleted_at == None
    )
    
    # Apply filters
    if patient_id:
        query = query.filter(PatientVisit.patient_id == patient_id)
    
    if symptom_id:
        query = query.filter(VisitSymptom.symptom_id == symptom_id)
    
    if doctor_id:
        query = query.filter(PatientVisit.doctor_id == doctor_id)
    
    if start_date:
        query = query.filter(PatientVisit.visit_date >= start_date)
    
    if end_date:
        query = query.filter(PatientVisit.visit_date <= end_date)
    
    if severity:
        query = query.filter(VisitSymptom.severity == severity)
    
    total = query.count()
    visit_symptoms = query.order_by(PatientVisit.visit_date.desc()).offset(skip).limit(limit).all()
    
    return visit_symptoms, total

def get_patient_symptom_history(db: Session, patient_id: int) -> List[Dict[str, Any]]:
    """Get symptom history for a patient"""
    symptoms = db.query(
        Symptom.symptom_code,
        Symptom.symptom_name,
        VisitSymptom.severity,
        VisitSymptom.duration_days,
        VisitSymptom.notes,
        PatientVisit.visit_date,
        Doctor.first_name,
        Doctor.last_name
    ).join(
        VisitSymptom, Symptom.id == VisitSymptom.symptom_id
    ).join(
        PatientVisit, VisitSymptom.visit_id == PatientVisit.id
    ).join(
        Doctor, PatientVisit.doctor_id == Doctor.id
    ).filter(
        PatientVisit.patient_id == patient_id,
        VisitSymptom.deleted_at == None,
        Symptom.deleted_at == None,
        PatientVisit.deleted_at == None,
        Doctor.deleted_at == None
    ).order_by(
        PatientVisit.visit_date.desc()
    ).all()
    
    return [
        {
            "symptom_code": symptom.symptom_code,
            "symptom_name": symptom.symptom_name,
            "severity": symptom.severity,
            "duration_days": symptom.duration_days,
            "notes": symptom.notes,
            "visit_date": symptom.visit_date,
            "doctor_name": f"{symptom.first_name} {symptom.last_name}"
        }
        for symptom in symptoms
    ]