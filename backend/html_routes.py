"""
HTML Routes Module for Cabinet Management System
Provides organized routing for all HTML pages with proper navigation structure
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from pathlib import Path
from typing import Dict, List, Optional

# Setup paths
BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "front_end"

# Create router for HTML routes
html_router = APIRouter()

# Define page categories and their routes
PAGE_CATEGORIES = {
    "main": {
        "name": "Main Pages",
        "pages": [
            {"route": "/", "file": "index.html", "title": "Dashboard", "description": "Main dashboard"},
            {"route": "/login", "file": "login.html", "title": "Login", "description": "User login page"},
            {"route": "/loading", "file": "loading.html", "title": "Loading", "description": "Loading screen"},
        ]
    },
    "patients": {
        "name": "Patient Management",
        "pages": [
            {"route": "/patients", "file": "patients.html", "title": "Patients", "description": "Patient list"},
            {"route": "/add-patient", "file": "add-patient.html", "title": "Add Patient", "description": "Add new patient"},
            {"route": "/edit-patient", "file": "edit-patient.html", "title": "Edit Patient", "description": "Edit patient details"},
            {"route": "/patient-details", "file": "patient-details.html", "title": "Patient Details", "description": "Patient overview"},
            {"route": "/patient-details/appointments", "file": "patient-details-appointments.html", "title": "Patient Appointments", "description": "Patient appointment history"},
            {"route": "/patient-details/billings", "file": "patient-details-billings.html", "title": "Patient Billings", "description": "Patient billing information"},
            {"route": "/patient-details/documents", "file": "patient-details-documents.html", "title": "Patient Documents", "description": "Patient document management"},
            {"route": "/patient-details/lab-results", "file": "patient-details-lab-results.html", "title": "Lab Results", "description": "Patient lab results"},
            {"route": "/patient-details/medical-history", "file": "patient-details-medical-history.html", "title": "Medical History", "description": "Patient medical history"},
            {"route": "/patient-details/prescription", "file": "patient-details-prescription.html", "title": "Prescriptions", "description": "Patient prescriptions"},
            {"route": "/patient-details/visit-history", "file": "patient-details-visit-history.html", "title": "Visit History", "description": "Patient visit history"},
            {"route": "/patient-details/vital-signs", "file": "patient-details-vital-signs.html", "title": "Vital Signs", "description": "Patient vital signs"},
        ]
    },
    "doctors": {
        "name": "Doctor Management",
        "pages": [
            {"route": "/doctors", "file": "doctors.html", "title": "Doctors", "description": "Doctor list"},
            {"route": "/add-doctors", "file": "add-doctors.html", "title": "Add Doctor", "description": "Add new doctor"},
            {"route": "/edit-doctors", "file": "edit-doctors.html", "title": "Edit Doctor", "description": "Edit doctor details"},
            {"route": "/doctor-details", "file": "doctor-details.html", "title": "Doctor Details", "description": "Doctor profile"},
        ]
    },
    "appointments": {
        "name": "Appointment Management",
        "pages": [
            {"route": "/appointments", "file": "appointments.html", "title": "Appointments", "description": "Appointment management"},
            {"route": "/appointment-consultation", "file": "appointment-consultation.html", "title": "Consultation", "description": "Appointment consultation"},
        ]
    },
    "visits": {
        "name": "Visit Management",
        "pages": [
            {"route": "/visits", "file": "visits.html", "title": "Visits", "description": "Visit management"},
            {"route": "/start-visits", "file": "start-visits.html", "title": "Start Visit", "description": "Start new visit"},
        ]
    },
    "medical": {
        "name": "Medical Services",
        "pages": [
            {"route": "/lab-results", "file": "lab-results.html", "title": "Lab Results", "description": "Laboratory results"},
            {"route": "/medical-results", "file": "medical-results.html", "title": "Medical Results", "description": "Medical test results"},
            {"route": "/pharmacy", "file": "pharmacy.html", "title": "Pharmacy", "description": "Pharmacy management"},
        ]
    },
    "staff": {
        "name": "Staff Management",
        "pages": [
            {"route": "/staffs", "file": "staffs.html", "title": "Staff", "description": "Staff management"},
        ]
    },
    "settings": {
        "name": "Settings",
        "pages": [
            {"route": "/general-settings", "file": "general-settings.html", "title": "General Settings", "description": "General application settings"},
            {"route": "/permission-settings", "file": "permission-settings.html", "title": "Permissions", "description": "Permission management"},
            {"route": "/roles", "file": "roles.html", "title": "Roles", "description": "Role management"},
            {"route": "/security-settings", "file": "security-settings.html", "title": "Security", "description": "Security settings"},
        ]
    },
    "additional": {
        "name": "Additional Pages",
        "pages": [
            {"route": "/charts", "file": "additional_pages/charts/chart-apex.html", "title": "Charts", "description": "Data visualization"},
            {"route": "/chat", "file": "additional_pages/chat.html", "title": "Chat", "description": "Communication"},
            {"route": "/contacts", "file": "additional_pages/contacts/contacts.html", "title": "Contacts", "description": "Contact management"},
            {"route": "/email", "file": "additional_pages/email/email-compose.html", "title": "Email", "description": "Email management"},
            {"route": "/file-manager", "file": "additional_pages/file-manager.html", "title": "File Manager", "description": "File management"},
            {"route": "/forms", "file": "additional_pages/form/form-basic-inputs.html", "title": "Forms", "description": "Form management"},
            {"route": "/invoices", "file": "additional_pages/invoice/invoice.html", "title": "Invoices", "description": "Invoice management"},
            {"route": "/tables", "file": "additional_pages/table/tables-basic.html", "title": "Tables", "description": "Data tables"},
            {"route": "/ui", "file": "additional_pages/ui/ui-alerts.html", "title": "UI Components", "description": "User interface components"},
        ]
    }
}

def get_page_info(route: str) -> Optional[Dict]:
    """Get page information for a given route"""
    for category in PAGE_CATEGORIES.values():
        for page in category["pages"]:
            if page["route"] == route:
                return page
    return None

def get_all_routes() -> List[Dict]:
    """Get all available routes"""
    all_routes = []
    for category in PAGE_CATEGORIES.values():
        all_routes.extend(category["pages"])
    return all_routes

def get_routes_by_category() -> Dict:
    """Get routes organized by category"""
    return PAGE_CATEGORIES

@html_router.get("/", response_class=RedirectResponse)
async def root_redirect():
    """Redirect root to dashboard"""
    return RedirectResponse(url="/app/index.html", status_code=307)

@html_router.get("/routes")
async def get_all_routes_info():
    """Get information about all available routes"""
    return {
        "categories": get_routes_by_category(),
        "all_routes": get_all_routes(),
        "total_pages": len(get_all_routes())
    }

@html_router.get("/routes/{category}")
async def get_routes_by_category_info(category: str):
    """Get routes for a specific category"""
    if category in PAGE_CATEGORIES:
        return PAGE_CATEGORIES[category]
    else:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

@html_router.get("/page-info/{route:path}")
async def get_page_info_endpoint(route: str):
    """Get information about a specific page route"""
    # Ensure route starts with /
    if not route.startswith("/"):
        route = "/" + route
    
    page_info = get_page_info(route)
    if page_info:
        return page_info
    else:
        raise HTTPException(status_code=404, detail=f"Route '{route}' not found")

# Specific route handlers for known pages
@html_router.get("/")
async def serve_dashboard():
    """Serve the main dashboard"""
    html_file = FRONTEND_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Dashboard not found")

@html_router.get("/index")
async def serve_index():
    """Serve the index page"""
    html_file = FRONTEND_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Index page not found")

@html_router.get("/login")
async def serve_login():
    """Serve the login page"""
    html_file = FRONTEND_DIR / "login.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Login page not found")

@html_router.get("/patients")
async def serve_patients():
    """Serve the patients page"""
    html_file = FRONTEND_DIR / "patients.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patients page not found")

@html_router.get("/doctors")
async def serve_doctors():
    """Serve the doctors page"""
    html_file = FRONTEND_DIR / "doctors.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Doctors page not found")

@html_router.get("/appointments")
async def serve_appointments():
    """Serve the appointments page"""
    html_file = FRONTEND_DIR / "appointments.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Appointments page not found")

# Add all other routes from PAGE_CATEGORIES
@html_router.get("/loading")
async def serve_loading():
    html_file = FRONTEND_DIR / "loading.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Loading page not found")

@html_router.get("/add-patient")
async def serve_add_patient():
    html_file = FRONTEND_DIR / "add-patient.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Add patient page not found")

@html_router.get("/edit-patient")
async def serve_edit_patient():
    html_file = FRONTEND_DIR / "edit-patient.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Edit patient page not found")

@html_router.get("/patient-details")
async def serve_patient_details():
    html_file = FRONTEND_DIR / "patient-details.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient details page not found")

@html_router.get("/patient-details/appointments")
async def serve_patient_details_appointments():
    html_file = FRONTEND_DIR / "patient-details-appointments.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient appointments page not found")

@html_router.get("/patient-details/billings")
async def serve_patient_details_billings():
    html_file = FRONTEND_DIR / "patient-details-billings.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient billings page not found")

@html_router.get("/patient-details/documents")
async def serve_patient_details_documents():
    html_file = FRONTEND_DIR / "patient-details-documents.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient documents page not found")

@html_router.get("/patient-details/lab-results")
async def serve_patient_details_lab_results():
    html_file = FRONTEND_DIR / "patient-details-lab-results.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient lab results page not found")

@html_router.get("/patient-details/medical-history")
async def serve_patient_details_medical_history():
    html_file = FRONTEND_DIR / "patient-details-medical-history.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient medical history page not found")

@html_router.get("/patient-details/prescription")
async def serve_patient_details_prescription():
    html_file = FRONTEND_DIR / "patient-details-prescription.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient prescription page not found")

@html_router.get("/patient-details/visit-history")
async def serve_patient_details_visit_history():
    html_file = FRONTEND_DIR / "patient-details-visit-history.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient visit history page not found")

@html_router.get("/patient-details/vital-signs")
async def serve_patient_details_vital_signs():
    html_file = FRONTEND_DIR / "patient-details-vital-signs.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Patient vital signs page not found")

@html_router.get("/add-doctors")
async def serve_add_doctors():
    html_file = FRONTEND_DIR / "add-doctors.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Add doctors page not found")

@html_router.get("/edit-doctors")
async def serve_edit_doctors():
    html_file = FRONTEND_DIR / "edit-doctors.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Edit doctors page not found")

@html_router.get("/doctor-details")
async def serve_doctor_details():
    html_file = FRONTEND_DIR / "doctor-details.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Doctor details page not found")

@html_router.get("/appointment-consultation")
async def serve_appointment_consultation():
    html_file = FRONTEND_DIR / "appointment-consultation.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Appointment consultation page not found")

@html_router.get("/visits")
async def serve_visits():
    html_file = FRONTEND_DIR / "visits.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Visits page not found")

@html_router.get("/start-visits")
async def serve_start_visits():
    html_file = FRONTEND_DIR / "start-visits.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Start visits page not found")

@html_router.get("/lab-results")
async def serve_lab_results():
    html_file = FRONTEND_DIR / "lab-results.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Lab results page not found")

@html_router.get("/medical-results")
async def serve_medical_results():
    html_file = FRONTEND_DIR / "medical-results.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Medical results page not found")

@html_router.get("/pharmacy")
async def serve_pharmacy():
    html_file = FRONTEND_DIR / "pharmacy.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Pharmacy page not found")

@html_router.get("/staffs")
async def serve_staffs():
    html_file = FRONTEND_DIR / "staffs.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Staffs page not found")

@html_router.get("/general-settings")
async def serve_general_settings():
    html_file = FRONTEND_DIR / "general-settings.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="General settings page not found")

@html_router.get("/permission-settings")
async def serve_permission_settings():
    html_file = FRONTEND_DIR / "permission-settings.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Permission settings page not found")

@html_router.get("/roles")
async def serve_roles_settings():
    html_file = FRONTEND_DIR / "roles.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Roles settings page not found")

@html_router.get("/security-settings")
async def serve_security_settings():
    html_file = FRONTEND_DIR / "security-settings.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Security settings page not found")

# Additional pages routes
@html_router.get("/charts")
async def serve_charts():
    html_file = FRONTEND_DIR / "additional_pages/charts/chart-apex.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Charts page not found")

@html_router.get("/chat")
async def serve_chat():
    html_file = FRONTEND_DIR / "additional_pages/chat.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Chat page not found")

@html_router.get("/contacts")
async def serve_contacts():
    html_file = FRONTEND_DIR / "additional_pages/contacts/contacts.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Contacts page not found")

@html_router.get("/email")
async def serve_email():
    html_file = FRONTEND_DIR / "additional_pages/email/email-compose.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Email page not found")

@html_router.get("/file-manager")
async def serve_file_manager():
    html_file = FRONTEND_DIR / "additional_pages/file-manager.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="File manager page not found")

@html_router.get("/forms")
async def serve_forms():
    html_file = FRONTEND_DIR / "additional_pages/form/form-basic-inputs.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Forms page not found")

@html_router.get("/invoices")
async def serve_invoices():
    html_file = FRONTEND_DIR / "additional_pages/invoice/invoice.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Invoices page not found")

@html_router.get("/tables")
async def serve_tables():
    html_file = FRONTEND_DIR / "additional_pages/table/tables-basic.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Tables page not found")

@html_router.get("/ui")
async def serve_ui():
    html_file = FRONTEND_DIR / "additional_pages/ui/ui-alerts.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="UI page not found")

# Demo and test pages
@html_router.get("/route-demo")
async def serve_route_demo():
    html_file = FRONTEND_DIR / "route-demo.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Route demo page not found")

@html_router.get("/test-assets")
async def serve_test_assets():
    html_file = FRONTEND_DIR / "test-assets.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Test assets page not found")

@html_router.get("/clean-urls-demo")
async def serve_clean_urls_demo():
    html_file = FRONTEND_DIR / "clean-urls-demo.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Clean URLs demo page not found")

@html_router.get("/redirect-test")
async def serve_redirect_test():
    html_file = FRONTEND_DIR / "redirect-test.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="Redirect test page not found")

# Redirect handlers for .html extension to clean URLs
@html_router.get("/index.html")
async def redirect_index():
    """Redirect index.html to /app/index"""
    return RedirectResponse(url="/app/index", status_code=301)

@html_router.get("/login.html")
async def redirect_login():
    """Redirect login.html to clean URL"""
    return RedirectResponse(url="/app/login", status_code=301)

@html_router.get("/loading.html")
async def redirect_loading():
    """Redirect loading.html to clean URL"""
    return RedirectResponse(url="/app/loading", status_code=301)

@html_router.get("/patients.html")
async def redirect_patients():
    """Redirect patients.html to clean URL"""
    return RedirectResponse(url="/app/patients", status_code=301)

@html_router.get("/add-patient.html")
async def redirect_add_patient():
    """Redirect add-patient.html to clean URL"""
    return RedirectResponse(url="/app/add-patient", status_code=301)

@html_router.get("/edit-patient.html")
async def redirect_edit_patient():
    """Redirect edit-patient.html to clean URL"""
    return RedirectResponse(url="/app/edit-patient", status_code=301)

@html_router.get("/patient-details.html")
async def redirect_patient_details():
    """Redirect patient-details.html to clean URL"""
    return RedirectResponse(url="/app/patient-details", status_code=301)

@html_router.get("/patient-details-appointments.html")
async def redirect_patient_details_appointments():
    """Redirect patient-details-appointments.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/appointments", status_code=301)

