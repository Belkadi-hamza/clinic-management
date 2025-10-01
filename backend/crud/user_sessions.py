from sqlalchemy.orm import Session
from ..models.user_sessions import UserSession
from ..schemas.user_sessions import UserSessionCreate, UserSessionUpdate

def get_user_sessions(db: Session):
    return db.query(UserSession).order_by(UserSession.created_at.desc()).all()

def get_user_session_by_id(db: Session, session_id: int):
    return db.query(UserSession).filter(UserSession.id == session_id).first()

def get_user_session_by_token(db: Session, token: str):
    return db.query(UserSession).filter(UserSession.session_token == token).first()

def create_user_session(db: Session, session: UserSessionCreate):
    db_session = UserSession(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_user_session(db: Session, session_id: int, session: UserSessionUpdate):
    db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not db_session:
        return None
    for key, value in session.dict(exclude_unset=True).items():
        setattr(db_session, key, value)
    db.commit()
    db.refresh(db_session)
    return db_session

def delete_user_session(db: Session, session_id: int):
    db_session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not db_session:
        return None
    db.delete(db_session)
    db.commit()
    return db_session