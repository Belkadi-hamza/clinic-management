from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.role_permissions import RolePermissionCreate, RolePermissionUpdate, RolePermissionResponse
from ..crud.role_permissions import (
    get_role_permissions, get_role_permission_by_id, get_role_permission_by_role_module,
    create_role_permission, update_role_permission, soft_delete_role_permission, restore_role_permission
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[RolePermissionResponse])
def read_role_permissions(current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    rps = get_role_permissions(db)
    return [
        RolePermissionResponse(
            **rp.__dict__,
            status="Active" if rp.deleted_at is None else "Inactive"
        )
        for rp in rps
    ]

@router.get("/{rp_id}", response_model=RolePermissionResponse)
def read_role_permission(rp_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    rp = get_role_permission_by_id(db, rp_id)
    if not rp:
        raise HTTPException(status_code=404, detail="Role permission not found")
    return RolePermissionResponse(
        **rp.__dict__,
        status="Active" if rp.deleted_at is None else "Inactive"
    )

@router.post("/", response_model=RolePermissionResponse)
def create_role_permission_item(rp: RolePermissionCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_role_permission_by_role_module(db, rp.role_id, rp.module_id):
        raise HTTPException(status_code=400, detail="Permission for this role and module already exists")
    db_rp = create_role_permission(db, rp, current_user["id"])
    return RolePermissionResponse(
        **db_rp.__dict__,
        status="Active"
    )

@router.put("/{rp_id}", response_model=RolePermissionResponse)
def update_role_permission_item(rp_id: int, rp: RolePermissionUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_rp = update_role_permission(db, rp_id, rp, current_user["id"])
    if not db_rp:
        raise HTTPException(status_code=404, detail="Role permission not found")
    return RolePermissionResponse(
        **db_rp.__dict__,
        status="Active" if db_rp.deleted_at is None else "Inactive"
    )

@router.delete("/{rp_id}", response_model=dict)
def delete_role_permission_item(rp_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_rp = soft_delete_role_permission(db, rp_id, current_user["id"])
    if not db_rp:
        raise HTTPException(status_code=404, detail="Role permission not found")
    return {"message": "Role permission deleted successfully"}

@router.post("/{rp_id}/restore", response_model=dict)
def restore_role_permission_item(rp_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_rp = restore_role_permission(db, rp_id, current_user["id"])
    if not db_rp:
        raise HTTPException(status_code=404, detail="Role permission not found or not deleted")
    return {"message": "Role permission restored successfully"}