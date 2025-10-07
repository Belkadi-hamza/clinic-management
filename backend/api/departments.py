from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..crud import departments as crud
from ..schemas import departments as schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.DepartmentOut])
def read_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_departments(db, skip=skip, limit=limit)


@router.get("/{department_id}", response_model=schemas.DepartmentOut)
def read_department(department_id: int, db: Session = Depends(get_db)):
    db_department = crud.get_department(db, department_id)
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department


@router.post("/", response_model=schemas.DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    return crud.create_department(db, department)


@router.put("/{department_id}", response_model=schemas.DepartmentOut)
def update_department(department_id: int, department: schemas.DepartmentUpdate, db: Session = Depends(get_db)):
    db_department = crud.update_department(db, department_id, department)
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department


@router.delete("/{department_id}", response_model=schemas.DepartmentOut)
def delete_department(department_id: int, deleted_by: int, db: Session = Depends(get_db)):
    db_department = crud.delete_department(db, department_id, deleted_by)
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department
