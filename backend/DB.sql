-- SQLBook: Code
-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'doctor', 'staff');
CREATE TYPE gender_type AS ENUM ('male', 'female');
CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced', 'widowed');
CREATE TYPE blood_type AS ENUM ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-');
CREATE TYPE appointment_status AS ENUM ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show');
CREATE TYPE payment_method AS ENUM ('cash', 'check', 'card', 'transfer');
CREATE TYPE allergy_type AS ENUM ('food', 'drug', 'environmental', 'other');
CREATE TYPE visit_type AS ENUM ('consultation', 'follow_up', 'emergency', 'routine_checkup');
CREATE TYPE diagnosis_certainty AS ENUM ('confirmed', 'probable', 'suspected', 'ruled_out');
CREATE TYPE allergy_severity AS ENUM ('mild', 'moderate', 'severe', 'life_threatening');
CREATE TYPE staff_gender AS ENUM ('M', 'F', 'O');

-- ===========================
-- Staff (all people working in the clinic)
-- ===========================
CREATE TABLE staff (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender staff_gender,
    marital_status VARCHAR(50),
    mobile_phone VARCHAR(20),
    home_phone VARCHAR(20),
    fax VARCHAR(20),
    email VARCHAR(150),
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    profile_image TEXT,
    position VARCHAR(100),
    hire_date DATE,
    department VARCHAR(100),
    created_by INTEGER,
    updated_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL
);

-- ===========================
-- Roles
-- ===========================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_by INTEGER,
    updated_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL
);

-- ===========================
-- Module Permissions
-- ===========================
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- Role Permissions
-- ===========================
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    
    can_create BOOLEAN DEFAULT FALSE,
    can_read BOOLEAN DEFAULT FALSE,
    can_update BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_export BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE,
    
    created_by INTEGER,
    updated_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(role_id, module_id)
);

-- ===========================
-- Users (subset of staff who can log in)
-- ===========================
CREATE TABLE system_users (
    id SERIAL PRIMARY KEY,
    staff_id INTEGER UNIQUE NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    username VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    must_change_password BOOLEAN DEFAULT FALSE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_by INTEGER,
    updated_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id) ON DELETE SET NULL
);

-- ===========================
-- User Sessions
-- ===========================
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES system_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- Audit Logs
-- ===========================
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER NOT NULL REFERENCES system_users(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Insert default modules
INSERT INTO modules (name, description) VALUES
('patients', 'Patient Management Module'),
('doctors', 'Doctor Management Module'),
('appointments', 'Appointment Scheduling Module'),
('medical_records', 'Medical Records Module'),
('prescriptions', 'Prescription Management Module'),
('lab_tests', 'Laboratory Tests Module'),
('radiology', 'Radiology Module'),
('billing', 'Billing and Payments Module'),
('inventory', 'Medical Inventory Module'),
('staff', 'Staff Management Module'),
('reports', 'Reports and Analytics Module'),
('system', 'System Administration Module');

-- Insert default roles
INSERT INTO roles (name, description) VALUES
('super_admin', 'Full system access with user management privileges'),
('admin', 'Administrative access with most system privileges'),
('doctor', 'Medical professional with patient care privileges'),
('nurse', 'Nursing staff with limited medical privileges'),
('lab_technician', 'Laboratory staff with test management privileges'),
('receptionist', 'Front desk staff with scheduling privileges'),
('accountant', 'Billing and financial staff'),
('pharmacist', 'Pharmacy staff with medication privileges');

-- Insert default Super Admin permissions (full access to everything)
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
SELECT 
    r.id, 
    m.id, 
    TRUE, TRUE, TRUE, TRUE, TRUE, TRUE
FROM roles r, modules m 
WHERE r.name = 'super_admin';

-- Insert Admin permissions (full access except user management)
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
SELECT 
    r.id, 
    m.id, 
    TRUE, TRUE, TRUE, TRUE, TRUE, FALSE
FROM roles r, modules m 
WHERE r.name = 'admin' AND m.name != 'system';

-- Give admin limited system access (read-only for system module)
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
SELECT 
    r.id, 
    m.id, 
    FALSE, TRUE, FALSE, FALSE, FALSE, FALSE
FROM roles r, modules m 
WHERE r.name = 'admin' AND m.name = 'system';

-- Insert Doctor permissions
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
VALUES
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'patients'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'appointments'), TRUE, TRUE, TRUE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'medical_records'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'prescriptions'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'lab_tests'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'radiology'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'doctor'), (SELECT id FROM modules WHERE name = 'reports'), FALSE, TRUE, FALSE, FALSE, TRUE, FALSE);

