from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from ..models.vaccines import Vaccine, VaccinationSchedule, VaccineInventory
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..schemas.vaccines import (
    VaccineCreate, VaccineUpdate, VaccinationScheduleCreate, 
    VaccinationScheduleUpdate, VaccineInventoryCreate, VaccineInventoryUpdate,
    VaccinationScheduleAdminister, VaccineSearch, VaccinationScheduleSearch
)

logger = logging.getLogger(__name__)

# Vaccine CRUD operations
def generate_vaccine_code(db: Session):
    """Generate unique vaccine code"""
    prefix = "VAC"
    
    # Find the highest number
    max_vaccine = db.query(Vaccine).order_by(Vaccine.id.desc()).first()
    next_num = (max_vaccine.id + 1) if max_vaccine else 1
    
    return f"{prefix}{next_num:04d}"

def get_vaccines(db: Session, skip: int = 0, limit: int = 100):
    """Get all vaccines"""
    return db.query(Vaccine).filter(Vaccine.deleted_at == None)\
        .order_by(Vaccine.vaccine_name.asc())\
        .offset(skip).limit(limit).all()

def get_vaccine_by_id(db: Session, vaccine_id: int):
    """Get vaccine by ID"""
    return db.query(Vaccine).filter(
        Vaccine.id == vaccine_id,
        Vaccine.deleted_at == None
    ).first()

def get_vaccine_by_code(db: Session, vaccine_code: str):
    """Get vaccine by code"""
    return db.query(Vaccine).filter(
        Vaccine.vaccine_code == vaccine_code,
        Vaccine.deleted_at == None
    ).first()

def search_vaccines(db: Session, search: VaccineSearch, skip: int = 0, limit: int = 100):
    """Search vaccines with filters"""
    query = db.query(Vaccine).filter(Vaccine.deleted_at == None)
    
    if search.vaccine_name:
        query = query.filter(Vaccine.vaccine_name.ilike(f"%{search.vaccine_name}%"))
    
    if search.manufacturer:
        query = query.filter(Vaccine.manufacturer.ilike(f"%{search.manufacturer}%"))
    
    if search.is_active is not None:
        query = query.filter(Vaccine.is_active == search.is_active)
    
    return query.order_by(Vaccine.vaccine_name.asc())\
        .offset(skip).limit(limit).all()

def create_vaccine(db: Session, vaccine: VaccineCreate, user_id: int):
    """Create new vaccine"""
    vaccine_code = generate_vaccine_code(db)
    db_vaccine = Vaccine(**vaccine.dict(), vaccine_code=vaccine_code, created_by=user_id)
    db.add(db_vaccine)
    db.commit()
    db.refresh(db_vaccine)
    return db_vaccine

def update_vaccine(db: Session, vaccine_id: int, vaccine: VaccineUpdate, user_id: int):
    """Update vaccine"""
    db_vaccine = db.query(Vaccine).filter(
        Vaccine.id == vaccine_id,
        Vaccine.deleted_at == None
    ).first()
    
    if not db_vaccine:
        return None
    
    for key, value in vaccine.dict(exclude_unset=True).items():
        setattr(db_vaccine, key, value)
    
    db_vaccine.updated_by = user_id
    db.commit()
    db.refresh(db_vaccine)
    return db_vaccine

def delete_vaccine(db: Session, vaccine_id: int, user_id: int):
    """Soft delete vaccine"""
    db_vaccine = db.query(Vaccine).filter(
        Vaccine.id == vaccine_id,
        Vaccine.deleted_at == None
    ).first()
    
    if not db_vaccine:
        return None
    
    db_vaccine.deleted_at = func.now()
    db_vaccine.deleted_by = user_id
    db.commit()
    return db_vaccine

# Vaccination Schedule CRUD operations
def generate_schedule_code(db: Session):
    """Generate unique schedule code"""
    from datetime import datetime
    prefix = "VSCH"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.schedule_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.schedule_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_vaccination_schedules(db: Session, skip: int = 0, limit: int = 100):
    """Get all vaccination schedules"""
    return db.query(VaccinationSchedule).filter(VaccinationSchedule.deleted_at == None)\
        .order_by(VaccinationSchedule.scheduled_date.desc())\
        .offset(skip).limit(limit).all()

def get_vaccination_schedule_by_id(db: Session, schedule_id: int):
    """Get vaccination schedule by ID"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()

def get_vaccination_schedules_by_patient(db: Session, patient_id: int):
    """Get all vaccination schedules for a patient"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.patient_id == patient_id,
        VaccinationSchedule.deleted_at == None
    ).order_by(VaccinationSchedule.scheduled_date.asc()).all()

