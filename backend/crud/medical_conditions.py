from sqlalchemy.orm import Session
from ..models.medical_conditions import MedicalCondition
from ..schemas.medical_conditions import MedicalConditionCreate, MedicalConditionUpdate

def get_medical_conditions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MedicalCondition).filter(MedicalCondition.deleted_at == None).order_by(MedicalCondition.created_at.desc()).offset(skip).limit(limit).all()

def get_medical_condition_by_id(db: Session, condition_id: int):
    return db.query(MedicalCondition).filter(MedicalCondition.id == condition_id, MedicalCondition.deleted_at == None).first()

def get_medical_condition_by_code(db: Session, condition_code: str):
    return db.query(MedicalCondition).filter(MedicalCondition.condition_code == condition_code, MedicalCondition.deleted_at == None).first()

def create_medical_condition(db: Session, condition: MedicalConditionCreate):
    db_condition = MedicalCondition(**condition.dict())
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    return db_condition

def update_medical_condition(db: Session, condition_id: int, condition: MedicalConditionUpdate):
    db_condition = db.query(MedicalCondition).filter(MedicalCondition.id == condition_id, MedicalCondition.deleted_at == None).first()
    if not db_condition:
        return None
    for key, value in condition.dict(exclude_unset=True).items():
        setattr(db_condition, key, value)
    db.commit()
    db.refresh(db_condition)
    return db_condition

def soft_delete_medical_condition(db: Session, condition_id: int, deleted_by: int):
    db_condition = db.query(MedicalCondition).filter(MedicalCondition.id == condition_id, MedicalCondition.deleted_at == None).first()
    if not db_condition:
        return None
    db_condition.deleted_at = db.func.now()
    db_condition.deleted_by = deleted_by
    db.commit()
    return db_condition