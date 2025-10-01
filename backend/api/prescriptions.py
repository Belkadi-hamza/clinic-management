from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.prescriptions import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse
from ..crud.prescriptions import (
    get_prescriptions, get_prescription_by_id,
    create_prescription, update_prescription, soft_delete_prescription
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PrescriptionResponse])
def read_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    prescriptions = get_prescriptions(db, skip=skip, limit=limit)
    return [PrescriptionResponse.from_orm(p) for p in prescriptions]

@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def read_prescription(prescription_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    prescription = get_prescription_by_id(db, prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return PrescriptionResponse.from_orm(prescription)

@router.post("/", response_model=PrescriptionResponse)
def create_prescription_item(prescription: PrescriptionCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_prescription = create_prescription(db, prescription)
    return PrescriptionResponse.from_orm(db_prescription)

@router.put("/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription_item(prescription_id: int, prescription: PrescriptionUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_prescription = update_prescription(db, prescription_id, prescription)
    if not db_prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return PrescriptionResponse.from_orm(db_prescription)

@router.delete("/{prescription_id}", response_model=dict)
def delete_prescription_item(prescription_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_prescription = soft_delete_prescription(db, prescription_id, current_user["id"])
    if not db_prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return {"message": "Prescription deleted successfully"}