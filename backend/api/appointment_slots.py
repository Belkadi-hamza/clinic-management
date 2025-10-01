from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.appointment_slots import AppointmentSlotCreate, AppointmentSlotUpdate, AppointmentSlotResponse
from ..crud.appointment_slots import (
    get_appointment_slots, get_appointment_slot_by_id,
    create_appointment_slot, update_appointment_slot, soft_delete_appointment_slot
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[AppointmentSlotResponse])
def read_appointment_slots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    slots = get_appointment_slots(db, skip=skip, limit=limit)
    return [AppointmentSlotResponse.from_orm(s) for s in slots]

@router.get("/{slot_id}", response_model=AppointmentSlotResponse)
def read_appointment_slot(slot_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    slot = get_appointment_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found")
    return AppointmentSlotResponse.from_orm(slot)

@router.post("/", response_model=AppointmentSlotResponse)
def create_appointment_slot_item(slot: AppointmentSlotCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_slot = create_appointment_slot(db, slot)
    return AppointmentSlotResponse.from_orm(db_slot)

@router.put("/{slot_id}", response_model=AppointmentSlotResponse)
def update_appointment_slot_item(slot_id: int, slot: AppointmentSlotUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_slot = update_appointment_slot(db, slot_id, slot)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found")
    return AppointmentSlotResponse.from_orm(db_slot)

@router.delete("/{slot_id}", response_model=dict)
def delete_appointment_slot_item(slot_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_slot = soft_delete_appointment_slot(db, slot_id, current_user["id"])
    if not db_slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found")
    return {"message": "Appointment slot deleted successfully"}