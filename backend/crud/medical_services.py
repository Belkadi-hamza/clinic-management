from sqlalchemy.orm import Session
from ..models.medical_services import MedicalService
from ..schemas.medical_services import MedicalServiceCreate, MedicalServiceUpdate

def get_medical_services(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MedicalService).filter(MedicalService.deleted_at == None).order_by(MedicalService.created_at.desc()).offset(skip).limit(limit).all()

def get_medical_service_by_id(db: Session, service_id: int):
    return db.query(MedicalService).filter(MedicalService.id == service_id, MedicalService.deleted_at == None).first()

def get_medical_service_by_code(db: Session, service_code: str):
    return db.query(MedicalService).filter(MedicalService.service_code == service_code, MedicalService.deleted_at == None).first()

def create_medical_service(db: Session, service: MedicalServiceCreate):
    db_service = MedicalService(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_medical_service(db: Session, service_id: int, service: MedicalServiceUpdate):
    db_service = db.query(MedicalService).filter(MedicalService.id == service_id, MedicalService.deleted_at == None).first()
    if not db_service:
        return None
    for key, value in service.dict(exclude_unset=True).items():
        setattr(db_service, key, value)
    db.commit()
    db.refresh(db_service)
    return db_service

def soft_delete_medical_service(db: Session, service_id: int, deleted_by: int):
    db_service = db.query(MedicalService).filter(MedicalService.id == service_id, MedicalService.deleted_at == None).first()
    if not db_service:
        return None
    db_service.deleted_at = db.func.now()
    db_service.deleted_by = deleted_by
    db.commit()
    return db_service