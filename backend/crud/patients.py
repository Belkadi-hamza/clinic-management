from sqlalchemy.orm import Session
from ..models.patients import Patient
from ..schemas.patients import PatientCreate, PatientUpdate

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Patient).filter(Patient.deleted_at == None).order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

def get_patient_by_id(db: Session, patient_id: int):
    return db.query(Patient).filter(Patient.id == patient_id, Patient.deleted_at == None).first()

def get_patient_by_code(db: Session, patient_code: str):
    return db.query(Patient).filter(Patient.patient_code == patient_code, Patient.deleted_at == None).first()

def create_patient(db: Session, patient: PatientCreate):
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient(db: Session, patient_id: int, patient: PatientUpdate):
    db_patient = db.query(Patient).filter(Patient.id == patient_id, Patient.deleted_at == None).first()
    if not db_patient:
        return None
    for key, value in patient.dict(exclude_unset=True).items():
        setattr(db_patient, key, value)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def soft_delete_patient(db: Session, patient_id: int, deleted_by: int):
    db_patient = db.query(Patient).filter(Patient.id == patient_id, Patient.deleted_at == None).first()
    if not db_patient:
        return None
    db_patient.deleted_at = db.func.now()
    db_patient.deleted_by = deleted_by
    db.commit()
    return db_patient