from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.system_users import SystemUserCreate, SystemUserUpdate, SystemUserResponse
from ..crud.system_users import (
    get_system_users, get_system_user_by_id, get_system_user_by_username,
    create_system_user, update_system_user, soft_delete_system_user, restore_system_user
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[SystemUserResponse])
def read_system_users(current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    users = get_system_users(db)
    return [
        SystemUserResponse(
            **user.__dict__,
            status="Active" if user.deleted_at is None else "Inactive"
        )
        for user in users
    ]

@router.get("/{user_id}", response_model=SystemUserResponse)
def read_system_user(user_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    user = get_system_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="System user not found")
    return SystemUserResponse(
        **user.__dict__,
        status="Active" if user.deleted_at is None else "Inactive"
    )

@router.post("/", response_model=SystemUserResponse)
def create_system_user_item(user: SystemUserCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_system_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    db_user = create_system_user(db, user, current_user["id"])
    return SystemUserResponse(
        **db_user.__dict__,
        status="Active"
    )

@router.put("/{user_id}", response_model=SystemUserResponse)
def update_system_user_item(user_id: int, user: SystemUserUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_user = update_system_user(db, user_id, user, current_user["id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="System user not found")
    return SystemUserResponse(
        **db_user.__dict__,
        status="Active" if db_user.deleted_at is None else "Inactive"
    )

@router.delete("/{user_id}", response_model=dict)
def delete_system_user_item(user_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_user = soft_delete_system_user(db, user_id, current_user["id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="System user not found")
    return {"message": "System user deleted successfully"}

@router.post("/{user_id}/restore", response_model=dict)
def restore_system_user_item(user_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_user = restore_system_user(db, user_id, current_user["id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="System user not found or not deleted")
    return {"message": "System user restored successfully"}