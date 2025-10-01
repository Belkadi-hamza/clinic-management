from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.lab_orders import LabOrderCreate, LabOrderUpdate, LabOrderResponse
from ..crud.lab_orders import (
    get_lab_orders, get_lab_order_by_id,
    create_lab_order, update_lab_order, soft_delete_lab_order
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[LabOrderResponse])
def read_lab_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    lab_orders = get_lab_orders(db, skip=skip, limit=limit)
    return [LabOrderResponse.from_orm(l) for l in lab_orders]

@router.get("/{lab_order_id}", response_model=LabOrderResponse)
def read_lab_order(lab_order_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    lab_order = get_lab_order_by_id(db, lab_order_id)
    if not lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return LabOrderResponse.from_orm(lab_order)

@router.post("/", response_model=LabOrderResponse)
def create_lab_order_item(lab_order: LabOrderCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_lab_order = create_lab_order(db, lab_order)
    return LabOrderResponse.from_orm(db_lab_order)

@router.put("/{lab_order_id}", response_model=LabOrderResponse)
def update_lab_order_item(lab_order_id: int, lab_order: LabOrderUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_lab_order = update_lab_order(db, lab_order_id, lab_order)
    if not db_lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return LabOrderResponse.from_orm(db_lab_order)

@router.delete("/{lab_order_id}", response_model=dict)
def delete_lab_order_item(lab_order_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_lab_order = soft_delete_lab_order(db, lab_order_id, current_user["id"])
    if not db_lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return {"message": "Lab order deleted successfully"}