from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Tuple, Dict, Any
from ..models.banks import Bank
from ..schemas.banks import BankCreate, BankUpdate, BankImportRow

# Bank CRUD operations
def get_banks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    search: str = None
) -> Tuple[List[Bank], int]:
    """Get all banks with optional search"""
    query = db.query(Bank).filter(Bank.deleted_at == None)
    
    if search:
        search_filter = or_(
            Bank.bank_code.ilike(f"%{search}%"),
            Bank.bank_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    total = query.count()
    banks = query.order_by(Bank.bank_name).offset(skip).limit(limit).all()
    return banks, total

def get_bank_by_id(db: Session, bank_id: int) -> Optional[Bank]:
    """Get a specific bank by ID"""
    return db.query(Bank).filter(
        Bank.id == bank_id, 
        Bank.deleted_at == None
    ).first()

def get_bank_by_code(db: Session, bank_code: str) -> Optional[Bank]:
    """Get a bank by its code"""
    return db.query(Bank).filter(
        Bank.bank_code == bank_code.upper(),
        Bank.deleted_at == None
    ).first()

def create_bank(db: Session, bank: BankCreate, user_id: int) -> Tuple[Optional[Bank], Optional[str]]:
    """Create a new bank"""
    # Check if bank code already exists
    existing_bank = get_bank_by_code(db, bank.bank_code)
    if existing_bank:
        return None, f"Bank code '{bank.bank_code}' already exists"
    
    db_bank = Bank(
        bank_code=bank.bank_code.upper(),
        bank_name=bank.bank_name,
        created_by=user_id
    )
    db.add(db_bank)
    db.commit()
    db.refresh(db_bank)
    return db_bank, None

def update_bank(db: Session, bank_id: int, bank: BankUpdate, user_id: int) -> Tuple[Optional[Bank], Optional[str]]:
    """Update an existing bank"""
    db_bank = get_bank_by_id(db, bank_id)
    if not db_bank:
        return None, "Bank not found"
    
    # Check if new bank code conflicts with existing one
    if bank.bank_code and bank.bank_code != db_bank.bank_code:
        existing_bank = get_bank_by_code(db, bank.bank_code)
        if existing_bank:
            return None, f"Bank code '{bank.bank_code}' already exists"
    
    update_data = bank.dict(exclude_unset=True)
    if 'bank_code' in update_data:
        update_data['bank_code'] = update_data['bank_code'].upper()
    
    for key, value in update_data.items():
        setattr(db_bank, key, value)
    
    db_bank.updated_by = user_id
    db.commit()
    db.refresh(db_bank)
    return db_bank, None

def soft_delete_bank(db: Session, bank_id: int, user_id: int) -> Tuple[Optional[Bank], Optional[str]]:
    """Soft delete a bank"""
    db_bank = get_bank_by_id(db, bank_id)
    if not db_bank:
        return None, "Bank not found"
    
    # Check if bank is being used in any transactions
    # This would require checking related tables like patient_payments, expenses, etc.
    # For now, we'll assume it's safe to delete
    
    db_bank.deleted_at = func.now()
    db_bank.deleted_by = user_id
    db.commit()
    return db_bank, None

def restore_bank(db: Session, bank_id: int, user_id: int) -> Tuple[Optional[Bank], Optional[str]]:
    """Restore a soft-deleted bank"""
    db_bank = db.query(Bank).filter(
        Bank.id == bank_id,
        Bank.deleted_at != None
    ).first()
    
    if not db_bank:
        return None, "Bank not found or not deleted"
    
    db_bank.deleted_at = None
    db_bank.deleted_by = None
    db_bank.updated_by = user_id
    db.commit()
    db.refresh(db_bank)
    return db_bank, None

def search_banks(db: Session, query: str, limit: int = 10) -> List[Bank]:
    """Search banks by code or name"""
    return db.query(Bank).filter(
        Bank.deleted_at == None,
        or_(
            Bank.bank_code.ilike(f"%{query}%"),
            Bank.bank_name.ilike(f"%{query}%")
        )
    ).order_by(Bank.bank_name).limit(limit).all()

def get_banks_for_dropdown(db: Session) -> List[Bank]:
    """Get simplified bank list for dropdowns"""
    return db.query(Bank).filter(
        Bank.deleted_at == None
    ).order_by(Bank.bank_name).all()

def bulk_create_banks(db: Session, banks: List[BankCreate], user_id: int) -> Dict[str, Any]:
    """Bulk create multiple banks"""
    created = []
    errors = []
    
    for bank_data in banks:
        # Check if bank code already exists
        existing_bank = get_bank_by_code(db, bank_data.bank_code)
        if existing_bank:
            errors.append({
                "bank_code": bank_data.bank_code,
                "bank_name": bank_data.bank_name,
                "error": f"Bank code '{bank_data.bank_code}' already exists"
            })
            continue
        
        try:
            db_bank = Bank(
                bank_code=bank_data.bank_code.upper(),
                bank_name=bank_data.bank_name,
                created_by=user_id
            )
            db.add(db_bank)
            created.append(db_bank)
        except Exception as e:
            errors.append({
                "bank_code": bank_data.bank_code,
                "bank_name": bank_data.bank_name,
                "error": str(e)
            })
    
    if created:
        db.commit()
        # Refresh all created banks to get their IDs
        for bank in created:
            db.refresh(bank)
    
    return {
        "created": created,
        "errors": errors,
        "total_created": len(created),
        "total_errors": len(errors)
    }

def import_banks(db: Session, import_data: List[BankImportRow], user_id: int, overwrite_existing: bool = False) -> Dict[str, Any]:
    """Import banks from external data"""
    created = []
    updated = []
    errors = []
    
    for bank_data in import_data:
        existing_bank = get_bank_by_code(db, bank_data.bank_code)
        
        if existing_bank:
            if overwrite_existing:
                # Update existing bank
                update_data = BankUpdate(
                    bank_code=bank_data.bank_code,
                    bank_name=bank_data.bank_name
                )
                updated_bank, error = update_bank(db, existing_bank.id, update_data, user_id)
                if error:
                    errors.append({
                        "bank_code": bank_data.bank_code,
                        "bank_name": bank_data.bank_name,
                        "error": error
                    })
                else:
                    updated.append(updated_bank)
            else:
                errors.append({
                    "bank_code": bank_data.bank_code,
                    "bank_name": bank_data.bank_name,
                    "error": f"Bank code '{bank_data.bank_code}' already exists"
                })
        else:
            # Create new bank
            create_data = BankCreate(
                bank_code=bank_data.bank_code,
                bank_name=bank_data.bank_name
            )
            new_bank, error = create_bank(db, create_data, user_id)
            if error:
                errors.append({
                    "bank_code": bank_data.bank_code,
                    "bank_name": bank_data.bank_name,
                    "error": error
                })
            else:
                created.append(new_bank)
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "total_created": len(created),
        "total_updated": len(updated),
        "total_errors": len(errors)
    }

def get_bank_stats(db: Session) -> Dict[str, Any]:
    """Get bank statistics"""
    total_banks = db.query(Bank).filter(Bank.deleted_at == None).count()
    
    # Get recently added banks (last 30 days)
    recently_added = db.query(Bank).filter(
        Bank.deleted_at == None,
        Bank.created_at >= func.now() - func.make_interval(days=30)
    ).order_by(Bank.created_at.desc()).limit(5).all()
    
    return {
        "total_banks": total_banks,
        "recently_added": recently_added
    }

def check_bank_usage(db: Session, bank_id: int) -> Dict[str, Any]:
    """Check if a bank is being used in any transactions"""
    # This would check related tables like:
    # - patient_payments
    # - expenses
    # - any other tables that reference banks
    
    # For now, return a placeholder response
    # In a real implementation, you would query these tables
    usage_info = {
        "is_used": False,
        "usage_count": 0,
        "usage_details": []
    }
    
    return usage_info