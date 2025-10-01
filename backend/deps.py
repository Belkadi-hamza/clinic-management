from typing import Literal, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import text
from .db import SessionLocal
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
                SELECT su.id, su.username, r.name as role_name, su.is_active, su.staff_id
                FROM system_users su
                LEFT JOIN roles r ON su.role_id = r.id
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
            "staff_id": user["staff_id"]
        }

def require_roles(*allowed_roles: Literal["super_admin", "admin", "doctor", "nurse", "receptionist", "pharmacist", "lab_technician", "accountant"]):
    """Dependency factory for role-based access control."""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Convenience dependencies for common role combinations
require_super_admin = require_roles("super_admin")
require_admin_or_super = require_roles("super_admin", "admin")
require_any_doctor = require_roles("super_admin", "admin", "doctor")
require_doctor_or_above = require_roles("super_admin", "admin", "doctor")
require_accountant_or_above = require_roles("super_admin", "admin", "accountant")
require_pharmacist_or_above = require_roles("super_admin", "admin", "pharmacist")
require_any_user = require_roles("super_admin", "admin", "doctor", "nurse", "receptionist", "pharmacist", "lab_technician", "accountant")

def get_current_staff_id(current_user: dict = Depends(get_current_user)):
    """Get the staff_id for the current user."""
    if current_user["staff_id"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be linked to a staff record"
        )
    return current_user["staff_id"]

def require_permission(current_user: dict, module: str, action: str):
    """
    Check if user has permission for a specific module and action.
    TODO: Implement proper permission checking against role_permissions table.
    For now, allows all authenticated users.
    """
    # Placeholder - implement actual permission checking logic here
    # You can query the role_permissions table based on current_user["role"]
    pass
