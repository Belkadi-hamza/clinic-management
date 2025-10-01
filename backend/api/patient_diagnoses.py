from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.patient_diagnoses import PatientDiagnosisCreate, PatientDiagnosisUpdate, PatientDiagnosisResponse
from ..crud.patient_diagnoses import (
    get_patient_diagnoses, get_patient_diagnosis_by_id,
    create_patient_diagnosis, update_patient_diagnosis, soft_delete_patient_diagnosis
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PatientDiagnosisResponse])
def read_patient_diagnoses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    diagnoses = get_patient_diagnoses(db, skip=skip, limit=limit)
    return [PatientDiagnosisResponse.from_orm(d) for d in diagnoses]

@router.get("/{diagnosis_id}", response_model=PatientDiagnosisResponse)
def read_patient_diagnosis(diagnosis_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    diagnosis = get_patient_diagnosis_by_id(db, diagnosis_id)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Patient diagnosis not found")
    return PatientDiagnosisResponse.from_orm(diagnosis)

@router.post("/", response_model=PatientDiagnosisResponse)
def create_patient_diagnosis_item(diagnosis: PatientDiagnosisCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_diagnosis = create_patient_diagnosis(db, diagnosis)
    return PatientDiagnosisResponse.from_orm(db_diagnosis)

@router.put("/{diagnosis_id}", response_model=PatientDiagnosisResponse)
def update_patient_diagnosis_item(diagnosis_id: int, diagnosis: PatientDiagnosisUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_diagnosis = update_patient_diagnosis(db, diagnosis_id, diagnosis)
    if not db_diagnosis:
        raise HTTPException(status_code=404, detail="Patient diagnosis not found")
    return PatientDiagnosisResponse.from_orm(db_diagnosis)

@router.delete("/{diagnosis_id}", response_model=dict)
def delete_patient_diagnosis_item(diagnosis_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_diagnosis = soft_delete_patient_diagnosis(db, diagnosis_id, current_user["id"])
    if not db_diagnosis:
        raise HTTPException(status_code=404, detail="Patient diagnosis not found")
    return {"message": "Patient diagnosis deleted successfully"}