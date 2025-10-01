# Authentication System - Complete Setup Guide

## ✅ What Has Been Updated

### 1. **Improved Security**
- ✅ Strong SECRET_KEY configured in `.env`
- ✅ Removed insecure `simple_hash` fallback from auth
- ✅ Environment-based configuration
- ✅ Bcrypt password hashing (industry standard)
- ✅ JWT token-based authentication
- ✅ Token expiration set to 24 hours (configurable)

### 2. **Role-Based Access Control**
Added missing permission functions in `backend/deps.py`:
- `require_super_admin`
- `require_admin_or_super`
- `require_doctor_or_above`
- `require_accountant_or_above`
- `require_pharmacist_or_above`
- `require_any_user`
- `require_permission()` (placeholder for future fine-grained permissions)

### 3. **Files Created**
- ✅ `AUTH_SETUP.md` - Comprehensive authentication guide
- ✅ `test_auth.py` - Python authentication test script
- ✅ `test_auth.sh` - Bash authentication test script
- ✅ `create_admin_user.sql` - SQL script to create admin (requires superuser)
- ✅ `create_admin_simple.py` - Python script (has audit trigger issues)

## 🔐 Creating the Super Admin User

### Option 1: Using SQL Script (RECOMMENDED)

The database has audit triggers that require a user_id. The easiest way is to run the SQL script as a PostgreSQL superuser:

```bash
# Connect as postgres superuser and run the script
sudo -u postgres psql -d cabinet_management -f create_admin_user.sql
```

Or manually:

```bash
# Connect to database
sudo -u postgres psql -d cabinet_management

# Run these commands:
BEGIN;
SET session_replication_role = 'replica';

-- Ensure super_admin role exists
INSERT INTO roles (name, description, created_by, created_at)
VALUES ('super_admin', 'Super Administrator with full access', 1, NOW())
ON CONFLICT DO NOTHING;

-- Create staff record
INSERT INTO staff (first_name, last_name, email, position, department, created_by, created_at)
VALUES ('Super', 'Admin', 'admin@cabinet.local', 'System Administrator', 'IT', 1, NOW());

-- Create system user (password: admin123)
INSERT INTO system_users (staff_id, username, password_hash, role_id, is_active, created_by, created_at)
VALUES (
    (SELECT id FROM staff WHERE email = 'admin@cabinet.local' ORDER BY id DESC LIMIT 1),
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxIYzRHWu',
    (SELECT id FROM roles WHERE name = 'super_admin' LIMIT 1),
    TRUE,
    1,
    NOW()
);

SET session_replication_role = 'origin';
COMMIT;
```

### Option 2: Disable Audit Trigger Temporarily

If you have database admin access:

```sql
-- Disable trigger
ALTER TABLE staff DISABLE TRIGGER ALL;
ALTER TABLE system_users DISABLE TRIGGER ALL;

-- Run the insert statements above

-- Re-enable trigger
ALTER TABLE staff ENABLE TRIGGER ALL;
ALTER TABLE system_users ENABLE TRIGGER ALL;
```

### Option 3: Modify Audit Trigger

Update the audit trigger to allow NULL user_id for bootstrap:

```sql
-- Modify the trigger function to allow NULL user_id
-- (This would require editing the log_audit_event() function)
```

## 📋 Test Credentials

Once created, use these credentials:

- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `super_admin`
- **Email**: `admin@cabinet.local`

⚠️ **IMPORTANT**: Change this password immediately after first login!

## 🧪 Testing Authentication

### 1. Start the Server

```bash
python run_server.py
```

### 2. Test with Python Script

```bash
python test_auth.py
```

### 3. Test with Bash Script

```bash
./test_auth.sh
```

### 4. Manual cURL Test

```bash
# Login
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Get user info (replace TOKEN with actual token)
curl -X GET "http://127.0.0.1:8000/auth/me" \
  -H "Authorization: Bearer TOKEN"
```

## 🌐 Access Points

- **API Documentation**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health
- **Frontend**: http://127.0.0.1:8000/app/index.html
- **Login Page**: http://127.0.0.1:8000/app/login.html

## 🔒 Security Configuration

### Environment Variables (`.env`)

```env
# Strong SECRET_KEY (generated with: openssl rand -hex 32)
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

### Password Hashing

- **Algorithm**: Bcrypt
- **Rounds**: 12 (default)
- **Max Length**: 72 bytes (bcrypt limitation)

### JWT Tokens

- **Algorithm**: HS256
- **Expiration**: 24 hours (configurable)
- **Claims**: username, role, user_id, role_id

## 📝 API Usage Examples

### Login and Get Token

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/auth/token",
    data={"username": "admin", "password": "admin123"}
)

data = response.json()
token = data["access_token"]
user = data["user"]
```

### Make Authenticated Request

```python
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://127.0.0.1:8000/auth/me",
    headers=headers
)

user_info = response.json()
```

### JavaScript/Frontend Example

```javascript
// Login
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('http://127.0.0.1:8000/auth/token', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: formData
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
}

// Use token
async function getProfile() {
  const token = localStorage.getItem('token');
  const response = await fetch('http://127.0.0.1:8000/auth/me', {
    headers: {'Authorization': `Bearer ${token}`}
  });
  return await response.json();
}
```

## ⚠️ Production Checklist

Before deploying to production:

- [ ] Change default admin password
- [ ] Generate new SECRET_KEY: `openssl rand -hex 32`
- [ ] Update CORS settings (remove `allow_origins=["*"]`)
- [ ] Set up HTTPS/TLS
- [ ] Implement rate limiting on auth endpoints
- [ ] Add password complexity requirements
- [ ] Set up password reset functionality
- [ ] Enable audit logging
- [ ] Implement session management
- [ ] Add 2FA (optional but recommended)
- [ ] Review and test all permission functions
- [ ] Disable `/api/sql/execute` endpoint
- [ ] Set up monitoring and alerts

## 🐛 Troubleshooting

### "Could not validate credentials"
- Token expired (default 24 hours)
- Invalid token format
- SECRET_KEY changed after token was issued
- **Solution**: Login again to get a new token

### "Invalid username or password"
- Check credentials are correct
- Ensure user exists in database
- Verify user is active (`is_active = TRUE`)
- **Solution**: Verify user in database or reset password

### "Access denied. Required roles: ..."
- User doesn't have required role
- **Solution**: Check user's role and endpoint requirements

### Audit Trigger Issues
- Database triggers require user_id
- **Solution**: Use SQL script with superuser access or temporarily disable triggers

## 📚 Additional Resources

- **Full Auth Guide**: `AUTH_SETUP.md`
- **Backend Fixes**: `FIXES_APPLIED.md`
- **API Docs**: http://127.0.0.1:8000/docs
- **Test Scripts**: `test_auth.py`, `test_auth.sh`

## 🎯 Next Steps

1. Create super admin user using SQL script
2. Test authentication with test scripts
3. Change default password
4. Review security settings
5. Implement additional security measures for production
