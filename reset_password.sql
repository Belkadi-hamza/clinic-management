-- Reset password for superadmin user
-- Run with: sudo -u postgres psql -d cabinet_management -f reset_password.sql
-- Or: PGPASSWORD=your_password psql -h 127.0.0.1 -U postgres -d cabinet_management -f reset_password.sql

BEGIN;

-- Temporarily disable triggers
SET session_replication_role = 'replica';

-- Reset password for superadmin (password: admin123)
UPDATE system_users
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxIYzRHWu',
    updated_at = NOW()
WHERE username = 'superadmin';

-- Re-enable triggers
SET session_replication_role = 'origin';

COMMIT;

-- Verify the update
SELECT 
    su.id,
    su.username,
    r.name as role,
    s.first_name,
    s.last_name,
    su.is_active
FROM system_users su
JOIN roles r ON su.role_id = r.id
JOIN staff s ON su.staff_id = s.id
WHERE su.username = 'superadmin';

\echo '=============================================='
\echo '✅ Password reset successfully!'
\echo '=============================================='
\echo 'Username: superadmin'
\echo 'New Password: admin123'
\echo '=============================================='
\echo 'Test with:'
\echo 'curl -X POST "http://127.0.0.1:8000/auth/token" \'
\echo '  -H "Content-Type: application/x-www-form-urlencoded" \'
\echo '  -d "username=superadmin&password=admin123"'
\echo '=============================================='
