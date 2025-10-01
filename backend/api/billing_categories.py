from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal

from ..db import get_db
from ..schemas.billing_categories import (
    BillingCategoryCreate, BillingCategoryUpdate, BillingCategoryResponse,
    BillingCategoryWithChildren, BillingCategoryTree, BillingCategorySearch,
    MedicalServiceCreate, MedicalServiceUpdate, MedicalServiceResponse, MedicalServiceSearch,
    VisitServiceCreate, VisitServiceUpdate, VisitServiceResponse, VisitServiceSearch,
    ServicePriceUpdate, BulkServicePriceUpdate, CategoryStats, ServiceUsageStats
)
from ..crud.billing_categories import (
    get_billing_categories, get_billing_category_by_id, get_billing_category_by_code,
    get_root_categories, get_sub_categories, get_category_tree, search_billing_categories,
    create_billing_category, update_billing_category, delete_billing_category,
    get_medical_services, get_medical_service_by_id, get_medical_service_by_code,
    get_medical_services_by_category, search_medical_services, create_medical_service,
    update_medical_service, update_service_price, bulk_update_service_prices, delete_medical_service,
    get_visit_services, get_visit_service_by_id, get_visit_services_by_visit,
    get_visit_services_by_patient, search_visit_services, create_visit_service,
    update_visit_service, delete_visit_service,
    get_category_stats, get_service_usage_stats, get_revenue_by_category
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouter()

# Billing Category Endpoints
@router.get("/categories/", response_model=List[BillingCategoryResponse])
def read_billing_categories(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all billing categories"""
    require_permission(current_user, "billing", "read")
    categories = get_billing_categories(db, skip=skip, limit=limit)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = BillingCategoryResponse.from_orm(category)
        
        # Add parent category name
        if category.parent_category:
            enhanced_data.parent_category_name = category.parent_category.category_name
        
        # Count sub-categories
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Count services
        services = get_medical_services_by_category(db, category.id)
        enhanced_data.service_count = len(services)
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

@router.get("/categories/root", response_model=List[BillingCategoryResponse])
def read_root_categories(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all root categories (no parent)"""
    require_permission(current_user, "billing", "read")
    categories = get_root_categories(db)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = BillingCategoryResponse.from_orm(category)
        
        # Count sub-categories
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Count services
        services = get_medical_services_by_category(db, category.id)
        enhanced_data.service_count = len(services)
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

@router.get("/categories/{category_id}", response_model=BillingCategoryWithChildren)
def read_billing_category(
    category_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing category by ID with children and services"""
    require_permission(current_user, "billing", "read")
    category = get_billing_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Billing category not found")
    
    enhanced_data = BillingCategoryWithChildren.from_orm(category)
    
    # Add parent category name
    if category.parent_category:
        enhanced_data.parent_category_name = category.parent_category.category_name
    
    # Get sub-categories
    sub_categories = get_sub_categories(db, category_id)
    enhanced_data.sub_categories = [
        BillingCategoryResponse.from_orm(sub_cat) for sub_cat in sub_categories
    ]
    
    # Get medical services
    services = get_medical_services_by_category(db, category_id)
    enhanced_data.medical_services = [
        MedicalServiceResponse.from_orm(service) for service in services
    ]
    
    return enhanced_data

@router.get("/categories/tree/hierarchy", response_model=List[BillingCategoryTree])
def read_category_tree(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete category hierarchy tree"""
    require_permission(current_user, "billing", "read")
    tree = get_category_tree(db)
    return tree

@router.post("/categories/", response_model=BillingCategoryResponse)
def create_billing_category_endpoint(
    category: BillingCategoryCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new billing category"""
    require_permission(current_user, "billing", "create")
    
    # Validate parent category if provided
    if category.parent_category_id:
        parent_category = get_billing_category_by_id(db, category.parent_category_id)
        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    db_category = create_billing_category(db, category, current_user.id)
    
    enhanced_data = BillingCategoryResponse.from_orm(db_category)
    
    # Add parent category name
    if db_category.parent_category:
        enhanced_data.parent_category_name = db_category.parent_category.category_name
    
    return enhanced_data

@router.put("/categories/{category_id}", response_model=BillingCategoryResponse)
def update_billing_category_endpoint(
    category_id: int,
    category: BillingCategoryUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update billing category"""
    require_permission(current_user, "billing", "update")
    try:
        db_category = update_billing_category(db, category_id, category, current_user.id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Billing category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = BillingCategoryResponse.from_orm(db_category)
    
    # Add parent category name
    if db_category.parent_category:
        enhanced_data.parent_category_name = db_category.parent_category.category_name
    
    # Count sub-categories
    sub_categories = get_sub_categories(db, category_id)
    enhanced_data.sub_category_count = len(sub_categories)
    
    # Count services
    services = get_medical_services_by_category(db, category_id)
    enhanced_data.service_count = len(services)
    
    return enhanced_data

@router.delete("/categories/{category_id}")
def delete_billing_category_endpoint(
    category_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete billing category"""
    require_permission(current_user, "billing", "delete")
    try:
        db_category = delete_billing_category(db, category_id, current_user.id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Billing category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Billing category deleted successfully"}

@router.post("/categories/search/", response_model=List[BillingCategoryResponse])
def search_billing_categories_endpoint(
    search: BillingCategorySearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search billing categories with filters"""
    require_permission(current_user, "billing", "read")
    categories = search_billing_categories(db, search, skip=skip, limit=limit)
    
    enhanced_categories = []
    for category in categories:
        enhanced_data = BillingCategoryResponse.from_orm(category)
        
        # Add parent category name
        if category.parent_category:
            enhanced_data.parent_category_name = category.parent_category.category_name
        
        # Count sub-categories
        sub_categories = get_sub_categories(db, category.id)
        enhanced_data.sub_category_count = len(sub_categories)
        
        # Count services
        services = get_medical_services_by_category(db, category.id)
        enhanced_data.service_count = len(services)
        
        enhanced_categories.append(enhanced_data)
    
    return enhanced_categories

# Medical Service Endpoints
@router.get("/services/", response_model=List[MedicalServiceResponse])
def read_medical_services(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical services"""
    require_permission(current_user, "billing", "read")
    services = get_medical_services(db, skip=skip, limit=limit)
    
    enhanced_services = []
    for service in services:
        enhanced_data = MedicalServiceResponse.from_orm(service)
        
        # Add category information
        if service.billing_category:
            enhanced_data.category_name = service.billing_category.category_name
            enhanced_data.category_code = service.billing_category.category_code
        
        enhanced_services.append(enhanced_data)
    
    return enhanced_services

@router.get("/services/{service_id}", response_model=MedicalServiceResponse)
def read_medical_service(
    service_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical service by ID"""
    require_permission(current_user, "billing", "read")
    service = get_medical_service_by_id(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    
    enhanced_data = MedicalServiceResponse.from_orm(service)
    
    # Add category information
    if service.billing_category:
        enhanced_data.category_name = service.billing_category.category_name
        enhanced_data.category_code = service.billing_category.category_code
    
    return enhanced_data

@router.post("/services/", response_model=MedicalServiceResponse)
def create_medical_service_endpoint(
    service: MedicalServiceCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new medical service"""
    require_permission(current_user, "billing", "create")
    
    # Validate category if provided
    if service.category_id:
        category = get_billing_category_by_id(db, service.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Billing category not found")
    
    db_service = create_medical_service(db, service, current_user.id)
    
    enhanced_data = MedicalServiceResponse.from_orm(db_service)
    
    # Add category information
    if db_service.billing_category:
        enhanced_data.category_name = db_service.billing_category.category_name
        enhanced_data.category_code = db_service.billing_category.category_code
    
    return enhanced_data

@router.put("/services/{service_id}", response_model=MedicalServiceResponse)
def update_medical_service_endpoint(
    service_id: int,
    service: MedicalServiceUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medical service"""
    require_permission(current_user, "billing", "update")
    db_service = update_medical_service(db, service_id, service, current_user.id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    
    enhanced_data = MedicalServiceResponse.from_orm(db_service)
    
    # Add category information
    if db_service.billing_category:
        enhanced_data.category_name = db_service.billing_category.category_name
        enhanced_data.category_code = db_service.billing_category.category_code
    
    return enhanced_data

@router.patch("/services/prices/update")
def update_service_price_endpoint(
    price_update: ServicePriceUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medical service price"""
    require_permission(current_user, "billing", "update")
    db_service = update_service_price(db, price_update, current_user.id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    
    return {"message": "Service price updated successfully", "new_price": price_update.new_price}

@router.patch("/services/prices/bulk-update")
def bulk_update_service_prices_endpoint(
    bulk_update: BulkServicePriceUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update multiple service prices"""
    require_permission(current_user, "billing", "update")
    updated_services = bulk_update_service_prices(db, bulk_update.price_updates, current_user.id)
    
    return {
        "message": f"Updated prices for {len(updated_services)} services",
        "updated_services": [s.service_code for s in updated_services]
    }

@router.delete("/services/{service_id}")
def delete_medical_service_endpoint(
    service_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete medical service"""
    require_permission(current_user, "billing", "delete")
    try:
        db_service = delete_medical_service(db, service_id, current_user.id)
        if not db_service:
            raise HTTPException(status_code=404, detail="Medical service not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Medical service deleted successfully"}

@router.post("/services/search/", response_model=List[MedicalServiceResponse])
def search_medical_services_endpoint(
    search: MedicalServiceSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search medical services with filters"""
    require_permission(current_user, "billing", "read")
    services = search_medical_services(db, search, skip=skip, limit=limit)
    
    enhanced_services = []
    for service in services:
        enhanced_data = MedicalServiceResponse.from_orm(service)
        
        # Add category information
        if service.billing_category:
            enhanced_data.category_name = service.billing_category.category_name
            enhanced_data.category_code = service.billing_category.category_code
        
        enhanced_services.append(enhanced_data)
    
    return enhanced_services

# Visit Service Endpoints
@router.get("/visit-services/", response_model=List[VisitServiceResponse])
def read_visit_services(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all visit services"""
    require_permission(current_user, "billing", "read")
    visit_services = get_visit_services(db, skip=skip, limit=limit)
    
    enhanced_services = []
    for visit_service in visit_services:
        enhanced_data = VisitServiceResponse.from_orm(visit_service)
        
        # Add related information
        if visit_service.medical_service:
            enhanced_data.service_name = visit_service.medical_service.service_name
            enhanced_data.service_code = visit_service.medical_service.service_code
        
        if visit_service.visit and visit_service.visit.patient:
            enhanced_data.patient_name = f"{visit_service.visit.patient.first_name} {visit_service.visit.patient.last_name}"
        
        if visit_service.performed_by_doctor:
            enhanced_data.doctor_name = f"{visit_service.performed_by_doctor.first_name} {visit_service.performed_by_doctor.last_name}"
        
        if visit_service.visit:
            enhanced_data.visit_date = visit_service.visit.visit_date
        
        enhanced_services.append(enhanced_data)
    
    return enhanced_services

@router.get("/visit-services/{visit_service_id}", response_model=VisitServiceResponse)
def read_visit_service(
    visit_service_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get visit service by ID"""
    require_permission(current_user, "billing", "read")
    visit_service = get_visit_service_by_id(db, visit_service_id)
    if not visit_service:
        raise HTTPException(status_code=404, detail="Visit service not found")
    
    enhanced_data = VisitServiceResponse.from_orm(visit_service)
    
    # Add related information
    if visit_service.medical_service:
        enhanced_data.service_name = visit_service.medical_service.service_name
        enhanced_data.service_code = visit_service.medical_service.service_code
    
    if visit_service.visit and visit_service.visit.patient:
        enhanced_data.patient_name = f"{visit_service.visit.patient.first_name} {visit_service.visit.patient.last_name}"
    
    if visit_service.performed_by_doctor:
        enhanced_data.doctor_name = f"{visit_service.performed_by_doctor.first_name} {visit_service.performed_by_doctor.last_name}"
    
    if visit_service.visit:
        enhanced_data.visit_date = visit_service.visit.visit_date
    
    return enhanced_data

@router.post("/visit-services/", response_model=VisitServiceResponse)
def create_visit_service_endpoint(
    visit_service: VisitServiceCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new visit service"""
    require_permission(current_user, "billing", "create")
    
    # Validate visit and service exist
    from ..crud.patients import get_patient_visit_by_id
    from ..crud.medical_services import get_medical_service_by_id
    
    visit = get_patient_visit_by_id(db, visit_service.visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Patient visit not found")
    
    service = get_medical_service_by_id(db, visit_service.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Medical service not found")
    
    # Validate doctor if provided
    if visit_service.performed_by_doctor_id:
        from ..crud.doctors import get_doctor_by_id
        doctor = get_doctor_by_id(db, visit_service.performed_by_doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
    
    db_visit_service = create_visit_service(db, visit_service, current_user.id)
    
    enhanced_data = VisitServiceResponse.from_orm(db_visit_service)
    
    # Add related information
    if db_visit_service.medical_service:
        enhanced_data.service_name = db_visit_service.medical_service.service_name
        enhanced_data.service_code = db_visit_service.medical_service.service_code
    
    if db_visit_service.visit and db_visit_service.visit.patient:
        enhanced_data.patient_name = f"{db_visit_service.visit.patient.first_name} {db_visit_service.visit.patient.last_name}"
    
    if db_visit_service.performed_by_doctor:
        enhanced_data.doctor_name = f"{db_visit_service.performed_by_doctor.first_name} {db_visit_service.performed_by_doctor.last_name}"
    
    if db_visit_service.visit:
        enhanced_data.visit_date = db_visit_service.visit.visit_date
    
    return enhanced_data

@router.put("/visit-services/{visit_service_id}", response_model=VisitServiceResponse)
def update_visit_service_endpoint(
    visit_service_id: int,
    visit_service: VisitServiceUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update visit service"""
    require_permission(current_user, "billing", "update")
    db_visit_service = update_visit_service(db, visit_service_id, visit_service, current_user.id)
    if not db_visit_service:
        raise HTTPException(status_code=404, detail="Visit service not found")
    
    enhanced_data = VisitServiceResponse.from_orm(db_visit_service)
    
    # Add related information
    if db_visit_service.medical_service:
        enhanced_data.service_name = db_visit_service.medical_service.service_name
        enhanced_data.service_code = db_visit_service.medical_service.service_code
    
    if db_visit_service.visit and db_visit_service.visit.patient:
        enhanced_data.patient_name = f"{db_visit_service.visit.patient.first_name} {db_visit_service.visit.patient.last_name}"
    
    if db_visit_service.performed_by_doctor:
        enhanced_data.doctor_name = f"{db_visit_service.performed_by_doctor.first_name} {db_visit_service.performed_by_doctor.last_name}"
    
    if db_visit_service.visit:
        enhanced_data.visit_date = db_visit_service.visit.visit_date
    
    return enhanced_data

@router.delete("/visit-services/{visit_service_id}")
def delete_visit_service_endpoint(
    visit_service_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete visit service"""
    require_permission(current_user, "billing", "delete")
    db_visit_service = delete_visit_service(db, visit_service_id, current_user.id)
    if not db_visit_service:
        raise HTTPException(status_code=404, detail="Visit service not found")
    
    return {"message": "Visit service deleted successfully"}

@router.post("/visit-services/search/", response_model=List[VisitServiceResponse])
def search_visit_services_endpoint(
    search: VisitServiceSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search visit services with filters"""
    require_permission(current_user, "billing", "read")
    visit_services = search_visit_services(db, search, skip=skip, limit=limit)
    
    enhanced_services = []
    for visit_service in visit_services:
        enhanced_data = VisitServiceResponse.from_orm(visit_service)
        
        # Add related information
        if visit_service.medical_service:
            enhanced_data.service_name = visit_service.medical_service.service_name
            enhanced_data.service_code = visit_service.medical_service.service_code
        
        if visit_service.visit and visit_service.visit.patient:
            enhanced_data.patient_name = f"{visit_service.visit.patient.first_name} {visit_service.visit.patient.last_name}"
        
        if visit_service.performed_by_doctor:
            enhanced_data.doctor_name = f"{visit_service.performed_by_doctor.first_name} {visit_service.performed_by_doctor.last_name}"
        
        if visit_service.visit:
            enhanced_data.visit_date = visit_service.visit.visit_date
        
        enhanced_services.append(enhanced_data)
    
    return enhanced_services

# Statistics and Reports
@router.get("/stats/categories", response_model=List[CategoryStats])
def get_category_statistics(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics for all billing categories"""
    require_permission(current_user, "billing", "read")
    stats = get_category_stats(db)
    return stats

@router.get("/stats/service-usage", response_model=List[ServiceUsageStats])
def get_service_usage_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get service usage statistics"""
    require_permission(current_user, "billing", "read")
    stats = get_service_usage_stats(db, days)
    return stats

@router.get("/stats/revenue-by-category")
def get_revenue_by_category_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get revenue breakdown by category"""
    require_permission(current_user, "billing", "read")
    revenue_data = get_revenue_by_category(db, start_date, end_date)
    return {"revenue_by_category": revenue_data}

@router.get("/reports/service-pricing")
def get_service_pricing_report(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive service pricing report"""
    require_permission(current_user, "billing", "read")
    
    services = get_medical_services(db)
    categories = get_billing_categories(db)
    
    report = {
        "total_services": len(services),
        "total_categories": len(categories),
        "services_by_category": [],
        "pricing_summary": {
            "highest_price": max([s.standard_price for s in services]) if services else 0,
            "lowest_price": min([s.standard_price for s in services]) if services else 0,
            "average_price": sum([s.standard_price for s in services]) / len(services) if services else 0
        }
    }
    
    for category in categories:
        category_services = get_medical_services_by_category(db, category.id)
        if category_services:
            report["services_by_category"].append({
                "category_name": category.category_name,
                "service_count": len(category_services),
                "average_price": sum([s.standard_price for s in category_services]) / len(category_services),
                "services": [
                    {
                        "service_name": s.service_name,
                        "standard_price": s.standard_price,
                        "is_active": s.is_active
                    }
                    for s in category_services
                ]
            })
    
    return report