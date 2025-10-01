from sqlalchemy.orm import Session
from ..models.patient_diagnoses import PatientDiagnosis
from ..schemas.patient_diagnoses import PatientDiagnosisCreate, PatientDiagnosisUpdate

def get_patient_diagnoses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(PatientDiagnosis).filter(PatientDiagnosis.deleted_at == None).order_by(PatientDiagnosis.created_at.desc()).offset(skip).limit(limit).all()

def get_patient_diagnosis_by_id(db: Session, diagnosis_id: int):
    return db.query(PatientDiagnosis).filter(PatientDiagnosis.id == diagnosis_id, PatientDiagnosis.deleted_at == None).first()

def create_patient_diagnosis(db: Session, diagnosis: PatientDiagnosisCreate):
    db_diagnosis = PatientDiagnosis(**diagnosis.dict())
    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)
    return db_diagnosis

def update_patient_diagnosis(db: Session, diagnosis_id: int, diagnosis: PatientDiagnosisUpdate):
    db_diagnosis = db.query(PatientDiagnosis).filter(PatientDiagnosis.id == diagnosis_id, PatientDiagnosis.deleted_at == None).first()
    if not db_diagnosis:
        return None
    for key, value in diagnosis.dict(exclude_unset=True).items():
        setattr(db_diagnosis, key, value)
    db.commit()
    db.refresh(db_diagnosis)
    return db_diagnosis

def soft_delete_patient_diagnosis(db: Session, diagnosis_id: int, deleted_by: int):
    db_diagnosis = db.query(PatientDiagnosis).filter(PatientDiagnosis.id == diagnosis_id, PatientDiagnosis.deleted_at == None).first()
    if not db_diagnosis:
        return None
    db_diagnosis.deleted_at = db.func.now()
    db_diagnosis.deleted_by = deleted_by
    db.commit()
    return db_diagnosis