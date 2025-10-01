from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.doctors import DoctorCreate, DoctorUpdate, DoctorResponse
from ..crud.doctors import (
    get_doctors, get_doctor_by_id, get_doctor_by_code,
    create_doctor, update_doctor, soft_delete_doctor
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[DoctorResponse])
def read_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    doctors = get_doctors(db, skip=skip, limit=limit)
    return [DoctorResponse.from_orm(d) for d in doctors]

@router.get("/{doctor_id}", response_model=DoctorResponse)
def read_doctor(doctor_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return DoctorResponse.from_orm(doctor)

@router.post("/", response_model=DoctorResponse)
def create_doctor_item(doctor: DoctorCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_doctor_by_code(db, doctor.doctor_code):
        raise HTTPException(status_code=400, detail="Doctor code already exists")
    db_doctor = create_doctor(db, doctor)
    return DoctorResponse.from_orm(db_doctor)

@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor_item(doctor_id: int, doctor: DoctorUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_doctor = update_doctor(db, doctor_id, doctor)
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return DoctorResponse.from_orm(db_doctor)

@router.delete("/{doctor_id}", response_model=dict)
def delete_doctor_item(doctor_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_doctor = soft_delete_doctor(db, doctor_id, current_user["id"])
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"message": "Doctor deleted successfully"}