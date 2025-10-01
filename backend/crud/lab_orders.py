from sqlalchemy.orm import Session
from ..models.lab_orders import LabOrder
from ..schemas.lab_orders import LabOrderCreate, LabOrderUpdate

def get_lab_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(LabOrder).filter(LabOrder.deleted_at == None).order_by(LabOrder.created_at.desc()).offset(skip).limit(limit).all()

def get_lab_order_by_id(db: Session, lab_order_id: int):
    return db.query(LabOrder).filter(LabOrder.id == lab_order_id, LabOrder.deleted_at == None).first()

def create_lab_order(db: Session, lab_order: LabOrderCreate):
    db_lab_order = LabOrder(**lab_order.dict())
    db.add(db_lab_order)
    db.commit()
    db.refresh(db_lab_order)
    return db_lab_order

def update_lab_order(db: Session, lab_order_id: int, lab_order: LabOrderUpdate):
    db_lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id, LabOrder.deleted_at == None).first()
    if not db_lab_order:
        return None
    for key, value in lab_order.dict(exclude_unset=True).items():
        setattr(db_lab_order, key, value)
    db.commit()
    db.refresh(db_lab_order)
    return db_lab_order

def soft_delete_lab_order(db: Session, lab_order_id: int, deleted_by: int):
    db_lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id, LabOrder.deleted_at == None).first()
    if not db_lab_order:
        return None
    db_lab_order.deleted_at = db.func.now()
    db_lab_order.deleted_by = deleted_by
    db.commit()
    return db_lab_order