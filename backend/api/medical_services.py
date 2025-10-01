from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.medical_services import MedicalServiceCreate, MedicalServiceUpdate, MedicalServiceResponse
from ..crud.medical_services import (
    get_medical_services, get_medical_service_by_id, get_medical_service_by_code,
    create_medical_service, update_medical_service, soft_delete_medical_service
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[MedicalServiceResponse])
def read_medical_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    services = get_medical_services(db, skip=skip, limit=limit)
    return [MedicalServiceResponse.from_orm(s) for s in services]

@router.get("/{service_id}", response_model=MedicalServiceResponse)
def read_medical_service(service_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    service = get_medical_service_by_id(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    return MedicalServiceResponse.from_orm(service)

@router.post("/", response_model=MedicalServiceResponse)
def create_medical_service_item(service: MedicalServiceCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_medical_service_by_code(db, service.service_code):
        raise HTTPException(status_code=400, detail="Service code already exists")
    db_service = create_medical_service(db, service)
    return MedicalServiceResponse.from_orm(db_service)

@router.put("/{service_id}", response_model=MedicalServiceResponse)
def update_medical_service_item(service_id: int, service: MedicalServiceUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_service = update_medical_service(db, service_id, service)
    if not db_service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    return MedicalServiceResponse.from_orm(db_service)

@router.delete("/{service_id}", response_model=dict)
def delete_medical_service_item(service_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_service = soft_delete_medical_service(db, service_id, current_user["id"])
    if not db_service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    return {"message": "Medical service deleted successfully"}