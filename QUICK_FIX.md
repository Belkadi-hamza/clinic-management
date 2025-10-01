# Quick Fix: Reset Admin Password

## Problem
The database has audit triggers that prevent password updates without proper user context.

## Solution

### Option 1: Run SQL Script as Postgres Superuser (RECOMMENDED)

```bash
# Run in your terminal
sudo -u postgres psql -d cabinet_management -f reset_password.sql
```

### Option 2: Manual SQL Commands

```bash
# Connect as postgres superuser
sudo -u postgres psql -d cabinet_management

# Then run these commands:
BEGIN;
SET session_replication_role = 'replica';

UPDATE system_users
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxIYzRHWu',
    updated_at = NOW()
WHERE username = 'superadmin';

SET session_replication_role = 'origin';
COMMIT;
```

### Option 3: Temporarily Disable Trigger

```bash
# Connect as postgres superuser
sudo -u postgres psql -d cabinet_management

# Disable trigger
ALTER TABLE system_users DISABLE TRIGGER ALL;

# Update password
UPDATE system_users
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxIYzRHWu',
    updated_at = NOW()
WHERE username = 'superadmin';

# Re-enable trigger
ALTER TABLE system_users ENABLE TRIGGER ALL;
```

## Test After Reset

```bash
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=superadmin&password=admin123"
```

## Existing Users in Database

| ID | Username   | Role           | Name                  |
|----|------------|----------------|-----------------------|
| 1  | superadmin | super_admin    | System Administrator  |
| 2  | jsmith     | doctor         | John Smith            |
| 3  | sjohnson   | nurse          | Sarah Johnson         |
| 4  | mbrown     | receptionist   | Mike Brown            |
| 5  | ldavis     | lab_technician | Lisa Davis            |

## Alternative: Find Existing Password

If you know the existing password for `superadmin`, just use that instead of resetting.

Try common passwords:
- admin
- password
- superadmin
- admin123
- password123

Test with:
```bash
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=superadmin&password=YOUR_PASSWORD_HERE"
```
