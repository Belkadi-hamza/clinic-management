from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.lab_tests import LabTestCreate, LabTestUpdate, LabTestResponse
from ..crud.lab_tests import (
    get_lab_tests, get_lab_test_by_id,
    create_lab_test, update_lab_test, soft_delete_lab_test
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[LabTestResponse])
def read_lab_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    lab_tests = get_lab_tests(db, skip=skip, limit=limit)
    return [LabTestResponse.from_orm(l) for l in lab_tests]

@router.get("/{lab_test_id}", response_model=LabTestResponse)
def read_lab_test(lab_test_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    lab_test = get_lab_test_by_id(db, lab_test_id)
    if not lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    return LabTestResponse.from_orm(lab_test)

@router.post("/", response_model=LabTestResponse)
def create_lab_test_item(lab_test: LabTestCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_lab_test = create_lab_test(db, lab_test)
    return LabTestResponse.from_orm(db_lab_test)

@router.put("/{lab_test_id}", response_model=LabTestResponse)
def update_lab_test_item(lab_test_id: int, lab_test: LabTestUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_lab_test = update_lab_test(db, lab_test_id, lab_test)
    if not db_lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    return LabTestResponse.from_orm(db_lab_test)

@router.delete("/{lab_test_id}", response_model=dict)
def delete_lab_test_item(lab_test_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_lab_test = soft_delete_lab_test(db, lab_test_id, current_user["id"])
    if not db_lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    return {"message": "Lab test deleted successfully"}