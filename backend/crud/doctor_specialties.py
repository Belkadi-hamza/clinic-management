from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Tuple, Dict, Any

from ..models.doctor_specialties import DoctorSpecialty
from ..models.doctors import Doctor
from ..schemas.doctor_specialties import DoctorSpecialtyCreate, DoctorSpecialtyUpdate

# Doctor Specialty CRUD operations
def get_doctor_specialties(
    db: Session, 
    doctor_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[DoctorSpecialty], int]:
    """Get all doctor specialties with optional doctor filter"""
    query = db.query(DoctorSpecialty).filter(DoctorSpecialty.deleted_at == None)
    
    if doctor_id:
        query = query.filter(DoctorSpecialty.doctor_id == doctor_id)
    
    total = query.count()
    doctor_specialties = query.order_by(DoctorSpecialty.specialty).offset(skip).limit(limit).all()
    return doctor_specialties, total

def get_doctor_specialty_by_id(db: Session, doctor_specialty_id: int) -> Optional[DoctorSpecialty]:
    """Get a specific doctor specialty by ID"""
    return db.query(DoctorSpecialty).filter(
        DoctorSpecialty.id == doctor_specialty_id,
        DoctorSpecialty.deleted_at == None
    ).first()

def get_doctor_specialties_by_doctor(db: Session, doctor_id: int) -> List[DoctorSpecialty]:
    """Get all specialties for a specific doctor"""
    return db.query(DoctorSpecialty).filter(
        DoctorSpecialty.doctor_id == doctor_id,
        DoctorSpecialty.deleted_at == None
    ).order_by(DoctorSpecialty.specialty).all()

def create_doctor_specialty(db: Session, doctor_specialty: DoctorSpecialtyCreate, user_id: int) -> Tuple[Optional[DoctorSpecialty], Optional[str]]:
    """Add a specialty to a doctor"""
    # Check if doctor exists
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_specialty.doctor_id,
        Doctor.deleted_at == None
    ).first()
    
    if not doctor:
        return None, "Doctor not found"
    
    # Check if specialty is already assigned to this doctor
    existing = db.query(DoctorSpecialty).filter(
        DoctorSpecialty.doctor_id == doctor_specialty.doctor_id,
        DoctorSpecialty.specialty == doctor_specialty.specialty,
        DoctorSpecialty.deleted_at == None
    ).first()
    
    if existing:
        return None, f"Specialty '{doctor_specialty.specialty}' is already assigned to this doctor"
    
    db_doctor_specialty = DoctorSpecialty(
        doctor_id=doctor_specialty.doctor_id,
        specialty=doctor_specialty.specialty,
        created_by=user_id
    )
    db.add(db_doctor_specialty)
    db.commit()
    db.refresh(db_doctor_specialty)
    return db_doctor_specialty, None

def update_doctor_specialty(db: Session, doctor_specialty_id: int, doctor_specialty: DoctorSpecialtyUpdate, user_id: int) -> Tuple[Optional[DoctorSpecialty], Optional[str]]:
    """Update a doctor specialty"""
    db_doctor_specialty = get_doctor_specialty_by_id(db, doctor_specialty_id)
    if not db_doctor_specialty:
        return None, "Doctor specialty not found"
    
    # Check if new specialty name conflicts with existing one for this doctor
    if doctor_specialty.specialty and doctor_specialty.specialty != db_doctor_specialty.specialty:
        existing = db.query(DoctorSpecialty).filter(
            DoctorSpecialty.doctor_id == db_doctor_specialty.doctor_id,
            DoctorSpecialty.specialty == doctor_specialty.specialty,
            DoctorSpecialty.deleted_at == None
        ).first()
        
        if existing:
            return None, f"Specialty '{doctor_specialty.specialty}' is already assigned to this doctor"
    
    update_data = doctor_specialty.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_doctor_specialty, key, value)
    
    db.commit()
    db.refresh(db_doctor_specialty)
    return db_doctor_specialty, None

def delete_doctor_specialty(db: Session, doctor_specialty_id: int, user_id: int) -> Tuple[Optional[DoctorSpecialty], Optional[str]]:
    """Remove a specialty from a doctor"""
    db_doctor_specialty = get_doctor_specialty_by_id(db, doctor_specialty_id)
    if not db_doctor_specialty:
        return None, "Doctor specialty not found"
    
    db_doctor_specialty.deleted_at = func.now()
    db_doctor_specialty.deleted_by = user_id
    db.commit()
    return db_doctor_specialty, None

