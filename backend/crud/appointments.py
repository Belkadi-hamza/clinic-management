from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from backend.schemas.appointment_slots import AppointmentSlotCreate, AppointmentSlotUpdate

from ..models.appointments import Appointment, AppointmentSlot
from ..models.patients import Patient
from ..models.doctors import Doctor
from ..schemas.appointments import AppointmentCreate, AppointmentUpdate, AppointmentSearch

logger = logging.getLogger(__name__)

# Appointment Slot CRUD operations
def get_appointment_slots(db: Session, skip: int = 0, limit: int = 100):
    """Get all appointment slots"""
    return db.query(AppointmentSlot).filter(AppointmentSlot.deleted_at == None)\
        .order_by(AppointmentSlot.slot_index.asc())\
        .offset(skip).limit(limit).all()

def get_appointment_slot_by_id(db: Session, slot_id: int):
    """Get appointment slot by ID"""
    return db.query(AppointmentSlot).filter(
        AppointmentSlot.id == slot_id,
        AppointmentSlot.deleted_at == None
    ).first()

def get_appointment_slot_by_time(db: Session, slot_time: str):
    """Get appointment slot by time"""
    return db.query(AppointmentSlot).filter(
        AppointmentSlot.slot_time == slot_time,
        AppointmentSlot.deleted_at == None
    ).first()

def create_appointment_slot(db: Session, slot: AppointmentSlotCreate, user_id: int):
    """Create new appointment slot"""
    db_slot = AppointmentSlot(**slot.dict(), created_by=user_id)
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def update_appointment_slot(db: Session, slot_id: int, slot: AppointmentSlotUpdate, user_id: int):
    """Update appointment slot"""
    db_slot = db.query(AppointmentSlot).filter(
        AppointmentSlot.id == slot_id,
        AppointmentSlot.deleted_at == None
    ).first()
    
    if not db_slot:
        return None
    
    for key, value in slot.dict(exclude_unset=True).items():
        setattr(db_slot, key, value)
    
    db_slot.updated_by = user_id
    db.commit()
    db.refresh(db_slot)
    return db_slot

def delete_appointment_slot(db: Session, slot_id: int, user_id: int):
    """Soft delete appointment slot"""
    db_slot = db.query(AppointmentSlot).filter(
        AppointmentSlot.id == slot_id,
        AppointmentSlot.deleted_at == None
    ).first()
    
    if not db_slot:
        return None
    
    db_slot.deleted_at = func.now()
    db_slot.deleted_by = user_id
    db.commit()
    return db_slot

# Appointment CRUD operations
def generate_appointment_code(db: Session):
    """Generate unique appointment code"""
    from datetime import datetime
    prefix = "APT"
    date_str = datetime.now().strftime("%y%m%d")
    
    # Find the highest number for today
    today_codes = db.query(Appointment).filter(
        Appointment.appointment_code.like(f"{prefix}{date_str}%")
    ).all()
    
    if today_codes:
        max_num = max([int(code.appointment_code[-4:]) for code in today_codes])
        next_num = max_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{date_str}{next_num:04d}"

def get_appointments(db: Session, skip: int = 0, limit: int = 100):
    """Get all appointments with patient and doctor details"""
    return db.query(Appointment).filter(Appointment.deleted_at == None)\
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())\
        .offset(skip).limit(limit).all()

def get_appointment_by_id(db: Session, appointment_id: int):
    """Get appointment by ID with details"""
    return db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.deleted_at == None
    ).first()

def get_appointment_by_code(db: Session, appointment_code: str):
    """Get appointment by code"""
    return db.query(Appointment).filter(
        Appointment.appointment_code == appointment_code,
        Appointment.deleted_at == None
    ).first()

def get_appointments_by_patient(db: Session, patient_id: int):
    """Get all appointments for a patient"""
    return db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.deleted_at == None
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

def get_appointments_by_doctor(db: Session, doctor_id: int, date_from: date = None, date_to: date = None):
    """Get appointments for a doctor within date range"""
    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.deleted_at == None
    )
    
    if date_from:
        query = query.filter(Appointment.appointment_date >= date_from)
    if date_to:
        query = query.filter(Appointment.appointment_date <= date_to)
    
    return query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

def get_appointments_by_date(db: Session, appointment_date: date):
    """Get appointments for a specific date"""
    return db.query(Appointment).filter(
        Appointment.appointment_date == appointment_date,
        Appointment.deleted_at == None
    ).order_by(Appointment.appointment_time.asc()).all()

def get_available_slots(db: Session, doctor_id: int, appointment_date: date):
    """Get available time slots for a doctor on a specific date"""
    # Get all booked appointments for the doctor on the date
    booked_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.deleted_at == None,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).all()
    
    booked_slot_ids = [appt.slot_id for appt in booked_appointments if appt.slot_id]
    
    # Get all available slots
    available_slots = db.query(AppointmentSlot).filter(
        AppointmentSlot.deleted_at == None,
        AppointmentSlot.is_available == True,
        ~AppointmentSlot.id.in_(booked_slot_ids) if booked_slot_ids else True
    ).order_by(AppointmentSlot.slot_index.asc()).all()
    
    return available_slots

