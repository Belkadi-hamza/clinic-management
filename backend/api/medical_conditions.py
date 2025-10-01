from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.medical_conditions import MedicalConditionCreate, MedicalConditionUpdate, MedicalConditionResponse
from ..crud.medical_conditions import (
    get_medical_conditions, get_medical_condition_by_id, get_medical_condition_by_code,
    create_medical_condition, update_medical_condition, soft_delete_medical_condition
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[MedicalConditionResponse])
def read_medical_conditions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    conditions = get_medical_conditions(db, skip=skip, limit=limit)
    return [MedicalConditionResponse.from_orm(c) for c in conditions]

@router.get("/{condition_id}", response_model=MedicalConditionResponse)
def read_medical_condition(condition_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    condition = get_medical_condition_by_id(db, condition_id)
    if not condition:
        raise HTTPException(status_code=404, detail="Medical condition not found")
    return MedicalConditionResponse.from_orm(condition)

@router.post("/", response_model=MedicalConditionResponse)
def create_medical_condition_item(condition: MedicalConditionCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_medical_condition_by_code(db, condition.condition_code):
        raise HTTPException(status_code=400, detail="Condition code already exists")
    db_condition = create_medical_condition(db, condition)
    return MedicalConditionResponse.from_orm(db_condition)

@router.put("/{condition_id}", response_model=MedicalConditionResponse)
def update_medical_condition_item(condition_id: int, condition: MedicalConditionUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_condition = update_medical_condition(db, condition_id, condition)
    if not db_condition:
        raise HTTPException(status_code=404, detail="Medical condition not found")
    return MedicalConditionResponse.from_orm(db_condition)

@router.delete("/{condition_id}", response_model=dict)
def delete_medical_condition_item(condition_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_condition = soft_delete_medical_condition(db, condition_id, current_user["id"])
    if not db_condition:
        raise HTTPException(status_code=404, detail="Medical condition not found")
    return {"message": "Medical condition deleted successfully"}