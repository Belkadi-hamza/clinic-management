from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from typing import List, Optional, Dict, Any
from ..models.pharmacies import Pharmacy
from ..schemas.pharmacies import PharmacyCreate, PharmacyUpdate

# Pharmacy CRUD operations
def get_pharmacies(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    search: str = None,
    city: str = None,
    is_active: bool = None
):
    query = db.query(Pharmacy).filter(Pharmacy.deleted_at == None)
    
    # Apply filters
    if search:
        search_filter = or_(
            Pharmacy.pharmacy_code.ilike(f"%{search}%"),
            Pharmacy.pharmacy_name.ilike(f"%{search}%"),
            Pharmacy.owner_name.ilike(f"%{search}%"),
            Pharmacy.address.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if city:
        query = query.filter(Pharmacy.city.ilike(f"%{city}%"))
    
    if is_active is not None:
        query = query.filter(Pharmacy.is_active == is_active)
    
    total = query.count()
    pharmacies = query.order_by(Pharmacy.pharmacy_name).offset(skip).limit(limit).all()
    return pharmacies, total

def get_pharmacy_by_id(db: Session, pharmacy_id: int):
    return db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id, 
        Pharmacy.deleted_at == None
    ).first()

def get_pharmacy_by_code(db: Session, pharmacy_code: str):
    return db.query(Pharmacy).filter(
        Pharmacy.pharmacy_code == pharmacy_code.upper(),
        Pharmacy.deleted_at == None
    ).first()

def create_pharmacy(db: Session, pharmacy: PharmacyCreate, user_id: int):
    # Check if pharmacy code already exists
    existing_pharmacy = get_pharmacy_by_code(db, pharmacy.pharmacy_code)
    if existing_pharmacy:
        return None, "Pharmacy code already exists"
    
    db_pharmacy = Pharmacy(
        pharmacy_code=pharmacy.pharmacy_code.upper(),
        pharmacy_name=pharmacy.pharmacy_name,
        owner_name=pharmacy.owner_name,
        address=pharmacy.address,
        city=pharmacy.city,
        phone=pharmacy.phone,
        mobile=pharmacy.mobile,
        email=pharmacy.email,
        is_active=pharmacy.is_active,
        created_by=user_id
    )
    db.add(db_pharmacy)
    db.commit()
    db.refresh(db_pharmacy)
    return db_pharmacy, None

def update_pharmacy(db: Session, pharmacy_id: int, pharmacy: PharmacyUpdate, user_id: int):
    db_pharmacy = get_pharmacy_by_id(db, pharmacy_id)
    if not db_pharmacy:
        return None, "Pharmacy not found"
    
    # Check if new pharmacy code conflicts with existing one
    if pharmacy.pharmacy_code and pharmacy.pharmacy_code != db_pharmacy.pharmacy_code:
        existing_pharmacy = get_pharmacy_by_code(db, pharmacy.pharmacy_code)
        if existing_pharmacy:
            return None, "Pharmacy code already exists"
    
    update_data = pharmacy.dict(exclude_unset=True)
    if 'pharmacy_code' in update_data:
        update_data['pharmacy_code'] = update_data['pharmacy_code'].upper()
    
    for key, value in update_data.items():
        setattr(db_pharmacy, key, value)
    
    db_pharmacy.updated_by = user_id
    db.commit()
    db.refresh(db_pharmacy)
    return db_pharmacy, None

def soft_delete_pharmacy(db: Session, pharmacy_id: int, user_id: int):
    db_pharmacy = get_pharmacy_by_id(db, pharmacy_id)
    if not db_pharmacy:
        return None, "Pharmacy not found"
    
    db_pharmacy.deleted_at = func.now()
    db_pharmacy.deleted_by = user_id
    db.commit()
    return db_pharmacy, None

def restore_pharmacy(db: Session, pharmacy_id: int, user_id: int):
    db_pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id,
        Pharmacy.deleted_at != None
    ).first()
    
    if not db_pharmacy:
        return None, "Pharmacy not found or not deleted"
    
    db_pharmacy.deleted_at = None
    db_pharmacy.deleted_by = None
    db_pharmacy.updated_by = user_id
    db.commit()
    db.refresh(db_pharmacy)
    return db_pharmacy, None

def toggle_pharmacy_status(db: Session, pharmacy_id: int, user_id: int):
    db_pharmacy = get_pharmacy_by_id(db, pharmacy_id)
    if not db_pharmacy:
        return None, "Pharmacy not found"
    
    db_pharmacy.is_active = not db_pharmacy.is_active
    db_pharmacy.updated_by = user_id
    db.commit()
    db.refresh(db_pharmacy)
    return db_pharmacy, None

def search_pharmacies(db: Session, query: str, limit: int = 10, active_only: bool = True):
    base_query = db.query(Pharmacy).filter(Pharmacy.deleted_at == None)
    
    if active_only:
        base_query = base_query.filter(Pharmacy.is_active == True)
    
    pharmacies = base_query.filter(
        or_(
            Pharmacy.pharmacy_code.ilike(f"%{query}%"),
            Pharmacy.pharmacy_name.ilike(f"%{query}%"),
            Pharmacy.city.ilike(f"%{query}%")
        )
    ).order_by(Pharmacy.pharmacy_name).limit(limit).all()
    
    return pharmacies

def get_pharmacies_by_city(db: Session):
    """Get pharmacy count grouped by city"""
    result = db.query(
        Pharmacy.city,
        func.count(Pharmacy.id).label('count')
    ).filter(
        Pharmacy.deleted_at == None,
        Pharmacy.is_active == True
    ).group_by(Pharmacy.city).all()
    
    return [{"city": city, "count": count} for city, count in result if city]

def get_pharmacy_stats(db: Session):
    """Get comprehensive pharmacy statistics"""
    total_pharmacies = db.query(Pharmacy).filter(Pharmacy.deleted_at == None).count()
    active_pharmacies = db.query(Pharmacy).filter(
        Pharmacy.deleted_at == None,
        Pharmacy.is_active == True
    ).count()
    inactive_pharmacies = total_pharmacies - active_pharmacies
    
    pharmacies_by_city = get_pharmacies_by_city(db)
    
    recently_added = db.query(Pharmacy).filter(
        Pharmacy.deleted_at == None
    ).order_by(Pharmacy.created_at.desc()).limit(5).all()
    
    return {
        "total_pharmacies": total_pharmacies,
        "active_pharmacies": active_pharmacies,
        "inactive_pharmacies": inactive_pharmacies,
        "pharmacies_by_city": pharmacies_by_city,
        "recently_added": recently_added
    }

def get_pharmacies_for_dropdown(db: Session):
    """Get simplified pharmacy list for dropdowns"""
    return db.query(
        Pharmacy.id,
        Pharmacy.pharmacy_code,
        Pharmacy.pharmacy_name,
        Pharmacy.city,
        Pharmacy.phone,
        Pharmacy.is_active
    ).filter(
        Pharmacy.deleted_at == None,
        Pharmacy.is_active == True
    ).order_by(Pharmacy.pharmacy_name).all()

def bulk_update_pharmacy_status(
    db: Session, 
    pharmacy_ids: List[int], 
    is_active: bool, 
    user_id: int
):
    """Bulk update pharmacy status"""
    updated_count = db.query(Pharmacy).filter(
        Pharmacy.id.in_(pharmacy_ids),
        Pharmacy.deleted_at == None
    ).update(
        {"is_active": is_active, "updated_by": user_id},
        synchronize_session=False
    )
    db.commit()
    return updated_count