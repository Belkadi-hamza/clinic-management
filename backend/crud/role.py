from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.roles import Role
from ..schemas.role import RoleCreate, RoleUpdate

def get_roles(db: Session):
    # Exclude superadmin role from the list
    return db.query(Role).filter(Role.name != 'superadmin').order_by(Role.created_at.desc()).all()

def get_role_by_id(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name, Role.deleted_at == None).first()

def create_role(db: Session, role: RoleCreate, user_id: int):
    db_role = Role(**role.dict(), created_by=user_id)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, role_id: int, role: RoleUpdate, user_id: int):
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()
    if not db_role:
        return None
    for key, value in role.dict(exclude_unset=True).items():
        setattr(db_role, key, value)
    db_role.updated_by = user_id
    db.commit()
    db.refresh(db_role)
    return db_role

def soft_delete_role(db: Session, role_id: int, user_id: int):
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at == None).first()
    if not db_role:
        return None
    # Prevent deletion of superadmin role
    if db_role.name.lower() == 'superadmin':
        return None
    db_role.deleted_at = func.now()
    db_role.deleted_by = user_id
    db.commit()
    return db_role

def restore_role(db: Session, role_id: int, user_id: int):
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at != None).first()
    if not db_role:
        return None
    db_role.deleted_at = None
    db_role.deleted_by = None
    db_role.updated_by = user_id
    db.commit()
    db.refresh(db_role)
    return db_role