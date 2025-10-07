# Database Migration Guide: DB-1 to DB-2

## Overview
This guide explains how to migrate your existing database from version 1 (DB-1.sql) to version 2 (DB-2.sql).

## Key Changes in DB-2

### 1. **New Departments Table**
- Added a dedicated `departments` table for better organization
- Replaces the VARCHAR `department` field in staff table with a foreign key relationship

### 2. **Staff Table Enhancements**
- **Added columns:**
  - `department_id` (INTEGER) - Foreign key to departments table
  - `role_id` (INTEGER) - Foreign key to roles table
  - `doctor_code` (VARCHAR) - Unique identifier for doctors
  - `specialization` (VARCHAR) - Doctor's specialization
  - `license_number` (VARCHAR) - Professional license number

- **Deprecated columns:**
  - `department` (VARCHAR) - Replaced by `department_id`
  - `position` (VARCHAR) - Role information now in `role_id`

### 3. **Fixed Syntax Error**
- Fixed missing comma in roles table definition (line 57 in DB-1)

## Migration Options

### Option 1: Fresh Installation (Recommended for Development)
If you don't have important data or can recreate it:

```bash
# 1. Drop existing database
psql -h localhost -p 5432 -U postgres -c "DROP DATABASE IF EXISTS cabinet_management;"

# 2. Create fresh database
psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE cabinet_management;"

# 3. Run DB-2.sql
psql -h localhost -p 5432 -U cabinet_management -d cabinet_management -f backend/db/DB-2.sql
```

### Option 2: In-Place Migration (Recommended for Production)
If you have existing data to preserve:

```bash
# 1. Backup your current database
pg_dump -h localhost -p 5432 -U cabinet_management -d cabinet_management > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run the migration script
psql -h localhost -p 5432 -U cabinet_management -d cabinet_management -f backend/db/migration_v1_to_v2.sql

# 3. Verify the migration (see verification section below)
```

## Step-by-Step Migration Process

### Step 1: Backup Current Database
```bash
# Create a timestamped backup
pg_dump -h localhost -p 5432 -U cabinet_management -d cabinet_management > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup was created
ls -lh backup_*.sql
```

### Step 2: Run Migration Script
```bash
psql -h localhost -p 5432 -U cabinet_management -d cabinet_management -f backend/db/migration_v1_to_v2.sql
```

### Step 3: Verify Migration

Connect to your database:
```bash
psql -h localhost -p 5432 -U cabinet_management -d cabinet_management
```

Run verification queries:
```sql
-- Check departments table exists and has data
SELECT * FROM departments;

-- Check staff table has new columns
\d staff

-- Verify department migration
SELECT id, first_name, last_name, department, department_id 
FROM staff 
LIMIT 10;

-- Check for unmigrated departments
SELECT id, first_name, last_name, department 
FROM staff 
WHERE department IS NOT NULL AND department_id IS NULL;

-- Verify indexes were created
\di idx_staff_department_id
\di idx_staff_role_id
```

### Step 4: Manual Data Cleanup (Optional)

After verifying the migration:

```sql
-- If everything looks good, you can drop old columns
ALTER TABLE staff DROP COLUMN department;
ALTER TABLE staff DROP COLUMN position;
```

## Rollback Procedure

If something goes wrong, restore from backup:

```bash
# 1. Drop current database
psql -h localhost -p 5432 -U postgres -c "DROP DATABASE cabinet_management;"

# 2. Create fresh database
psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE cabinet_management;"

# 3. Restore from backup
psql -h localhost -p 5432 -U cabinet_management -d cabinet_management < backup_YYYYMMDD_HHMMSS.sql
```

## Post-Migration Tasks

### 1. Update Application Code
Ensure your application code is updated to use:
- `department_id` instead of `department` (VARCHAR)
- `role_id` for staff roles
- New doctor-specific fields (`doctor_code`, `specialization`, `license_number`)

### 2. Update Department Heads
If you have department heads, update them:
```sql
UPDATE departments 
SET head_id = (SELECT id FROM staff WHERE ... )
WHERE name = 'Department Name';
```

### 3. Populate Role IDs
Map staff positions to role_id:
```sql
-- Example: Update staff role_id based on old position
UPDATE staff 
SET role_id = (SELECT id FROM roles WHERE name = 'doctor')
WHERE position = 'Doctor';

UPDATE staff 
SET role_id = (SELECT id FROM roles WHERE name = 'nurse')
WHERE position = 'Nurse';
-- Add more mappings as needed
```

### 4. Populate Doctor-Specific Fields
For staff members who are doctors:
```sql
-- Generate doctor codes
UPDATE staff 
SET doctor_code = 'DOC' || LPAD(id::TEXT, 4, '0')
WHERE role_id = (SELECT id FROM roles WHERE name = 'doctor');
```

## Testing Checklist

- [ ] Backup created successfully
- [ ] Migration script ran without errors
- [ ] Departments table created and populated
- [ ] Staff table has new columns
- [ ] Department data migrated correctly
- [ ] Indexes created
- [ ] Triggers working
- [ ] Application can connect and query
- [ ] No data loss verified
- [ ] Old columns dropped (if desired)

## Common Issues & Solutions

### Issue 1: Permission Denied
**Error:** `permission denied for table staff`

**Solution:**
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cabinet_management;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cabinet_management;
```

### Issue 2: Foreign Key Constraint Violation
**Error:** `foreign key constraint fails`

**Solution:** Ensure referenced tables exist and have data before creating foreign keys.

### Issue 3: Duplicate Department Names
**Error:** `duplicate key value violates unique constraint`

**Solution:** Clean up duplicate department names before migration:
```sql
-- Find duplicates
SELECT department, COUNT(*) 
FROM staff 
WHERE department IS NOT NULL 
GROUP BY department 
HAVING COUNT(*) > 1;
```

## Support

For issues or questions:
1. Check the error logs: `tail -f /var/log/postgresql/postgresql-*.log`
2. Review the migration script: `backend/db/migration_v1_to_v2.sql`
3. Restore from backup if needed

## Database Connection Commands

### Connect to Database
```bash
psql -h localhost -p 5432 -U cabinet_management -d cabinet_management
```

### Useful psql Commands
```sql
\dt              -- List all tables
\d table_name    -- Describe table structure
\di              -- List all indexes
\df              -- List all functions
\dv              -- List all views
\l               -- List all databases
\q               -- Quit
```
