from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import get_db
from ..schemas.pharmacies import (
    PharmacyCreate, PharmacyUpdate, PharmacyResponse, PharmacyListResponse,
    PharmacySimpleResponse, PharmacySearchResponse, PharmacyStatsResponse
)
from ..crud.pharmacies import (
    get_pharmacies, get_pharmacy_by_id, create_pharmacy, update_pharmacy,
    soft_delete_pharmacy, restore_pharmacy, toggle_pharmacy_status,
    search_pharmacies, get_pharmacy_stats, get_pharmacies_for_dropdown,
    bulk_update_pharmacy_status
)
from ..deps import get_current_user, require_admin_or_super, require_pharmacist_or_above

router = APIRouter()

# Pharmacy endpoints
@router.get("/", response_model=PharmacyListResponse)
def read_pharmacies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    city: str = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pharmacies with pagination and filtering"""
    pharmacies, total = get_pharmacies(
        db, 
        skip=skip, 
        limit=limit, 
        search=search,
        city=city,
        is_active=is_active
    )
    
    # Count active/inactive for stats
    active_count = len([p for p in pharmacies if p.is_active])
    inactive_count = len(pharmacies) - active_count
    
    pharmacy_responses = [
        PharmacyResponse(
            **pharmacy.__dict__,
            status="Active" if pharmacy.deleted_at is None else "Inactive",
            created_by_username=pharmacy.creator.username if pharmacy.creator else None,
            updated_by_username=pharmacy.updater.username if pharmacy.updater else None
        )
        for pharmacy in pharmacies
    ]
    
    return PharmacyListResponse(
        pharmacies=pharmacy_responses,
        total=total,
        active_count=active_count,
        inactive_count=inactive_count
    )

@router.get("/dropdown", response_model=List[PharmacySimpleResponse])
def read_pharmacies_dropdown(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get simplified pharmacy list for dropdowns"""
    pharmacies = get_pharmacies_for_dropdown(db)
    
    return [
        PharmacySimpleResponse(
            id=pharmacy.id,
            pharmacy_code=pharmacy.pharmacy_code,
            pharmacy_name=pharmacy.pharmacy_name,
            city=pharmacy.city,
            phone=pharmacy.phone,
            is_active=pharmacy.is_active
        )
        for pharmacy in pharmacies
    ]

