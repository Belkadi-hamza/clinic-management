from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.patient_allergies import PatientAllergyCreate, PatientAllergyUpdate, PatientAllergyResponse
from ..crud.patient_allergies import (
    get_patient_allergies, get_patient_allergy_by_id,
    create_patient_allergy, update_patient_allergy, soft_delete_patient_allergy
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PatientAllergyResponse])
def read_patient_allergies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    allergies = get_patient_allergies(db, skip=skip, limit=limit)
    return [PatientAllergyResponse.from_orm(a) for a in allergies]

@router.get("/{allergy_id}", response_model=PatientAllergyResponse)
def read_patient_allergy(allergy_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    allergy = get_patient_allergy_by_id(db, allergy_id)
    if not allergy:
        raise HTTPException(status_code=404, detail="Patient allergy not found")
    return PatientAllergyResponse.from_orm(allergy)

@router.post("/", response_model=PatientAllergyResponse)
def create_patient_allergy_item(allergy: PatientAllergyCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_allergy = create_patient_allergy(db, allergy)
    return PatientAllergyResponse.from_orm(db_allergy)

@router.put("/{allergy_id}", response_model=PatientAllergyResponse)
def update_patient_allergy_item(allergy_id: int, allergy: PatientAllergyUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_allergy = update_patient_allergy(db, allergy_id, allergy)
    if not db_allergy:
        raise HTTPException(status_code=404, detail="Patient allergy not found")
    return PatientAllergyResponse.from_orm(db_allergy)

@router.delete("/{allergy_id}", response_model=dict)
def delete_patient_allergy_item(allergy_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_allergy = soft_delete_patient_allergy(db, allergy_id, current_user["id"])
    if not db_allergy:
        raise HTTPException(status_code=404, detail="Patient allergy not found")
    return {"message": "Patient allergy deleted successfully"}