-- Insert Nurse permissions
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
VALUES
((SELECT id FROM roles WHERE name = 'nurse'), (SELECT id FROM modules WHERE name = 'patients'), TRUE, TRUE, TRUE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'nurse'), (SELECT id FROM modules WHERE name = 'appointments'), TRUE, TRUE, TRUE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'nurse'), (SELECT id FROM modules WHERE name = 'medical_records'), TRUE, TRUE, FALSE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'nurse'), (SELECT id FROM modules WHERE name = 'prescriptions'), FALSE, TRUE, FALSE, FALSE, FALSE, FALSE);

-- Insert Receptionist permissions
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
VALUES
((SELECT id FROM roles WHERE name = 'receptionist'), (SELECT id FROM modules WHERE name = 'patients'), TRUE, TRUE, TRUE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'receptionist'), (SELECT id FROM modules WHERE name = 'appointments'), TRUE, TRUE, TRUE, TRUE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'receptionist'), (SELECT id FROM modules WHERE name = 'billing'), TRUE, TRUE, TRUE, FALSE, FALSE, FALSE);

-- Insert Lab Technician permissions
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
VALUES
((SELECT id FROM roles WHERE name = 'lab_technician'), (SELECT id FROM modules WHERE name = 'patients'), FALSE, TRUE, FALSE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'lab_technician'), (SELECT id FROM modules WHERE name = 'lab_tests'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'lab_technician'), (SELECT id FROM modules WHERE name = 'medical_records'), FALSE, TRUE, TRUE, FALSE, FALSE, FALSE);

-- Insert Accountant permissions
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
VALUES
((SELECT id FROM roles WHERE name = 'accountant'), (SELECT id FROM modules WHERE name = 'patients'), FALSE, TRUE, FALSE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'accountant'), (SELECT id FROM modules WHERE name = 'billing'), TRUE, TRUE, TRUE, TRUE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'accountant'), (SELECT id FROM modules WHERE name = 'reports'), FALSE, TRUE, FALSE, FALSE, TRUE, FALSE);

