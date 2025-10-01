from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..db import get_db
from ..schemas.banks import (
    BankCreate, BankUpdate, BankResponse, BankListResponse,
    BankSimpleResponse, BankSearchResponse, BankBulkCreate,
    BankBulkCreateResponse, BankImportRequest
)
from ..crud.banks import (
    get_banks, get_bank_by_id, create_bank, update_bank,
    soft_delete_bank, restore_bank, search_banks,
    get_banks_for_dropdown, bulk_create_banks, import_banks,
    get_bank_stats, check_bank_usage
)
from ..deps import get_current_user, require_admin_or_super, require_accountant_or_above

router = APIRouter()
logger = logging.getLogger(__name__)

# Bank endpoints
@router.get("/", response_model=BankListResponse)
def read_banks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all banks with pagination and search"""
    banks, total = get_banks(db, skip=skip, limit=limit, search=search)
    
    bank_responses = [
        BankResponse(
            **bank.__dict__,
            status="Active" if bank.deleted_at is None else "Inactive",
            created_by_username=bank.creator.username if bank.creator else None,
            updated_by_username=bank.updater.username if bank.updater else None
        )
        for bank in banks
    ]
    
    return BankListResponse(
        banks=bank_responses,
        total=total
    )

@router.get("/dropdown", response_model=List[BankSimpleResponse])
def read_banks_dropdown(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get simplified bank list for dropdowns"""
    banks = get_banks_for_dropdown(db)
    
    return [
        BankSimpleResponse(
            id=bank.id,
            bank_code=bank.bank_code,
            bank_name=bank.bank_name
        )
        for bank in banks
    ]

