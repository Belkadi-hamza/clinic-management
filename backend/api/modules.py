from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.modules import ModuleCreate, ModuleUpdate, ModuleResponse
from ..crud.modules import (
    get_modules, get_module_by_id, get_module_by_name,
    create_module, update_module, delete_module
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[ModuleResponse])
def read_modules(current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    modules = get_modules(db)
    return [ModuleResponse.from_orm(m) for m in modules]

@router.get("/{module_id}", response_model=ModuleResponse)
def read_module(module_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    module = get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return ModuleResponse.from_orm(module)

@router.post("/", response_model=ModuleResponse)
def create_module_item(module: ModuleCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_module_by_name(db, module.name):
        raise HTTPException(status_code=400, detail="Module name already exists")
    db_module = create_module(db, module)
    return ModuleResponse.from_orm(db_module)

@router.put("/{module_id}", response_model=ModuleResponse)
def update_module_item(module_id: int, module: ModuleUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_module = update_module(db, module_id, module)
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")
    return ModuleResponse.from_orm(db_module)

@router.delete("/{module_id}", response_model=dict)
def delete_module_item(module_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_module = delete_module(db, module_id)
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"message": "Module deleted successfully"}