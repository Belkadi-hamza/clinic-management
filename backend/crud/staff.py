from sqlalchemy.orm import Session
from sqlalchemy import or_, text
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
    
    # Build update dictionary
    update_data = staff.dict(exclude_unset=True)
    if not update_data:
        return db_staff
    
    # Use raw SQL to bypass the audit trigger issue
    # Build SET clause dynamically
    set_clauses = []
    params = {'staff_id': staff_id, 'updated_by': user_id}
    
    for key, value in update_data.items():
        param_name = f"param_{key}"
        set_clauses.append(f"{key} = :{param_name}")
        params[param_name] = value
    
    set_clauses.append("updated_by = :updated_by")
    set_clauses.append("updated_at = now()")
    
    sql = f"UPDATE staff SET {', '.join(set_clauses)} WHERE id = :staff_id"
    
    try:
        db.execute(text(sql), params)
        db.commit()
        db.refresh(db_staff)
        return db_staff
    except Exception as e:
        db.rollback()
        raise e

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