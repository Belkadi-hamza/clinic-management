from sqlalchemy.orm import Session
from ..models.patient_allergies import PatientAllergy
from ..schemas.patient_allergies import PatientAllergyCreate, PatientAllergyUpdate

def get_patient_allergies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(PatientAllergy).filter(PatientAllergy.deleted_at == None).order_by(PatientAllergy.created_at.desc()).offset(skip).limit(limit).all()

def get_patient_allergy_by_id(db: Session, allergy_id: int):
    return db.query(PatientAllergy).filter(PatientAllergy.id == allergy_id, PatientAllergy.deleted_at == None).first()

def create_patient_allergy(db: Session, allergy: PatientAllergyCreate):
    db_allergy = PatientAllergy(**allergy.dict())
    db.add(db_allergy)
    db.commit()
    db.refresh(db_allergy)
    return db_allergy

def update_patient_allergy(db: Session, allergy_id: int, allergy: PatientAllergyUpdate):
    db_allergy = db.query(PatientAllergy).filter(PatientAllergy.id == allergy_id, PatientAllergy.deleted_at == None).first()
    if not db_allergy:
        return None
    for key, value in allergy.dict(exclude_unset=True).items():
        setattr(db_allergy, key, value)
    db.commit()
    db.refresh(db_allergy)
    return db_allergy

def soft_delete_patient_allergy(db: Session, allergy_id: int, deleted_by: int):
    db_allergy = db.query(PatientAllergy).filter(PatientAllergy.id == allergy_id, PatientAllergy.deleted_at == None).first()
    if not db_allergy:
        return None
    db_allergy.deleted_at = db.func.now()
    db_allergy.deleted_by = deleted_by
    db.commit()
    return db_allergy