@html_router.get("/patient-details-billings.html")
async def redirect_patient_details_billings():
    """Redirect patient-details-billings.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/billings", status_code=301)

@html_router.get("/patient-details-documents.html")
async def redirect_patient_details_documents():
    """Redirect patient-details-documents.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/documents", status_code=301)

@html_router.get("/patient-details-lab-results.html")
async def redirect_patient_details_lab_results():
    """Redirect patient-details-lab-results.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/lab-results", status_code=301)

@html_router.get("/patient-details-medical-history.html")
async def redirect_patient_details_medical_history():
    """Redirect patient-details-medical-history.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/medical-history", status_code=301)

@html_router.get("/patient-details-prescription.html")
async def redirect_patient_details_prescription():
    """Redirect patient-details-prescription.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/prescription", status_code=301)

@html_router.get("/patient-details-visit-history.html")
async def redirect_patient_details_visit_history():
    """Redirect patient-details-visit-history.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/visit-history", status_code=301)

@html_router.get("/patient-details-vital-signs.html")
async def redirect_patient_details_vital_signs():
    """Redirect patient-details-vital-signs.html to clean URL"""
    return RedirectResponse(url="/app/patient-details/vital-signs", status_code=301)

@html_router.get("/doctors.html")
async def redirect_doctors():
    """Redirect doctors.html to clean URL"""
    return RedirectResponse(url="/app/doctors", status_code=301)

