from sqlalchemy.orm import Session
from ..models.prescriptions import Prescription
from ..schemas.prescriptions import PrescriptionCreate, PrescriptionUpdate

def get_prescriptions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Prescription).filter(Prescription.deleted_at == None).order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()

def get_prescription_by_id(db: Session, prescription_id: int):
    return db.query(Prescription).filter(Prescription.id == prescription_id, Prescription.deleted_at == None).first()

def create_prescription(db: Session, prescription: PrescriptionCreate):
    db_prescription = Prescription(**prescription.dict())
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription

def update_prescription(db: Session, prescription_id: int, prescription: PrescriptionUpdate):
    db_prescription = db.query(Prescription).filter(Prescription.id == prescription_id, Prescription.deleted_at == None).first()
    if not db_prescription:
        return None
    for key, value in prescription.dict(exclude_unset=True).items():
        setattr(db_prescription, key, value)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription

def soft_delete_prescription(db: Session, prescription_id: int, deleted_by: int):
    db_prescription = db.query(Prescription).filter(Prescription.id == prescription_id, Prescription.deleted_at == None).first()
    if not db_prescription:
        return None
    db_prescription.deleted_at = db.func.now()
    db_prescription.deleted_by = deleted_by
    db.commit()
    return db_prescription