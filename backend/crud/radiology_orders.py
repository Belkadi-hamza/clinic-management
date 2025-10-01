from sqlalchemy.orm import Session
from ..models.radiology_orders import RadiologyOrder
from ..schemas.radiology_orders import RadiologyOrderCreate, RadiologyOrderUpdate

def get_radiology_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RadiologyOrder).filter(RadiologyOrder.deleted_at == None).order_by(RadiologyOrder.created_at.desc()).offset(skip).limit(limit).all()

def get_radiology_order_by_id(db: Session, order_id: int):
    return db.query(RadiologyOrder).filter(RadiologyOrder.id == order_id, RadiologyOrder.deleted_at == None).first()

def create_radiology_order(db: Session, order: RadiologyOrderCreate):
    db_order = RadiologyOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_radiology_order(db: Session, order_id: int, order: RadiologyOrderUpdate):
    db_order = db.query(RadiologyOrder).filter(RadiologyOrder.id == order_id, RadiologyOrder.deleted_at == None).first()
    if not db_order:
        return None
    for key, value in order.dict(exclude_unset=True).items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

def soft_delete_radiology_order(db: Session, order_id: int, deleted_by: int):
    db_order = db.query(RadiologyOrder).filter(RadiologyOrder.id == order_id, RadiologyOrder.deleted_at == None).first()
    if not db_order:
        return None
    db_order.deleted_at = db.func.now()
    db_order.deleted_by = deleted_by
    db.commit()
    return db_order