from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract, case
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from ..models.vaccination_schedules import VaccinationSchedule
from ..models.vaccines import Vaccine, VaccineInventory
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..schemas.vaccination_schedules import (
    VaccinationScheduleCreate, VaccinationScheduleUpdate, 
    VaccinationScheduleAdminister, VaccinationScheduleSearch
)

logger = logging.getLogger(__name__)

def generate_schedule_code(db: Session):
    """Generate unique vaccination schedule code"""
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
    """Get all vaccination schedules with related data"""
    return db.query(VaccinationSchedule).filter(VaccinationSchedule.deleted_at == None)\
        .order_by(VaccinationSchedule.scheduled_date.desc())\
        .offset(skip).limit(limit).all()

def get_vaccination_schedule_by_id(db: Session, schedule_id: int):
    """Get vaccination schedule by ID with related data"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()

def get_vaccination_schedule_by_code(db: Session, schedule_code: str):
    """Get vaccination schedule by code"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.schedule_code == schedule_code,
        VaccinationSchedule.deleted_at == None
    ).first()

def get_vaccination_schedules_by_patient(db: Session, patient_id: int):
    """Get all vaccination schedules for a specific patient"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.patient_id == patient_id,
        VaccinationSchedule.deleted_at == None
    ).order_by(VaccinationSchedule.scheduled_date.asc()).all()

def get_vaccination_schedules_by_vaccine(db: Session, vaccine_id: int):
    """Get all vaccination schedules for a specific vaccine"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.vaccine_id == vaccine_id,
        VaccinationSchedule.deleted_at == None
    ).order_by(VaccinationSchedule.scheduled_date.desc()).all()