def create_appointment(db: Session, appointment: AppointmentCreate, user_id: int):
    """Create new appointment"""
    # Generate appointment code
    appointment_code = generate_appointment_code(db)
    
    # Create appointment
    db_appointment = Appointment(
        **appointment.dict(),
        appointment_code=appointment_code,
        created_by=user_id
    )
    
    # Mark slot as unavailable if slot_id is provided
    if appointment.slot_id:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appointment.slot_id).first()
        if slot:
            slot.is_available = False
    
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def update_appointment(db: Session, appointment_id: int, appointment: AppointmentUpdate, user_id: int):
    """Update appointment"""
    db_appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.deleted_at == None
    ).first()
    
    if not db_appointment:
        return None
    
    # Handle slot availability changes
    old_slot_id = db_appointment.slot_id
    new_slot_id = appointment.slot_id
    
    for key, value in appointment.dict(exclude_unset=True).items():
        setattr(db_appointment, key, value)
    
    db_appointment.updated_by = user_id
    
    # Update slot availability
    if old_slot_id != new_slot_id:
        # Free old slot
        if old_slot_id:
            old_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == old_slot_id).first()
            if old_slot:
                old_slot.is_available = True
        
        # Reserve new slot
        if new_slot_id:
            new_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == new_slot_id).first()
            if new_slot:
                new_slot.is_available = False
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def delete_appointment(db: Session, appointment_id: int, user_id: int):
    """Soft delete appointment"""
    db_appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.deleted_at == None
    ).first()
    
    if not db_appointment:
        return None
    
    # Free the slot
    if db_appointment.slot_id:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == db_appointment.slot_id).first()
        if slot:
            slot.is_available = True
    
    db_appointment.deleted_at = func.now()
    db_appointment.deleted_by = user_id
    db.commit()
    return db_appointment

def cancel_appointment(db: Session, appointment_id: int, user_id: int):
    """Cancel appointment and free the slot"""
    db_appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.deleted_at == None
    ).first()
    
    if not db_appointment:
        return None
    
    # Free the slot
    if db_appointment.slot_id:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == db_appointment.slot_id).first()
        if slot:
            slot.is_available = True
    
    db_appointment.status = 'cancelled'
    db_appointment.updated_by = user_id
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def complete_appointment(db: Session, appointment_id: int, user_id: int):
    """Mark appointment as completed"""
    db_appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.deleted_at == None
    ).first()
    
    if not db_appointment:
        return None
    
    db_appointment.status = 'completed'
    db_appointment.updated_by = user_id
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def search_appointments(db: Session, search: AppointmentSearch, skip: int = 0, limit: int = 100):
    """Search appointments with filters"""
    query = db.query(Appointment).filter(Appointment.deleted_at == None)
    
    if search.patient_name:
        query = query.join(Patient).filter(
            or_(
                Patient.first_name.ilike(f"%{search.patient_name}%"),
                Patient.last_name.ilike(f"%{search.patient_name}%")
            )
        )
    
    if search.doctor_name:
        query = query.join(Doctor).filter(
            or_(
                Doctor.first_name.ilike(f"%{search.doctor_name}%"),
                Doctor.last_name.ilike(f"%{search.doctor_name}%")
            )
        )
    
    if search.date_from:
        query = query.filter(Appointment.appointment_date >= search.date_from)
    
    if search.date_to:
        query = query.filter(Appointment.appointment_date <= search.date_to)
    
    if search.status:
        query = query.filter(Appointment.status == search.status)
    
    return query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())\
        .offset(skip).limit(limit).all()

def get_appointment_stats(db: Session, start_date: date = None, end_date: date = None):
    """Get appointment statistics"""
    query = db.query(Appointment).filter(Appointment.deleted_at == None)
    
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date)
    
    total = query.count()
    scheduled = query.filter(Appointment.status == 'scheduled').count()
    confirmed = query.filter(Appointment.status == 'confirmed').count()
    completed = query.filter(Appointment.status == 'completed').count()
    cancelled = query.filter(Appointment.status == 'cancelled').count()
    no_show = query.filter(Appointment.status == 'no_show').count()
    
    return {
        "total": total,
        "scheduled": scheduled,
        "confirmed": confirmed,
        "completed": completed,
        "cancelled": cancelled,
        "no_show": no_show
    }

def get_todays_appointments(db: Session):
    """Get today's appointments"""
    today = date.today()
    return db.query(Appointment).filter(
        Appointment.appointment_date == today,
        Appointment.deleted_at == None,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).order_by(Appointment.appointment_time.asc()).all()

def get_upcoming_appointments(db: Session, days: int = 7):
    """Get upcoming appointments for the next n days"""
    today = date.today()
    end_date = today + timedelta(days=days)
    
    return db.query(Appointment).filter(
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= end_date,
        Appointment.deleted_at == None,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()