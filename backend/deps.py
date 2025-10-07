from typing import Literal, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session
from .db import SessionLocal, get_db
from .auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    with SessionLocal() as db:
        user = db.execute(
            text("""
            SELECT su.id, su.staff_id, su.username, su.password_hash, su.is_active, s.role_id, r.name as role_name, 
                   s.first_name, s.last_name, s.date_of_birth, s.gender, s.marital_status, s.mobile_phone, 
                   s.home_phone, s.fax, s.email, s.line, s.city, d.name as departments
            FROM system_users su
            JOIN staff s ON su.staff_id = s.id
            LEFT JOIN roles r ON s.role_id = r.id
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE su.username = :username AND su.deleted_at IS NULL
            """),
            {"username": username}
        ).mappings().first()
        
        if not user:
            raise credentials_exception
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role_name"],
            "role_id": user["role_id"],
            "staff_id": user["staff_id"]
        }

def require_roles(*allowed_roles: Literal["superadmin", "admin", "doctor", "nurse", "receptionist", "pharmacist", "lab_technician", "accountant"]):
    """Dependency factory for role-based access control."""
    def role_checker(current_user: dict = Depends(get_current_user)):
        # Superadmin has access to everything
        if current_user.get("role") == "superadmin":
            return current_user
        
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Convenience dependencies for common role combinations
require_superadmin = require_roles("superadmin")
require_admin_or_super = require_roles("superadmin", "admin")
require_any_doctor = require_roles("superadmin", "admin", "doctor")
require_doctor_or_above = require_roles("superadmin", "admin", "doctor")
require_accountant_or_above = require_roles("superadmin", "admin", "accountant")
require_pharmacist_or_above = require_roles("superadmin", "admin", "pharmacist")
require_any_user = require_roles("superadmin", "admin", "doctor", "nurse", "receptionist", "pharmacist", "lab_technician", "accountant")

def get_current_staff_id(current_user: dict = Depends(get_current_user)):
    """Get the staff_id for the current user."""
    if current_user["staff_id"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be linked to a staff record"
        )
    return current_user["staff_id"]

def require_permission(current_user: dict, module: str, action: str, db: Session = Depends(get_db)):
    """Check if user has permission for a specific module and action."""
    # Query role_permissions table
    permission = db.execute(
        text("""
        SELECT rp.* FROM role_permissions rp
        WHERE rp.role_id = :role_id 
        AND rp.module_id = (SELECT id FROM modules WHERE name = :module)
        AND rp.can_read = true  -- or can_create, can_update, can_delete based on action
        """),
        {"role_id": current_user["role_id"], "module": module}
    ).first()
    
    if not permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return True
