from sqlalchemy.orm import Session
from ..models.doctors import Doctor
from ..schemas.doctors import DoctorCreate, DoctorUpdate

def get_doctors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Doctor).filter(Doctor.deleted_at == None).order_by(Doctor.created_at.desc()).offset(skip).limit(limit).all()

def get_doctor_by_id(db: Session, doctor_id: int):
    return db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.deleted_at == None).first()

def get_doctor_by_code(db: Session, doctor_code: str):
    return db.query(Doctor).filter(Doctor.doctor_code == doctor_code, Doctor.deleted_at == None).first()

def create_doctor(db: Session, doctor: DoctorCreate):
    db_doctor = Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def update_doctor(db: Session, doctor_id: int, doctor: DoctorUpdate):
    db_doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.deleted_at == None).first()
    if not db_doctor:
        return None
    for key, value in doctor.dict(exclude_unset=True).items():
        setattr(db_doctor, key, value)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def soft_delete_doctor(db: Session, doctor_id: int, deleted_by: int):
    db_doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.deleted_at == None).first()
    if not db_doctor:
        return None
    db_doctor.deleted_at = db.func.now()
    db_doctor.deleted_by = deleted_by
    db.commit()
    return db_doctor