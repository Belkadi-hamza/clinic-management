from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from backend.models.appointments import Appointment

from ..db import get_db
from ..schemas.appointments import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, 
    AppointmentSlotCreate, AppointmentSlotUpdate, AppointmentSlotResponse,
    AppointmentSearch, AppointmentStats, DailySchedule, TimeSlot,
    AppointmentWithDetails
)
from ..crud.appointments import (
    get_appointments, get_appointment_by_id, get_appointment_by_code,
    create_appointment, update_appointment, delete_appointment,
    cancel_appointment, complete_appointment, search_appointments,
    get_appointment_stats, get_todays_appointments, get_upcoming_appointments,
    get_appointments_by_patient, get_appointments_by_doctor, get_appointments_by_date,
    get_available_slots, get_appointment_slots, get_appointment_slot_by_id,
    create_appointment_slot, update_appointment_slot, delete_appointment_slot
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouter()

# Appointment Slot Endpoints
@router.get("/slots/", response_model=List[AppointmentSlotResponse])
def read_appointment_slots(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all appointment slots"""
    require_permission(current_user, "appointments", "read")
    slots = get_appointment_slots(db, skip=skip, limit=limit)
    return slots

@router.get("/slots/{slot_id}", response_model=AppointmentSlotResponse)
def read_appointment_slot(
    slot_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appointment slot by ID"""
    require_permission(current_user, "appointments", "read")
    slot = get_appointment_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found")
    return slot

@router.post("/slots/", response_model=AppointmentSlotResponse)
def create_appointment_slot_endpoint(
    slot: AppointmentSlotCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new appointment slot"""
    require_permission(current_user, "appointments", "create")
    db_slot = create_appointment_slot(db, slot, current_user.id)
    return db_slot

@router.put("/slots/{slot_id}", response_model=AppointmentSlotResponse)
def update_appointment_slot_endpoint(
    slot_id: int,
    slot: AppointmentSlotUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update appointment slot"""
    require_permission(current_user, "appointments", "update")
    db_slot = update_appointment_slot(db, slot_id, slot, current_user.id)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found")
    return db_slot

@router.delete("/slots/{slot_id}")
def delete_appointment_slot_endpoint(
    slot_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete appointment slot"""
    require_permission(current_user, "appointments", "delete")
    db_slot = delete_appointment_slot(db, slot_id, current_user.id)
    if not db_slot:
        raise HTTPException(status_code=404, detail="Appointment slot not found")
    return {"message": "Appointment slot deleted successfully"}

# Appointment Endpoints
@router.get("/", response_model=List[AppointmentResponse])
def read_appointments(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all appointments"""
    require_permission(current_user, "appointments", "read")
    appointments = get_appointments(db, skip=skip, limit=limit)
    
    # Enhance response with patient and doctor names
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        # Add patient name
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        # Add doctor name
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments

@router.get("/{appointment_id}", response_model=AppointmentWithDetails)
def read_appointment(
    appointment_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appointment by ID"""
    require_permission(current_user, "appointments", "read")
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Build detailed response
    response = AppointmentWithDetails.from_orm(appointment)
    
    # Add patient details
    if appointment.patient:
        response.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
        response.patient_code = appointment.patient.patient_code
        response.patient_details = {
            "id": appointment.patient.id,
            "code": appointment.patient.patient_code,
            "name": f"{appointment.patient.first_name} {appointment.patient.last_name}",
            "date_of_birth": appointment.patient.date_of_birth,
            "gender": appointment.patient.gender
        }
    
    # Add doctor details
    if appointment.doctor:
        response.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
        response.doctor_code = appointment.doctor.doctor_code
        response.doctor_details = {
            "id": appointment.doctor.id,
            "code": appointment.doctor.doctor_code,
            "name": f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            "specialization": appointment.doctor.specialization
        }
    
    # Add slot details
    if appointment.slot:
        response.slot_details = {
            "id": appointment.slot.id,
            "time": appointment.slot.slot_time.strftime("%H:%M"),
            "slot_index": appointment.slot.slot_index
        }
    
    return response

@router.post("/", response_model=AppointmentResponse)
def create_appointment_endpoint(
    appointment: AppointmentCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new appointment"""
    require_permission(current_user, "appointments", "create")
    
    # Check if slot is available
    if appointment.slot_id:
        slot = get_appointment_slot_by_id(db, appointment.slot_id)
        if not slot or not slot.is_available:
            raise HTTPException(
                status_code=400, 
                detail="Selected time slot is not available"
            )
    
    # Check for conflicting appointments
    existing_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.appointment_time == appointment.appointment_time,
        Appointment.deleted_at == None,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).first()
    
    if existing_appointment:
        raise HTTPException(
            status_code=400,
            detail="Doctor already has an appointment at this time"
        )
    
    db_appointment = create_appointment(db, appointment, current_user.id)
    
    # Enhance response
    response = AppointmentResponse.from_orm(db_appointment)
    if db_appointment.patient:
        response.patient_name = f"{db_appointment.patient.first_name} {db_appointment.patient.last_name}"
        response.patient_code = db_appointment.patient.patient_code
    if db_appointment.doctor:
        response.doctor_name = f"{db_appointment.doctor.first_name} {db_appointment.doctor.last_name}"
        response.doctor_code = db_appointment.doctor.doctor_code
    
    return response

@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment_endpoint(
    appointment_id: int,
    appointment: AppointmentUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update appointment"""
    require_permission(current_user, "appointments", "update")
    
    # Check for conflicting appointments if time/date/doctor is being changed
    if any([appointment.doctor_id, appointment.appointment_date, appointment.appointment_time]):
        existing_appointment = get_appointment_by_id(db, appointment_id)
        if not existing_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        doctor_id = appointment.doctor_id or existing_appointment.doctor_id
        appointment_date = appointment.appointment_date or existing_appointment.appointment_date
        appointment_time = appointment.appointment_time or existing_appointment.appointment_time
        
        conflicting_appointment = db.query(Appointment).filter(
            Appointment.id != appointment_id,
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.deleted_at == None,
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).first()
        
        if conflicting_appointment:
            raise HTTPException(
                status_code=400,
                detail="Doctor already has an appointment at this time"
            )
    
    db_appointment = update_appointment(db, appointment_id, appointment, current_user.id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Enhance response
    response = AppointmentResponse.from_orm(db_appointment)
    if db_appointment.patient:
        response.patient_name = f"{db_appointment.patient.first_name} {db_appointment.patient.last_name}"
        response.patient_code = db_appointment.patient.patient_code
    if db_appointment.doctor:
        response.doctor_name = f"{db_appointment.doctor.first_name} {db_appointment.doctor.last_name}"
        response.doctor_code = db_appointment.doctor.doctor_code
    
    return response

@router.delete("/{appointment_id}")
def delete_appointment_endpoint(
    appointment_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete appointment"""
    require_permission(current_user, "appointments", "delete")
    db_appointment = delete_appointment(db, appointment_id, current_user.id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}

@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment_endpoint(
    appointment_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel appointment"""
    require_permission(current_user, "appointments", "update")
    db_appointment = cancel_appointment(db, appointment_id, current_user.id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    response = AppointmentResponse.from_orm(db_appointment)
    if db_appointment.patient:
        response.patient_name = f"{db_appointment.patient.first_name} {db_appointment.patient.last_name}"
        response.patient_code = db_appointment.patient.patient_code
    if db_appointment.doctor:
        response.doctor_name = f"{db_appointment.doctor.first_name} {db_appointment.doctor.last_name}"
        response.doctor_code = db_appointment.doctor.doctor_code
    
    return response

@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
def complete_appointment_endpoint(
    appointment_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark appointment as completed"""
    require_permission(current_user, "appointments", "update")
    db_appointment = complete_appointment(db, appointment_id, current_user.id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    response = AppointmentResponse.from_orm(db_appointment)
    if db_appointment.patient:
        response.patient_name = f"{db_appointment.patient.first_name} {db_appointment.patient.last_name}"
        response.patient_code = db_appointment.patient.patient_code
    if db_appointment.doctor:
        response.doctor_name = f"{db_appointment.doctor.first_name} {db_appointment.doctor.last_name}"
        response.doctor_code = db_appointment.doctor.doctor_code
    
    return response

# Search and Filter Endpoints
@router.post("/search/", response_model=List[AppointmentResponse])
def search_appointments_endpoint(
    search: AppointmentSearch,
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search appointments with filters"""
    require_permission(current_user, "appointments", "read")
    appointments = search_appointments(db, search, skip=skip, limit=limit)
    
    # Enhance response
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments

@router.get("/patient/{patient_id}", response_model=List[AppointmentResponse])
def read_patient_appointments(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all appointments for a patient"""
    require_permission(current_user, "appointments", "read")
    appointments = get_appointments_by_patient(db, patient_id)
    
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments

@router.get("/doctor/{doctor_id}", response_model=List[AppointmentResponse])
def read_doctor_appointments(
    doctor_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appointments for a doctor"""
    require_permission(current_user, "appointments", "read")
    appointments = get_appointments_by_doctor(db, doctor_id, date_from, date_to)
    
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments

@router.get("/date/{appointment_date}", response_model=List[AppointmentResponse])
def read_date_appointments(
    appointment_date: date,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appointments for a specific date"""
    require_permission(current_user, "appointments", "read")
    appointments = get_appointments_by_date(db, appointment_date)
    
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments

# Availability Endpoints
@router.get("/availability/{doctor_id}/{appointment_date}", response_model=DailySchedule)
def get_doctor_availability(
    doctor_id: int,
    appointment_date: date,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available time slots for a doctor on a specific date"""
    require_permission(current_user, "appointments", "read")
    
    # Check if date is in the past
    if appointment_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot check availability for past dates")
    
    available_slots = get_available_slots(db, doctor_id, appointment_date)
    
    time_slots = []
    for slot in available_slots:
        time_slots.append(TimeSlot(
            time=slot.slot_time.strftime("%H:%M"),
            available=slot.is_available,
            slot_id=slot.id
        ))
    
    return DailySchedule(date=appointment_date, slots=time_slots)

# Statistics Endpoints
@router.get("/stats/overview", response_model=AppointmentStats)
def get_appointment_stats_overview(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appointment statistics"""
    require_permission(current_user, "appointments", "read")
    stats = get_appointment_stats(db, start_date, end_date)
    return AppointmentStats(**stats)

@router.get("/today/", response_model=List[AppointmentResponse])
def get_todays_appointments_endpoint(
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's appointments"""
    require_permission(current_user, "appointments", "read")
    appointments = get_todays_appointments(db)
    
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments

@router.get("/upcoming/", response_model=List[AppointmentResponse])
def get_upcoming_appointments_endpoint(
    days: int = Query(7, ge=1, le=30),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming appointments"""
    require_permission(current_user, "appointments", "read")
    appointments = get_upcoming_appointments(db, days)
    
    enhanced_appointments = []
    for appointment in appointments:
        enhanced_data = AppointmentResponse.from_orm(appointment)
        
        if appointment.patient:
            enhanced_data.patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
            enhanced_data.patient_code = appointment.patient.patient_code
        
        if appointment.doctor:
            enhanced_data.doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            enhanced_data.doctor_code = appointment.doctor.doctor_code
        
        enhanced_appointments.append(enhanced_data)
    
    return enhanced_appointments