def get_vaccination_schedules_by_vaccine(db: Session, vaccine_id: int):
    """Get all vaccination schedules for a vaccine"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.vaccine_id == vaccine_id,
        VaccinationSchedule.deleted_at == None
    ).order_by(VaccinationSchedule.scheduled_date.desc()).all()

def get_patient_vaccination_status(db: Session, patient_id: int):
    """Get vaccination status for a patient"""
    schedules = get_vaccination_schedules_by_patient(db, patient_id)
    
    status = {}
    for schedule in schedules:
        if schedule.vaccine_id not in status:
            vaccine = schedule.vaccine
            status[schedule.vaccine_id] = {
                'vaccine_id': vaccine.id,
                'vaccine_name': vaccine.vaccine_name,
                'total_doses_required': vaccine.total_doses_required,
                'doses_administered': 0,
                'schedules': []
            }
        
        status[schedule.vaccine_id]['schedules'].append(schedule)
        if schedule.is_administered:
            status[schedule.vaccine_id]['doses_administered'] += 1
    
    # Calculate next dose and completion status
    result = []
    for vaccine_id, data in status.items():
        administered_count = data['doses_administered']
        total_required = data['total_doses_required']
        
        # Find next scheduled dose
        next_schedule = None
        for schedule in data['schedules']:
            if not schedule.is_administered and schedule.scheduled_date >= date.today():
                if not next_schedule or schedule.scheduled_date < next_schedule.scheduled_date:
                    next_schedule = schedule
        
        # Find last administered date
        last_administered = None
        for schedule in data['schedules']:
            if schedule.is_administered and schedule.administered_date:
                if not last_administered or schedule.administered_date > last_administered:
                    last_administered = schedule.administered_date
        
        result.append({
            'vaccine_id': vaccine_id,
            'vaccine_name': data['vaccine_name'],
            'total_doses_required': total_required,
            'doses_administered': administered_count,
            'next_dose_number': next_schedule.dose_number if next_schedule else None,
            'next_scheduled_date': next_schedule.scheduled_date if next_schedule else None,
            'is_complete': administered_count >= total_required,
            'last_administered_date': last_administered
        })
    
    return result

def create_vaccination_schedule(db: Session, schedule: VaccinationScheduleCreate, user_id: int):
    """Create new vaccination schedule"""
    schedule_code = generate_schedule_code(db)
    db_schedule = VaccinationSchedule(**schedule.dict(), schedule_code=schedule_code, created_by=user_id)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def create_bulk_vaccination_schedules(db: Session, patient_id: int, schedules: List, user_id: int):
    """Create multiple vaccination schedules for a patient"""
    created_schedules = []
    for schedule_data in schedules:
        schedule = VaccinationScheduleCreate(
            patient_id=patient_id,
            vaccine_id=schedule_data['vaccine_id'],
            dose_number=schedule_data['dose_number'],
            scheduled_date=schedule_data['scheduled_date']
        )
        db_schedule = create_vaccination_schedule(db, schedule, user_id)
        created_schedules.append(db_schedule)
    
    return created_schedules

def update_vaccination_schedule(db: Session, schedule_id: int, schedule: VaccinationScheduleUpdate, user_id: int):
    """Update vaccination schedule"""
    db_schedule = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()
    
    if not db_schedule:
        return None
    
    for key, value in schedule.dict(exclude_unset=True).items():
        setattr(db_schedule, key, value)
    
    db_schedule.updated_by = user_id
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def administer_vaccination(db: Session, schedule_id: int, administration: VaccinationScheduleAdminister, user_id: int):
    """Administer vaccination"""
    db_schedule = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()
    
    if not db_schedule:
        return None
    
    # Check inventory
    inventory = db.query(VaccineInventory).filter(
        VaccineInventory.vaccine_id == db_schedule.vaccine_id,
        VaccineInventory.lot_number == administration.lot_number,
        VaccineInventory.quantity_available > 0,
        VaccineInventory.expiration_date >= date.today()
    ).first()
    
    if not inventory:
        raise ValueError("Vaccine not available in inventory or expired")
    
    # Update inventory
    inventory.quantity_available -= 1
    inventory.quantity_used += 1
    
    # Update schedule
    for key, value in administration.dict().items():
        setattr(db_schedule, key, value)
    
    db_schedule.is_administered = True
    db_schedule.updated_by = user_id
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def delete_vaccination_schedule(db: Session, schedule_id: int, user_id: int):
    """Soft delete vaccination schedule"""
    db_schedule = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()
    
    if not db_schedule:
        return None
    
    db_schedule.deleted_at = func.now()
    db_schedule.deleted_by = user_id
    db.commit()
    return db_schedule

def search_vaccination_schedules(db: Session, search: VaccinationScheduleSearch, skip: int = 0, limit: int = 100):
    """Search vaccination schedules with filters"""
    query = db.query(VaccinationSchedule).filter(VaccinationSchedule.deleted_at == None)
    
    if search.patient_name:
        query = query.join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.vaccine_name:
        query = query.join(Vaccine).filter(Vaccine.vaccine_name.ilike(f"%{search.vaccine_name}%"))
    
    if search.date_from:
        query = query.filter(VaccinationSchedule.scheduled_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(VaccinationSchedule.scheduled_date <= search.date_to)
    
    if search.is_administered is not None:
        query = query.filter(VaccinationSchedule.is_administered == search.is_administered)
    
    if search.dose_number:
        query = query.filter(VaccinationSchedule.dose_number == search.dose_number)
    
    return query.order_by(VaccinationSchedule.scheduled_date.desc())\
        .offset(skip).limit(limit).all()

def get_upcoming_vaccinations(db: Session, days: int = 30):
    """Get upcoming vaccinations within the next n days"""
    today = date.today()
    end_date = today + timedelta(days=days)
    
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date >= today,
        VaccinationSchedule.scheduled_date <= end_date,
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == False
    ).order_by(VaccinationSchedule.scheduled_date.asc()).all()

def get_overdue_vaccinations(db: Session):
    """Get overdue vaccinations"""
    today = date.today()
    
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date < today,
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == False
    ).order_by(VaccinationSchedule.scheduled_date.asc()).all()

# Vaccine Inventory CRUD operations
def get_vaccine_inventory(db: Session, skip: int = 0, limit: int = 100):
    """Get all vaccine inventory"""
    return db.query(VaccineInventory).filter(VaccineInventory.deleted_at == None)\
        .order_by(VaccineInventory.expiration_date.asc())\
        .offset(skip).limit(limit).all()

def get_vaccine_inventory_by_id(db: Session, inventory_id: int):
    """Get vaccine inventory by ID"""
    return db.query(VaccineInventory).filter(
        VaccineInventory.id == inventory_id,
        VaccineInventory.deleted_at == None
    ).first()

def get_vaccine_inventory_by_vaccine(db: Session, vaccine_id: int):
    """Get inventory for a specific vaccine"""
    return db.query(VaccineInventory).filter(
        VaccineInventory.vaccine_id == vaccine_id,
        VaccineInventory.deleted_at == None
    ).order_by(VaccineInventory.expiration_date.asc()).all()

def create_vaccine_inventory(db: Session, inventory: VaccineInventoryCreate, user_id: int):
    """Create new vaccine inventory record"""
    db_inventory = VaccineInventory(**inventory.dict(), created_by=user_id)
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def update_vaccine_inventory(db: Session, inventory_id: int, inventory: VaccineInventoryUpdate, user_id: int):
    """Update vaccine inventory"""
    db_inventory = db.query(VaccineInventory).filter(
        VaccineInventory.id == inventory_id,
        VaccineInventory.deleted_at == None
    ).first()
    
    if not db_inventory:
        return None
    
    for key, value in inventory.dict(exclude_unset=True).items():
        setattr(db_inventory, key, value)
    
    db_inventory.updated_by = user_id
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def delete_vaccine_inventory(db: Session, inventory_id: int, user_id: int):
    """Soft delete vaccine inventory"""
    db_inventory = db.query(VaccineInventory).filter(
        VaccineInventory.id == inventory_id,
        VaccineInventory.deleted_at == None
    ).first()
    
    if not db_inventory:
        return None
    
    db_inventory.deleted_at = func.now()
    db_inventory.deleted_by = user_id
    db.commit()
    return db_inventory

def get_low_stock_vaccines(db: Session):
    """Get vaccines with low stock"""
    return db.query(VaccineInventory).filter(
        VaccineInventory.quantity_available <= VaccineInventory.reorder_level,
        VaccineInventory.deleted_at == None
    ).all()

def get_expired_vaccines(db: Session):
    """Get expired vaccines"""
    today = date.today()
    return db.query(VaccineInventory).filter(
        VaccineInventory.expiration_date < today,
        VaccineInventory.deleted_at == None,
        VaccineInventory.quantity_available > 0
    ).all()

# Statistics
def get_vaccination_stats(db: Session):
    """Get vaccination statistics"""
    total_vaccines = db.query(Vaccine).filter(Vaccine.deleted_at == None).count()
    total_schedules = db.query(VaccinationSchedule).filter(VaccinationSchedule.deleted_at == None).count()
    administered_count = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.is_administered == True,
        VaccinationSchedule.deleted_at == None
    ).count()
    pending_count = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.is_administered == False,
        VaccinationSchedule.deleted_at == None
    ).count()
    
    upcoming_schedules = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date >= date.today(),
        VaccinationSchedule.scheduled_date <= date.today() + timedelta(days=7),
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == False
    ).count()
    
    expired_vaccines = len(get_expired_vaccines(db))
    low_stock_vaccines = len(get_low_stock_vaccines(db))
    
    return {
        "total_vaccines": total_vaccines,
        "total_schedules": total_schedules,
        "administered_count": administered_count,
        "pending_count": pending_count,
        "upcoming_schedules": upcoming_schedules,
        "expired_vaccines": expired_vaccines,
        "low_stock_vaccines": low_stock_vaccines
    }