@html_router.get("/add-doctors.html")
async def redirect_add_doctors():
    """Redirect add-doctors.html to clean URL"""
    return RedirectResponse(url="/app/add-doctors", status_code=301)

@html_router.get("/edit-doctors.html")
async def redirect_edit_doctors():
    """Redirect edit-doctors.html to clean URL"""
    return RedirectResponse(url="/app/edit-doctors", status_code=301)

@html_router.get("/doctor-details.html")
async def redirect_doctor_details():
    """Redirect doctor-details.html to clean URL"""
    return RedirectResponse(url="/app/doctor-details", status_code=301)

@html_router.get("/appointments.html")
async def redirect_appointments():
    """Redirect appointments.html to clean URL"""
    return RedirectResponse(url="/app/appointments", status_code=301)

@html_router.get("/appointment-consultation.html")
async def redirect_appointment_consultation():
    """Redirect appointment-consultation.html to clean URL"""
    return RedirectResponse(url="/app/appointment-consultation", status_code=301)

@html_router.get("/visits.html")
async def redirect_visits():
    """Redirect visits.html to clean URL"""
    return RedirectResponse(url="/app/visits", status_code=301)

@html_router.get("/start-visits.html")
async def redirect_start_visits():
    """Redirect start-visits.html to clean URL"""
    return RedirectResponse(url="/app/start-visits", status_code=301)

