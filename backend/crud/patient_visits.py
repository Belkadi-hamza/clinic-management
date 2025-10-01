from sqlalchemy.orm import Session
from ..models.patient_visits import PatientVisit
from ..schemas.patient_visits import PatientVisitCreate, PatientVisitUpdate

def get_patient_visits(db: Session, skip: int = 0, limit: int = 100):
    return db.query(PatientVisit).filter(PatientVisit.deleted_at == None).order_by(PatientVisit.created_at.desc()).offset(skip).limit(limit).all()

def get_patient_visit_by_id(db: Session, visit_id: int):
    return db.query(PatientVisit).filter(PatientVisit.id == visit_id, PatientVisit.deleted_at == None).first()

def get_patient_visit_by_code(db: Session, visit_code: str):
    return db.query(PatientVisit).filter(PatientVisit.visit_code == visit_code, PatientVisit.deleted_at == None).first()

def create_patient_visit(db: Session, visit: PatientVisitCreate):
    db_visit = PatientVisit(**visit.dict())
    db.add(db_visit)
    db.commit()
    db.refresh(db_visit)
    return db_visit

def update_patient_visit(db: Session, visit_id: int, visit: PatientVisitUpdate):
    db_visit = db.query(PatientVisit).filter(PatientVisit.id == visit_id, PatientVisit.deleted_at == None).first()
    if not db_visit:
        return None
    for key, value in visit.dict(exclude_unset=True).items():
        setattr(db_visit, key, value)
    db.commit()
    db.refresh(db_visit)
    return db_visit

def soft_delete_patient_visit(db: Session, visit_id: int, deleted_by: int):
    db_visit = db.query(PatientVisit).filter(PatientVisit.id == visit_id, PatientVisit.deleted_at == None).first()
    if not db_visit:
        return None
    db_visit.deleted_at = db.func.now()
    db_visit.deleted_by = deleted_by
    db.commit()
    return db_visit