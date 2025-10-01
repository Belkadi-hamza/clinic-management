from sqlalchemy.orm import Session
from ..models.medications import Medication
from ..schemas.medications import MedicationCreate, MedicationUpdate

def get_medications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Medication).filter(Medication.deleted_at == None).order_by(Medication.created_at.desc()).offset(skip).limit(limit).all()

def get_medication_by_id(db: Session, medication_id: int):
    return db.query(Medication).filter(Medication.id == medication_id, Medication.deleted_at == None).first()

def create_medication(db: Session, medication: MedicationCreate):
    db_medication = Medication(**medication.dict())
    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)
    return db_medication

def update_medication(db: Session, medication_id: int, medication: MedicationUpdate):
    db_medication = db.query(Medication).filter(Medication.id == medication_id, Medication.deleted_at == None).first()
    if not db_medication:
        return None
    for key, value in medication.dict(exclude_unset=True).items():
        setattr(db_medication, key, value)
    db.commit()
    db.refresh(db_medication)
    return db_medication

def soft_delete_medication(db: Session, medication_id: int, deleted_by: int):
    db_medication = db.query(Medication).filter(Medication.id == medication_id, Medication.deleted_at == None).first()
    if not db_medication:
        return None
    db_medication.deleted_at = db.func.now()
    db_medication.deleted_by = deleted_by
    db.commit()
    return db_medication