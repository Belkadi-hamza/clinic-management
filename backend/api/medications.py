from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.medications import MedicationCreate, MedicationUpdate, MedicationResponse
from ..crud.medications import (
    get_medications, get_medication_by_id,
    create_medication, update_medication, soft_delete_medication
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[MedicationResponse])
def read_medications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    medications = get_medications(db, skip=skip, limit=limit)
    return [MedicationResponse.from_orm(m) for m in medications]

@router.get("/{medication_id}", response_model=MedicationResponse)
def read_medication(medication_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    medication = get_medication_by_id(db, medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return MedicationResponse.from_orm(medication)

@router.post("/", response_model=MedicationResponse)
def create_medication_item(medication: MedicationCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_medication = create_medication(db, medication)
    return MedicationResponse.from_orm(db_medication)

@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication_item(medication_id: int, medication: MedicationUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_medication = update_medication(db, medication_id, medication)
    if not db_medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return MedicationResponse.from_orm(db_medication)

@router.delete("/{medication_id}", response_model=dict)
def delete_medication_item(medication_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_medication = soft_delete_medication(db, medication_id, current_user["id"])
    if not db_medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"message": "Medication deleted successfully"}