@html_router.get("/lab-results.html")
async def redirect_lab_results():
    """Redirect lab-results.html to clean URL"""
    return RedirectResponse(url="/app/lab-results", status_code=301)

@html_router.get("/medical-results.html")
async def redirect_medical_results():
    """Redirect medical-results.html to clean URL"""
    return RedirectResponse(url="/app/medical-results", status_code=301)

@html_router.get("/pharmacy.html")
async def redirect_pharmacy():
    """Redirect pharmacy.html to clean URL"""
    return RedirectResponse(url="/app/pharmacy", status_code=301)

@html_router.get("/staffs.html")
async def redirect_staffs():
    """Redirect staffs.html to clean URL"""
    return RedirectResponse(url="/app/staffs", status_code=301)

@html_router.get("/general-settings.html")
async def redirect_general_settings():
    """Redirect general-settings.html to clean URL"""
    return RedirectResponse(url="/app/general-settings", status_code=301)

@html_router.get("/permission-settings.html")
async def redirect_permission_settings():
    """Redirect permission-settings.html to clean URL"""
    return RedirectResponse(url="/app/permission-settings", status_code=301)

@html_router.get("/roles.html")
async def redirect_roles_settings():
    """Redirect roles.html to clean URL"""
    return RedirectResponse(url="/app/roles", status_code=301)

