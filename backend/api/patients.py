from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.patients import PatientCreate, PatientUpdate, PatientResponse
from ..crud.patients import (
    get_patients, get_patient_by_id, get_patient_by_code,
    create_patient, update_patient, soft_delete_patient
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    patients = get_patients(db, skip=skip, limit=limit)
    return [PatientResponse.from_orm(p) for p in patients]

@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(patient_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.from_orm(patient)

@router.post("/", response_model=PatientResponse)
def create_patient_item(patient: PatientCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_patient_by_code(db, patient.patient_code):
        raise HTTPException(status_code=400, detail="Patient code already exists")
    db_patient = create_patient(db, patient)
    return PatientResponse.from_orm(db_patient)

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient_item(patient_id: int, patient: PatientUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_patient = update_patient(db, patient_id, patient)
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.from_orm(db_patient)

@router.delete("/{patient_id}", response_model=dict)
def delete_patient_item(patient_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_patient = soft_delete_patient(db, patient_id, current_user["id"])
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}