from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.patient_visits import PatientVisitCreate, PatientVisitUpdate, PatientVisitResponse
from ..crud.patient_visits import (
    get_patient_visits, get_patient_visit_by_id, get_patient_visit_by_code,
    create_patient_visit, update_patient_visit, soft_delete_patient_visit
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PatientVisitResponse])
def read_patient_visits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    visits = get_patient_visits(db, skip=skip, limit=limit)
    return [PatientVisitResponse.from_orm(v) for v in visits]

@router.get("/{visit_id}", response_model=PatientVisitResponse)
def read_patient_visit(visit_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    visit = get_patient_visit_by_id(db, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Patient visit not found")
    return PatientVisitResponse.from_orm(visit)

@router.post("/", response_model=PatientVisitResponse)
def create_patient_visit_item(visit: PatientVisitCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_patient_visit_by_code(db, visit.visit_code):
        raise HTTPException(status_code=400, detail="Visit code already exists")
    db_visit = create_patient_visit(db, visit)
    return PatientVisitResponse.from_orm(db_visit)

@router.put("/{visit_id}", response_model=PatientVisitResponse)
def update_patient_visit_item(visit_id: int, visit: PatientVisitUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_visit = update_patient_visit(db, visit_id, visit)
    if not db_visit:
        raise HTTPException(status_code=404, detail="Patient visit not found")
    return PatientVisitResponse.from_orm(db_visit)

@router.delete("/{visit_id}", response_model=dict)
def delete_patient_visit_item(visit_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_visit = soft_delete_patient_visit(db, visit_id, current_user["id"])
    if not db_visit:
        raise HTTPException(status_code=404, detail="Patient visit not found")
    return {"message": "Patient visit deleted successfully"}