from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from ..db import get_db
from ..schemas.vaccination_schedules import (
    VaccinationScheduleCreate, VaccinationScheduleUpdate, VaccinationScheduleResponse,
    VaccinationScheduleAdminister, VaccinationScheduleWithDetails,
    VaccinationScheduleSearch, VaccinationStats, PatientVaccinationStatus,
    VaccinationDueAlert, VaccinationCalendarEvent, BulkVaccinationScheduleCreate,
    VaccinationReport
)
from ..crud.vaccination_schedules import (
    get_vaccination_schedules, get_vaccination_schedule_by_id, get_vaccination_schedule_by_code,
    get_vaccination_schedules_by_patient, get_vaccination_schedules_by_vaccine,
    get_vaccination_schedules_by_doctor, get_vaccination_schedules_by_date_range,
    get_patient_vaccination_status, create_vaccination_schedule, create_bulk_vaccination_schedules,
    update_vaccination_schedule, administer_vaccination, cancel_vaccination_administration,
    delete_vaccination_schedule, search_vaccination_schedules, get_upcoming_vaccinations,
    get_overdue_vaccinations, get_vaccination_calendar_events, get_vaccination_stats,
    get_vaccination_trends, reschedule_vaccination
)
from ..deps import get_current_user, require_permission
from ..models.system_users import SystemUser

router = APIRouterouter = APIRouter()

@router.get("/", response_model=List[VaccinationScheduleResponse])
def read_vaccination_schedules(
    skip: int = 0,
    limit: int = 100,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vaccination schedules"""
    require_permission(current_user, "patients", "read")
    schedules = get_vaccination_schedules(db, skip=skip, limit=limit)
    
    enhanced_schedules = []
    for schedule in schedules:
        enhanced_data = VaccinationScheduleResponse.from_orm(schedule)
        
        # Add patient information
        if schedule.patient:
            enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
            enhanced_data.patient_code = schedule.patient.patient_code
            enhanced_data.patient_gender = schedule.patient.gender
            
            # Calculate patient age
            if schedule.patient.date_of_birth:
                today = date.today()
                age = today.year - schedule.patient.date_of_birth.year
                if today.month < schedule.patient.date_of_birth.month or (
                    today.month == schedule.patient.date_of_birth.month and 
                    today.day < schedule.patient.date_of_birth.day
                ):
                    age -= 1
                enhanced_data.patient_age = age
        
        # Add vaccine information
        if schedule.vaccine:
            enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
            enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
        
        # Add doctor information
        if schedule.administering_doctor:
            enhanced_data.doctor_name = f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}"
        
        enhanced_schedules.append(enhanced_data)
    
    return enhanced_schedules

@router.get("/{schedule_id}", response_model=VaccinationScheduleWithDetails)
def read_vaccination_schedule(
    schedule_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination schedule by ID with full details"""
    require_permission(current_user, "patients", "read")
    schedule = get_vaccination_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    
    enhanced_data = VaccinationScheduleWithDetails.from_orm(schedule)
    
    # Add patient details
    if schedule.patient:
        enhanced_data.patient_name = f"{schedule.patient.first_name} {schedule.patient.last_name}"
        enhanced_data.patient_code = schedule.patient.patient_code
        enhanced_data.patient_details = {
            "id": schedule.patient.id,
            "code": schedule.patient.patient_code,
            "name": f"{schedule.patient.first_name} {schedule.patient.last_name}",
            "date_of_birth": schedule.patient.date_of_birth,
            "gender": schedule.patient.gender,
            "contact_info": schedule.patient.mobile_phone or schedule.patient.email
        }
    
    # Add vaccine details
    if schedule.vaccine:
        enhanced_data.vaccine_name = schedule.vaccine.vaccine_name
        enhanced_data.vaccine_code = schedule.vaccine.vaccine_code
        enhanced_data.vaccine_details = {
            "id": schedule.vaccine.id,
            "code": schedule.vaccine.vaccine_code,
            "name": schedule.vaccine.vaccine_name,
            "manufacturer": schedule.vaccine.manufacturer,
            "total_doses_required": schedule.vaccine.total_doses_required,
            "booster_required": schedule.vaccine.booster_required
        }
    
    # Add doctor details
    if schedule.administering_doctor:
        enhanced_data.doctor_name = f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}"
        enhanced_data.doctor_details = {
            "id": schedule.administering_doctor.id,
            "name": f"{schedule.administering_doctor.first_name} {schedule.administering_doctor.last_name}",
            "specialization": schedule.administering_doctor.specialization
        }
    
    return enhanced_data

