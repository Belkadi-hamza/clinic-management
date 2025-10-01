from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from ..models.symptoms import Symptom, VisitSymptom
from ..schemas.symptoms import SymptomCreate, SymptomUpdate, VisitSymptomCreate, VisitSymptomUpdate

# Symptom CRUD operations
def get_symptoms(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(Symptom).filter(Symptom.deleted_at == None)
    
    if search:
        search_filter = or_(
            Symptom.symptom_code.ilike(f"%{search}%"),
            Symptom.symptom_name.ilike(f"%{search}%"),
            Symptom.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    total = query.count()
    symptoms = query.order_by(Symptom.symptom_name).offset(skip).limit(limit).all()
    return symptoms, total

def get_symptom_by_id(db: Session, symptom_id: int):
    return db.query(Symptom).filter(
        Symptom.id == symptom_id, 
        Symptom.deleted_at == None
    ).first()

def get_symptom_by_code(db: Session, symptom_code: str):
    return db.query(Symptom).filter(
        Symptom.symptom_code == symptom_code.upper(),
        Symptom.deleted_at == None
    ).first()

def create_symptom(db: Session, symptom: SymptomCreate, user_id: int):
    # Check if symptom code already exists
    existing_symptom = get_symptom_by_code(db, symptom.symptom_code)
    if existing_symptom:
        return None, "Symptom code already exists"
    
    db_symptom = Symptom(
        symptom_code=symptom.symptom_code.upper(),
        symptom_name=symptom.symptom_name,
        description=symptom.description,
        created_by=user_id
    )
    db.add(db_symptom)
    db.commit()
    db.refresh(db_symptom)
    return db_symptom, None

def update_symptom(db: Session, symptom_id: int, symptom: SymptomUpdate, user_id: int):
    db_symptom = get_symptom_by_id(db, symptom_id)
    if not db_symptom:
        return None, "Symptom not found"
    
    # Check if new symptom code conflicts with existing one
    if symptom.symptom_code and symptom.symptom_code != db_symptom.symptom_code:
        existing_symptom = get_symptom_by_code(db, symptom.symptom_code)
        if existing_symptom:
            return None, "Symptom code already exists"
    
    update_data = symptom.dict(exclude_unset=True)
    if 'symptom_code' in update_data:
        update_data['symptom_code'] = update_data['symptom_code'].upper()
    
    for key, value in update_data.items():
        setattr(db_symptom, key, value)
    
    db_symptom.updated_by = user_id
    db.commit()
    db.refresh(db_symptom)
    return db_symptom, None

def soft_delete_symptom(db: Session, symptom_id: int, user_id: int):
    db_symptom = get_symptom_by_id(db, symptom_id)
    if not db_symptom:
        return None, "Symptom not found"
    
    # Check if symptom is being used in any visits
    usage_count = db.query(VisitSymptom).filter(
        VisitSymptom.symptom_id == symptom_id,
        VisitSymptom.deleted_at == None
    ).count()
    
    if usage_count > 0:
        return None, f"Cannot delete symptom. It is being used in {usage_count} patient visit(s)."
    
    db_symptom.deleted_at = func.now()
    db_symptom.deleted_by = user_id
    db.commit()
    return db_symptom, None

def restore_symptom(db: Session, symptom_id: int, user_id: int):
    db_symptom = db.query(Symptom).filter(
        Symptom.id == symptom_id,
        Symptom.deleted_at != None
    ).first()
    
    if not db_symptom:
        return None, "Symptom not found or not deleted"
    
    db_symptom.deleted_at = None
    db_symptom.deleted_by = None
    db_symptom.updated_by = user_id
    db.commit()
    db.refresh(db_symptom)
    return db_symptom, None

def get_symptoms_with_usage(db: Session, skip: int = 0, limit: int = 100):
    symptoms = db.query(Symptom).filter(Symptom.deleted_at == None).offset(skip).limit(limit).all()
    
    result = []
    for symptom in symptoms:
        usage_count = db.query(VisitSymptom).filter(
            VisitSymptom.symptom_id == symptom.id,
            VisitSymptom.deleted_at == None
        ).count()
        
        result.append({
            **symptom.__dict__,
            'usage_count': usage_count
        })
    
    return result

# Visit Symptom CRUD operations
def get_visit_symptoms(db: Session, visit_id: int):
    return db.query(VisitSymptom).filter(
        VisitSymptom.visit_id == visit_id,
        VisitSymptom.deleted_at == None
    ).all()

def get_visit_symptom_by_id(db: Session, visit_symptom_id: int):
    return db.query(VisitSymptom).filter(
        VisitSymptom.id == visit_symptom_id,
        VisitSymptom.deleted_at == None
    ).first()

def create_visit_symptom(db: Session, visit_symptom: VisitSymptomCreate, user_id: int):
    # Check if symptom exists
    symptom = get_symptom_by_id(db, visit_symptom.symptom_id)
    if not symptom:
        return None, "Symptom not found"
    
    # Check if visit exists (you might want to add this check)
    # visit = get_visit_by_id(db, visit_symptom.visit_id)
    # if not visit:
    #     return None, "Visit not found"
    
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

def update_visit_symptom(db: Session, visit_symptom_id: int, visit_symptom: VisitSymptomUpdate, user_id: int):
    db_visit_symptom = get_visit_symptom_by_id(db, visit_symptom_id)
    if not db_visit_symptom:
        return None, "Visit symptom not found"
    
    update_data = visit_symptom.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_visit_symptom, key, value)
    
    db.commit()
    db.refresh(db_visit_symptom)
    return db_visit_symptom, None

def delete_visit_symptom(db: Session, visit_symptom_id: int, user_id: int):
    db_visit_symptom = get_visit_symptom_by_id(db, visit_symptom_id)
    if not db_visit_symptom:
        return None, "Visit symptom not found"
    
    db_visit_symptom.deleted_at = func.now()
    db_visit_symptom.deleted_by = user_id
    db.commit()
    return db_visit_symptom, None

def search_symptoms(db: Session, query: str, limit: int = 10):
    return db.query(Symptom).filter(
        Symptom.deleted_at == None,
        or_(
            Symptom.symptom_code.ilike(f"%{query}%"),
            Symptom.symptom_name.ilike(f"%{query}%")
        )
    ).order_by(Symptom.symptom_name).limit(limit).all()