@router.get("/search", response_model=PharmacySearchResponse)
def search_pharmacies_endpoint(
    q: str = Query(..., min_length=1, description="Search query for pharmacies"),
    limit: int = Query(10, ge=1, le=50),
    active_only: bool = Query(True, description="Only return active pharmacies"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search pharmacies by code, name, or city"""
    pharmacies = search_pharmacies(db, query=q, limit=limit, active_only=active_only)
    
    pharmacy_responses = [
        PharmacySimpleResponse(
            id=pharmacy.id,
            pharmacy_code=pharmacy.pharmacy_code,
            pharmacy_name=pharmacy.pharmacy_name,
            city=pharmacy.city,
            phone=pharmacy.phone,
            is_active=pharmacy.is_active
        )
        for pharmacy in pharmacies
    ]
    
    return PharmacySearchResponse(
        pharmacies=pharmacy_responses,
        total=len(pharmacy_responses)
    )

@router.get("/stats", response_model=PharmacyStatsResponse)
def get_pharmacy_statistics(
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Get pharmacy statistics"""
    stats = get_pharmacy_stats(db)
    
    recently_added = [
        PharmacySimpleResponse(
            id=pharmacy.id,
            pharmacy_code=pharmacy.pharmacy_code,
            pharmacy_name=pharmacy.pharmacy_name,
            city=pharmacy.city,
            phone=pharmacy.phone,
            is_active=pharmacy.is_active
        )
        for pharmacy in stats["recently_added"]
    ]
    
    return PharmacyStatsResponse(
        total_pharmacies=stats["total_pharmacies"],
        active_pharmacies=stats["active_pharmacies"],
        inactive_pharmacies=stats["inactive_pharmacies"],
        pharmacies_by_city=stats["pharmacies_by_city"],
        recently_added=recently_added
    )

@router.get("/{pharmacy_id}", response_model=PharmacyResponse)
def read_pharmacy(
    pharmacy_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific pharmacy by ID"""
    pharmacy = get_pharmacy_by_id(db, pharmacy_id)
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    return PharmacyResponse(
        **pharmacy.__dict__,
        status="Active" if pharmacy.deleted_at is None else "Inactive",
        created_by_username=pharmacy.creator.username if pharmacy.creator else None,
        updated_by_username=pharmacy.updater.username if pharmacy.updater else None
    )

@router.post("/", response_model=PharmacyResponse)
def create_new_pharmacy(
    pharmacy: PharmacyCreate,
    current_user: dict = Depends(require_pharmacist_or_above),
    db: Session = Depends(get_db)
):
    """Create a new pharmacy"""
    db_pharmacy, error = create_pharmacy(db, pharmacy, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return PharmacyResponse(
        **db_pharmacy.__dict__,
        status="Active",
        created_by_username=db_pharmacy.creator.username if db_pharmacy.creator else None
    )

@router.put("/{pharmacy_id}", response_model=PharmacyResponse)
def update_pharmacy_endpoint(
    pharmacy_id: int,
    pharmacy: PharmacyUpdate,
    current_user: dict = Depends(require_pharmacist_or_above),
    db: Session = Depends(get_db)
):
    """Update a pharmacy"""
    db_pharmacy, error = update_pharmacy(db, pharmacy_id, pharmacy, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return PharmacyResponse(
        **db_pharmacy.__dict__,
        status="Active" if db_pharmacy.deleted_at is None else "Inactive",
        created_by_username=db_pharmacy.creator.username if db_pharmacy.creator else None,
        updated_by_username=db_pharmacy.updater.username if db_pharmacy.updater else None
    )

@router.delete("/{pharmacy_id}")
def delete_pharmacy(
    pharmacy_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Soft delete a pharmacy"""
    db_pharmacy, error = soft_delete_pharmacy(db, pharmacy_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "Pharmacy deleted successfully"}

@router.post("/{pharmacy_id}/restore", response_model=PharmacyResponse)
def restore_pharmacy_endpoint(
    pharmacy_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted pharmacy"""
    db_pharmacy, error = restore_pharmacy(db, pharmacy_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return PharmacyResponse(
        **db_pharmacy.__dict__,
        status="Active",
        created_by_username=db_pharmacy.creator.username if db_pharmacy.creator else None,
        updated_by_username=db_pharmacy.updater.username if db_pharmacy.updater else None
    )

@router.patch("/{pharmacy_id}/toggle-status", response_model=PharmacyResponse)
def toggle_pharmacy_status_endpoint(
    pharmacy_id: int,
    current_user: dict = Depends(require_pharmacist_or_above),
    db: Session = Depends(get_db)
):
    """Toggle pharmacy active status"""
    db_pharmacy, error = toggle_pharmacy_status(db, pharmacy_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    action = "activated" if db_pharmacy.is_active else "deactivated"
    
    return PharmacyResponse(
        **db_pharmacy.__dict__,
        status="Active" if db_pharmacy.deleted_at is None else "Inactive",
        created_by_username=db_pharmacy.creator.username if db_pharmacy.creator else None,
        updated_by_username=db_pharmacy.updater.username if db_pharmacy.updater else None
    )

@router.post("/bulk-update-status")
def bulk_update_pharmacy_status_endpoint(
    pharmacy_ids: List[int],
    is_active: bool,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Bulk update pharmacy status"""
    if not pharmacy_ids:
        raise HTTPException(status_code=400, detail="No pharmacy IDs provided")
    
    updated_count = bulk_update_pharmacy_status(db, pharmacy_ids, is_active, current_user["id"])
    
    action = "activated" if is_active else "deactivated"
    return {
        "message": f"Successfully {action} {updated_count} pharmacy(s)",
        "updated_count": updated_count
    }

@router.get("/city/{city}", response_model=List[PharmacySimpleResponse])
def get_pharmacies_by_city_endpoint(
    city: str,
    active_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pharmacies by city"""
    pharmacies, total = get_pharmacies(db, city=city, is_active=active_only if active_only else None)
    
    return [
        PharmacySimpleResponse(
            id=pharmacy.id,
            pharmacy_code=pharmacy.pharmacy_code,
            pharmacy_name=pharmacy.pharmacy_name,
            city=pharmacy.city,
            phone=pharmacy.phone,
            is_active=pharmacy.is_active
        )
        for pharmacy in pharmacies
    ]