from sqlalchemy.orm import Session
from ..models.system_users import SystemUser
from ..schemas.system_users import SystemUserCreate, SystemUserUpdate
from passlib.hash import bcrypt

def get_system_users(db: Session):
    return db.query(SystemUser).order_by(SystemUser.created_at.desc()).all()

def get_system_user_by_id(db: Session, user_id: int):
    return db.query(SystemUser).filter(SystemUser.id == user_id).first()

def get_system_user_by_username(db: Session, username: str):
    return db.query(SystemUser).filter(SystemUser.username == username, SystemUser.deleted_at == None).first()

def create_system_user(db: Session, user: SystemUserCreate, creator_id: int):
    password_hash = bcrypt.hash(user.password)
    db_user = SystemUser(
        staff_id=user.staff_id,
        username=user.username,
        password_hash=password_hash,
        role_id=user.role_id,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        created_by=creator_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_system_user(db: Session, user_id: int, user: SystemUserUpdate, updater_id: int):
    db_user = db.query(SystemUser).filter(SystemUser.id == user_id, SystemUser.deleted_at == None).first()
    if not db_user:
        return None
    for key, value in user.dict(exclude_unset=True).items():
        if key == "password" and value:
            db_user.password_hash = bcrypt.hash(value)
        elif key != "password":
            setattr(db_user, key, value)
    db_user.updated_by = updater_id
    db.commit()
    db.refresh(db_user)
    return db_user

def soft_delete_system_user(db: Session, user_id: int, deleter_id: int):
    db_user = db.query(SystemUser).filter(SystemUser.id == user_id, SystemUser.deleted_at == None).first()
    if not db_user:
        return None
    db_user.deleted_at = db.func.now()
    db_user.deleted_by = deleter_id
    db.commit()
    return db_user

def restore_system_user(db: Session, user_id: int, updater_id: int):
    db_user = db.query(SystemUser).filter(SystemUser.id == user_id, SystemUser.deleted_at != None).first()
    if not db_user:
        return None
    db_user.deleted_at = None
    db_user.deleted_by = None
    db_user.updated_by = updater_id
    db.commit()
    db.refresh(db_user)
    return db_user