from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import get_db
from ..schemas.symptoms import (
    SymptomCreate, SymptomUpdate, SymptomResponse, SymptomListResponse,
    VisitSymptomCreate, VisitSymptomUpdate, VisitSymptomResponse, VisitSymptomListResponse,
    SymptomWithUsageResponse
)
from ..crud.symptoms import (
    get_symptoms, get_symptom_by_id, create_symptom, update_symptom,
    soft_delete_symptom, restore_symptom, get_symptoms_with_usage,
    get_visit_symptoms, create_visit_symptom, update_visit_symptom,
    delete_visit_symptom, search_symptoms
)
from ..deps import get_current_user, require_doctor_or_above

router = APIRouter()

# Symptom endpoints
@router.get("/", response_model=SymptomListResponse)
def read_symptoms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all symptoms with pagination and search"""
    symptoms, total = get_symptoms(db, skip=skip, limit=limit, search=search)
    
    symptom_responses = [
        SymptomResponse(
            **symptom.__dict__,
            status="Active" if symptom.deleted_at is None else "Inactive"
        )
        for symptom in symptoms
    ]
    
    return SymptomListResponse(
        symptoms=symptom_responses,
        total=total
    )

@router.get("/with-usage", response_model=List[SymptomWithUsageResponse])
def read_symptoms_with_usage(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get symptoms with their usage count"""
    symptoms_with_usage = get_symptoms_with_usage(db, skip=skip, limit=limit)
    
    return [
        SymptomWithUsageResponse(
            **symptom,
            status="Active" if symptom['deleted_at'] is None else "Inactive"
        )
        for symptom in symptoms_with_usage
    ]

@router.get("/search", response_model=List[SymptomResponse])
def search_symptoms_endpoint(
    q: str = Query(..., min_length=1, description="Search query for symptoms"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search symptoms by code or name"""
    symptoms = search_symptoms(db, query=q, limit=limit)
    
    return [
        SymptomResponse(
            **symptom.__dict__,
            status="Active" if symptom.deleted_at is None else "Inactive"
        )
        for symptom in symptoms
    ]

@router.get("/{symptom_id}", response_model=SymptomResponse)
def read_symptom(
    symptom_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific symptom by ID"""
    symptom = get_symptom_by_id(db, symptom_id)
    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    
    return SymptomResponse(
        **symptom.__dict__,
        status="Active" if symptom.deleted_at is None else "Inactive"
    )

@router.post("/", response_model=SymptomResponse)
def create_new_symptom(
    symptom: SymptomCreate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Create a new symptom"""
    db_symptom, error = create_symptom(db, symptom, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return SymptomResponse(
        **db_symptom.__dict__,
        status="Active"
    )

@router.put("/{symptom_id}", response_model=SymptomResponse)
def update_symptom_endpoint(
    symptom_id: int,
    symptom: SymptomUpdate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Update a symptom"""
    db_symptom, error = update_symptom(db, symptom_id, symptom, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return SymptomResponse(
        **db_symptom.__dict__,
        status="Active" if db_symptom.deleted_at is None else "Inactive"
    )

@router.delete("/{symptom_id}")
def delete_symptom(
    symptom_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Soft delete a symptom"""
    db_symptom, error = soft_delete_symptom(db, symptom_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "Symptom deleted successfully"}

@router.post("/{symptom_id}/restore", response_model=SymptomResponse)
def restore_symptom_endpoint(
    symptom_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted symptom"""
    db_symptom, error = restore_symptom(db, symptom_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return SymptomResponse(
        **db_symptom.__dict__,
        status="Active"
    )

# Visit Symptom endpoints
@router.get("/visits/{visit_id}/symptoms", response_model=VisitSymptomListResponse)
def read_visit_symptoms(
    visit_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all symptoms for a specific visit"""
    visit_symptoms = get_visit_symptoms(db, visit_id)
    
    visit_symptom_responses = []
    for vs in visit_symptoms:
        visit_symptom_responses.append(
            VisitSymptomResponse(
                id=vs.id,
                visit_id=vs.visit_id,
                symptom_id=vs.symptom_id,
                symptom_name=vs.symptom.symptom_name,
                symptom_code=vs.symptom.symptom_code,
                severity=vs.severity,
                duration_days=vs.duration_days,
                notes=vs.notes,
                created_at=vs.created_at,
                status="Active" if vs.deleted_at is None else "Inactive"
            )
        )
    
    return VisitSymptomListResponse(
        visit_symptoms=visit_symptom_responses,
        total=len(visit_symptom_responses)
    )

@router.post("/visits/symptoms", response_model=VisitSymptomResponse)
def create_new_visit_symptom(
    visit_symptom: VisitSymptomCreate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Add a symptom to a visit"""
    db_visit_symptom, error = create_visit_symptom(db, visit_symptom, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return VisitSymptomResponse(
        id=db_visit_symptom.id,
        visit_id=db_visit_symptom.visit_id,
        symptom_id=db_visit_symptom.symptom_id,
        symptom_name=db_visit_symptom.symptom.symptom_name,
        symptom_code=db_visit_symptom.symptom.symptom_code,
        severity=db_visit_symptom.severity,
        duration_days=db_visit_symptom.duration_days,
        notes=db_visit_symptom.notes,
        created_at=db_visit_symptom.created_at,
        status="Active"
    )

@router.put("/visits/symptoms/{visit_symptom_id}", response_model=VisitSymptomResponse)
def update_visit_symptom_endpoint(
    visit_symptom_id: int,
    visit_symptom: VisitSymptomUpdate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Update a visit symptom"""
    db_visit_symptom, error = update_visit_symptom(db, visit_symptom_id, visit_symptom, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return VisitSymptomResponse(
        id=db_visit_symptom.id,
        visit_id=db_visit_symptom.visit_id,
        symptom_id=db_visit_symptom.symptom_id,
        symptom_name=db_visit_symptom.symptom.symptom_name,
        symptom_code=db_visit_symptom.symptom.symptom_code,
        severity=db_visit_symptom.severity,
        duration_days=db_visit_symptom.duration_days,
        notes=db_visit_symptom.notes,
        created_at=db_visit_symptom.created_at,
        status="Active"
    )

@router.delete("/visits/symptoms/{visit_symptom_id}")
def delete_visit_symptom_endpoint(
    visit_symptom_id: int,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Remove a symptom from a visit"""
    db_visit_symptom, error = delete_visit_symptom(db, visit_symptom_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "Symptom removed from visit successfully"}