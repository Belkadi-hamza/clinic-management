from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from ..db import SessionLocal

# Load configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set!")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # Default 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt."""
    # Truncate password if too long for bcrypt (72 bytes max)
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log the error but don't expose details to user
        print(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token."""
    if not form_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Form data required"
        )
    
    with SessionLocal() as db:
        # Get user from database with role information
        result = db.execute(
            text("""
                SELECT su.id, su.username, su.password_hash, su.is_active, su.role_id,
                       r.name as role_name, s.first_name, s.last_name, s.email
                FROM system_users su
                JOIN roles r ON su.role_id = r.id
                JOIN staff s ON su.staff_id = s.id
                WHERE su.username = :username AND su.deleted_at IS NULL
            """),
            {"username": form_data.username}
        )
        user = result.mappings().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["username"],
                "role": user["role_name"],
                "user_id": user["id"],
                "role_id": user["role_id"]
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role_name"],
                "role_id": user["role_id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"]
            }
        }

@router.post("/register")
def register_user(
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_id: int = Form(...),
    position: str = Form(...),
    department: str = Form(...)
):
    """Register a new user (admin only - should be protected)."""
    
    with SessionLocal() as db:
        # Check if username already exists
        existing_user = db.execute(
            text("SELECT id FROM system_users WHERE username = :username AND deleted_at IS NULL"),
            {"username": username}
        ).mappings().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        if email:
            existing_email = db.execute(
                text("SELECT id FROM staff WHERE email = :email AND deleted_at IS NULL"),
                {"email": email}
            ).mappings().first()
            
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Verify role exists
        role_check = db.execute(
            text("SELECT id FROM roles WHERE id = :role_id AND deleted_at IS NULL"),
            {"role_id": role_id}
        ).mappings().first()
        
        if not role_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role ID"
            )
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Create staff record first
        staff_result = db.execute(
            text("""
                INSERT INTO staff (first_name, last_name, email, position, department, created_by)
                VALUES (:first_name, :last_name, :email, :position, :department, 1)
                RETURNING id
            """),
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "position": position,
                "department": department
            }
        )
        staff_id = staff_result.fetchone().id
        
        # Create system user
        db.execute(
            text("""
                INSERT INTO system_users (staff_id, username, password_hash, role_id, created_by)
                VALUES (:staff_id, :username, :password_hash, :role_id, 1)
            """),
            {
                "staff_id": staff_id,
                "username": username,
                "password_hash": password_hash,
                "role_id": role_id
            }
        )
        db.commit()
        
        return {"message": "User created successfully"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Resolve and return the current authenticated user from JWT."""
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
                SELECT su.id, su.username, su.is_active, su.role_id,
                       r.name as role_name, s.first_name, s.last_name, s.email
                FROM system_users su
                JOIN roles r ON su.role_id = r.id
                JOIN staff s ON su.staff_id = s.id
                WHERE su.username = :username AND su.deleted_at IS NULL
            """),
            {"username": username}
        ).mappings().first()
        if not user or not user["is_active"]:
            raise credentials_exception
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role_name"],
            "role_id": user["role_id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"]
        }

@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return current_user