@html_router.get("/security-settings.html")
async def redirect_security_settings():
    """Redirect security-settings.html to clean URL"""
    return RedirectResponse(url="/app/security-settings", status_code=301)

# Helper functions for navigation
def generate_navigation_menu():
    """Generate navigation menu structure"""
    menu = []
    for category_name, category_data in PAGE_CATEGORIES.items():
        category_menu = {
            "name": category_data["name"],
            "key": category_name,
            "pages": []
        }
        
        for page in category_data["pages"]:
            category_menu["pages"].append({
                "title": page["title"],
                "route": page["route"],
                "description": page["description"]
            })
        
        menu.append(category_menu)
    
    return menu

def get_breadcrumb(route: str) -> List[Dict]:
    """Generate breadcrumb navigation for a route"""
    page_info = get_page_info(route)
    if not page_info:
        return []
    
    breadcrumb = [
        {"title": "Home", "route": "/", "active": False}
    ]
    
    # Add category if we can determine it
    for category_name, category_data in PAGE_CATEGORIES.items():
        for page in category_data["pages"]:
            if page["route"] == route:
                breadcrumb.append({
                    "title": category_data["name"],
                    "route": None,
                    "active": False
                })
                break
    
    # Add current page
    breadcrumb.append({
        "title": page_info["title"],
        "route": route,
        "active": True
    })
    
    return breadcrumb

# Export navigation helpers
__all__ = [
    "html_router",
    "PAGE_CATEGORIES", 
    "get_page_info",
    "get_all_routes",
    "get_routes_by_category",
    "generate_navigation_menu",
    "get_breadcrumb"
]
