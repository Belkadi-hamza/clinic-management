from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from .sql import router as sql_router
from .auth import router as auth_router
from .api.role import router as roles_router
from .api.staff import router as staff_router

app = FastAPI(title="Cabinet Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# API routes
app.include_router(auth_router)  # /auth/token, /auth/register, /auth/me
app.include_router(sql_router, prefix="/api/sql", tags=["sql"])
app.include_router(roles_router, prefix="/api/roles", tags=["roles"])
app.include_router(staff_router, prefix="/api/staff", tags=["staff"]) 

# Serve static frontend under /app to avoid route conflicts
BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "front_end"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

    @app.get("/")
    def root_redirect():
        return RedirectResponse(url="/app/index.html", status_code=307)
