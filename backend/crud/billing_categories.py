from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, date
import logging

from ..models.billing_categories import BillingCategory, MedicalService, VisitService
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..models.patient_visits import PatientVisit
from ..schemas.billing_categories import (
    BillingCategoryCreate, BillingCategoryUpdate, MedicalServiceCreate, MedicalServiceUpdate,
    VisitServiceCreate, VisitServiceUpdate, BillingCategorySearch, MedicalServiceSearch,
    VisitServiceSearch, ServicePriceUpdate
)

logger = logging.getLogger(__name__)

# Billing Category CRUD operations
def generate_category_code(db: Session):
    """Generate unique billing category code"""
    prefix = "BCAT"
    
    # Find the highest number
    max_category = db.query(BillingCategory).order_by(BillingCategory.id.desc()).first()
    next_num = (max_category.id + 1) if max_category else 1
    
    return f"{prefix}{next_num:04d}"

def get_billing_categories(db: Session, skip: int = 0, limit: int = 100):
    """Get all billing categories"""
    return db.query(BillingCategory).filter(BillingCategory.deleted_at == None)\
        .order_by(BillingCategory.category_name.asc())\
        .offset(skip).limit(limit).all()

def get_billing_category_by_id(db: Session, category_id: int):
    """Get billing category by ID"""
    return db.query(BillingCategory).filter(
        BillingCategory.id == category_id,
        BillingCategory.deleted_at == None
    ).first()

def get_billing_category_by_code(db: Session, category_code: str):
    """Get billing category by code"""
    return db.query(BillingCategory).filter(
        BillingCategory.category_code == category_code,
        BillingCategory.deleted_at == None
    ).first()

def get_root_categories(db: Session):
    """Get all root categories (no parent)"""
    return db.query(BillingCategory).filter(
        BillingCategory.parent_category_id == None,
        BillingCategory.deleted_at == None
    ).order_by(BillingCategory.category_name.asc()).all()

def get_sub_categories(db: Session, parent_category_id: int):
    """Get all sub-categories for a parent category"""
    return db.query(BillingCategory).filter(
        BillingCategory.parent_category_id == parent_category_id,
        BillingCategory.deleted_at == None
    ).order_by(BillingCategory.category_name.asc()).all()

def get_category_tree(db: Session):
    """Get complete category hierarchy"""
    root_categories = get_root_categories(db)
    tree = []
    
    for category in root_categories:
        tree.append(_build_category_tree(db, category))
    
    return tree

def _build_category_tree(db: Session, category: BillingCategory):
    """Recursively build category tree"""
    sub_categories = get_sub_categories(db, category.id)
    services = get_medical_services_by_category(db, category.id)
    
    tree_node = {
        'category': category,
        'children': [],
        'services': services
    }
    
    for sub_category in sub_categories:
        tree_node['children'].append(_build_category_tree(db, sub_category))
    
    return tree_node

def search_billing_categories(db: Session, search: BillingCategorySearch, skip: int = 0, limit: int = 100):
    """Search billing categories with filters"""
    query = db.query(BillingCategory).filter(BillingCategory.deleted_at == None)
    
    if search.category_name:
        query = query.filter(BillingCategory.category_name.ilike(f"%{search.category_name}%"))
    
    if search.is_active is not None:
        query = query.filter(BillingCategory.is_active == search.is_active)
    
    if search.parent_category_id is not None:
        if search.parent_category_id == 0:  # Special case for root categories
            query = query.filter(BillingCategory.parent_category_id == None)
        else:
            query = query.filter(BillingCategory.parent_category_id == search.parent_category_id)
    
    return query.order_by(BillingCategory.category_name.asc())\
        .offset(skip).limit(limit).all()

def create_billing_category(db: Session, category: BillingCategoryCreate, user_id: int):
    """Create new billing category"""
    category_code = generate_category_code(db)
    db_category = BillingCategory(**category.dict(), category_code=category_code, created_by=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_billing_category(db: Session, category_id: int, category: BillingCategoryUpdate, user_id: int):
    """Update billing category"""
    db_category = db.query(BillingCategory).filter(
        BillingCategory.id == category_id,
        BillingCategory.deleted_at == None
    ).first()
    
    if not db_category:
        return None
    
    # Prevent circular reference
    if category.parent_category_id == category_id:
        raise ValueError("Category cannot be its own parent")
    
    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)
    
    db_category.updated_by = user_id
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_billing_category(db: Session, category_id: int, user_id: int):
    """Soft delete billing category"""
    db_category = db.query(BillingCategory).filter(
        BillingCategory.id == category_id,
        BillingCategory.deleted_at == None
    ).first()
    
    if not db_category:
        return None
    
    # Check if category has sub-categories
    sub_categories = get_sub_categories(db, category_id)
    if sub_categories:
        raise ValueError("Cannot delete category with sub-categories")
    
    # Check if category has services
    services = get_medical_services_by_category(db, category_id)
    if services:
        raise ValueError("Cannot delete category with associated services")
    
    db_category.deleted_at = func.now()
    db_category.deleted_by = user_id
    db.commit()
    return db_category

