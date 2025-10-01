from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.role import RoleCreate, RoleUpdate, RoleResponse
from ..crud.role import (
    get_roles, get_role_by_id, get_role_by_name,
    create_role, update_role, soft_delete_role, restore_role
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
def read_roles(current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    roles = get_roles(db)
    return [
        RoleResponse(
            **role.__dict__,
            status="Active" if role.deleted_at is None else "Inactive"
        )
        for role in roles
    ]

@router.get("/{role_id}", response_model=RoleResponse)
def read_role(role_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    role = get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleResponse(
        **role.__dict__,
        status="Active" if role.deleted_at is None else "Inactive"
    )

@router.post("/", response_model=RoleResponse)
def create_role_item(role: RoleCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_role_by_name(db, role.name):
        raise HTTPException(status_code=400, detail="Role name already exists")
    db_role = create_role(db, role, current_user["id"])
    return RoleResponse(
        **db_role.__dict__,
        status="Active"
    )

@router.put("/{role_id}", response_model=RoleResponse)
def update_role_item(role_id: int, role: RoleUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_role = update_role(db, role_id, role, current_user["id"])
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleResponse(
        **db_role.__dict__,
        status="Active" if db_role.deleted_at is None else "Inactive"
    )

@router.delete("/{role_id}", response_model=dict)
def delete_role_item(role_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_role = soft_delete_role(db, role_id, current_user["id"])
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}

@router.post("/{role_id}/restore", response_model=dict)
def restore_role_item(role_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_role = restore_role(db, role_id, current_user["id"])
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found or not deleted")
    return {"message": "Role restored successfully"}