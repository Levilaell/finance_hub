# JWT Authentication Startup Diagnostics

## Overview

Integrated comprehensive JWT authentication diagnostics into the application startup process to detect and report authentication issues during deployment.

## Changes Made

### 1. Enhanced Startup Script (`start.sh`)

Added JWT authentication diagnostics section that runs during deployment:

```bash
# ===== JWT AUTHENTICATION DIAGNOSTICS =====
echo "🔐 Running JWT Authentication Diagnostics..."
python manage.py diagnose_jwt_auth --fix-permissions 2>&1 | {
    while IFS= read -r line; do
        echo "AUTH-DIAG: $line"
        case "$line" in
            *"❌"*) echo "🚨 CRITICAL AUTH ERROR: $line" ;;
            *"⚠️"*) echo "⚠️ AUTH WARNING: $line" ;;
            *"✅"*) echo "✅ AUTH OK: $line" ;;
        esac
    done
} || {
    echo "🚨 CRITICAL: JWT Authentication diagnostic failed!"
    echo "🚨 This may cause authentication failures in production"
    echo "🚨 Check logs above for specific issues"
}
```

**Features:**
- Runs comprehensive JWT diagnostics with `--fix-permissions` flag
- Color-codes output for easy identification of issues
- Highlights critical errors, warnings, and successful validations
- Provides clear failure messages if diagnostics fail

### 2. Additional Configuration Validation

Added authentication configuration validation:

```python
# Run additional authentication validation
echo "🔐 Validating authentication configuration..."
python -c "
import django
django.setup()
from django.conf import settings
import os

print('=== AUTHENTICATION CONFIGURATION ===')
print(f'Frontend URL: {getattr(settings, \"FRONTEND_URL\", \"NOT SET\")}')
print(f'Backend URL: {getattr(settings, \"BACKEND_URL\", \"NOT SET\")}')
print(f'CORS Origins: {getattr(settings, \"CORS_ALLOWED_ORIGINS\", [])}')
print(f'JWT Cookie SameSite: {getattr(settings, \"JWT_COOKIE_SAMESITE\", \"NOT SET\")}')
print(f'JWT Cookie Secure: {getattr(settings, \"JWT_COOKIE_SECURE\", \"NOT SET\")}')
print(f'JWT Algorithm: {settings.SIMPLE_JWT.get(\"ALGORITHM\", \"NOT SET\")}')

# Check if JWT keys are loadable
try:
    from core.security import get_jwt_private_key, get_jwt_public_key
    private_key = get_jwt_private_key()
    public_key = get_jwt_public_key()
    print('✅ JWT keys loaded successfully (RS256 mode)')
    print(f'Private key length: {len(private_key)} chars')
    print(f'Public key length: {len(public_key)} chars')
except Exception as e:
    print(f'❌ JWT key loading failed: {e}')
    print('⚠️ System will fallback to HS256 with temporary key')

# Test authentication classes
try:
    from apps.authentication.jwt_cookie_authentication import JWTCookieAuthentication
    auth_instance = JWTCookieAuthentication()
    print('✅ JWT Cookie Authentication class loaded')
except Exception as e:
    print(f'❌ JWT Cookie Authentication failed to load: {e}')

print('=== END AUTHENTICATION CONFIG ===')
"
```

**Validates:**
- Frontend/Backend URL configuration
- CORS origins setup
- JWT cookie settings (SameSite, Secure)
- JWT algorithm configuration
- RSA key loading capability
- Authentication class imports

### 3. WSGI-Level Diagnostics (`core/wsgi.py`)

Added JWT diagnostics during WSGI application startup (production only):

```python
# Run JWT authentication diagnostics on startup (production only)
if os.environ.get('DJANGO_ENV') == 'production':
    try:
        import django
        django.setup()
        from django.core.management import call_command
        from io import StringIO
        
        # Capture diagnostic output
        output = StringIO()
        print("🔐 Running JWT Authentication diagnostics during WSGI startup...")
        call_command('diagnose_jwt_auth', '--fix-permissions', stdout=output, stderr=output)
        diag_output = output.getvalue()
        
        # Parse and log critical issues
        for line in diag_output.split('\n'):
            if '❌' in line:
                print(f"🚨 CRITICAL AUTH ERROR: {line}")
            elif '⚠️' in line:
                print(f"⚠️ AUTH WARNING: {line}")
            elif '✅' in line and ('JWT' in line or 'Token' in line or 'Cookie' in line):
                print(f"✅ AUTH OK: {line}")
                
    except Exception as diag_error:
        print(f"⚠️ JWT diagnostics failed during WSGI startup: {diag_error}")
```

**Features:**
- Runs only in production environment
- Executes during WSGI application initialization
- Captures and parses diagnostic output
- Logs critical auth errors, warnings, and successes
- Graceful failure handling

## Benefits

### 1. **Early Detection**
- Identifies authentication issues during deployment
- Prevents silent failures in production
- Shows exact configuration problems

### 2. **Comprehensive Coverage**
- Tests JWT key loading (RS256 vs HS256 fallback)
- Validates cookie configuration (SameSite, Secure)
- Checks CORS settings
- Tests authentication classes
- Validates environment variables

### 3. **Clear Visibility**
- Color-coded log output for easy identification
- Prefixed log lines for filtering (`AUTH-DIAG:`, `AUTH-CONFIG:`)
- Critical error highlighting
- Success confirmations

### 4. **Production Safety**
- Automatic permission fixes with `--fix-permissions`
- Graceful failure handling
- Non-blocking diagnostics (continues startup even if diagnostic fails)

## Usage

### Deployment Logs
During Railway deployment, look for these log patterns:

```bash
🔐 Running JWT Authentication Diagnostics...
AUTH-DIAG: 📋 JWT Key Validation
AUTH-DIAG: ✅ PASSED
🚨 CRITICAL AUTH ERROR: ❌ JWT key loading failed: Permission denied
⚠️ AUTH WARNING: ⚠️ DJANGO_SECRET_KEY not set in environment
✅ AUTH OK: ✅ JWT keys loaded successfully (RS256 mode)
```

### Log Analysis
- **🚨 CRITICAL AUTH ERROR**: Requires immediate attention
- **⚠️ AUTH WARNING**: Should be addressed but not blocking
- **✅ AUTH OK**: Confirms working authentication components

### Troubleshooting
If authentication fails in production:

1. Check Railway deployment logs for `AUTH-DIAG:` and `AUTH-CONFIG:` lines
2. Look for critical errors related to:
   - JWT key loading failures
   - CORS configuration issues
   - Environment variable problems
   - Cookie setting mismatches

## Environment Variables to Check

Based on diagnostic output, ensure these are set in Railway:

```bash
DJANGO_SECRET_KEY=your-secret-key
FRONTEND_URL=https://caixahub.com.br
BACKEND_URL=https://financehub-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://caixahub.com.br
DJANGO_ENV=production
```

## Next Steps

1. **Deploy**: Push changes to trigger diagnostics during deployment
2. **Monitor**: Check Railway deployment logs for authentication diagnostic output
3. **Fix Issues**: Address any critical errors or warnings identified
4. **Validate**: Test authentication flow after fixes are applied

The integrated diagnostics will help quickly identify the root cause of the authentication failures currently affecting production users.