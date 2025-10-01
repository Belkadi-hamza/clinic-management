from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.audit_logs import AuditLogCreate, AuditLogResponse
from ..crud.audit_logs import (
    get_audit_logs, get_audit_log_by_id, create_audit_log
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[AuditLogResponse])
def read_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(require_admin_or_super),
    db: Session = Depends(get_db)
):
    logs = get_audit_logs(db, skip=skip, limit=limit)
    return [AuditLogResponse.from_orm(log) for log in logs]

@router.get("/{log_id}", response_model=AuditLogResponse)
def read_audit_log(log_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    log = get_audit_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return AuditLogResponse.from_orm(log)

@router.post("/", response_model=AuditLogResponse)
def create_audit_log_item(log: AuditLogCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_log = create_audit_log(db, log)
    return AuditLogResponse.from_orm(db_log)