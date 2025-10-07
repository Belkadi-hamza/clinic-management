from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from pydantic import BaseModel
from ..db import SessionLocal

# Charger la configuration à partir des variables d'environnement
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("La variable d'environnement SECRET_KEY doit être définie !")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # Par défaut : 24 heures

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Modèles Pydantic
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe par rapport à son hachage en utilisant bcrypt."""
    # Tronquer le mot de passe s’il dépasse la limite de bcrypt (72 octets max)
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Journaliser l’erreur sans exposer de détails à l’utilisateur
        print(f"Échec de la vérification du mot de passe : {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hache un mot de passe."""
    # Tronquer le mot de passe s'il dépasse la limite de bcrypt (72 octets max)
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # Journaliser l'erreur sans exposer de détails à l'utilisateur
        print(f"Échec du hachage du mot de passe : {e}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un jeton d’accès JWT."""
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
    """Authentifie un utilisateur et renvoie un jeton d’accès."""
    if not form_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les données du formulaire sont requises"
        )
    
    with SessionLocal() as db:
        # Récupère l'utilisateur depuis la base de données avec les informations de rôle
        result = db.execute(
            text("""
            SELECT su.id, su.username, su.password_hash, su.is_active, r.name as role, r.id as role_id, s.first_name, s.last_name, s.email
            FROM system_users su
            JOIN staff s ON su.staff_id = s.id
            LEFT JOIN roles r ON s.role_id = r.id
            WHERE su.username = :username AND su.deleted_at IS NULL;
            """),
            {"username": form_data.username}
        )
        user = result.mappings().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d’utilisateur ou mot de passe invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Le compte est désactivé",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d’utilisateur ou mot de passe invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Créer le jeton d'accès
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["username"],
                "role": user["role"],
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
                "role": user["role"],
                "role_id": user["role_id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"]
            }
        }

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Récupère et renvoie l’utilisateur actuellement authentifié à partir du JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
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
            SELECT su.id, su.staff_id, su.username, su.is_active, su.is_superadmin, s.role_id, r.name as role_name, 
                   s.first_name, s.last_name, s.date_of_birth, s.gender, s.marital_status, s.mobile_phone, 
                   s.home_phone, s.fax, s.email, s.line, s.city, s.doctor_code, s.specialization, s.license_number, s.is_doctor, d.name as department_name
            FROM system_users su
            JOIN staff s ON su.staff_id = s.id
            LEFT JOIN roles r ON s.role_id = r.id
            LEFT JOIN departments d ON s.department_id = d.id
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
            "email": user["email"],
            "staff_id": user["staff_id"],
            "date_of_birth": user["date_of_birth"],
            "gender": user["gender"],
            "marital_status": user["marital_status"],
            "mobile_phone": user["mobile_phone"],
            "home_phone": user["home_phone"],
            "fax": user["fax"],
            "line": user["line"],
            "city": user["city"],
            "doctor_code": user["doctor_code"],
            "specialization": user["specialization"],
            "license_number": user["license_number"],
            "department": user["department_name"],
            "is_doctor": user["is_doctor"]
        }

@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations de l’utilisateur connecté."""
    return current_user

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Modifier le mot de passe de l’utilisateur."""
    with SessionLocal() as db:
        # Récupère le mot de passe actuel de l’utilisateur
        user = db.execute(
            text("SELECT password_hash FROM system_users WHERE id = :user_id"),
            {"user_id": current_user["id"]}
        ).mappings().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable"
            )
        
        # Vérifie le mot de passe actuel
        if not verify_password(request.current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le mot de passe actuel est incorrect"
            )
        
        # Hache le nouveau mot de passe
        new_password_hash = get_password_hash(request.new_password)
        
        # Met à jour le mot de passe
        db.execute(
            text("""
                UPDATE system_users 
                SET password_hash = :password_hash, 
                    updated_at = now(),
                    must_change_password = false
                WHERE id = :user_id
            """),
            {"password_hash": new_password_hash, "user_id": current_user["id"]}
        )
        db.commit()
        
        return {"message": "Mot de passe modifié avec succès"}