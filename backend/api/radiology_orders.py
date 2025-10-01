from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.radiology_orders import RadiologyOrderCreate, RadiologyOrderUpdate, RadiologyOrderResponse
from ..crud.radiology_orders import (
    get_radiology_orders, get_radiology_order_by_id,
    create_radiology_order, update_radiology_order, soft_delete_radiology_order
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[RadiologyOrderResponse])
def read_radiology_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    orders = get_radiology_orders(db, skip=skip, limit=limit)
    return [RadiologyOrderResponse.from_orm(o) for o in orders]

@router.get("/{order_id}", response_model=RadiologyOrderResponse)
def read_radiology_order(order_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    order = get_radiology_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Radiology order not found")
    return RadiologyOrderResponse.from_orm(order)

@router.post("/", response_model=RadiologyOrderResponse)
def create_radiology_order_item(order: RadiologyOrderCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_order = create_radiology_order(db, order)
    return RadiologyOrderResponse.from_orm(db_order)

@router.put("/{order_id}", response_model=RadiologyOrderResponse)
def update_radiology_order_item(order_id: int, order: RadiologyOrderUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_order = update_radiology_order(db, order_id, order)
    if not db_order:
        raise HTTPException(status_code=404, detail="Radiology order not found")
    return RadiologyOrderResponse.from_orm(db_order)

@router.delete("/{order_id}", response_model=dict)
def delete_radiology_order_item(order_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_order = soft_delete_radiology_order(db, order_id, current_user["id"])
    if not db_order:
        raise HTTPException(status_code=404, detail="Radiology order not found")
    return {"message": "Radiology order deleted successfully"}