@router.get("/search", response_model=BankSearchResponse)
def search_banks_endpoint(
    q: str = Query(..., min_length=1, description="Search query for banks"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search banks by code or name"""
    banks = search_banks(db, query=q, limit=limit)
    
    bank_responses = [
        BankSimpleResponse(
            id=bank.id,
            bank_code=bank.bank_code,
            bank_name=bank.bank_name
        )
        for bank in banks
    ]
    
    return BankSearchResponse(
        banks=bank_responses,
        total=len(bank_responses)
    )

@router.get("/stats")
def get_bank_statistics(
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Get bank statistics"""
    stats = get_bank_stats(db)
    
    recently_added = [
        BankSimpleResponse(
            id=bank.id,
            bank_code=bank.bank_code,
            bank_name=bank.bank_name
        )
        for bank in stats["recently_added"]
    ]
    
    return {
        "total_banks": stats["total_banks"],
        "recently_added": recently_added
    }

@router.get("/{bank_id}", response_model=BankResponse)
def read_bank(
    bank_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bank by ID"""
    bank = get_bank_by_id(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    return BankResponse(
        **bank.__dict__,
        status="Active" if bank.deleted_at is None else "Inactive",
        created_by_username=bank.creator.username if bank.creator else None,
        updated_by_username=bank.updater.username if bank.updater else None
    )

@router.get("/{bank_id}/usage")
def check_bank_usage_endpoint(
    bank_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Check if a bank is being used in any transactions"""
    bank = get_bank_by_id(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    usage_info = check_bank_usage(db, bank_id)
    return {
        "bank_id": bank_id,
        "bank_code": bank.bank_code,
        "bank_name": bank.bank_name,
        **usage_info
    }

@router.post("/", response_model=BankResponse)
def create_new_bank(
    bank: BankCreate,
    current_user: dict = Depends(require_accountant_or_above),
    db: Session = Depends(get_db)
):
    """Create a new bank"""
    db_bank, error = create_bank(db, bank, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return BankResponse(
        **db_bank.__dict__,
        status="Active",
        created_by_username=db_bank.creator.username if db_bank.creator else None
    )

@router.post("/bulk", response_model=BankBulkCreateResponse)
def bulk_create_banks_endpoint(
    bulk_data: BankBulkCreate,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Bulk create multiple banks"""
    if not bulk_data.banks:
        raise HTTPException(status_code=400, detail="No banks provided")
    
    result = bulk_create_banks(db, bulk_data.banks, current_user["id"])
    
    # Convert created banks to response format
    created_banks = [
        BankResponse(
            **bank.__dict__,
            status="Active",
            created_by_username=bank.creator.username if bank.creator else None
        )
        for bank in result["created"]
    ]
    
    return BankBulkCreateResponse(
        created=created_banks,
        errors=result["errors"],
        total_created=result["total_created"],
        total_errors=result["total_errors"]
    )

@router.post("/import")
def import_banks_endpoint(
    import_request: BankImportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Import banks from external data"""
    if not import_request.banks:
        raise HTTPException(status_code=400, detail="No banks provided for import")
    
    result = import_banks(
        db, 
        import_request.banks, 
        current_user["id"],
        import_request.overwrite_existing
    )
    
    # Convert results to response format
    created_banks = [
        BankResponse(
            **bank.__dict__,
            status="Active",
            created_by_username=bank.creator.username if bank.creator else None
        )
        for bank in result["created"]
    ]
    
    updated_banks = [
        BankResponse(
            **bank.__dict__,
            status="Active",
            created_by_username=bank.creator.username if bank.creator else None,
            updated_by_username=bank.updater.username if bank.updater else None
        )
        for bank in result["updated"]
    ]
    
    return {
        "message": f"Import completed: {result['total_created']} created, {result['total_updated']} updated, {result['total_errors']} errors",
        "created": created_banks,
        "updated": updated_banks,
        "errors": result["errors"],
        "summary": {
            "total_created": result["total_created"],
            "total_updated": result["total_updated"],
            "total_errors": result["total_errors"]
        }
    }

@router.put("/{bank_id}", response_model=BankResponse)
def update_bank_endpoint(
    bank_id: int,
    bank: BankUpdate,
    current_user: dict = Depends(require_accountant_or_above),
    db: Session = Depends(get_db)
):
    """Update a bank"""
    db_bank, error = update_bank(db, bank_id, bank, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return BankResponse(
        **db_bank.__dict__,
        status="Active" if db_bank.deleted_at is None else "Inactive",
        created_by_username=db_bank.creator.username if db_bank.creator else None,
        updated_by_username=db_bank.updater.username if db_bank.updater else None
    )

@router.delete("/{bank_id}")
def delete_bank(
    bank_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Soft delete a bank"""
    # First check if bank is being used
    usage_info = check_bank_usage(db, bank_id)
    if usage_info["is_used"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete bank. It is being used in {usage_info['usage_count']} transaction(s)."
        )
    
    db_bank, error = soft_delete_bank(db, bank_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "Bank deleted successfully"}

@router.post("/{bank_id}/restore", response_model=BankResponse)
def restore_bank_endpoint(
    bank_id: int,
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted bank"""
    db_bank, error = restore_bank(db, bank_id, current_user["id"])
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return BankResponse(
        **db_bank.__dict__,
        status="Active",
        created_by_username=db_bank.creator.username if db_bank.creator else None,
        updated_by_username=db_bank.updater.username if db_bank.updater else None
    )

@router.get("/code/{bank_code}", response_model=BankResponse)
def read_bank_by_code(
    bank_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a bank by its code"""
    from ..crud.banks import get_bank_by_code
    
    bank = get_bank_by_code(db, bank_code)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    return BankResponse(
        **bank.__dict__,
        status="Active" if bank.deleted_at is None else "Inactive",
        created_by_username=bank.creator.username if bank.creator else None,
        updated_by_username=bank.updater.username if bank.updater else None
    )

@router.post("/validate-code")
def validate_bank_code(
    bank_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate if a bank code is available"""
    from ..crud.banks import get_bank_by_code
    
    existing_bank = get_bank_by_code(db, bank_code)
    
    return {
        "bank_code": bank_code,
        "is_available": existing_bank is None,
        "existing_bank": existing_bank.bank_name if existing_bank else None
    }