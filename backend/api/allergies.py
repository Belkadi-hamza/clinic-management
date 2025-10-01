from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.allergies import AllergyCreate, AllergyUpdate, AllergyResponse
from ..crud.allergies import (
    get_allergies, get_allergy_by_id,
    create_allergy, update_allergy, soft_delete_allergy
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[AllergyResponse])
def read_allergies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    allergies = get_allergies(db, skip=skip, limit=limit)
    return [AllergyResponse.from_orm(a) for a in allergies]

@router.get("/{allergy_id}", response_model=AllergyResponse)
def read_allergy(allergy_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    allergy = get_allergy_by_id(db, allergy_id)
    if not allergy:
        raise HTTPException(status_code=404, detail="Allergy not found")
    return AllergyResponse.from_orm(allergy)

@router.post("/", response_model=AllergyResponse)
def create_allergy_item(allergy: AllergyCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_allergy = create_allergy(db, allergy)
    return AllergyResponse.from_orm(db_allergy)

@router.put("/{allergy_id}", response_model=AllergyResponse)
def update_allergy_item(allergy_id: int, allergy: AllergyUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_allergy = update_allergy(db, allergy_id, allergy)
    if not db_allergy:
        raise HTTPException(status_code=404, detail="Allergy not found")
    return AllergyResponse.from_orm(db_allergy)

@router.delete("/{allergy_id}", response_model=dict)
def delete_allergy_item(allergy_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_allergy = soft_delete_allergy(db, allergy_id, current_user["id"])
    if not db_allergy:
        raise HTTPException(status_code=404, detail="Allergy not found")
    return {"message": "Allergy deleted successfully"}