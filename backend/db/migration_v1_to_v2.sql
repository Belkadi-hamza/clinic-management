-- ===========================
-- Migration Script: DB-1 to DB-2
-- ===========================
-- This script migrates the database from version 1 to version 2
-- Run this on an existing DB-1 database to upgrade to DB-2 structure

BEGIN;

-- ===========================
-- Step 1: Create departments table
-- ===========================
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    head_id INTEGER,
    created_by INTEGER,
    updated_by INTEGER,
    deleted_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ
);

-- ===========================
-- Step 2: Modify staff table
-- ===========================

-- Add new columns to staff table
ALTER TABLE staff 
    ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS doctor_code VARCHAR(20),
    ADD COLUMN IF NOT EXISTS specialization VARCHAR(100),
    ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);

-- Add unique constraint to doctor_code
ALTER TABLE staff 
    ADD CONSTRAINT staff_doctor_code_unique UNIQUE (doctor_code);

-- Migrate department data from VARCHAR to department_id
-- First, create departments from existing staff.department values
INSERT INTO departments (name, created_by, created_at)
SELECT DISTINCT 
    department,
    1, -- created by system admin
    CURRENT_TIMESTAMP
FROM staff 
WHERE department IS NOT NULL 
    AND department != ''
    AND NOT EXISTS (
        SELECT 1 FROM departments d WHERE d.name = staff.department
    );

-- Update staff.department_id based on staff.department
UPDATE staff s
SET department_id = d.id
FROM departments d
WHERE s.department = d.name;

-- ===========================
-- Step 3: Add foreign key constraint from departments to staff
-- ===========================
ALTER TABLE departments
    ADD CONSTRAINT fk_department_head FOREIGN KEY (head_id)
    REFERENCES staff(id) ON DELETE SET NULL;

-- ===========================
-- Step 4: Update roles table (fix missing comma if needed)
-- ===========================
-- The roles table in DB-1 has a syntax error on line 57 (missing comma)
-- This is already fixed in DB-2, no migration needed if table exists

-- ===========================
-- Step 5: Create indexes for new columns
-- ===========================
CREATE INDEX IF NOT EXISTS idx_staff_department_id ON staff(department_id);
CREATE INDEX IF NOT EXISTS idx_staff_role_id ON staff(role_id);
CREATE INDEX IF NOT EXISTS idx_departments_head_id ON departments(head_id);
CREATE INDEX IF NOT EXISTS idx_departments_deleted_at ON departments(deleted_at);

-- ===========================
-- Step 6: Add triggers for departments table
-- ===========================
CREATE TRIGGER update_departments_updated_at 
    BEFORE UPDATE ON departments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================
-- Step 7: Optional - Keep old department column for reference
-- ===========================
-- You can choose to drop the old department column or keep it for reference
-- Uncomment the line below to drop it:
-- ALTER TABLE staff DROP COLUMN IF EXISTS department;

-- ===========================
-- Step 8: Optional - Keep old position column for reference
-- ===========================
-- The position column is removed in DB-2 but might contain useful data
-- Consider migrating position data to role_id or keeping it
-- Uncomment the line below to drop it:
-- ALTER TABLE staff DROP COLUMN IF EXISTS position;

COMMIT;

-- ===========================
-- Verification Queries
-- ===========================
-- Run these after migration to verify:

-- Check departments were created
-- SELECT * FROM departments;

-- Check staff department_id is populated
-- SELECT id, first_name, last_name, department, department_id FROM staff;

-- Check for any staff without department_id (should migrate manually)
-- SELECT id, first_name, last_name, department FROM staff WHERE department IS NOT NULL AND department_id IS NULL;
