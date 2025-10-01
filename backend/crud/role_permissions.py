from sqlalchemy.orm import Session
from ..models.role_permissions import RolePermission
from ..schemas.role_permissions import RolePermissionCreate, RolePermissionUpdate

def get_role_permissions(db: Session):
    return db.query(RolePermission).order_by(RolePermission.created_at.desc()).all()

def get_role_permission_by_id(db: Session, rp_id: int):
    return db.query(RolePermission).filter(RolePermission.id == rp_id).first()

def get_role_permission_by_role_module(db: Session, role_id: int, module_id: int):
    return db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.module_id == module_id,
        RolePermission.deleted_at == None
    ).first()

def create_role_permission(db: Session, rp: RolePermissionCreate, user_id: int):
    db_rp = RolePermission(**rp.dict(), created_by=user_id)
    db.add(db_rp)
    db.commit()
    db.refresh(db_rp)
    return db_rp

def update_role_permission(db: Session, rp_id: int, rp: RolePermissionUpdate, user_id: int):
    db_rp = db.query(RolePermission).filter(RolePermission.id == rp_id, RolePermission.deleted_at == None).first()
    if not db_rp:
        return None
    for key, value in rp.dict(exclude_unset=True).items():
        setattr(db_rp, key, value)
    db_rp.updated_by = user_id
    db.commit()
    db.refresh(db_rp)
    return db_rp

def soft_delete_role_permission(db: Session, rp_id: int, user_id: int):
    db_rp = db.query(RolePermission).filter(RolePermission.id == rp_id, RolePermission.deleted_at == None).first()
    if not db_rp:
        return None
    db_rp.deleted_at = db.func.now()
    db_rp.deleted_by = user_id
    db.commit()
    return db_rp

def restore_role_permission(db: Session, rp_id: int, user_id: int):
    db_rp = db.query(RolePermission).filter(RolePermission.id == rp_id, RolePermission.deleted_at != None).first()
    if not db_rp:
        return None
    db_rp.deleted_at = None
    db_rp.deleted_by = None
    db_rp.updated_by = user_id
    db.commit()
    db.refresh(db_rp)
    return db_rp