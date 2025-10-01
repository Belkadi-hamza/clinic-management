from sqlalchemy.orm import Session
from ..models.audit_logs import AuditLog
from ..schemas.audit_logs import AuditLogCreate

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

def get_audit_log_by_id(db: Session, log_id: int):
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()

def create_audit_log(db: Session, log: AuditLogCreate):
    db_log = AuditLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log