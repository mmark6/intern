"""
SECURITY IMPLEMENTATION GUIDE
==============================

This document outlines all security measures implemented in the Uedcl Django backend application.

## 1. AUTHENTICATION & AUTHORIZATION

### JWT Token Security
- Access tokens expire in 15 minutes (previously 60 minutes)
- Refresh tokens expire in 7 days
- Token rotation enabled (refresh token changed on each refresh)
- Tokens automatically blacklisted after rotation
- Only "Bearer" auth header type accepted (not "Token")
- Algorithm: HS256

### Role-Based Access Control (RBAC)
Three user roles with different permissions:
- ADMIN: Full access to all features
- MANAGER: Can create/manage projects and tasks
- MEMBER: Can view and update own tasks

### Permission Classes
- `IsAdminUser`: Admin role only
- `IsManagerUser`: Manager or Admin
- `IsManagerOrAdmin`: Manager or Admin
- `IsAssigneeOrManager`: Task assignee or manager can modify
- `IsOwnerOrAdmin`: Resource owner or admin can modify
- Rate limiting per role

## 2. PASSWORD SECURITY

### Password Strength Requirements
- Minimum 8 characters
- Must contain uppercase letter
- Must contain lowercase letter
- Must contain number
- Must contain special character (!@#$%^&*(),.?":{}|<>)
- Rejects common passwords (password, 12345678, qwerty, admin, password123)

### Password Handling
- Passwords always hashed using Django's PBKDF2 algorithm
- Password validation on both registration and updates
- Write-only in serializers (never exposed in API responses)
- Never logged or stored in plain text

## 3. INPUT VALIDATION & SANITIZATION

### Username Validation
- Length: 3-30 characters
- Allowed characters: letters, numbers, periods, hyphens, underscores
- Must be unique
- Sanitization applied before validation

### Email Validation
- Format validation with regex
- Must be unique
- Case-insensitive (converted to lowercase)
- Sanitization applied

### Phone Validation
- Format validation (7+ digits, spaces, hyphens, parentheses allowed)
- Optional field
- Sanitization applied

### Text Field Sanitization
All string inputs sanitized to prevent XSS and injection attacks:
- HTML escaping
- Removal of dangerous characters
- Whitespace stripping
- Length limiting
- Applied to: name, description, first_name, last_name

### Input Length Constraints
- Username: 3-30 chars
- Email: max 254 chars
- First/Last name: max 150 chars
- Project name: 3-200 chars
- Project description: max 5000 chars
- Phone: max 20 chars

## 4. RATE LIMITING

### DRF Throttling Configuration
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Login attempts: 5 attempts/minute

### Application
- Prevents brute force attacks
- Prevents DoS attacks
- Per-user and per-IP tracking

## 5. CORS SECURITY

### Configuration
Allowed origins (development):
- http://localhost:3000
- http://localhost:8000
- http://127.0.0.1:3000
- http://127.0.0.1:8000

### Features
- CORS credentials enabled
- Specific methods allowed: GET, POST, PUT, PATCH, DELETE, OPTIONS
- In production: Set `DEBUG = False` and add specific domain origins

## 6. SECURITY HEADERS

### Implemented Headers
- X-Frame-Options: DENY (prevents clickjacking)
- X-XSS-Protection: enabled
- Content-Security-Policy: restricts resource loading

### Cookie Security
- SESSION_COOKIE_SECURE: True (HTTPS only, except dev)
- SESSION_COOKIE_HTTPONLY: True (no JavaScript access)
- SESSION_COOKIE_SAMESITE: 'Lax'
- CSRF_COOKIE_SECURE: True (HTTPS only, except dev)
- CSRF_COOKIE_HTTPONLY: True
- CSRF_COOKIE_SAMESITE: 'Lax'

### Additional Security
- HSTS (HTTP Strict Transport Security): 31536000 seconds (1 year)
- HSTS subdomains: enabled
- HSTS preload: enabled
- SSL redirect: enabled in production

## 7. ERROR HANDLING

### Custom Exception Handler
- Consistent error response format
- Sensitive information not exposed
- Logging of security issues
- User-friendly error messages

### Error Response Format
```json
{
  "success": false,
  "status_code": 400,
  "errors": {...},
  "message": "Description of error"
}
```

### Logged Events
- Authentication failures (401)
- Permission denials (403)
- Validation errors (400)
- Server errors (500) with traceback

## 8. FIELD-LEVEL PROTECTION

### Database-Level Validation
- Enum constraints for status and priority fields
- Foreign key constraints for relationships
- Unique constraints for username and email
- NOT NULL constraints where appropriate

### View-Level Validation
- Explicit permission checks before operations
- Owner/role verification for resource access
- Input type validation

### Serializer-Level Validation
- Field type validation
- Min/max length validation
- Format validation (email, phone, etc.)
- Enum value validation
- Custom validation methods

## 9. AUTHENTICATION ENDPOINTS

### Public Endpoints (AllowAny)
- POST /api/users/register/ - User registration
- POST /api/users/login/ - User login (rate limited)
- POST /api/users/logout/ - Logout notification

### Protected Endpoints (IsAuthenticated)
- GET /api/users/me/ - Current user info
- GET /api/users/users/ - List users (Manager/Admin only)
- POST/PUT/DELETE - All modifications require auth + role check

## 10. AUTHORIZATION EXAMPLES

### Project Access
- Only Admin can see all projects
- Regular users see only their own projects
- Only owner or Admin can modify project
- Only Manager/Admin can create projects

### User Management
- Only Admin can create/delete users
- Users can view/edit own profile
- Only Admin can view all users
- Admin cannot delete own account

## 11. ATTACK PREVENTION

### XSS (Cross-Site Scripting)
- HTML escaping in all text fields
- Content-Security-Policy headers
- No raw HTML in responses

### SQL Injection
- Django ORM used (parameterized queries)
- No raw SQL queries in application code
- Input validation on all search/filter parameters

### CSRF (Cross-Site Request Forgery)
- CSRF middleware enabled
- CSRF cookies secured (HttpOnly, Secure, SameSite)
- Token validation on all state-changing operations

### Brute Force
- Rate limiting on login attempts (5/minute)
- Login throttle class applied
- Invalid credentials logged

### Information Disclosure
- Error messages sanitized
- Stack traces not exposed to clients
- Sensitive data marked as write_only in serializers
- Database errors caught and converted to generic messages

## 12. COMPLIANCE & BEST PRACTICES

### OWASP Top 10
✓ Injection - Prevented via ORM + input validation
✓ Broken Auth - JWT + rate limiting + strong passwords
✓ Sensitive Data Exposure - Encryption + secure cookies
✓ XXE - No XML parsing
✓ Broken Access Control - RBAC + permission checks
✓ Security Misconfiguration - Best practices applied
✓ XSS - Input sanitization + CSP headers
✓ Insecure Deserialization - No unsafe deserialization
✓ Using Components with Known Vulnerabilities - Regular updates required
✓ Insufficient Logging & Monitoring - Custom exception handler logs issues

### Django Security
- `DEBUG = False` in production
- `SECRET_KEY` should be changed for production
- Allowed hosts explicitly set
- HTTPS enforced in production
- SECURE_PROXY_SSL_HEADER may be needed for proxies

## 13. PRODUCTION RECOMMENDATIONS

1. Change SECRET_KEY from default
2. Set `DEBUG = False`
3. Update ALLOWED_HOSTS with your domain
4. Use environment variables for sensitive settings
5. Enable HTTPS/SSL
6. Use strong database credentials
7. Implement database backups
8. Set up monitoring and alerting
9. Regular security updates
10. Implement API documentation with security info
11. Add API versioning
12. Consider adding 2FA for admin accounts
13. Implement audit logging for sensitive operations
14. Set up WAF (Web Application Firewall)

## 14. TESTING SECURITY

Test these scenarios:
- Invalid credentials rejection
- Token expiration handling
- Role-based access (try unauthorized operations)
- Input validation (try XSS, SQL injection payloads)
- Rate limiting (make rapid requests)
- CORS (test from different origins)
- Permission checks (try accessing other users' data)
- Password requirements (try weak passwords)

## 15. MAINTENANCE

Regular tasks:
- Update Django and dependencies
- Review security logs
- Update password policies as needed
- Test authorization rules
- Audit database access logs
- Review API usage patterns
- Update CORS origins as needed

"""
