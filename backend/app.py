from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
from .sql import router as sql_router
from .auth import router as auth_router
from .api.role import router as roles_router
from .api.staff import router as staff_router
from .api.departments import router as departments_router
from .html_routes import html_router

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

# Setup paths
BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "front_end"

# Custom error handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom HTML error pages"""
    # For API routes, return JSON
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # For other routes, return HTML error pages
    if exc.status_code == 404:
        error_page = FRONTEND_DIR / "error-404.html"
        if error_page.exists():
            return FileResponse(error_page, status_code=404)
    elif exc.status_code == 500:
        error_page = FRONTEND_DIR / "error-500.html"
        if error_page.exists():
            return FileResponse(error_page, status_code=500)
    
    # Fallback to JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    # For API routes, return JSON
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error", "errors": exc.errors()}
        )
    
    # For other routes, show 404 page
    error_page = FRONTEND_DIR / "error-404.html"
    if error_page.exists():
        return FileResponse(error_page, status_code=400)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with 500 error page"""
    import traceback
    traceback.print_exc()  # Print traceback for debugging
    
    # For API routes, return JSON
    if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
    
    # For other routes, show 500 page
    error_page = FRONTEND_DIR / "error-500.html"
    if error_page.exists():
        return FileResponse(error_page, status_code=500)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# API routes
app.include_router(auth_router)  # /auth/token, /auth/register, /auth/me
app.include_router(sql_router, prefix="/api/sql", tags=["sql"])
app.include_router(roles_router, prefix="/api/roles", tags=["roles"])
app.include_router(staff_router, prefix="/api/staff", tags=["staff"])
app.include_router(departments_router, prefix="/api/departments", tags=["departments"])

# Serve static assets first (CSS, JS, images)
if FRONTEND_DIR.exists():
    # Mount assets under /assets for direct access
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets"), html=True), name="static-assets-direct")
    # Mount assets under /app/assets for HTML routes
    app.mount("/app/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets"), html=True), name="static-assets")
    
    # Add catch-all for assets in subdirectories (e.g., /app/patient-details/assets/...)
    @app.get("/app/{path:path}/assets/{asset_path:path}")
    async def serve_nested_assets(path: str, asset_path: str):
        """Serve assets from nested paths"""
        asset_file = FRONTEND_DIR / "assets" / asset_path
        if asset_file.exists():
            return FileResponse(asset_file)
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_path}")

# HTML routes - organized page routing (including redirects)
# This must come BEFORE static file mounting to handle redirects
app.include_router(html_router, prefix="/app", tags=["html-pages"])

# Mount entire frontend for fallback (after HTML routes and redirects)
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static-frontend")

@app.get("/")
def root_redirect():
    return RedirectResponse(url="/app/index", status_code=307)
