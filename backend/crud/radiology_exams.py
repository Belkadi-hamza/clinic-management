from sqlalchemy.orm import Session
from ..models.radiology_exams import RadiologyExam
from ..schemas.radiology_exams import RadiologyExamCreate, RadiologyExamUpdate

def get_radiology_exams(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RadiologyExam).filter(RadiologyExam.deleted_at == None).order_by(RadiologyExam.created_at.desc()).offset(skip).limit(limit).all()

def get_radiology_exam_by_id(db: Session, exam_id: int):
    return db.query(RadiologyExam).filter(RadiologyExam.id == exam_id, RadiologyExam.deleted_at == None).first()

def create_radiology_exam(db: Session, exam: RadiologyExamCreate):
    db_exam = RadiologyExam(**exam.dict())
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam

def update_radiology_exam(db: Session, exam_id: int, exam: RadiologyExamUpdate):
    db_exam = db.query(RadiologyExam).filter(RadiologyExam.id == exam_id, RadiologyExam.deleted_at == None).first()
    if not db_exam:
        return None
    for key, value in exam.dict(exclude_unset=True).items():
        setattr(db_exam, key, value)
    db.commit()
    db.refresh(db_exam)
    return db_exam

def soft_delete_radiology_exam(db: Session, exam_id: int, deleted_by: int):
    db_exam = db.query(RadiologyExam).filter(RadiologyExam.id == exam_id, RadiologyExam.deleted_at == None).first()
    if not db_exam:
        return None
    db_exam.deleted_at = db.func.now()
    db_exam.deleted_by = deleted_by
    db.commit()
    return db_exam