from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.user_sessions import UserSessionCreate, UserSessionUpdate, UserSessionResponse
from ..crud.user_sessions import (
    get_user_sessions, get_user_session_by_id, get_user_session_by_token,
    create_user_session, update_user_session, delete_user_session
)
from ..deps import require_admin_or_super
from typing import List

router = APIRouter()

@router.get("/", response_model=List[UserSessionResponse])
def read_user_sessions(current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    sessions = get_user_sessions(db)
    return [UserSessionResponse.from_orm(s) for s in sessions]

@router.get("/{session_id}", response_model=UserSessionResponse)
def read_user_session(session_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    session = get_user_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="User session not found")
    return UserSessionResponse.from_orm(session)

@router.post("/", response_model=UserSessionResponse)
def create_user_session_item(session: UserSessionCreate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    if get_user_session_by_token(db, session.session_token):
        raise HTTPException(status_code=400, detail="Session token already exists")
    db_session = create_user_session(db, session)
    return UserSessionResponse.from_orm(db_session)

@router.put("/{session_id}", response_model=UserSessionResponse)
def update_user_session_item(session_id: int, session: UserSessionUpdate, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_session = update_user_session(db, session_id, session)
    if not db_session:
        raise HTTPException(status_code=404, detail="User session not found")
    return UserSessionResponse.from_orm(db_session)

@router.delete("/{session_id}", response_model=dict)
def delete_user_session_item(session_id: int, current_user: dict = Depends(require_admin_or_super), db: Session = Depends(get_db)):
    db_session = delete_user_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="User session not found")
    return {"message": "User session deleted successfully"}