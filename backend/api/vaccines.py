from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from ..db import get_db
from ..schemas.vaccines import (
    VaccineCreate, VaccineUpdate, VaccineResponse,
    VaccinationScheduleCreate, VaccinationScheduleUpdate, VaccinationScheduleResponse,
    VaccinationScheduleAdminister, VaccineInventoryCreate, VaccineInventoryUpdate, VaccineInventoryResponse,
    VaccinationStats, PatientVaccinationStatus, BulkVaccinationSchedule, VaccineSchedulePlan,
    VaccineSearch, VaccinationScheduleSearch, InventoryAlert, VaccinationDueAlert
)
from ..crud.vaccines import (
    get_vaccines, get_vaccine_by_id, get_vaccine_by_code, search_vaccines,
    create_vaccine, update_vaccine, delete_vaccine,
    get_vaccination_schedules, get_vaccination_schedule_by_id, get_vaccination_schedules_by_patient,
    get_vaccination_schedules_by_vaccine, get_patient_vaccination_status,
    create_vaccination_schedule, create_bulk_vaccination_schedules, update_vaccination_schedule,
    administer_vaccination, delete_vaccination_schedule, search_vaccination_schedules,
    get_upcoming_vaccinations, get_overdue_vaccinations,
    get_vaccine_inventory, get_vaccine_inventory_by_id, get_vaccine_inventory_by_vaccine,
    create_vaccine_inventory, update_vaccine_inventory, delete_vaccine_inventory,
    get_low_stock_vaccines, get_expired_vaccines, get_vaccination_stats
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouter()

# Vaccine Endpoints
@router.get("/", response_model=List[VaccineResponse])
def read_vaccines(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vaccines"""
    require_permission(current_user, "patients", "read")  # Using patients module permission
    vaccines = get_vaccines(db, skip=skip, limit=limit)
    return vaccines

@router.get("/{vaccine_id}", response_model=VaccineResponse)
def read_vaccine(
    vaccine_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccine by ID"""
    require_permission(current_user, "patients", "read")
    vaccine = get_vaccine_by_id(db, vaccine_id)
    if not vaccine:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    return vaccine

@router.post("/", response_model=VaccineResponse)
def create_vaccine_endpoint(
    vaccine: VaccineCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new vaccine"""
    require_permission(current_user, "patients", "create")
    db_vaccine = create_vaccine(db, vaccine, current_user.id)
    return db_vaccine

@router.put("/{vaccine_id}", response_model=VaccineResponse)
def update_vaccine_endpoint(
    vaccine_id: int,
    vaccine: VaccineUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update vaccine"""
    require_permission(current_user, "patients", "update")
    db_vaccine = update_vaccine(db, vaccine_id, vaccine, current_user.id)
    if not db_vaccine:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    return db_vaccine

@router.delete("/{vaccine_id}")
def delete_vaccine_endpoint(
    vaccine_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete vaccine"""
    require_permission(current_user, "patients", "delete")
    db_vaccine = delete_vaccine(db, vaccine_id, current_user.id)
    if not db_vaccine:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    return {"message": "Vaccine deleted successfully"}

@router.post("/search/", response_model=List[VaccineResponse])
def search_vaccines_endpoint(
    search: VaccineSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search vaccines with filters"""
    require_permission(current_user, "patients", "read")
    vaccines = search_vaccines(db, search, skip=skip, limit=limit)
    return vaccines

# Vaccination Schedule Endpoints
@router.get("/schedules/", response_model=List[VaccinationScheduleResponse])
def read_vaccination_schedules(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vaccination schedules"""
    require_permission(current_user, "patients", "read")
    schedules = get_vaccination_schedules(db, skip=skip, limit=limit)
    
    # Enhance response with related data
    enhanced_schedules = []
    for schedule in schedules:
        enhanced_data = VaccinationScheduleResponse.from_orm(schedule)
        
        if schedule.patient:
            enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
            enhanced_data.patient_code = schedule.patient.patient_code
        
        if schedule.vaccine:
            enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
            enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
        
        if schedule.administering_doctor:
            enhanced_data.doctor_name = f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}"
        
        enhanced_schedules.append(enhanced_data)
    
    return enhanced_schedules

@router.get("/schedules/{schedule_id}", response_model=VaccinationScheduleResponse)
def read_vaccination_schedule(
    schedule_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination schedule by ID"""
    require_permission(current_user, "patients", "read")
    schedule = get_vaccination_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    
    enhanced_data = VaccinationScheduleResponse.from_orm(schedule)
    
    if schedule.patient:
        enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
        enhanced_data.patient_code = schedule.patient.patient_code
    
    if schedule.vaccine:
        enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
        enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
    
    if schedule.administering_doctor:
        enhanced_data.doctor_name = f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}"
    
    return enhanced_data

@router.get("/patients/{patient_id}/schedules", response_model=List[VaccinationScheduleResponse])
def read_patient_vaccination_schedules(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination schedules for a patient"""
    require_permission(current_user, "patients", "read")
    schedules = get_vaccination_schedules_by_patient(db, patient_id)
    
    enhanced_schedules = []
    for schedule in schedules:
        enhanced_data = VaccinationScheduleResponse.from_orm(schedule)
        
        if schedule.patient:
            enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
            enhanced_data.patient_code = schedule.patient.patient_code
        
        if schedule.vaccine:
            enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
            enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
        
        if schedule.administering_doctor:
            enhanced_data.doctor_name = f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}"
        
        enhanced_schedules.append(enhanced_data)
    
    return enhanced_schedules

@router.get("/patients/{patient_id}/status", response_model=List[PatientVaccinationStatus])
def read_patient_vaccination_status(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination status for a patient"""
    require_permission(current_user, "patients", "read")
    status = get_patient_vaccination_status(db, patient_id)
    return status

@router.post("/schedules/", response_model=VaccinationScheduleResponse)
def create_vaccination_schedule_endpoint(
    schedule: VaccinationScheduleCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new vaccination schedule"""
    require_permission(current_user, "patients", "create")
    db_schedule = create_vaccination_schedule(db, schedule, current_user.id)
    
    enhanced_data = VaccinationScheduleResponse.from_orm(db_schedule)
    
    if db_schedule.patient:
        enhanced_data.patient_name = f"{db_schedule.patient.first_name} {db_schedule.patient.last_name}"
        enhanced_data.patient_code = db_schedule.patient.patient_code
    
    if db_schedule.vaccine:
        enhanced_data.vaccine_name = db_schedule.vaccine.vaccine_name
        enhanced_data.vaccine_code = db_schedule.vaccine.vaccine_code
    
    return enhanced_data

@router.post("/patients/{patient_id}/schedules/bulk", response_model=List[VaccinationScheduleResponse])
def create_bulk_vaccination_schedules_endpoint(
    patient_id: int,
    bulk_schedule: BulkVaccinationSchedule,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple vaccination schedules for a patient"""
    require_permission(current_user, "patients", "create")
    schedules = create_bulk_vaccination_schedules(db, patient_id, bulk_schedule.schedules, current_user.id)
    
    enhanced_schedules = []
    for schedule in schedules:
        enhanced_data = VaccinationScheduleResponse.from_orm(schedule)
        
        if schedule.patient:
            enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
            enhanced_data.patient_code = schedule.patient.patient_code
        
        if schedule.vaccine:
            enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
            enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
        
        enhanced_schedules.append(enhanced_data)
    
    return enhanced_schedules

@router.put("/schedules/{schedule_id}", response_model=VaccinationScheduleResponse)
def update_vaccination_schedule_endpoint(
    schedule_id: int,
    schedule: VaccinationScheduleUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update vaccination schedule"""
    require_permission(current_user, "patients", "update")
    db_schedule = update_vaccination_schedule(db, schedule_id, schedule, current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    
    enhanced_data = VaccinationScheduleResponse.from_orm(db_schedule)
    
    if db_schedule.patient:
        enhanced_data.patient_name = f"{db_schedule.patient.first_name} {db_schedule.patient.last_name}"
        enhanced_data.patient_code = db_schedule.patient.patient_code
    
    if db_schedule.vaccine:
        enhanced_data.vaccine_name = db_schedule.vaccine.vaccine_name
        enhanced_data.vaccine_code = db_schedule.vaccine.vaccine_code
    
    if db_schedule.administering_doctor:
        enhanced_data.doctor_name = f"{db_schedule.administering_doctor.first_name} {db_schedule.administering_doctor.last_name}"
    
    return enhanced_data

@router.post("/schedules/{schedule_id}/administer", response_model=VaccinationScheduleResponse)
def administer_vaccination_endpoint(
    schedule_id: int,
    administration: VaccinationScheduleAdminister,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Administer vaccination"""
    require_permission(current_user, "patients", "update")
    try:
        db_schedule = administer_vaccination(db, schedule_id, administration, current_user.id)
        if not db_schedule:
            raise HTTPException(status_code=404, detail="Vaccination schedule not found")
        
        enhanced_data = VaccinationScheduleResponse.from_orm(db_schedule)
        
        if db_schedule.patient:
            enhanced_data.patient_name = f"{db_schedule.patient.first_name} {db_schedule.patient.last_name}"
            enhanced_data.patient_code = db_schedule.patient.patient_code
        
        if db_schedule.vaccine:
            enhanced_data.vaccine_name = db_schedule.vaccine.vaccine_name
            enhanced_data.vaccine_code = db_schedule.vaccine.vaccine_code
        
        if db_schedule.administering_doctor:
            enhanced_data.doctor_name = f"{db_schedule.administering_doctor.first_name} {db_schedule.administering_doctor.last_name}"
        
        return enhanced_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/schedules/{schedule_id}")
def delete_vaccination_schedule_endpoint(
    schedule_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete vaccination schedule"""
    require_permission(current_user, "patients", "delete")
    db_schedule = delete_vaccination_schedule(db, schedule_id, current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    return {"message": "Vaccination schedule deleted successfully"}

@router.post("/schedules/search/", response_model=List[VaccinationScheduleResponse])
def search_vaccination_schedules_endpoint(
    search: VaccinationScheduleSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search vaccination schedules with filters"""
    require_permission(current_user, "patients", "read")
    schedules = search_vaccination_schedules(db, search, skip=skip, limit=limit)
    
    enhanced_schedules = []
    for schedule in schedules:
        enhanced_data = VaccinationScheduleResponse.from_orm(schedule)
        
        if schedule.patient:
            enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
            enhanced_data.patient_code = schedule.patient.patient_code
        
        if schedule.vaccine:
            enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
            enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
        
        if schedule.administering_doctor:
            enhanced_data.doctor_name = f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}"
        
        enhanced_schedules.append(enhanced_data)
    
    return enhanced_schedules

# Vaccine Inventory Endpoints
@router.get("/inventory/", response_model=List[VaccineInventoryResponse])
def read_vaccine_inventory(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vaccine inventory"""
    require_permission(current_user, "inventory", "read")
    inventory = get_vaccine_inventory(db, skip=skip, limit=limit)
    
    enhanced_inventory = []
    for item in inventory:
        enhanced_data = VaccineInventoryResponse.from_orm(item)
        
        if item.vaccine:
            enhanced_data.vaccine_name = item.vaccine.vaccine_name
            enhanced_data.vaccine_code = item.vaccine.vaccine_code
        
        enhanced_inventory.append(enhanced_data)
    
    return enhanced_inventory

@router.get("/inventory/{inventory_id}", response_model=VaccineInventoryResponse)
def read_vaccine_inventory_item(
    inventory_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccine inventory by ID"""
    require_permission(current_user, "inventory", "read")
    inventory = get_vaccine_inventory_by_id(db, inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Vaccine inventory not found")
    
    enhanced_data = VaccineInventoryResponse.from_orm(inventory)
    
    if inventory.vaccine:
        enhanced_data.vaccine_name = inventory.vaccine.vaccine_name
        enhanced_data.vaccine_code = inventory.vaccine.vaccine_code
    
    return enhanced_data

@router.post("/inventory/", response_model=VaccineInventoryResponse)
def create_vaccine_inventory_endpoint(
    inventory: VaccineInventoryCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new vaccine inventory record"""
    require_permission(current_user, "inventory", "create")
    db_inventory = create_vaccine_inventory(db, inventory, current_user.id)
    
    enhanced_data = VaccineInventoryResponse.from_orm(db_inventory)
    
    if db_inventory.vaccine:
        enhanced_data.vaccine_name = db_inventory.vaccine.vaccine_name
        enhanced_data.vaccine_code = db_inventory.vaccine.vaccine_code
    
    return enhanced_data

@router.put("/inventory/{inventory_id}", response_model=VaccineInventoryResponse)
def update_vaccine_inventory_endpoint(
    inventory_id: int,
    inventory: VaccineInventoryUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update vaccine inventory"""
    require_permission(current_user, "inventory", "update")
    db_inventory = update_vaccine_inventory(db, inventory_id, inventory, current_user.id)
    if not db_inventory:
        raise HTTPException(status_code=404, detail="Vaccine inventory not found")
    
    enhanced_data = VaccineInventoryResponse.from_orm(db_inventory)
    
    if db_inventory.vaccine:
        enhanced_data.vaccine_name = db_inventory.vaccine.vaccine_name
        enhanced_data.vaccine_code = db_inventory.vaccine.vaccine_code
    
    return enhanced_data

@router.delete("/inventory/{inventory_id}")
def delete_vaccine_inventory_endpoint(
    inventory_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete vaccine inventory"""
    require_permission(current_user, "inventory", "delete")
    db_inventory = delete_vaccine_inventory(db, inventory_id, current_user.id)
    if not db_inventory:
        raise HTTPException(status_code=404, detail="Vaccine inventory not found")
    return {"message": "Vaccine inventory deleted successfully"}

# Statistics and Reports
@router.get("/stats/overview", response_model=VaccinationStats)
def get_vaccination_stats_overview(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination statistics"""
    require_permission(current_user, "patients", "read")
    stats = get_vaccination_stats(db)
    return VaccinationStats(**stats)

@router.get("/alerts/low-stock", response_model=List[InventoryAlert])
def get_low_stock_alerts(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get low stock vaccine alerts"""
    require_permission(current_user, "inventory", "read")
    low_stock = get_low_stock_vaccines(db)
    
    alerts = []
    for item in low_stock:
        status = "out_of_stock" if item.quantity_available == 0 else "low_stock"
        alerts.append(InventoryAlert(
            vaccine_id=item.vaccine_id,
            vaccine_name=item.vaccine.vaccine_name,
            lot_number=item.lot_number,
            quantity_available=item.quantity_available,
            reorder_level=item.reorder_level,
            status=status
        ))
    
    return alerts

@router.get("/alerts/expired", response_model=List[InventoryAlert])
def get_expired_vaccine_alerts(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expired vaccine alerts"""
    require_permission(current_user, "inventory", "read")
    expired = get_expired_vaccines(db)
    
    alerts = []
    for item in expired:
        alerts.append(InventoryAlert(
            vaccine_id=item.vaccine_id,
            vaccine_name=item.vaccine.vaccine_name,
            lot_number=item.lot_number,
            quantity_available=item.quantity_available,
            reorder_level=item.reorder_level,
            status="expired"
        ))
    
    return alerts

@router.get("/alerts/upcoming", response_model=List[VaccinationDueAlert])
def get_upcoming_vaccination_alerts(
    days: int = Query(7, ge=1, le=30),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming vaccination due alerts"""
    require_permission(current_user, "patients", "read")
    upcoming = get_upcoming_vaccinations(db, days)
    
    alerts = []
    for schedule in upcoming:
        days_until_due = (schedule.scheduled_date - date.today()).days
        alerts.append(VaccinationDueAlert(
            patient_id=schedule.patient_id,
            patient_name=f"{schedule.patient.first_name} {schedule.patient.last_name}",
            vaccine_name=schedule.vaccine.vaccine_name,
            dose_number=schedule.dose_number,
            scheduled_date=schedule.scheduled_date,
            days_until_due=days_until_due
        ))
    
    return alerts

@router.get("/alerts/overdue", response_model=List[VaccinationDueAlert])
def get_overdue_vaccination_alerts(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overdue vaccination alerts"""
    require_permission(current_user, "patients", "read")
    overdue = get_overdue_vaccinations(db)
    
    alerts = []
    for schedule in overdue:
        days_overdue = (date.today() - schedule.scheduled_date).days
        alerts.append(VaccinationDueAlert(
            patient_id=schedule.patient_id,
            patient_name=f"{schedule.patient.first_name} {schedule.patient.last_name}",
            vaccine_name=schedule.vaccine.vaccine_name,
            dose_number=schedule.dose_number,
            scheduled_date=schedule.scheduled_date,
            days_until_due=-days_overdue  # Negative to indicate overdue
        ))
    
    return alerts