def get_vaccination_schedules_by_doctor(db: Session, doctor_id: int):
    """Get all vaccination schedules administered by a specific doctor"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.administering_doctor_id == doctor_id,
        VaccinationSchedule.deleted_at == None
    ).order_by(VaccinationSchedule.administered_date.desc()).all()

def get_vaccination_schedules_by_date_range(db: Session, start_date: date, end_date: date):
    """Get vaccination schedules within a date range"""
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date >= start_date,
        VaccinationSchedule.scheduled_date <= end_date,
        VaccinationSchedule.deleted_at == None
    ).order_by(VaccinationSchedule.scheduled_date.asc()).all()

def get_patient_vaccination_status(db: Session, patient_id: int):
    """Get comprehensive vaccination status for a patient"""
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
                'schedules': [],
                'last_administered_date': None
            }
        
        status[schedule.vaccine_id]['schedules'].append(schedule)
        if schedule.is_administered:
            status[schedule.vaccine_id]['doses_administered'] += 1
            if schedule.administered_date:
                if (status[schedule.vaccine_id]['last_administered_date'] is None or 
                    schedule.administered_date > status[schedule.vaccine_id]['last_administered_date']):
                    status[schedule.vaccine_id]['last_administered_date'] = schedule.administered_date
    
    # Calculate status for each vaccine
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
        
        # Calculate completion percentage
        completion_percentage = (administered_count / total_required) * 100 if total_required > 0 else 0
        
        result.append({
            'vaccine_id': vaccine_id,
            'vaccine_name': data['vaccine_name'],
            'total_doses_required': total_required,
            'doses_administered': administered_count,
            'next_dose_number': next_schedule.dose_number if next_schedule else None,
            'next_scheduled_date': next_schedule.scheduled_date if next_schedule else None,
            'is_complete': administered_count >= total_required,
            'last_administered_date': data['last_administered_date'],
            'completion_percentage': round(completion_percentage, 2)
        })
    
    return result

def create_vaccination_schedule(db: Session, schedule: VaccinationScheduleCreate, user_id: int):
    """Create a new vaccination schedule"""
    schedule_code = generate_schedule_code(db)
    
    # Verify dose number doesn't exceed vaccine's total doses
    vaccine = db.query(Vaccine).filter(Vaccine.id == schedule.vaccine_id).first()
    if vaccine and schedule.dose_number > vaccine.total_doses_required:
        raise ValueError(f"Dose number {schedule.dose_number} exceeds total doses required ({vaccine.total_doses_required}) for this vaccine")
    
    db_schedule = VaccinationSchedule(**schedule.dict(), schedule_code=schedule_code, created_by=user_id)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def create_bulk_vaccination_schedules(db: Session, patient_id: int, schedules_data: List[dict], user_id: int):
    """Create multiple vaccination schedules for a patient"""
    created_schedules = []
    
    for schedule_data in schedules_data:
        schedule = VaccinationScheduleCreate(
            patient_id=patient_id,
            vaccine_id=schedule_data['vaccine_id'],
            dose_number=schedule_data['dose_number'],
            scheduled_date=schedule_data['scheduled_date']
        )
        try:
            db_schedule = create_vaccination_schedule(db, schedule, user_id)
            created_schedules.append(db_schedule)
        except ValueError as e:
            logger.warning(f"Failed to create schedule: {e}")
            continue
    
    return created_schedules

def update_vaccination_schedule(db: Session, schedule_id: int, schedule: VaccinationScheduleUpdate, user_id: int):
    """Update an existing vaccination schedule"""
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
    """Administer a vaccination and update inventory"""
    db_schedule = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()
    
    if not db_schedule:
        return None
    
    if db_schedule.is_administered:
        raise ValueError("Vaccination has already been administered")
    
    # Check vaccine inventory
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
    
    # Update schedule with administration details
    for key, value in administration.dict().items():
        setattr(db_schedule, key, value)
    
    db_schedule.is_administered = True
    db_schedule.updated_by = user_id
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def cancel_vaccination_administration(db: Session, schedule_id: int, user_id: int):
    """Cancel a vaccination administration and restore inventory"""
    db_schedule = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()
    
    if not db_schedule:
        return None
    
    if not db_schedule.is_administered:
        raise ValueError("Vaccination has not been administered yet")
    
    # Restore inventory if lot number exists
    if db_schedule.lot_number:
        inventory = db.query(VaccineInventory).filter(
            VaccineInventory.vaccine_id == db_schedule.vaccine_id,
            VaccineInventory.lot_number == db_schedule.lot_number
        ).first()
        
        if inventory:
            inventory.quantity_available += 1
            inventory.quantity_used -= 1
    
    # Reset administration fields
    db_schedule.is_administered = False
    db_schedule.administered_date = None
    db_schedule.administering_doctor_id = None
    db_schedule.lot_number = None
    db_schedule.batch_number = None
    db_schedule.expiration_date = None
    db_schedule.administration_site = None
    db_schedule.route = None
    db_schedule.adverse_reactions = None
    db_schedule.updated_by = user_id
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def delete_vaccination_schedule(db: Session, schedule_id: int, user_id: int):
    """Soft delete a vaccination schedule"""
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
    """Search vaccination schedules with various filters"""
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
    
    if search.doctor_name:
        query = query.join(Doctor, VaccinationSchedule.administering_doctor_id == Doctor.id).filter(
            or_(
                Doctor.first_name.ilike(f"%{search.doctor_name}%"),
                Doctor.last_name.ilike(f"%{search.doctor_name}%")
            )
        )
    
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

def get_upcoming_vaccinations(db: Session, days: int = 7):
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
    """Get overdue vaccinations (scheduled date passed but not administered)"""
    today = date.today()
    
    return db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date < today,
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == False
    ).order_by(VaccinationSchedule.scheduled_date.asc()).all()

def get_vaccination_calendar_events(db: Session, start_date: date, end_date: date):
    """Get vaccination schedules for calendar view"""
    schedules = get_vaccination_schedules_by_date_range(db, start_date, end_date)
    
    events = []
    for schedule in schedules:
        events.append({
            'id': schedule.id,
            'schedule_code': schedule.schedule_code,
            'patient_name': f"{schedule.patient.first_name} {schedule.patient.last_name}",
            'vaccine_name': schedule.vaccine.vaccine_name,
            'dose_number': schedule.dose_number,
            'scheduled_date': schedule.scheduled_date,
            'is_administered': schedule.is_administered,
            'patient_id': schedule.patient_id,
            'vaccine_id': schedule.vaccine_id
        })
    
    return events

def get_vaccination_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get vaccination statistics"""
    query = db.query(VaccinationSchedule).filter(VaccinationSchedule.deleted_at == None)
    
    if start_date:
        query = query.filter(VaccinationSchedule.scheduled_date >= start_date)
    if end_date:
        query = query.filter(VaccinationSchedule.scheduled_date <= end_date)
    
    total_schedules = query.count()
    administered_count = query.filter(VaccinationSchedule.is_administered == True).count()
    pending_count = query.filter(VaccinationSchedule.is_administered == False).count()
    
    # Upcoming (next 7 days)
    upcoming_count = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date >= date.today(),
        VaccinationSchedule.scheduled_date <= date.today() + timedelta(days=7),
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == False
    ).count()
    
    # Overdue
    overdue_count = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.scheduled_date < date.today(),
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == False
    ).count()
    
    # Completion rate
    completion_rate = (administered_count / total_schedules * 100) if total_schedules > 0 else 0
    
    return {
        "total_schedules": total_schedules,
        "administered_count": administered_count,
        "pending_count": pending_count,
        "upcoming_count": upcoming_count,
        "overdue_count": overdue_count,
        "completion_rate": round(completion_rate, 2)
    }

def get_vaccination_trends(db: Session, months: int = 12):
    """Get vaccination trends over time"""
    end_date = date.today()
    start_date = end_date - timedelta(days=months*30)
    
    trends = db.query(
        extract('year', VaccinationSchedule.administered_date).label('year'),
        extract('month', VaccinationSchedule.administered_date).label('month'),
        func.count(VaccinationSchedule.id).label('count')
    ).filter(
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == True,
        VaccinationSchedule.administered_date >= start_date,
        VaccinationSchedule.administered_date <= end_date
    ).group_by(
        'year', 'month'
    ).order_by('year', 'month').all()
    
    return [{'year': int(t.year), 'month': int(t.month), 'count': t.count} for t in trends]

def reschedule_vaccination(db: Session, schedule_id: int, new_date: date, user_id: int):
    """Reschedule a vaccination to a new date"""
    db_schedule = db.query(VaccinationSchedule).filter(
        VaccinationSchedule.id == schedule_id,
        VaccinationSchedule.deleted_at == None
    ).first()
    
    if not db_schedule:
        return None
    
    if db_schedule.is_administered:
        raise ValueError("Cannot reschedule an administered vaccination")
    
    db_schedule.scheduled_date = new_date
    db_schedule.updated_by = user_id
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule