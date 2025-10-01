from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..db import get_db
from ..schemas.visit_symptoms import (
    VisitSymptomCreate, VisitSymptomUpdate, VisitSymptomResponse,
    VisitSymptomListResponse, VisitSymptomDetailResponse,
    VisitSymptomBulkCreate, VisitSymptomBulkCreateResponse,
    SymptomAnalysisResponse, VisitSymptomsSummaryResponse,
    VisitSymptomDetailedListResponse
)
from ..crud.visit_symptoms import (
    get_visit_symptoms, get_visit_symptom_by_id, create_visit_symptom,
    update_visit_symptom, delete_visit_symptom, bulk_create_visit_symptoms,
    get_symptom_analysis, get_visit_symptoms_summary, search_visit_symptoms,
    get_patient_symptom_history
)
from ..deps import get_current_user, require_doctor_or_above

router = APIRouter()

# Visit Symptom endpoints
@router.get("/visits/{visit_id}/symptoms", response_model=VisitSymptomListResponse)
def read_visit_symptoms(
    visit_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all symptoms for a specific visit"""
    visit_symptoms, total = get_visit_symptoms(db, visit_id, skip=skip, limit=limit)
    
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
                status="Active" if vs.deleted_at is None else "Inactive",
                created_by_username=vs.creator.username if vs.creator else None
            )
        )
    
    return VisitSymptomListResponse(
        visit_symptoms=visit_symptom_responses,
        total=total
    )

@router.get("/visits/{visit_id}/symptoms/summary", response_model=VisitSymptomsSummaryResponse)
def get_visit_symptoms_summary_endpoint(
    visit_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of symptoms for a visit"""
    summary = get_visit_symptoms_summary(db, visit_id)
    
    symptoms_list = [
        VisitSymptomResponse(
            id=item["id"],
            visit_id=visit_id,
            symptom_id=item["symptom_id"],
            symptom_name=item["symptom_name"],
            symptom_code=item["symptom_code"],
            severity=item["severity"],
            duration_days=item["duration_days"],
            notes=item["notes"],
            created_at=item["created_at"],
            status="Active"
        )
        for item in summary["symptoms_list"]
    ]
    
    return VisitSymptomsSummaryResponse(
        visit_id=visit_id,
        total_symptoms=summary["total_symptoms"],
        symptoms_by_severity=summary["symptoms_by_severity"],
        symptoms_list=symptoms_list
    )

@router.get("/search", response_model=VisitSymptomDetailedListResponse)
def search_visit_symptoms_endpoint(
    patient_id: Optional[int] = Query(None),
    symptom_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search visit symptoms with various filters"""
    visit_symptoms, total = search_visit_symptoms(
        db,
        patient_id=patient_id,
        symptom_id=symptom_id,
        doctor_id=doctor_id,
        start_date=start_date,
        end_date=end_date,
        severity=severity,
        skip=skip,
        limit=limit
    )
    
    visit_symptom_responses = []
    for vs in visit_symptoms:
        visit_symptom_responses.append(
            VisitSymptomDetailResponse(
                id=vs.id,
                visit_id=vs.visit_id,
                symptom_id=vs.symptom_id,
                symptom_name=vs.symptom.symptom_name,
                symptom_code=vs.symptom.symptom_code,
                severity=vs.severity,
                duration_days=vs.duration_days,
                notes=vs.notes,
                created_at=vs.created_at,
                status="Active" if vs.deleted_at is None else "Inactive",
                created_by_username=vs.creator.username if vs.creator else None,
                patient_name=f"{vs.visit.patient.first_name} {vs.visit.patient.last_name}",
                patient_code=vs.visit.patient.patient_code,
                visit_date=vs.visit.visit_date,
                doctor_name=f"{vs.visit.doctor.first_name} {vs.visit.doctor.last_name}"
            )
        )
    
    return VisitSymptomDetailedListResponse(
        visit_symptoms=visit_symptom_responses,
        total=total
    )

@router.get("/{visit_symptom_id}", response_model=VisitSymptomResponse)
def read_visit_symptom(
    visit_symptom_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific visit symptom by ID"""
    visit_symptom = get_visit_symptom_by_id(db, visit_symptom_id)
    if not visit_symptom:
        raise HTTPException(status_code=404, detail="Visit symptom not found")
    
    return VisitSymptomResponse(
        id=visit_symptom.id,
        visit_id=visit_symptom.visit_id,
        symptom_id=visit_symptom.symptom_id,
        symptom_name=visit_symptom.symptom.symptom_name,
        symptom_code=visit_symptom.symptom.symptom_code,
        severity=visit_symptom.severity,
        duration_days=visit_symptom.duration_days,
        notes=visit_symptom.notes,
        created_at=visit_symptom.created_at,
        status="Active" if visit_symptom.deleted_at is None else "Inactive",
        created_by_username=visit_symptom.creator.username if visit_symptom.creator else None
    )

@router.post("/", response_model=VisitSymptomResponse)
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
        status="Active",
        created_by_username=db_visit_symptom.creator.username if db_visit_symptom.creator else None
    )

@router.post("/bulk", response_model=VisitSymptomBulkCreateResponse)
def bulk_create_visit_symptoms_endpoint(
    bulk_data: VisitSymptomBulkCreate,
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Bulk add multiple symptoms to a visit"""
    if not bulk_data.symptoms:
        raise HTTPException(status_code=400, detail="No symptoms provided")
    
    result = bulk_create_visit_symptoms(db, bulk_data.dict(), current_user["id"])
    
    # Convert created visit symptoms to response format
    created_symptoms = [
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
            status="Active",
            created_by_username=vs.creator.username if vs.creator else None
        )
        for vs in result["created"]
    ]
    
    return VisitSymptomBulkCreateResponse(
        created=created_symptoms,
        errors=result["errors"],
        total_created=result["total_created"],
        total_errors=result["total_errors"]
    )

@router.put("/{visit_symptom_id}", response_model=VisitSymptomResponse)
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
        status="Active",
        created_by_username=db_visit_symptom.creator.username if db_visit_symptom.creator else None
    )

@router.delete("/{visit_symptom_id}")
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

@router.get("/analysis/symptoms", response_model=List[SymptomAnalysisResponse])
def get_symptom_analysis_endpoint(
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: dict = Depends(require_doctor_or_above),
    db: Session = Depends(get_db)
):
    """Get symptom analysis for the specified period"""
    analysis_data = get_symptom_analysis(db, days)
    
    return [
        SymptomAnalysisResponse(**item)
        for item in analysis_data
    ]

@router.get("/patients/{patient_id}/symptom-history")
def get_patient_symptom_history_endpoint(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get symptom history for a patient"""
    symptom_history = get_patient_symptom_history(db, patient_id)
    
    return {
        "patient_id": patient_id,
        "symptom_history": symptom_history,
        "total_symptoms": len(symptom_history)
    }

@router.get("/symptoms/{symptom_id}/usage")
def get_symptom_usage_endpoint(
    symptom_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a specific symptom"""
    from ..crud.visit_symptoms import get_visit_symptoms_by_symptom_id
    
    visit_symptoms = get_visit_symptoms_by_symptom_id(db, symptom_id)
    
    # Get symptom details
    symptom = db.query(Symptom).filter(
        Symptom.id == symptom_id,
        Symptom.deleted_at == None
    ).first()
    
    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    
    severity_distribution = {}
    total_usage = len(visit_symptoms)
    
    for vs in visit_symptoms:
        severity = vs.severity or 'unknown'
        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
    
    return {
        "symptom_id": symptom_id,
        "symptom_code": symptom.symptom_code,
        "symptom_name": symptom.symptom_name,
        "total_usage": total_usage,
        "severity_distribution": severity_distribution,
        "first_used": min([vs.created_at for vs in visit_symptoms]) if visit_symptoms else None,
        "last_used": max([vs.created_at for vs in visit_symptoms]) if visit_symptoms else None
    }