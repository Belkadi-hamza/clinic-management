"""
API routers package
"""

from . import allergies
from . import appointment_slots
from . import appointments
from . import audit_logs
from . import banks
from . import billing_categories
from . import doctor_specialties
from . import doctors
from . import expenses
from . import lab_orders
from . import lab_tests
from . import medical_certificates
from . import medical_conditions
from . import medical_reports
from . import medical_services
from . import medications
from . import modules
from . import patient_allergies
from . import patient_diagnoses
from . import patient_payments
from . import patient_visits
from . import patients
from . import pharmacies
from . import prescriptions
from . import radiology_exams
from . import radiology_orders
from . import role_permissions
from . import role
from . import staff
from . import symptoms
from . import system_users
from . import user_sessions
from . import vaccination_schedules
from . import vaccines
from . import visit_symptoms


__all__ = [
    "allergies",
    "appointment_slots",
    "appointments",
    "audit_logs",
    "banks",
    "billing_categories",
    "doctor_specialties",
    "doctors",
    "expenses",
    "lab_orders",
    "lab_tests",
    "medical_certificates",
    "medical_conditions",
    "medical_reports",
    "medical_services",
    "medications",
    "modules",
    "patient_allergies",
    "patient_diagnoses",
    "patient_payments",
    "patient_visits",
    "patients",
    "pharmacies",
    "prescriptions",
    "radiology_exams",
    "radiology_orders",
    "role_permissions",
    "role",
    "staff",
    "symptoms",
    "system_users",
    "user_sessions",
    "vaccination_schedules",
    "vaccines",
    "visit_symptoms"
]