def bulk_create_doctor_specialties(db: Session, bulk_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Bulk add multiple specialties to a doctor"""
    doctor_id = bulk_data['doctor_id']
    specialties = bulk_data['specialties']
    
    created = []
    errors = []
    
    # Check if doctor exists
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.deleted_at == None
    ).first()
    
    if not doctor:
        return {
            "created": [],
            "errors": [{"error": "Doctor not found"}],
            "total_created": 0,
            "total_errors": 1
        }
    
    for specialty_name in specialties:
        # Validate specialty name
        if not specialty_name.strip():
            errors.append({
                "specialty": specialty_name,
                "error": "Specialty cannot be empty"
            })
            continue
        
        if len(specialty_name) > 100:
            errors.append({
                "specialty": specialty_name,
                "error": "Specialty cannot exceed 100 characters"
            })
            continue
        
        # Check if specialty is already assigned to this doctor
        existing = db.query(DoctorSpecialty).filter(
            DoctorSpecialty.doctor_id == doctor_id,
            DoctorSpecialty.specialty == specialty_name.strip(),
            DoctorSpecialty.deleted_at == None
        ).first()
        
        if existing:
            errors.append({
                "specialty": specialty_name,
                "error": f"Specialty '{specialty_name}' is already assigned to this doctor"
            })
            continue
        
        try:
            db_doctor_specialty = DoctorSpecialty(
                doctor_id=doctor_id,
                specialty=specialty_name.strip(),
                created_by=user_id
            )
            db.add(db_doctor_specialty)
            created.append(db_doctor_specialty)
        except Exception as e:
            errors.append({
                "specialty": specialty_name,
                "error": str(e)
            })
    
    if created:
        db.commit()
        # Refresh all created doctor specialties to get their IDs
        for ds in created:
            db.refresh(ds)
    
    return {
        "created": created,
        "errors": errors,
        "total_created": len(created),
        "total_errors": len(errors)
    }

def get_all_specialties(db: Session) -> List[str]:
    """Get all unique specialty names"""
    specialties = db.query(DoctorSpecialty.specialty).filter(
        DoctorSpecialty.deleted_at == None
    ).distinct().order_by(DoctorSpecialty.specialty).all()
    
    return [specialty[0] for specialty in specialties]

def search_specialties(db: Session, query: str, limit: int = 10) -> List[str]:
    """Search specialties by name"""
    specialties = db.query(DoctorSpecialty.specialty).filter(
        DoctorSpecialty.deleted_at == None,
        DoctorSpecialty.specialty.ilike(f"%{query}%")
    ).distinct().order_by(DoctorSpecialty.specialty).limit(limit).all()
    
    return [specialty[0] for specialty in specialties]

def get_specialty_stats(db: Session) -> List[Dict[str, Any]]:
    """Get statistics for specialties"""
    stats = db.query(
        DoctorSpecialty.specialty,
        func.count(DoctorSpecialty.id).label('doctor_count')
    ).filter(
        DoctorSpecialty.deleted_at == None
    ).group_by(
        DoctorSpecialty.specialty
    ).order_by(
        desc('doctor_count')
    ).all()
    
    total_doctors = db.query(Doctor).filter(Doctor.deleted_at == None).count()
    
    result = []
    for stat in stats:
        percentage = (stat.doctor_count / total_doctors * 100) if total_doctors > 0 else 0
        result.append({
            "specialty": stat.specialty,
            "doctor_count": stat.doctor_count,
            "percentage": round(percentage, 2)
        })
    
    return result

def get_doctors_by_specialty(db: Session, specialty: str) -> List[Doctor]:
    """Get all doctors with a specific specialty"""
    doctors = db.query(Doctor).join(
        DoctorSpecialty, Doctor.id == DoctorSpecialty.doctor_id
    ).filter(
        DoctorSpecialty.specialty == specialty,
        DoctorSpecialty.deleted_at == None,
        Doctor.deleted_at == None
    ).order_by(Doctor.first_name, Doctor.last_name).all()
    
    return doctors

def get_doctor_specialties_summary(db: Session, doctor_id: int) -> Dict[str, Any]:
    """Get summary of specialties for a doctor"""
    specialties = get_doctor_specialties_by_doctor(db, doctor_id)
    
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.deleted_at == None
    ).first()
    
    if not doctor:
        return None
    
    specialty_list = [spec.specialty for spec in specialties]
    
    return {
        "doctor_id": doctor_id,
        "doctor_name": f"{doctor.first_name} {doctor.last_name}",
        "specialties": specialty_list,
        "total_specialties": len(specialty_list)
    }

def search_doctor_specialties(
    db: Session, 
    specialty: Optional[str] = None,
    doctor_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[DoctorSpecialty], int]:
    """Search doctor specialties with various filters"""
    query = db.query(DoctorSpecialty).join(
        Doctor, DoctorSpecialty.doctor_id == Doctor.id
    ).filter(
        DoctorSpecialty.deleted_at == None,
        Doctor.deleted_at == None
    )
    
    # Apply filters
    if specialty:
        query = query.filter(DoctorSpecialty.specialty.ilike(f"%{specialty}%"))
    
    if doctor_name:
        query = query.filter(
            or_(
                Doctor.first_name.ilike(f"%{doctor_name}%"),
                Doctor.last_name.ilike(f"%{doctor_name}%")
            )
        )
    
    total = query.count()
    doctor_specialties = query.order_by(DoctorSpecialty.specialty).offset(skip).limit(limit).all()
    
    return doctor_specialties, total

def replace_doctor_specialties(db: Session, doctor_id: int, specialties: List[str], user_id: int) -> Dict[str, Any]:
    """Replace all specialties for a doctor (delete existing and add new)"""
    # Get existing specialties
    existing_specialties = get_doctor_specialties_by_doctor(db, doctor_id)
    
    # Soft delete existing specialties
    for existing in existing_specialties:
        existing.deleted_at = func.now()
        existing.deleted_by = user_id
    
    # Add new specialties
    created = []
    errors = []
    
    for specialty_name in specialties:
        if not specialty_name.strip():
            continue
        
        try:
            db_doctor_specialty = DoctorSpecialty(
                doctor_id=doctor_id,
                specialty=specialty_name.strip(),
                created_by=user_id
            )
            db.add(db_doctor_specialty)
            created.append(db_doctor_specialty)
        except Exception as e:
            errors.append({
                "specialty": specialty_name,
                "error": str(e)
            })
    
    db.commit()
    
    # Refresh created specialties
    for ds in created:
        db.refresh(ds)
    
    return {
        "created": created,
        "errors": errors,
        "deleted_count": len(existing_specialties),
        "total_created": len(created),
        "total_errors": len(errors)
    }