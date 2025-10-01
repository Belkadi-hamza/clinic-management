from sqlalchemy.orm import Session
from ..models.lab_tests import LabTest
from ..schemas.lab_tests import LabTestCreate, LabTestUpdate

def get_lab_tests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(LabTest).filter(LabTest.deleted_at == None).order_by(LabTest.created_at.desc()).offset(skip).limit(limit).all()

def get_lab_test_by_id(db: Session, lab_test_id: int):
    return db.query(LabTest).filter(LabTest.id == lab_test_id, LabTest.deleted_at == None).first()

def create_lab_test(db: Session, lab_test: LabTestCreate):
    db_lab_test = LabTest(**lab_test.dict())
    db.add(db_lab_test)
    db.commit()
    db.refresh(db_lab_test)
    return db_lab_test

def update_lab_test(db: Session, lab_test_id: int, lab_test: LabTestUpdate):
    db_lab_test = db.query(LabTest).filter(LabTest.id == lab_test_id, LabTest.deleted_at == None).first()
    if not db_lab_test:
        return None
    for key, value in lab_test.dict(exclude_unset=True).items():
        setattr(db_lab_test, key, value)
    db.commit()
    db.refresh(db_lab_test)
    return db_lab_test

def soft_delete_lab_test(db: Session, lab_test_id: int, deleted_by: int):
    db_lab_test = db.query(LabTest).filter(LabTest.id == lab_test_id, LabTest.deleted_at == None).first()
    if not db_lab_test:
        return None
    db_lab_test.deleted_at = db.func.now()
    db_lab_test.deleted_by = deleted_by
    db.commit()
    return db_lab_test