# Medical Service CRUD operations
def generate_service_code(db: Session):
    """Generate unique medical service code"""
    prefix = "MSVC"
    
    # Find the highest number
    max_service = db.query(MedicalService).order_by(MedicalService.id.desc()).first()
    next_num = (max_service.id + 1) if max_service else 1
    
    return f"{prefix}{next_num:04d}"

def get_medical_services(db: Session, skip: int = 0, limit: int = 100):
    """Get all medical services"""
    return db.query(MedicalService).filter(MedicalService.deleted_at == None)\
        .order_by(MedicalService.service_name.asc())\
        .offset(skip).limit(limit).all()

def get_medical_service_by_id(db: Session, service_id: int):
    """Get medical service by ID"""
    return db.query(MedicalService).filter(
        MedicalService.id == service_id,
        MedicalService.deleted_at == None
    ).first()

def get_medical_service_by_code(db: Session, service_code: str):
    """Get medical service by code"""
    return db.query(MedicalService).filter(
        MedicalService.service_code == service_code,
        MedicalService.deleted_at == None
    ).first()

def get_medical_services_by_category(db: Session, category_id: int):
    """Get all medical services for a category"""
    return db.query(MedicalService).filter(
        MedicalService.category_id == category_id,
        MedicalService.deleted_at == None
    ).order_by(MedicalService.service_name.asc()).all()

def search_medical_services(db: Session, search: MedicalServiceSearch, skip: int = 0, limit: int = 100):
    """Search medical services with filters"""
    query = db.query(MedicalService).filter(MedicalService.deleted_at == None)
    
    if search.service_name:
        query = query.filter(MedicalService.service_name.ilike(f"%{search.service_name}%"))
    
    if search.category_id:
        query = query.filter(MedicalService.category_id == search.category_id)
    
    if search.is_active is not None:
        query = query.filter(MedicalService.is_active == search.is_active)
    
    if search.min_price:
        query = query.filter(MedicalService.standard_price >= search.min_price)
    
    if search.max_price:
        query = query.filter(MedicalService.standard_price <= search.max_price)
    
    if search.service_type:
        if search.service_type == 'lab':
            query = query.filter(MedicalService.is_lab_service == True)
        elif search.service_type == 'radiology':
            query = query.filter(MedicalService.is_radiology_service == True)
        elif search.service_type == 'procedure':
            query = query.filter(MedicalService.is_procedure == True)
        elif search.service_type == 'consultation':
            query = query.filter(
                MedicalService.is_lab_service == False,
                MedicalService.is_radiology_service == False,
                MedicalService.is_procedure == False
            )
    
    return query.order_by(MedicalService.service_name.asc())\
        .offset(skip).limit(limit).all()

def create_medical_service(db: Session, service: MedicalServiceCreate, user_id: int):
    """Create new medical service"""
    service_code = generate_service_code(db)
    db_service = MedicalService(**service.dict(), service_code=service_code, created_by=user_id)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_medical_service(db: Session, service_id: int, service: MedicalServiceUpdate, user_id: int):
    """Update medical service"""
    db_service = db.query(MedicalService).filter(
        MedicalService.id == service_id,
        MedicalService.deleted_at == None
    ).first()
    
    if not db_service:
        return None
    
    for key, value in service.dict(exclude_unset=True).items():
        setattr(db_service, key, value)
    
    db_service.updated_by = user_id
    db.commit()
    db.refresh(db_service)
    return db_service

def update_service_price(db: Session, price_update: ServicePriceUpdate, user_id: int):
    """Update medical service price"""
    db_service = db.query(MedicalService).filter(
        MedicalService.id == price_update.service_id,
        MedicalService.deleted_at == None
    ).first()
    
    if not db_service:
        return None
    
    db_service.standard_price = price_update.new_price
    db_service.updated_by = user_id
    db.commit()
    db.refresh(db_service)
    return db_service

