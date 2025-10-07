from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.staff import StaffCreate, StaffUpdate, StaffResponse
from ..crud.staff import (
    get_staff, get_staff_by_id, get_staff_by_email,
    create_staff, update_staff, soft_delete_staff, restore_staff
)
from ..deps import require_admin_or_super, get_current_user
from typing import List

router = APIRouter()

@router.get("/", response_model=List[StaffResponse])
def read_staff(current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    staff_list = get_staff(db)
    return [
        StaffResponse(
            **staff.__dict__,
            status="Active" if staff.deleted_at is None else "Inactive"
        )
        for staff in staff_list
    ]

@router.put("/me/update", response_model=StaffResponse)
def update_my_profile(
    staff: StaffUpdate, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Update current user's own staff profile"""
    try:
        print(f"Updating staff profile for user {current_user['id']}, staff_id: {current_user['staff_id']}")
        
        # Users can only update their own staff profile
        staff_id = current_user["staff_id"]
        if not staff_id:
            raise HTTPException(status_code=400, detail="No staff profile associated with this user")
        
        db_staff = update_staff(db, staff_id, staff, current_user["id"])
        if not db_staff:
            raise HTTPException(status_code=404, detail="Staff profile not found")
        
        print(f"Successfully updated staff profile {staff_id}")
        return StaffResponse(
            **db_staff.__dict__,
            status="Active" if db_staff.deleted_at is None else "Inactive"
        )
    except Exception as e:
        print(f"Error updating staff profile {current_user['staff_id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{staff_id}", response_model=StaffResponse)
def read_staff_member(staff_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    staff = get_staff_by_id(db, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return StaffResponse(
        **staff.__dict__,
        status="Active" if staff.deleted_at is None else "Inactive"
    )

@router.post("/", response_model=StaffResponse)
def create_staff_member(staff: StaffCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_staff_by_email(db, staff.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    db_staff = create_staff(db, staff, current_user["id"])
    return StaffResponse(
        **db_staff.__dict__,
        status="Active"
    )

@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff_member(staff_id: int, staff: StaffUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_staff = update_staff(db, staff_id, staff, current_user["id"])
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return StaffResponse(
        **db_staff.__dict__,
        status="Active" if db_staff.deleted_at is None else "Inactive"
    )

@router.delete("/{staff_id}", response_model=dict)
def delete_staff_member(staff_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_staff = soft_delete_staff(db, staff_id, current_user["id"])
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return {"message": "Staff member deleted successfully"}

@router.post("/{staff_id}/restore", response_model=dict)
def restore_staff_member(staff_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_staff = restore_staff(db, staff_id, current_user["id"])
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found or not deleted")
    return {"message": "Staff member restored successfully"}