from sqlalchemy.orm import Session
from ..models.appointment_slots import AppointmentSlot
from ..schemas.appointment_slots import AppointmentSlotCreate, AppointmentSlotUpdate

def get_appointment_slots(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AppointmentSlot).filter(AppointmentSlot.deleted_at == None).order_by(AppointmentSlot.created_at.desc()).offset(skip).limit(limit).all()

def get_appointment_slot_by_id(db: Session, slot_id: int):
    return db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id, AppointmentSlot.deleted_at == None).first()

def create_appointment_slot(db: Session, slot: AppointmentSlotCreate):
    db_slot = AppointmentSlot(**slot.dict())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def update_appointment_slot(db: Session, slot_id: int, slot: AppointmentSlotUpdate):
    db_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id, AppointmentSlot.deleted_at == None).first()
    if not db_slot:
        return None
    for key, value in slot.dict(exclude_unset=True).items():
        setattr(db_slot, key, value)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def soft_delete_appointment_slot(db: Session, slot_id: int, deleted_by: int):
    db_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id, AppointmentSlot.deleted_at == None).first()
    if not db_slot:
        return None
    db_slot.deleted_at = db.func.now()
    db_slot.deleted_by = deleted_by
    db.commit()
    return db_slot