@router.get("/patient/{patient_id}", response_model=List[VaccinationScheduleResponse])
def read_patient_vaccination_schedules(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vaccination schedules for a specific patient"""
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

@router.get("/patient/{patient_id}/status", response_model=List[PatientVaccinationStatus])
def read_patient_vaccination_status(
    patient_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive vaccination status for a patient"""
    require_permission(current_user, "patients", "read")
    status = get_patient_vaccination_status(db, patient_id)
    return status

@router.get("/vaccine/{vaccine_id}", response_model=List[VaccinationScheduleResponse])
def read_vaccine_schedules(
    vaccine_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vaccination schedules for a specific vaccine"""
    require_permission(current_user, "patients", "read")
    schedules = get_vaccination_schedules_by_vaccine(db, vaccine_id)
    
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

@router.post("/", response_model=VaccinationScheduleResponse)
def create_vaccination_schedule_endpoint(
    schedule: VaccinationScheduleCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new vaccination schedule"""
    require_permission(current_user, "patients", "create")
    try:
        db_schedule = create_vaccination_schedule(db, schedule, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = VaccinationScheduleResponse.from_orm(db_schedule)
    
    if db_schedule.patient:
        enhanced_data.patient_name = f"{db_schedule.patient.first_name} {db_schedule.patient.last_name}"
        enhanced_data.patient_code = db_schedule.patient.patient_code
    
    if db_schedule.vaccine:
        enhanced_data.vaccine_name = db_schedule.vaccine.vaccine_name
        enhanced_data.vaccine_code = db_schedule.vaccine.vaccine_code
    
    return enhanced_data

@router.post("/bulk", response_model=List[VaccinationScheduleResponse])
def create_bulk_vaccination_schedules_endpoint(
    bulk_data: BulkVaccinationScheduleCreate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple vaccination schedules for a patient"""
    require_permission(current_user, "patients", "create")
    schedules = create_bulk_vaccination_schedules(db, bulk_data.patient_id, bulk_data.schedules, current_user.id)
    
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

@router.put("/{schedule_id}", response_model=VaccinationScheduleResponse)
def update_vaccination_schedule_endpoint(
    schedule_id: int,
    schedule: VaccinationScheduleUpdate,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a vaccination schedule"""
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

@router.post("/{schedule_id}/administer", response_model=VaccinationScheduleResponse)
def administer_vaccination_endpoint(
    schedule_id: int,
    administration: VaccinationScheduleAdminister,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Administer a vaccination"""
    require_permission(current_user, "patients", "update")
    try:
        db_schedule = administer_vaccination(db, schedule_id, administration, current_user.id)
        if not db_schedule:
            raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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

@router.post("/{schedule_id}/cancel-administration", response_model=VaccinationScheduleResponse)
def cancel_vaccination_administration_endpoint(
    schedule_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel vaccination administration"""
    require_permission(current_user, "patients", "update")
    try:
        db_schedule = cancel_vaccination_administration(db, schedule_id, current_user.id)
        if not db_schedule:
            raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    enhanced_data = VaccinationScheduleResponse.from_orm(db_schedule)
    
    if db_schedule.patient:
        enhanced_data.patient_name = f"{db_schedule.patient.first_name} {db_schedule.patient.last_name}"
        enhanced_data.patient_code = db_schedule.patient.patient_code
    
    if db_schedule.vaccine:
        enhanced_data.vaccine_name = db_schedule.vaccine.vaccine_name
        enhanced_data.vaccine_code = db_schedule.vaccine.vaccine_code
    
    return enhanced_data

@router.post("/{schedule_id}/reschedule")
def reschedule_vaccination_endpoint(
    schedule_id: int,
    new_date: date,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reschedule a vaccination"""
    require_permission(current_user, "patients", "update")
    try:
        db_schedule = reschedule_vaccination(db, schedule_id, new_date, current_user.id)
        if not db_schedule:
            raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Vaccination rescheduled successfully", "new_date": new_date}

@router.delete("/{schedule_id}")
def delete_vaccination_schedule_endpoint(
    schedule_id: int,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a vaccination schedule"""
    require_permission(current_user, "patients", "delete")
    db_schedule = delete_vaccination_schedule(db, schedule_id, current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Vaccination schedule not found")
    return {"message": "Vaccination schedule deleted successfully"}

@router.post("/search/", response_model=List[VaccinationScheduleResponse])
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
        contact_info = schedule.patient.mobile_phone or schedule.patient.email or "No contact info"
        
        alerts.append(VaccinationDueAlert(
            patient_id=schedule.patient_id,
            patient_name=f"{schedule.patient.first_name} {schedule.patient.last_name}",
            vaccine_name=schedule.vaccine.vaccine_name,
            dose_number=schedule.dose_number,
            scheduled_date=schedule.scheduled_date,
            days_until_due=days_until_due,
            contact_info=contact_info
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
        contact_info = schedule.patient.mobile_phone or schedule.patient.email or "No contact info"
        
        alerts.append(VaccinationDueAlert(
            patient_id=schedule.patient_id,
            patient_name=f"{schedule.patient.first_name} {schedule.patient.last_name}",
            vaccine_name=schedule.vaccine.vaccine_name,
            dose_number=schedule.dose_number,
            scheduled_date=schedule.scheduled_date,
            days_until_due=-days_overdue,  # Negative to indicate overdue
            contact_info=contact_info
        ))
    
    return alerts

@router.get("/calendar/events", response_model=List[VaccinationCalendarEvent])
def get_vaccination_calendar_events_endpoint(
    start_date: date,
    end_date: date,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination events for calendar view"""
    require_permission(current_user, "patients", "read")
    events = get_vaccination_calendar_events(db, start_date, end_date)
    return events

@router.get("/stats/overview", response_model=VaccinationStats)
def get_vaccination_stats_overview(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination statistics overview"""
    require_permission(current_user, "patients", "read")
    stats = get_vaccination_stats(db, start_date, end_date)
    return VaccinationStats(**stats)

@router.get("/reports/trends")
def get_vaccination_trends_report(
    months: int = Query(12, ge=1, le=36),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vaccination trends report"""
    require_permission(current_user, "reports", "read")
    trends = get_vaccination_trends(db, months)
    return {"trends": trends}

@router.get("/reports/comprehensive")
def get_comprehensive_vaccination_report(
    year: int = Query(None, description="Year for report"),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive vaccination report"""
    require_permission(current_user, "reports", "read")
    
    if not year:
        year = date.today().year
    
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Get basic stats
    stats = get_vaccination_stats(db, start_date, end_date)
    
    # Get schedules by vaccine
    schedules_by_vaccine = db.query(
        Vaccine.vaccine_name,
        func.count(VaccinationSchedule.id).label('total'),
        func.sum(case((VaccinationSchedule.is_administered == True, 1), else_=0)).label('administered')
    ).join(VaccinationSchedule).filter(
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.scheduled_date >= start_date,
        VaccinationSchedule.scheduled_date <= end_date
    ).group_by(Vaccine.vaccine_name).all()
    
    # Get monthly trends
    monthly_trends = db.query(
        extract('month', VaccinationSchedule.administered_date).label('month'),
        func.count(VaccinationSchedule.id).label('count')
    ).filter(
        VaccinationSchedule.deleted_at == None,
        VaccinationSchedule.is_administered == True,
        VaccinationSchedule.administered_date >= start_date,
        VaccinationSchedule.administered_date <= end_date
    ).group_by('month').order_by('month').all()
    
    report = VaccinationReport(
        period=f"{year}",
        total_administered=stats['administered_count'],
        by_vaccine=[
            {
                'vaccine_name': item.vaccine_name,
                'total': item.total,
                'administered': item.administered,
                'completion_rate': round((item.administered / item.total * 100) if item.total > 0 else 0, 2)
            }
            for item in schedules_by_vaccine
        ],
        by_month=[
            {
                'month': int(item.month),
                'count': item.count
            }
            for item in monthly_trends
        ],
        completion_rates=[
            {
                'metric': 'Overall Completion',
                'rate': stats['completion_rate']
            },
            {
                'metric': 'Administered Rate',
                'rate': round((stats['administered_count'] / stats['total_schedules'] * 100) if stats['total_schedules'] > 0 else 0, 2)
            }
        ]
    )
    
    return report