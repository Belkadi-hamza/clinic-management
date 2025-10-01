from sqlalchemy.orm import Session
from ..models.allergies import Allergy
from ..schemas.allergies import AllergyCreate, AllergyUpdate

def get_allergies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Allergy).filter(Allergy.deleted_at == None).order_by(Allergy.created_at.desc()).offset(skip).limit(limit).all()

def get_allergy_by_id(db: Session, allergy_id: int):
    return db.query(Allergy).filter(Allergy.id == allergy_id, Allergy.deleted_at == None).first()

def create_allergy(db: Session, allergy: AllergyCreate):
    db_allergy = Allergy(**allergy.dict())
    db.add(db_allergy)
    db.commit()
    db.refresh(db_allergy)
    return db_allergy

def update_allergy(db: Session, allergy_id: int, allergy: AllergyUpdate):
    db_allergy = db.query(Allergy).filter(Allergy.id == allergy_id, Allergy.deleted_at == None).first()
    if not db_allergy:
        return None
    for key, value in allergy.dict(exclude_unset=True).items():
        setattr(db_allergy, key, value)
    db.commit()
    db.refresh(db_allergy)
    return db_allergy

def soft_delete_allergy(db: Session, allergy_id: int, deleted_by: int):
    db_allergy = db.query(Allergy).filter(Allergy.id == allergy_id, Allergy.deleted_at == None).first()
    if not db_allergy:
        return None
    db_allergy.deleted_at = db.func.now()
    db_allergy.deleted_by = deleted_by
    db.commit()
    return db_allergy