from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import get_db
from ..schemas.doctor_specialties import (
    DoctorSpecialtyCreate, DoctorSpecialtyUpdate, DoctorSpecialtyResponse,
    DoctorSpecialtyListResponse, DoctorSpecialtyWithDoctorResponse,
    DoctorSpecialtyBulkCreate, DoctorSpecialtyBulkCreateResponse,
    SpecialtyStatsResponse, DoctorSpecialtySummaryResponse,
    DoctorSpecialtyDetailedListResponse, SpecialtySearchResponse
)
from ..crud.doctor_specialties import (
    get_doctor_specialties, get_doctor_specialty_by_id, create_doctor_specialty,
    update_doctor_specialty, delete_doctor_specialty, bulk_create_doctor_specialties,
    get_all_specialties, search_specialties, get_specialty_stats,
    get_doctors_by_specialty, get_doctor_specialties_summary,
    search_doctor_specialties, replace_doctor_specialties
)
from ..deps import get_current_user, require_admin_or_super, require_doctor_or_above

router = APIRouter()

# Doctor Specialty endpoints
@router.get("/", response_model=DoctorSpecialtyListResponse)
def read_doctor_specialties(
    doctor_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all doctor specialties with optional doctor filter"""
    doctor_specialties, total = get_doctor_specialties(
        db, doctor_id=doctor_id, skip=skip, limit=limit
    )
    
    doctor_specialty_responses = [
        DoctorSpecialtyResponse(
            id=ds.id,
            doctor_id=ds.doctor_id,
            specialty=ds.specialty,
            created_at=ds.created_at,
            status="Active" if ds.deleted_at is None else "Inactive",
            created_by_username=ds.creator.username if ds.creator else None
        )
        for ds in doctor_specialties
    ]
    
    return DoctorSpecialtyListResponse(
        doctor_specialties=doctor_specialty_responses,
        total=total
    )

@router.get("/search", response_model=DoctorSpecialtyDetailedListResponse)
def search_doctor_specialties_endpoint(
    specialty: Optional[str] = Query(None),
    doctor_name: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search doctor specialties with various filters"""
    doctor_specialties, total = search_doctor_specialties(
        db, specialty=specialty, doctor_name=doctor_name, skip=skip, limit=limit
    )
    
    doctor_specialty_responses = []
    for ds in doctor_specialties:
        doctor_specialty_responses.append(
            DoctorSpecialtyWithDoctorResponse(
                id=ds.id,
                doctor_id=ds.doctor_id,
                specialty=ds.specialty,
                created_at=ds.created_at,
                status="Active" if ds.deleted_at is None else "Inactive",
                created_by_username=ds.creator.username if ds.creator else None,
                doctor_name=f"{ds.doctor.first_name} {ds.doctor.last_name}",
                doctor_code=ds.doctor.doctor_code
            )
        )
    
    return DoctorSpecialtyDetailedListResponse(
        doctor_specialties=doctor_specialty_responses,
        total=total
    )

@router.get("/specialties", response_model=SpecialtySearchResponse)
def get_all_specialties_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all unique specialty names"""
    specialties = get_all_specialties(db)
    
    return SpecialtySearchResponse(
        specialties=specialties,
        total=len(specialties)
    )

@router.get("/specialties/search", response_model=SpecialtySearchResponse)
def search_specialties_endpoint(
    q: str = Query(..., min_length=1, description="Search query for specialties"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search specialties by name"""
    specialties = search_specialties(db, query=q, limit=limit)
    
    return SpecialtySearchResponse(
        specialties=specialties,
        total=len(specialties)
    )

@router.get("/stats", response_model=List[SpecialtyStatsResponse])
def get_specialty_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics for specialties"""
    stats = get_specialty_stats(db)
    
    return [
        SpecialtyStatsResponse(**stat)
        for stat in stats
    ]

@router.get("/doctors/{doctor_id}/summary", response_model=DoctorSpecialtySummaryResponse)
def get_doctor_specialties_summary_endpoint(
    doctor_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of specialties for a doctor"""
    summary = get_doctor_specialties_summary(db, doctor_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return DoctorSpecialtySummaryResponse(**summary)

@router.get("/specialties/{specialty}/doctors")
def get_doctors_by_specialty_endpoint(
    specialty: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all doctors with a specific specialty"""
    doctors = get_doctors_by_specialty(db, specialty)
    
    doctor_list = [
        {
            "id": doctor.id,
            "doctor_code": doctor.doctor_code,
            "first_name": doctor.first_name,
            "last_name": doctor.last_name,
            "specialization": doctor.specialization,
            "email": doctor.email,
            "phone": doctor.phone,
            "is_active": doctor.is_active
        }
        for doctor in doctors
    ]
    
    return {
        "specialty": specialty,
        "doctors": doctor_list,
        "total_doctors": len(doctor_list)
    }

@router.get("/{doctor_specialty_id}", response_model=DoctorSpecialtyResponse)
def read_doctor_specialty(
    doctor_specialty_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific doctor specialty by ID"""
    doctor_specialty = get_doctor_specialty_by_id(db, doctor_specialty_id)
    if not doctor_specialty:
        raise HTTPException(status_code=404, detail="Doctor specialty not found")
    
    return DoctorSpecialtyResponse(
        id=doctor_specialty.id,
        doctor_id=doctor_specialty.doctor_id,
        specialty=doctor_specialty.specialty,
        created_at=doctor_specialty.created_at,
        status="Active" if doctor_specialty.deleted_at is None else "Inactive",
        created_by_username=doctor_specialty.creator.username if doctor_specialty.creator else None
    )

@router.post("/", response_model=DoctorSpecialtyResponse)
def create_new_doctor_specialty(
    doctor_specialty: DoctorSpecialtyCreate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Add a specialty to a doctor"""
    db_doctor_specialty, error = create_doctor_specialty(db, doctor_specialty, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return DoctorSpecialtyResponse(
        id=db_doctor_specialty.id,
        doctor_id=db_doctor_specialty.doctor_id,
        specialty=db_doctor_specialty.specialty,
        created_at=db_doctor_specialty.created_at,
        status="Active",
        created_by_username=db_doctor_specialty.creator.username if db_doctor_specialty.creator else None
    )

@router.post("/bulk", response_model=DoctorSpecialtyBulkCreateResponse)
def bulk_create_doctor_specialties_endpoint(
    bulk_data: DoctorSpecialtyBulkCreate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Bulk add multiple specialties to a doctor"""
    if not bulk_data.specialties:
        raise HTTPException(status_code=400, detail="No specialties provided")
    
    result = bulk_create_doctor_specialties(db, bulk_data.dict(), current_user["id"])
    
    # Convert created doctor specialties to response format
    created_specialties = [
        DoctorSpecialtyResponse(
            id=ds.id,
            doctor_id=ds.doctor_id,
            specialty=ds.specialty,
            created_at=ds.created_at,
            status="Active",
            created_by_username=ds.creator.username if ds.creator else None
        )
        for ds in result["created"]
    ]
    
    return DoctorSpecialtyBulkCreateResponse(
        created=created_specialties,
        errors=result["errors"],
        total_created=result["total_created"],
        total_errors=result["total_errors"]
    )

@router.put("/{doctor_specialty_id}", response_model=DoctorSpecialtyResponse)
def update_doctor_specialty_endpoint(
    doctor_specialty_id: int,
    doctor_specialty: DoctorSpecialtyUpdate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Update a doctor specialty"""
    db_doctor_specialty, error = update_doctor_specialty(db, doctor_specialty_id, doctor_specialty, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return DoctorSpecialtyResponse(
        id=db_doctor_specialty.id,
        doctor_id=db_doctor_specialty.doctor_id,
        specialty=db_doctor_specialty.specialty,
        created_at=db_doctor_specialty.created_at,
        status="Active",
        created_by_username=db_doctor_specialty.creator.username if db_doctor_specialty.creator else None
    )

@router.delete("/{doctor_specialty_id}")
def delete_doctor_specialty_endpoint(
    doctor_specialty_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Remove a specialty from a doctor"""
    db_doctor_specialty, error = delete_doctor_specialty(db, doctor_specialty_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "Doctor specialty deleted successfully"}

@router.post("/doctors/{doctor_id}/replace-specialties")
def replace_doctor_specialties_endpoint(
    doctor_id: int,
    specialties: List[str],
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Replace all specialties for a doctor"""
    if not specialties:
        raise HTTPException(status_code=400, detail="No specialties provided")
    
    result = replace_doctor_specialties(db, doctor_id, specialties, current_user["id"])
    
    return {
        "message": f"Successfully replaced doctor specialties: {result['total_created']} added, {result['deleted_count']} removed",
        "deleted_count": result["deleted_count"],
        "created_count": result["total_created"],
        "error_count": result["total_errors"]
    }

@router.get("/doctors/{doctor_id}/specialties", response_model=List[DoctorSpecialtyResponse])
def get_doctor_specialties_endpoint(
    doctor_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all specialties for a specific doctor"""
    doctor_specialties = get_doctor_specialties_by_doctor(db, doctor_id)
    
    return [
        DoctorSpecialtyResponse(
            id=ds.id,
            doctor_id=ds.doctor_id,
            specialty=ds.specialty,
            created_at=ds.created_at,
            status="Active" if ds.deleted_at is None else "Inactive",
            created_by_username=ds.creator.username if ds.creator else None
        )
        for ds in doctor_specialties
    ]

@router.post("/doctors/{doctor_id}/specialties", response_model=DoctorSpecialtyResponse)
def add_doctor_specialty(
    doctor_id: int,
    specialty: str,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Add a specialty to a doctor using path parameters"""
    doctor_specialty_data = DoctorSpecialtyCreate(
        doctor_id=doctor_id,
        specialty=specialty
    )
    
    db_doctor_specialty, error = create_doctor_specialty(db, doctor_specialty_data, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return DoctorSpecialtyResponse(
        id=db_doctor_specialty.id,
        doctor_id=db_doctor_specialty.doctor_id,
        specialty=db_doctor_specialty.specialty,
        created_at=db_doctor_specialty.created_at,
        status="Active",
        created_by_username=db_doctor_specialty.creator.username if db_doctor_specialty.creator else None
    )