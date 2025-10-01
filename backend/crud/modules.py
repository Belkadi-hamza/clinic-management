from sqlalchemy.orm import Session
from ..models.modules import Module
from ..schemas.modules import ModuleCreate, ModuleUpdate

def get_modules(db: Session):
    return db.query(Module).order_by(Module.created_at.desc()).all()

def get_module_by_id(db: Session, module_id: int):
    return db.query(Module).filter(Module.id == module_id).first()

def get_module_by_name(db: Session, name: str):
    return db.query(Module).filter(Module.name == name).first()

def create_module(db: Session, module: ModuleCreate):
    db_module = Module(**module.dict())
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

def update_module(db: Session, module_id: int, module: ModuleUpdate):
    db_module = db.query(Module).filter(Module.id == module_id).first()
    if not db_module:
        return None
    for key, value in module.dict(exclude_unset=True).items():
        setattr(db_module, key, value)
    db.commit()
    db.refresh(db_module)
    return db_module

def delete_module(db: Session, module_id: int):
    db_module = db.query(Module).filter(Module.id == module_id).first()
    if not db_module:
        return None
    db.delete(db_module)
    db.commit()
    return db_module