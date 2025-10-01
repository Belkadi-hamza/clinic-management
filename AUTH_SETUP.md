# Authentication Setup Guide

## Overview

The authentication system has been updated with improved security:
- ✅ Strong SECRET_KEY configured
- ✅ Removed insecure password hash fallback
- ✅ Environment-based configuration
- ✅ Bcrypt password hashing
- ✅ JWT token-based authentication
- ✅ Role-based access control

## Quick Start

### 1. Create Test Super Admin User

Run the script to create a test super admin account:

```bash
python create_test_user.py
```

This will create:
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `super_admin`
- **Email**: `admin@cabinet.local`

⚠️ **IMPORTANT**: Change this password after first login in production!

### 2. Test Authentication

#### Option A: Using Python Script
```bash
python test_auth.py
```

#### Option B: Using Bash Script
```bash
./test_auth.sh
```

#### Option C: Manual cURL Test
```bash
# Login and get token
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token for authenticated request
curl -X GET "http://127.0.0.1:8000/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Authentication Flow

### 1. Login (Get Token)

**Endpoint**: `POST /auth/token`

**Request**:
```bash
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "super_admin",
    "role_id": 1,
    "first_name": "Super",
    "last_name": "Admin",
    "email": "admin@cabinet.local"
  }
}
```

### 2. Use Token for Authenticated Requests

Include the token in the `Authorization` header:

```bash
curl -X GET "http://127.0.0.1:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Get Current User Info

**Endpoint**: `GET /auth/me`

**Response**:
```json
{
  "id": 1,
  "username": "admin",
  "role": "super_admin",
  "role_id": 1,
  "first_name": "Super",
  "last_name": "Admin",
  "email": "admin@cabinet.local"
}
```

## Role-Based Access Control

The system supports the following roles:
- `super_admin` - Full system access
- `admin` - Administrative access
- `doctor` - Doctor-specific access
- `nurse` - Nurse-specific access
- `receptionist` - Reception desk access
- `pharmacist` - Pharmacy access
- `lab_technician` - Laboratory access
- `accountant` - Financial access

### Available Permission Functions

In `backend/deps.py`:

```python
# Single role requirements
require_super_admin = require_roles("super_admin")
require_admin_or_super = require_roles("super_admin", "admin")

# Role hierarchies
require_doctor_or_above = require_roles("super_admin", "admin", "doctor")
require_accountant_or_above = require_roles("super_admin", "admin", "accountant")
require_pharmacist_or_above = require_roles("super_admin", "admin", "pharmacist")

# Any authenticated user
require_any_user = require_roles("super_admin", "admin", "doctor", "nurse", "receptionist", "pharmacist", "lab_technician", "accountant")
```

### Using in API Endpoints

```python
from fastapi import APIRouter, Depends
from backend.deps import require_admin_or_super, get_current_user

router = APIRouter()

@router.get("/admin-only")
def admin_endpoint(current_user: dict = Depends(require_admin_or_super)):
    return {"message": "Admin access granted", "user": current_user}

@router.get("/authenticated")
def auth_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "Authenticated", "user": current_user}
```

## Security Configuration

### Environment Variables (.env)

```env
# Application Configuration
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Generate New SECRET_KEY

For production, generate a new secret key:

```bash
openssl rand -hex 32
```

Then update `.env`:
```env
SECRET_KEY=your_new_generated_key_here
```

## Token Expiration

- **Default**: 1440 minutes (24 hours)
- **Configurable**: Set `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`

## Password Requirements

- **Hashing**: Bcrypt (secure, industry-standard)
- **Max Length**: 72 bytes (bcrypt limitation)
- **Minimum**: No minimum enforced (add validation as needed)

## Frontend Integration

### JavaScript/Fetch Example

```javascript
// Login
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('http://127.0.0.1:8000/auth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData
  });
  
  const data = await response.json();
  
  // Store token
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  return data;
}

// Make authenticated request
async function fetchProtectedData() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

## Troubleshooting

### "Could not validate credentials"
- Token expired (default 24 hours)
- Invalid token format
- SECRET_KEY changed after token was issued

### "Invalid username or password"
- Check username/password are correct
- Ensure user exists in database
- Verify user is active (`is_active = TRUE`)

### "Account is deactivated"
- User's `is_active` flag is set to `FALSE`
- Contact admin to reactivate account

### "Access denied. Required roles: ..."
- User doesn't have required role
- Check user's role in database
- Verify endpoint permission requirements

## API Documentation

Access interactive API documentation:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Next Steps

1. ✅ Create test user: `python create_test_user.py`
2. ✅ Test authentication: `python test_auth.py`
3. ✅ Access API docs: http://127.0.0.1:8000/docs
4. ⚠️ Change default password in production
5. ⚠️ Generate new SECRET_KEY for production
6. ⚠️ Implement password complexity requirements
7. ⚠️ Add rate limiting to auth endpoints
8. ⚠️ Set up HTTPS in production