-- Insert Pharmacist permissions
INSERT INTO role_permissions (role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users)
VALUES
((SELECT id FROM roles WHERE name = 'pharmacist'), (SELECT id FROM modules WHERE name = 'patients'), FALSE, TRUE, FALSE, FALSE, FALSE, FALSE),
((SELECT id FROM roles WHERE name = 'pharmacist'), (SELECT id FROM modules WHERE name = 'prescriptions'), TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
((SELECT id FROM roles WHERE name = 'pharmacist'), (SELECT id FROM modules WHERE name = 'inventory'), TRUE, TRUE, TRUE, TRUE, TRUE, FALSE);

-- Create the first staff member (Super Admin)
INSERT INTO staff (
    first_name, 
    last_name, 
    position, 
    department, 
    hire_date,
    email
) VALUES (
    'System', 
    'Administrator', 
    'System Administrator', 
    'IT', 
    CURRENT_DATE,
    'admin@hospital.com'
);

-- Create the first system user (Super Admin)
INSERT INTO system_users (
    staff_id,
    username,
    password_hash,
    role_id,
    is_active
) VALUES (
    1,
    'superadmin',
    -- Password: 'Admin123!' - You should hash this properly in your application
    '$2b$12$LQv3c1yqBWVHxkd0g8f7O.FfG2c3Q7p8x8UZ8bR8X8N8eJ8vR8X8O',
    (SELECT id FROM roles WHERE name = 'super_admin'),
    TRUE
);

-- Update the created_by fields for the first records
UPDATE staff SET created_by = 1 WHERE id = 1;
UPDATE roles SET created_by = 1;
UPDATE role_permissions SET created_by = 1;
UPDATE system_users SET created_by = 1 WHERE id = 1;

-- ===========================
-- Core Medical Tables
-- ===========================

-- Doctors (medical professionals)
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    doctor_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    license_number VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    mobile VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Patients
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    patient_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender gender_type,
    marital_status marital_status,
    blood_type blood_type,
    place_of_birth VARCHAR(255),
    medical_history TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Medical Services & Procedures
CREATE TABLE medical_services (
    id SERIAL PRIMARY KEY,
    service_code VARCHAR(20) UNIQUE NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    description TEXT,
    standard_price DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Clinical Data
CREATE TABLE patient_visits (
    id SERIAL PRIMARY KEY,
    visit_code VARCHAR(20) UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    visit_date DATE NOT NULL,
    visit_time TIME,
    visit_type visit_type,
    chief_complaint TEXT,
    diagnosis TEXT,
    clinical_notes TEXT,
    weight DECIMAL(5,2),
    height DECIMAL(5,2),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    blood_glucose DECIMAL(5,2),
    temperature DECIMAL(4,2),
    status VARCHAR(50) DEFAULT 'completed',
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE visit_services (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES medical_services(id) ON DELETE CASCADE,
    actual_price DECIMAL(10,2),
    performed_by_doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Medical Conditions & Diagnoses
CREATE TABLE medical_conditions (
    id SERIAL PRIMARY KEY,
    condition_code VARCHAR(20) UNIQUE NOT NULL,
    condition_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    icd_code VARCHAR(20),
    description TEXT,
    general_information TEXT,
    diagnostic_criteria TEXT,
    treatment_guidelines TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE patient_diagnoses (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    condition_id INTEGER NOT NULL REFERENCES medical_conditions(id) ON DELETE CASCADE,
    diagnosis_date DATE NOT NULL,
    diagnosing_doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    certainty_level diagnosis_certainty,
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Allergies
CREATE TABLE allergies (
    id SERIAL PRIMARY KEY,
    allergy_name VARCHAR(255) NOT NULL,
    allergy_type allergy_type NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE patient_allergies (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    allergy_id INTEGER NOT NULL REFERENCES allergies(id) ON DELETE CASCADE,
    severity allergy_severity,
    reaction_description TEXT,
    diagnosed_date DATE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Medications & Prescriptions
CREATE TABLE medications (
    id SERIAL PRIMARY KEY,
    medication_code VARCHAR(20) UNIQUE NOT NULL,
    generic_name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    pharmaceutical_form VARCHAR(100),
    dosage_strength VARCHAR(100),
    manufacturer VARCHAR(255),
    unit_price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE prescriptions (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    medication_id INTEGER NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    prescribing_doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    dosage_instructions TEXT NOT NULL,
    quantity_prescribed INTEGER,
    duration_days INTEGER,
    is_free BOOLEAN DEFAULT FALSE,
    refills_allowed INTEGER DEFAULT 0,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Laboratory & Radiology
CREATE TABLE lab_tests (
    id SERIAL PRIMARY KEY,
    test_code VARCHAR(20) UNIQUE NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    specimen_type VARCHAR(100),
    reference_range_min DECIMAL(10,2),
    reference_range_max DECIMAL(10,2),
    measurement_unit VARCHAR(50),
    is_favorite BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE lab_orders (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES lab_tests(id) ON DELETE CASCADE,
    ordering_doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    order_date DATE NOT NULL,
    laboratory_name VARCHAR(255),
    clinical_notes TEXT,
    results TEXT,
    result_date DATE,
    is_abnormal BOOLEAN,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE radiology_exams (
    id SERIAL PRIMARY KEY,
    exam_code VARCHAR(20) UNIQUE NOT NULL,
    exam_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    exam_type VARCHAR(50),
    is_favorite BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE radiology_orders (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    exam_id INTEGER NOT NULL REFERENCES radiology_exams(id) ON DELETE CASCADE,
    ordering_doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    order_date DATE NOT NULL,
    imaging_center VARCHAR(255),
    clinical_notes TEXT,
    radiology_report TEXT,
    findings TEXT,
    conclusion TEXT,
    report_date DATE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Appointments & Scheduling
CREATE TABLE appointment_slots (
    id SERIAL PRIMARY KEY,
    slot_index INTEGER NOT NULL,
    slot_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    appointment_code VARCHAR(20) UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    slot_id INTEGER REFERENCES appointment_slots(id) ON DELETE SET NULL,
    appointment_type VARCHAR(50),
    status appointment_status DEFAULT 'scheduled',
    reason_for_visit TEXT,
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Vaccinations
CREATE TABLE vaccines (
    id SERIAL PRIMARY KEY,
    vaccine_code VARCHAR(20) UNIQUE NOT NULL,
    vaccine_name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(255),
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE vaccination_schedules (
    id SERIAL PRIMARY KEY,
    schedule_code VARCHAR(20) UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    vaccine_id INTEGER NOT NULL REFERENCES vaccines(id) ON DELETE CASCADE,
    dose_number INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    administered_date DATE,
    is_administered BOOLEAN DEFAULT FALSE,
    administering_doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
    lot_number VARCHAR(100),
    adverse_reactions TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Billing & Payments
CREATE TABLE billing_categories (
    id SERIAL PRIMARY KEY,
    category_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE patient_payments (
    id SERIAL PRIMARY KEY,
    payment_code VARCHAR(20) UNIQUE NOT NULL,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method payment_method NOT NULL,
    bank_name VARCHAR(100),
    check_number VARCHAR(50),
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    expense_code VARCHAR(20) UNIQUE NOT NULL,
    expense_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES billing_categories(id) ON DELETE SET NULL,
    description TEXT,
    payment_method payment_method,
    bank_name VARCHAR(100),
    check_number VARCHAR(50),
    recorded_by_doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Medical Documents
CREATE TABLE medical_certificates (
    id SERIAL PRIMARY KEY,
    certificate_code VARCHAR(20) UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    issuing_doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    issue_date DATE NOT NULL,
    certificate_type VARCHAR(100) NOT NULL,
    work_resumption_date DATE,
    accident_date DATE,
    medical_findings TEXT,
    restrictions TEXT,
    duration_days INTEGER,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE medical_reports (
    id SERIAL PRIMARY KEY,
    report_code VARCHAR(20) UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    report_type VARCHAR(100),
    title VARCHAR(255),
    content TEXT,
    additional_notes TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Reference Data
CREATE TABLE symptoms (
    id SERIAL PRIMARY KEY,
    symptom_code VARCHAR(20) UNIQUE NOT NULL,
    symptom_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE pharmacies (
    id SERIAL PRIMARY KEY,
    pharmacy_code VARCHAR(20) UNIQUE NOT NULL,
    pharmacy_name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    phone VARCHAR(20),
    mobile VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE banks (
    id SERIAL PRIMARY KEY,
    bank_code VARCHAR(20) UNIQUE NOT NULL,
    bank_name VARCHAR(255) NOT NULL,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    updated_by INTEGER REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- Junction tables for many-to-many relationships
CREATE TABLE visit_symptoms (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER NOT NULL REFERENCES patient_visits(id) ON DELETE CASCADE,
    symptom_id INTEGER NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
    severity VARCHAR(50),
    duration_days INTEGER,
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

CREATE TABLE doctor_specialties (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    specialty VARCHAR(100) NOT NULL,
    created_by INTEGER NOT NULL REFERENCES system_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    deleted_by INTEGER REFERENCES system_users(id)
);

-- ===========================
-- Indexes for Performance
-- ===========================

-- Staff management indexes
CREATE INDEX idx_staff_deleted_at ON staff(deleted_at);
CREATE INDEX idx_staff_department ON staff(department);
CREATE INDEX idx_staff_position ON staff(position);
CREATE INDEX idx_roles_deleted_at ON roles(deleted_at);
CREATE INDEX idx_role_permissions_role_module ON role_permissions(role_id, module_id);
CREATE INDEX idx_system_users_staff_id ON system_users(staff_id);
CREATE INDEX idx_system_users_role_id ON system_users(role_id);
CREATE INDEX idx_system_users_username ON system_users(username);
CREATE INDEX idx_system_users_deleted_at ON system_users(deleted_at);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Medical data indexes
CREATE INDEX idx_patient_visits_patient_id ON patient_visits(patient_id);
CREATE INDEX idx_patient_visits_doctor_id ON patient_visits(doctor_id);
CREATE INDEX idx_patient_visits_date ON patient_visits(visit_date);
CREATE INDEX idx_patient_visits_deleted_at ON patient_visits(deleted_at);
CREATE INDEX idx_patient_visits_created_by ON patient_visits(created_by);
CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_deleted_at ON appointments(deleted_at);
CREATE INDEX idx_appointments_created_by ON appointments(created_by);
CREATE INDEX idx_prescriptions_visit_id ON prescriptions(visit_id);
CREATE INDEX idx_prescriptions_deleted_at ON prescriptions(deleted_at);
CREATE INDEX idx_prescriptions_created_by ON prescriptions(created_by);
CREATE INDEX idx_lab_orders_visit_id ON lab_orders(visit_id);
CREATE INDEX idx_lab_orders_deleted_at ON lab_orders(deleted_at);
CREATE INDEX idx_lab_orders_created_by ON lab_orders(created_by);
CREATE INDEX idx_radiology_orders_visit_id ON radiology_orders(visit_id);
CREATE INDEX idx_radiology_orders_deleted_at ON radiology_orders(deleted_at);
CREATE INDEX idx_radiology_orders_created_by ON radiology_orders(created_by);
CREATE INDEX idx_patient_allergies_patient_id ON patient_allergies(patient_id);
CREATE INDEX idx_patient_allergies_deleted_at ON patient_allergies(deleted_at);
CREATE INDEX idx_patient_allergies_created_by ON patient_allergies(created_by);
CREATE INDEX idx_visit_services_visit_id ON visit_services(visit_id);
CREATE INDEX idx_visit_services_deleted_at ON visit_services(deleted_at);
CREATE INDEX idx_visit_services_created_by ON visit_services(created_by);
CREATE INDEX idx_patient_diagnoses_visit_id ON patient_diagnoses(visit_id);
CREATE INDEX idx_patient_diagnoses_deleted_at ON patient_diagnoses(deleted_at);
CREATE INDEX idx_patient_diagnoses_created_by ON patient_diagnoses(created_by);
CREATE INDEX idx_patients_deleted_at ON patients(deleted_at);
CREATE INDEX idx_patients_created_by ON patients(created_by);
CREATE INDEX idx_doctors_deleted_at ON doctors(deleted_at);
CREATE INDEX idx_doctors_created_by ON doctors(created_by);
CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id);

-- ===========================
-- Functions and Triggers
-- ===========================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to automatically set created_by and updated_by
CREATE OR REPLACE FUNCTION set_audit_fields()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.created_by = COALESCE(NEW.created_by, current_setting('app.current_user_id', TRUE)::INTEGER);
        NEW.updated_by = NEW.created_by;
    ELSIF TG_OP = 'UPDATE' THEN
        NEW.updated_by = COALESCE(NEW.updated_by, current_setting('app.current_user_id', TRUE)::INTEGER);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function for audit logging
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_action TEXT;
    v_user_id INTEGER;
BEGIN
    v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;
    
    IF TG_OP = 'INSERT' THEN
        v_action := 'INSERT';
        v_new_data := to_jsonb(NEW);
        v_old_data := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_action := 'UPDATE';
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_action := 'DELETE';
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    END IF;

    INSERT INTO audit_logs (
        table_name,
        record_id,
        action,
        old_values,
        new_values,
        user_id,
        ip_address,
        user_agent
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        v_action,
        v_old_data,
        v_new_data,
        v_user_id,
        current_setting('app.ip_address', TRUE)::INET,
        current_setting('app.user_agent', TRUE)
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ language 'plpgsql';

-- Function for permission checking
CREATE OR REPLACE FUNCTION check_permission(
    p_user_id INTEGER,
    p_module_name VARCHAR,
    p_action VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_has_permission BOOLEAN;
    v_user_role_id INTEGER;
BEGIN
    -- Get user's role
    SELECT role_id INTO v_user_role_id 
    FROM system_users 
    WHERE id = p_user_id AND deleted_at IS NULL AND is_active = TRUE;
    
    IF v_user_role_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user is super admin (has all permissions)
    IF EXISTS (SELECT 1 FROM roles WHERE id = v_user_role_id AND name = 'super_admin') THEN
        RETURN TRUE;
    END IF;
    
    -- Check specific permission
    SELECT 
        CASE p_action
            WHEN 'create' THEN can_create
            WHEN 'read' THEN can_read
            WHEN 'update' THEN can_update
            WHEN 'delete' THEN can_delete
            WHEN 'export' THEN can_export
            WHEN 'manage_users' THEN can_manage_users
            ELSE FALSE
        END INTO v_has_permission
    FROM role_permissions rp
    JOIN modules m ON rp.module_id = m.id
    WHERE rp.role_id = v_user_role_id AND m.name = p_module_name;
    
    RETURN COALESCE(v_has_permission, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function for soft delete with user attribution
CREATE OR REPLACE FUNCTION soft_delete_record()
RETURNS TRIGGER AS $$
BEGIN
    NEW.deleted_at = CURRENT_TIMESTAMP;
    NEW.deleted_by = current_setting('app.current_user_id', TRUE)::INTEGER;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ===========================
-- Triggers
-- ===========================

-- Triggers for updated_at
CREATE TRIGGER update_staff_updated_at BEFORE UPDATE ON staff FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_permissions_updated_at BEFORE UPDATE ON role_permissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_users_updated_at BEFORE UPDATE ON system_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON doctors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_services_updated_at BEFORE UPDATE ON medical_services FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patient_visits_updated_at BEFORE UPDATE ON patient_visits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_conditions_updated_at BEFORE UPDATE ON medical_conditions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_allergies_updated_at BEFORE UPDATE ON allergies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medications_updated_at BEFORE UPDATE ON medications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lab_tests_updated_at BEFORE UPDATE ON lab_tests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lab_orders_updated_at BEFORE UPDATE ON lab_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_radiology_exams_updated_at BEFORE UPDATE ON radiology_exams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_radiology_orders_updated_at BEFORE UPDATE ON radiology_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_appointment_slots_updated_at BEFORE UPDATE ON appointment_slots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vaccines_updated_at BEFORE UPDATE ON vaccines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vaccination_schedules_updated_at BEFORE UPDATE ON vaccination_schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pharmacies_updated_at BEFORE UPDATE ON pharmacies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for audit fields
CREATE TRIGGER set_staff_audit_fields BEFORE INSERT OR UPDATE ON staff FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_roles_audit_fields BEFORE INSERT OR UPDATE ON roles FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_role_permissions_audit_fields BEFORE INSERT OR UPDATE ON role_permissions FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_system_users_audit_fields BEFORE INSERT OR UPDATE ON system_users FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_doctors_audit_fields BEFORE INSERT OR UPDATE ON doctors FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_patients_audit_fields BEFORE INSERT OR UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_medical_services_audit_fields BEFORE INSERT OR UPDATE ON medical_services FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_patient_visits_audit_fields BEFORE INSERT OR UPDATE ON patient_visits FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_medical_conditions_audit_fields BEFORE INSERT OR UPDATE ON medical_conditions FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_allergies_audit_fields BEFORE INSERT OR UPDATE ON allergies FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_medications_audit_fields BEFORE INSERT OR UPDATE ON medications FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_lab_tests_audit_fields BEFORE INSERT OR UPDATE ON lab_tests FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_lab_orders_audit_fields BEFORE INSERT OR UPDATE ON lab_orders FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_radiology_exams_audit_fields BEFORE INSERT OR UPDATE ON radiology_exams FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_radiology_orders_audit_fields BEFORE INSERT OR UPDATE ON radiology_orders FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_appointment_slots_audit_fields BEFORE INSERT OR UPDATE ON appointment_slots FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_appointments_audit_fields BEFORE INSERT OR UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_vaccines_audit_fields BEFORE INSERT OR UPDATE ON vaccines FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_vaccination_schedules_audit_fields BEFORE INSERT OR UPDATE ON vaccination_schedules FOR EACH ROW EXECUTE FUNCTION set_audit_fields();
CREATE TRIGGER set_pharmacies_audit_fields BEFORE INSERT OR UPDATE ON pharmacies FOR EACH ROW EXECUTE FUNCTION set_audit_fields();

-- Triggers for audit logging (main tables only)
CREATE TRIGGER audit_staff AFTER INSERT OR UPDATE OR DELETE ON staff FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_roles AFTER INSERT OR UPDATE OR DELETE ON roles FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_system_users AFTER INSERT OR UPDATE OR DELETE ON system_users FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_doctors AFTER INSERT OR UPDATE OR DELETE ON doctors FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_patients AFTER INSERT OR UPDATE OR DELETE ON patients FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_patient_visits AFTER INSERT OR UPDATE OR DELETE ON patient_visits FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_appointments AFTER INSERT OR UPDATE OR DELETE ON appointments FOR EACH ROW EXECUTE FUNCTION log_audit_event();
CREATE TRIGGER audit_prescriptions AFTER INSERT OR UPDATE OR DELETE ON prescriptions FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- Triggers for soft delete
CREATE TRIGGER soft_delete_doctors BEFORE UPDATE ON doctors FOR EACH ROW WHEN (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) EXECUTE FUNCTION soft_delete_record();
CREATE TRIGGER soft_delete_patients BEFORE UPDATE ON patients FOR EACH ROW WHEN (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) EXECUTE FUNCTION soft_delete_record();
CREATE TRIGGER soft_delete_staff BEFORE UPDATE ON staff FOR EACH ROW WHEN (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) EXECUTE FUNCTION soft_delete_record();

-- ===========================
-- Views
-- ===========================

-- View for user permissions
CREATE VIEW user_permissions AS
SELECT 
    su.id as user_id,
    su.username,
    s.first_name,
    s.last_name,
    r.name as role_name,
    m.name as module_name,
    rp.can_create,
    rp.can_read,
    rp.can_update,
    rp.can_delete,
    rp.can_export,
    rp.can_manage_users
FROM system_users su
JOIN staff s ON su.staff_id = s.id
JOIN roles r ON su.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN modules m ON rp.module_id = m.id
WHERE su.deleted_at IS NULL AND su.is_active = TRUE
AND r.deleted_at IS NULL;

-- View for active records
CREATE VIEW active_patients AS
SELECT p.*, u1.username as created_by_username, u2.username as updated_by_username
FROM patients p
LEFT JOIN system_users u1 ON p.created_by = u1.id
LEFT JOIN system_users u2 ON p.updated_by = u2.id
WHERE p.deleted_at IS NULL;

CREATE VIEW active_doctors AS
SELECT d.*, u1.username as created_by_username, u2.username as updated_by_username
FROM doctors d
LEFT JOIN system_users u1 ON d.created_by = u1.id
LEFT JOIN system_users u2 ON d.updated_by = u2.id
WHERE d.deleted_at IS NULL;

CREATE VIEW active_staff AS
SELECT s.*, u1.username as created_by_username, u2.username as updated_by_username
FROM staff s
LEFT JOIN system_users u1 ON s.created_by = u1.id
LEFT JOIN system_users u2 ON s.updated_by = u2.id
WHERE s.deleted_at IS NULL;

CREATE VIEW active_appointments AS
SELECT a.*, u1.username as created_by_username, u2.username as updated_by_username
FROM appointments a
LEFT JOIN system_users u1 ON a.created_by = u1.id
LEFT JOIN system_users u2 ON a.updated_by = u2.id
WHERE a.deleted_at IS NULL;

CREATE VIEW active_patient_visits AS
SELECT pv.*, u1.username as created_by_username, u2.username as updated_by_username
FROM patient_visits pv
LEFT JOIN system_users u1 ON pv.created_by = u1.id
LEFT JOIN system_users u2 ON pv.updated_by = u2.id
WHERE pv.deleted_at IS NULL;

-- ===========================
-- Comments
-- ===========================

COMMENT ON TABLE staff IS 'All staff members working in the clinic';
COMMENT ON TABLE roles IS 'System roles with different permission levels';
COMMENT ON TABLE role_permissions IS 'Detailed permissions for each role per module';
COMMENT ON TABLE system_users IS 'Staff members with system login access';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for all data changes';
COMMENT ON FUNCTION check_permission IS 'Checks if a user has specific permission for a module action';

COMMENT ON COLUMN patients.created_by IS 'User who created this patient record';
COMMENT ON COLUMN patients.updated_by IS 'User who last updated this patient record';
COMMENT ON COLUMN patients.deleted_by IS 'User who soft deleted this patient record';
COMMENT ON COLUMN doctors.created_by IS 'User who created this doctor record';
COMMENT ON COLUMN doctors.updated_by IS 'User who last updated this doctor record';
COMMENT ON COLUMN doctors.deleted_by IS 'User who soft deleted this doctor record';

-- ===========================
-- Usage Examples in Application
-- ===========================

COMMENT ON TABLE system_users IS '
Application Usage:
1. Set user context before operations:
   SELECT set_config(''app.current_user_id'', ''1'', false);
   SELECT set_config(''app.ip_address'', ''192.168.1.1'', false);
   SELECT set_config(''app.user_agent'', ''Mozilla/5.0...'', false);

2. Check permissions:
   SELECT check_permission(1, ''patients'', ''create'');

3. Insert records (audit fields auto-populated):
   INSERT INTO patients (patient_code, first_name, last_name) VALUES (''PAT004'', ''John'', ''Doe'');

4. View user permissions:
   SELECT * FROM user_permissions WHERE user_id = 1;
';

-- Grant permissions (adjust based on your database users)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;