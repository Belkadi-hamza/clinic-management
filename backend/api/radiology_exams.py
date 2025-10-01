from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.radiology_exams import RadiologyExamCreate, RadiologyExamUpdate, RadiologyExamResponse
from ..crud.radiology_exams import (
    get_radiology_exams, get_radiology_exam_by_id,
    create_radiology_exam, update_radiology_exam, soft_delete_radiology_exam
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[RadiologyExamResponse])
def read_radiology_exams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    exams = get_radiology_exams(db, skip=skip, limit=limit)
    return [RadiologyExamResponse.from_orm(e) for e in exams]

@router.get("/{exam_id}", response_model=RadiologyExamResponse)
def read_radiology_exam(exam_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    exam = get_radiology_exam_by_id(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Radiology exam not found")
    return RadiologyExamResponse.from_orm(exam)

@router.post("/", response_model=RadiologyExamResponse)
def create_radiology_exam_item(exam: RadiologyExamCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_exam = create_radiology_exam(db, exam)
    return RadiologyExamResponse.from_orm(db_exam)

@router.put("/{exam_id}", response_model=RadiologyExamResponse)
def update_radiology_exam_item(exam_id: int, exam: RadiologyExamUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_exam = update_radiology_exam(db, exam_id, exam)
    if not db_exam:
        raise HTTPException(status_code=404, detail="Radiology exam not found")
    return RadiologyExamResponse.from_orm(db_exam)

@router.delete("/{exam_id}", response_model=dict)
def delete_radiology_exam_item(exam_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_exam = soft_delete_radiology_exam(db, exam_id, current_user["id"])
    if not db_exam:
        raise HTTPException(status_code=404, detail="Radiology exam not found")
    return {"message": "Radiology exam deleted successfully"}