def bulk_update_service_prices(db: Session, price_updates: List[ServicePriceUpdate], user_id: int):
    """Update multiple service prices"""
    updated_services = []
    
    for price_update in price_updates:
        db_service = update_service_price(db, price_update, user_id)
        if db_service:
            updated_services.append(db_service)
    
    return updated_services

def delete_medical_service(db: Session, service_id: int, user_id: int):
    """Soft delete medical service"""
    db_service = db.query(MedicalService).filter(
        MedicalService.id == service_id,
        MedicalService.deleted_at == None
    ).first()
    
    if not db_service:
        return None
    
    # Check if service has been used in visits
    visit_services = db.query(VisitService).filter(
        VisitService.service_id == service_id,
        VisitService.deleted_at == None
    ).first()
    
    if visit_services:
        raise ValueError("Cannot delete service that has been used in patient visits")
    
    db_service.deleted_at = func.now()
    db_service.deleted_by = user_id
    db.commit()
    return db_service

# Visit Service CRUD operations
def get_visit_services(db: Session, skip: int = 0, limit: int = 100):
    """Get all visit services"""
    return db.query(VisitService).filter(VisitService.deleted_at == None)\
        .order_by(VisitService.created_at.desc())\
        .offset(skip).limit(limit).all()

def get_visit_service_by_id(db: Session, visit_service_id: int):
    """Get visit service by ID"""
    return db.query(VisitService).filter(
        VisitService.id == visit_service_id,
        VisitService.deleted_at == None
    ).first()

def get_visit_services_by_visit(db: Session, visit_id: int):
    """Get all visit services for a specific visit"""
    return db.query(VisitService).filter(
        VisitService.visit_id == visit_id,
        VisitService.deleted_at == None
    ).order_by(VisitService.created_at.asc()).all()

def get_visit_services_by_patient(db: Session, patient_id: int):
    """Get all visit services for a specific patient"""
    return db.query(VisitService).join(PatientVisit).filter(
        PatientVisit.patient_id == patient_id,
        VisitService.deleted_at == None
    ).order_by(VisitService.created_at.desc()).all()

