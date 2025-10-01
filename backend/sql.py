from fastapi import APIRouter, HTTPException, Depends 
from pydantic import BaseModel
from sqlalchemy import text
from .db import SessionLocal
from .deps import require_admin_or_super

router = APIRouter()

class SQLRequest(BaseModel):
    query: str
    params: dict | None = None

@router.post("/execute")
def execute_sql(req: SQLRequest, current_user: dict = Depends(require_admin_or_super)):
    """Execute SQL query - requires admin or super admin role."""
    try:
        with SessionLocal() as db:
            result = db.execute(text(req.query), req.params or {})
            if result.returns_rows:
                rows = [dict(r._mapping) for r in result.fetchall()]
                return {
                    "rows": rows,
                    "user": {
                        "username": current_user["username"],
                        "role": current_user["role"]
                    }
                }
            else:
                db.commit()
                return {
                    "rows": [], 
                    "message": "OK",
                    "user": {
                        "username": current_user["username"],
                        "role": current_user["role"]
                    }
                }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

