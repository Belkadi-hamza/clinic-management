from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models.staff import Staff
from ..schemas.staff import StaffCreate, StaffUpdate

def get_staff(db: Session):
    return db.query(Staff).order_by(Staff.created_at.desc()).all()

def get_staff_by_id(db: Session, staff_id: int):
    return db.query(Staff).filter(Staff.id == staff_id).first()

def get_staff_by_email(db: Session, email: str):
    return db.query(Staff).filter(Staff.email == email, Staff.deleted_at == None).first()

def create_staff(db: Session, staff: StaffCreate, user_id: int):
    db_staff = Staff(**staff.dict(), created_by=user_id)
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

def update_staff(db: Session, staff_id: int, staff: StaffUpdate, user_id: int):
    db_staff = db.query(Staff).filter(Staff.id == staff_id, Staff.deleted_at == None).first()
    if not db_staff:
        return None
    for key, value in staff.dict(exclude_unset=True).items():
        setattr(db_staff, key, value)
    db_staff.updated_by = user_id
    db.commit()
    db.refresh(db_staff)
    return db_staff

def soft_delete_staff(db: Session, staff_id: int, user_id: int):
    db_staff = db.query(Staff).filter(Staff.id == staff_id, Staff.deleted_at == None).first()
    if not db_staff:
        return None
    db_staff.deleted_at = db.func.now()
    db_staff.deleted_by = user_id
    db.commit()
    return db_staff

def restore_staff(db: Session, staff_id: int, user_id: int):
    db_staff = db.query(Staff).filter(Staff.id == staff_id, Staff.deleted_at != None).first()
    if not db_staff:
        return None
    db_staff.deleted_at = None
    db_staff.deleted_by = None
    db_staff.updated_by = user_id
    db.commit()
    db.refresh(db_staff)
    return db_staff