from sqlalchemy.orm import Session
from ..models.departments import Department
from ..schemas.departments import DepartmentCreate, DepartmentUpdate
from datetime import datetime


def get_departments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Department).filter(Department.deleted_at.is_(None)).offset(skip).limit(limit).all()


def get_department(db: Session, department_id: int):
    return db.query(Department).filter(Department.id == department_id, Department.deleted_at.is_(None)).first()


def create_department(db: Session, department: DepartmentCreate):
    db_department = Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


def update_department(db: Session, department_id: int, department: DepartmentUpdate):
    db_department = db.query(Department).filter(Department.id == department_id, Department.deleted_at.is_(None)).first()
    if not db_department:
        return None
    for key, value in department.dict(exclude_unset=True).items():
        setattr(db_department, key, value)
    db.commit()
    db.refresh(db_department)
    return db_department


def delete_department(db: Session, department_id: int, deleted_by: int):
    db_department = db.query(Department).filter(Department.id == department_id, Department.deleted_at.is_(None)).first()
    if not db_department:
        return None
    db_department.deleted_by = deleted_by
    db_department.deleted_at = datetime.utcnow()
    db.commit()
    return db_department