def search_visit_services(db: Session, search: VisitServiceSearch, skip: int = 0, limit: int = 100):
    """Search visit services with filters"""
    query = db.query(VisitService).filter(VisitService.deleted_at == None)
    
    if search.visit_id:
        query = query.filter(VisitService.visit_id == search.visit_id)
    
    if search.service_id:
        query = query.filter(VisitService.service_id == search.service_id)
    
    if search.patient_name:
        query = query.join(PatientVisit).join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.date_from:
        query = query.filter(VisitService.service_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(VisitService.service_date <= search.date_to)
    
    return query.order_by(VisitService.service_date.desc())\
        .offset(skip).limit(limit).all()

def create_visit_service(db: Session, visit_service: VisitServiceCreate, user_id: int):
    """Create new visit service"""
    # Calculate final price
    total_before_discount = visit_service.actual_price * visit_service.quantity
    discount_from_percentage = total_before_discount * (visit_service.discount_percentage / 100)
    total_discount = visit_service.discount_amount + discount_from_percentage
    final_price = total_before_discount - total_discount + visit_service.tax_amount
    
    db_visit_service = VisitService(
        **visit_service.dict(),
        final_price=final_price,
        created_by=user_id
    )
    db.add(db_visit_service)
    db.commit()
    db.refresh(db_visit_service)
    return db_visit_service

def update_visit_service(db: Session, visit_service_id: int, visit_service: VisitServiceUpdate, user_id: int):
    """Update visit service"""
    db_visit_service = db.query(VisitService).filter(
        VisitService.id == visit_service_id,
        VisitService.deleted_at == None
    ).first()
    
    if not db_visit_service:
        return None
    
    # Store original values for price calculation
    original_values = {
        'actual_price': db_visit_service.actual_price,
        'quantity': db_visit_service.quantity,
        'discount_amount': db_visit_service.discount_amount,
        'discount_percentage': db_visit_service.discount_percentage,
        'tax_amount': db_visit_service.tax_amount
    }
    
    for key, value in visit_service.dict(exclude_unset=True).items():
        setattr(db_visit_service, key, value)
    
    # Recalculate final price if any price-related fields changed
    price_fields = ['actual_price', 'quantity', 'discount_amount', 'discount_percentage', 'tax_amount']
    if any(field in visit_service.dict(exclude_unset=True) for field in price_fields):
        actual_price = visit_service.actual_price if visit_service.actual_price is not None else original_values['actual_price']
        quantity = visit_service.quantity if visit_service.quantity is not None else original_values['quantity']
        discount_amount = visit_service.discount_amount if visit_service.discount_amount is not None else original_values['discount_amount']
        discount_percentage = visit_service.discount_percentage if visit_service.discount_percentage is not None else original_values['discount_percentage']
        tax_amount = visit_service.tax_amount if visit_service.tax_amount is not None else original_values['tax_amount']
        
        total_before_discount = actual_price * quantity
        discount_from_percentage = total_before_discount * (discount_percentage / 100)
        total_discount = discount_amount + discount_from_percentage
        final_price = total_before_discount - total_discount + tax_amount
        
        db_visit_service.final_price = final_price
    
    db_visit_service.updated_by = user_id
    db.commit()
    db.refresh(db_visit_service)
    return db_visit_service

def delete_visit_service(db: Session, visit_service_id: int, user_id: int):
    """Soft delete visit service"""
    db_visit_service = db.query(VisitService).filter(
        VisitService.id == visit_service_id,
        VisitService.deleted_at == None
    ).first()
    
    if not db_visit_service:
        return None
    
    db_visit_service.deleted_at = func.now()
    db_visit_service.deleted_by = user_id
    db.commit()
    return db_visit_service

# Statistics and Reports
def get_category_stats(db: Session):
    """Get statistics for all billing categories"""
    categories = db.query(BillingCategory).filter(BillingCategory.deleted_at == None).all()
    
    stats = []
    for category in categories:
        services = get_medical_services_by_category(db, category.id)
        active_services = [s for s in services if s.is_active]
        
        # Calculate revenue from visit services
        revenue_result = db.query(
            func.sum(VisitService.final_price).label('total_revenue')
        ).join(MedicalService).filter(
            MedicalService.category_id == category.id,
            VisitService.deleted_at == None
        ).first()
        
        total_revenue = revenue_result.total_revenue or 0
        
        # Find most used service
        most_used = db.query(
            MedicalService.service_name,
            func.count(VisitService.id).label('usage_count')
        ).join(VisitService).filter(
            MedicalService.category_id == category.id,
            VisitService.deleted_at == None
        ).group_by(MedicalService.service_name)\
         .order_by(desc('usage_count')).first()
        
        stats.append({
            'category_id': category.id,
            'category_name': category.category_name,
            'total_services': len(services),
            'active_services': len(active_services),
            'total_revenue': total_revenue,
            'average_price': total_revenue / len(services) if services else 0,
            'most_used_service': most_used.service_name if most_used else None
        })
    
    return stats

def get_service_usage_stats(db: Session, days: int = 30):
    """Get service usage statistics"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    usage_stats = db.query(
        MedicalService.id,
        MedicalService.service_name,
        func.count(VisitService.id).label('usage_count'),
        func.sum(VisitService.final_price).label('total_revenue'),
        func.avg(VisitService.final_price).label('average_price')
    ).join(VisitService).filter(
        VisitService.deleted_at == None,
        VisitService.service_date >= start_date
    ).group_by(MedicalService.id, MedicalService.service_name)\
     .order_by(desc('usage_count')).all()
    
    return [
        {
            'service_id': stat.id,
            'service_name': stat.service_name,
            'usage_count': stat.usage_count,
            'total_revenue': stat.total_revenue or 0,
            'average_price': stat.average_price or 0
        }
        for stat in usage_stats
    ]

def get_revenue_by_category(db: Session, start_date: date = None, end_date: date = None):
    """Get revenue breakdown by category"""
    query = db.query(
        BillingCategory.category_name,
        func.sum(VisitService.final_price).label('revenue')
    ).join(MedicalService, BillingCategory.id == MedicalService.category_id)\
     .join(VisitService, MedicalService.id == VisitService.service_id)\
     .filter(VisitService.deleted_at == None)
    
    if start_date:
        query = query.filter(VisitService.service_date >= start_date)
    if end_date:
        query = query.filter(VisitService.service_date <= end_date)
    
    results = query.group_by(BillingCategory.category_name)\
                  .order_by(desc('revenue')).all()
    
    return [{'category_name': r.category_name, 'revenue': r.revenue or 0} for r in results]