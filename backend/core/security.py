"""
Security utilities and middleware
"""
import logging
import os
import time
import uuid
from typing import Optional, Tuple
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.core.cache import cache
from django.core.management.utils import get_random_secret_key
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


# JWT Key Management
def get_jwt_keys_path() -> Tuple[Path, Path]:
    """Get paths for JWT private and public keys"""
    # Use BASE_DIR directly from __file__ to avoid settings import issues
    base_dir = Path(__file__).resolve().parent.parent  # This is backend/
    
    # Try to create keys directory in a writable location
    # In production (Railway), we'll use the app directory
    # Check if we're in a container/production environment
    if os.environ.get('RAILWAY_ENVIRONMENT') or not os.access('/tmp', os.W_OK):
        # Use app directory for keys (writable in Railway)
        keys_dir = base_dir / 'core' / 'keys'
    else:
        # Use /tmp for local development (always writable)
        keys_dir = Path('/tmp') / 'finance_hub_keys'
    
    try:
        keys_dir.mkdir(exist_ok=True, mode=0o700, parents=True)  # Secure permissions
    except PermissionError:
        # Fallback to app directory if /tmp is not writable
        keys_dir = base_dir / 'core' / 'keys'
        keys_dir.mkdir(exist_ok=True, mode=0o700, parents=True)
    
    private_key_path = keys_dir / 'jwt_private.pem'
    public_key_path = keys_dir / 'jwt_public.pem'
    
    return private_key_path, public_key_path


def generate_jwt_keypair() -> Tuple[str, str]:
    """Generate new RSA keypair for JWT signing"""
    logger.info("Generating new JWT RSA keypair")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem


def save_jwt_keys(private_key: str, public_key: str) -> None:
    """Save JWT keys to secure files"""
    private_key_path, public_key_path = get_jwt_keys_path()
    
    # Save private key with secure permissions
    private_key_path.write_text(private_key)
    private_key_path.chmod(0o600)  # Read/write for owner only
    
    # Save public key
    public_key_path.write_text(public_key)
    public_key_path.chmod(0o644)  # Read for all, write for owner
    
    logger.info(f"JWT keys saved to {private_key_path.parent}")


def load_jwt_keys() -> Tuple[str, str]:
    """Load JWT keys from files or environment variables"""
    # First, try base64-encoded environment variables (Railway-compatible)
    private_key_b64 = os.environ.get('JWT_PRIVATE_KEY_B64')
    public_key_b64 = os.environ.get('JWT_PUBLIC_KEY_B64')
    
    # Debug logging for environment variable detection
    logger.info("AUTH-CONFIG: Checking for JWT environment variables...")
    logger.info(f"AUTH-CONFIG: JWT_PRIVATE_KEY_B64 found: {'Yes' if private_key_b64 else 'No'}")
    logger.info(f"AUTH-CONFIG: JWT_PUBLIC_KEY_B64 found: {'Yes' if public_key_b64 else 'No'}")
    
    if private_key_b64:
        logger.info(f"AUTH-CONFIG: Private key B64 length: {len(private_key_b64)} chars")
        logger.info(f"AUTH-CONFIG: Private key B64 starts with: {private_key_b64[:20]}...")
    
    if public_key_b64:
        logger.info(f"AUTH-CONFIG: Public key B64 length: {len(public_key_b64)} chars")
        logger.info(f"AUTH-CONFIG: Public key B64 starts with: {public_key_b64[:20]}...")
    
    if private_key_b64 and public_key_b64:
        try:
            import base64
            logger.info("AUTH-CONFIG: Attempting to decode base64 JWT keys...")
            private_key = base64.b64decode(private_key_b64).decode('utf-8')
            public_key = base64.b64decode(public_key_b64).decode('utf-8')
            
            # Validate PEM format
            logger.info(f"AUTH-CONFIG: Private key decoded length: {len(private_key)} chars")
            logger.info(f"AUTH-CONFIG: Public key decoded length: {len(public_key)} chars")
            logger.info(f"AUTH-CONFIG: Private key starts with: {'-----BEGIN PRIVATE KEY-----' if private_key.startswith('-----BEGIN PRIVATE KEY-----') else 'INVALID FORMAT'}")
            logger.info(f"AUTH-CONFIG: Public key starts with: {'-----BEGIN PUBLIC KEY-----' if public_key.startswith('-----BEGIN PUBLIC KEY-----') else 'INVALID FORMAT'}")
            
            logger.info("AUTH-CONFIG: ✅ JWT keys loaded successfully from base64 environment variables (Railway-compatible)")
            return private_key, public_key
        except Exception as e:
            logger.error(f"AUTH-CONFIG: ❌ Failed to decode base64 JWT keys from environment: {e}")
            import traceback
            logger.error(f"AUTH-CONFIG: Traceback: {traceback.format_exc()}")
    
    # Try environment variables first (for containerized deployments)
    logger.info("AUTH-CONFIG: Checking for raw PEM environment variables...")
    private_key_env = os.environ.get('JWT_PRIVATE_KEY')
    public_key_env = os.environ.get('JWT_PUBLIC_KEY')
    
    logger.info(f"AUTH-CONFIG: JWT_PRIVATE_KEY found: {'Yes' if private_key_env else 'No'}")
    logger.info(f"AUTH-CONFIG: JWT_PUBLIC_KEY found: {'Yes' if public_key_env else 'No'}")
    
    if private_key_env and public_key_env:
        logger.info("AUTH-CONFIG: ✅ Using JWT keys from raw PEM environment variables")
        return private_key_env, public_key_env
    
    # Try loading from files
    logger.info("AUTH-CONFIG: Checking for JWT key files...")
    try:
        private_key_path, public_key_path = get_jwt_keys_path()
        logger.info(f"AUTH-CONFIG: Key paths - Private: {private_key_path}, Public: {public_key_path}")
        logger.info(f"AUTH-CONFIG: Private key file exists: {private_key_path.exists()}")
        logger.info(f"AUTH-CONFIG: Public key file exists: {public_key_path.exists()}")
        
        if private_key_path.exists() and public_key_path.exists():
            logger.info(f"AUTH-CONFIG: ✅ Using JWT keys from file system: {private_key_path.parent}")
            private_key = private_key_path.read_text()
            public_key = public_key_path.read_text()
            return private_key, public_key
    except Exception as e:
        logger.warning(f"AUTH-CONFIG: Could not access JWT key files: {e}")
    
    # Generate new keys if none exist
    logger.warning("AUTH-CONFIG: ❌ No JWT keys found, generating new keypair")
    private_key, public_key = generate_jwt_keypair()
    
    # Try to save the keys, but don't fail if we can't
    try:
        save_jwt_keys(private_key, public_key)
        logger.info("AUTH-CONFIG: ✅ Generated keys saved to disk")
    except Exception as e:
        logger.warning(f"AUTH-CONFIG: Could not save JWT keys to disk (using in-memory only): {e}")
        # In production, you should set JWT_PRIVATE_KEY and JWT_PUBLIC_KEY env vars
        logger.warning("AUTH-CONFIG: ⚠️  IMPORTANT: Set JWT_PRIVATE_KEY_B64 and JWT_PUBLIC_KEY_B64 environment variables for production!")
    
    return private_key, public_key


def clean_jwt_key(key: str) -> str:
    """Clean and validate JWT key format for PyJWT compatibility"""
    if not key:
        raise ValueError("JWT key cannot be empty")
    
    # Remove any extra whitespace and normalize line endings
    key = key.strip()
    
    # Ensure consistent line endings (Unix style)
    key = key.replace('\r\n', '\n').replace('\r', '\n')
    
    # Validate PEM format
    if 'BEGIN PRIVATE KEY' in key:
        # Private key validation
        if not key.startswith('-----BEGIN PRIVATE KEY-----'):
            raise ValueError("Invalid private key format: missing header")
        if not key.endswith('-----END PRIVATE KEY-----'):
            raise ValueError("Invalid private key format: missing footer")
    elif 'BEGIN PUBLIC KEY' in key:
        # Public key validation  
        if not key.startswith('-----BEGIN PUBLIC KEY-----'):
            raise ValueError("Invalid public key format: missing header")
        if not key.endswith('-----END PUBLIC KEY-----'):
            raise ValueError("Invalid public key format: missing footer")
    elif 'BEGIN RSA PRIVATE KEY' in key:
        # Legacy RSA private key format
        if not key.startswith('-----BEGIN RSA PRIVATE KEY-----'):
            raise ValueError("Invalid RSA private key format: missing header")
        if not key.endswith('-----END RSA PRIVATE KEY-----'):
            raise ValueError("Invalid RSA private key format: missing footer")
    else:
        raise ValueError(f"Unrecognized key format. Key starts with: {key[:50]}")
    
    # Test PyJWT compatibility
    try:
        from cryptography.hazmat.primitives import serialization
        
        if 'PRIVATE KEY' in key:
            # Test private key parsing
            serialization.load_pem_private_key(
                key.encode('utf-8'), 
                password=None
            )
        else:
            # Test public key parsing
            serialization.load_pem_public_key(
                key.encode('utf-8')
            )
            
        logger.info("JWT key format validation: SUCCESS")
        
    except Exception as validation_error:
        logger.error(f"JWT key validation failed: {validation_error}")
        raise ValueError(f"Key format invalid for cryptography library: {validation_error}")
    
    return key


def get_jwt_private_key() -> str:
    """Get JWT private key for signing tokens"""
    try:
        logger.info("AUTH-CONFIG: Getting JWT private key...")
        private_key, _ = load_jwt_keys()
        logger.info(f"AUTH-CONFIG: Private key length: {len(private_key)} chars")
        
        # Clean and validate key for PyJWT compatibility
        cleaned_key = clean_jwt_key(private_key)
        logger.info("AUTH-CONFIG: Private key cleaning and validation: SUCCESS")
        
        return cleaned_key
    except Exception as e:
        logger.error(f"AUTH-CONFIG: ❌ Failed to load JWT private key: {e}")
        # In development/testing, generate a temporary key
        if settings.DEBUG or os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('.development'):
            logger.warning("AUTH-CONFIG: Generating temporary JWT key for development")
            private_key, _ = generate_jwt_keypair()
            return clean_jwt_key(private_key)
        raise ValueError("JWT private key configuration is invalid")


def get_jwt_public_key() -> str:
    """Get JWT public key for verifying tokens"""
    try:
        logger.info("AUTH-CONFIG: Getting JWT public key...")
        _, public_key = load_jwt_keys()
        logger.info(f"AUTH-CONFIG: Public key length: {len(public_key)} chars")
        
        # Clean and validate key for PyJWT compatibility
        cleaned_key = clean_jwt_key(public_key)
        logger.info("AUTH-CONFIG: Public key cleaning and validation: SUCCESS")
        
        logger.info(f"AUTH-CONFIG: JWT Algorithm: RS256")
        return cleaned_key
    except Exception as e:
        logger.error(f"AUTH-CONFIG: ❌ Failed to load JWT public key: {e}")
        # In development/testing, generate a temporary key
        if settings.DEBUG or os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('.development'):
            logger.warning("AUTH-CONFIG: Generating temporary JWT key for development")
            _, public_key = generate_jwt_keypair()
            return clean_jwt_key(public_key)
        raise ValueError("JWT public key configuration is invalid")


def rotate_jwt_keys() -> None:
    """Rotate JWT keys (generate new keypair)"""
    logger.info("Starting JWT key rotation")
    
    # Generate new keypair
    new_private_key, new_public_key = generate_jwt_keypair()
    
    # Backup existing keys
    private_key_path, public_key_path = get_jwt_keys_path()
    if private_key_path.exists():
        backup_path = private_key_path.with_suffix('.pem.backup')
        private_key_path.rename(backup_path)
        logger.info(f"Backed up old private key to {backup_path}")
    
    if public_key_path.exists():
        backup_path = public_key_path.with_suffix('.pem.backup')
        public_key_path.rename(backup_path)
        logger.info(f"Backed up old public key to {backup_path}")
    
    # Save new keys
    save_jwt_keys(new_private_key, new_public_key)
    logger.info("JWT key rotation completed")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add comprehensive security headers to all responses"""
    
    def process_response(self, request, response):
        # Basic security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(self)'
        
        # HSTS - Strict Transport Security
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Enhanced Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://api.stripe.com https://api.pluggy.ai wss: ws:",
            "frame-src 'self' https://js.stripe.com https://hooks.stripe.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        
        if not settings.DEBUG:
            csp_directives.extend([
                "upgrade-insecure-requests",
                "block-all-mixed-content"
            ])
            
        # Add nonce support for inline scripts if available
        if hasattr(request, 'csp_nonce'):
            csp_directives[1] = f"script-src 'self' 'nonce-{request.csp_nonce}' https://js.stripe.com"
            
        
        # Set CSP based on environment
        if not settings.DEBUG:
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        else:
            # Relaxed CSP for development
            response['Content-Security-Policy-Report-Only'] = '; '.join(csp_directives)
        
        # Enhanced Permissions Policy
        permissions_policy = [
            'geolocation=()',
            'microphone=()',
            'camera=()',
            'magnetometer=()',
            'gyroscope=()',
            'accelerometer=()',
            'ambient-light-sensor=()',
            'autoplay=()',
            'encrypted-media=()',
            'fullscreen=(self)',
            'midi=()',
            'payment=*',  # Allow for Stripe/payment processing
            'picture-in-picture=()',
            'usb=()',
            'web-share=()',
        ]
        response['Permissions-Policy'] = ', '.join(permissions_policy)
        
        # HSTS (HTTP Strict Transport Security) - only in production with HTTPS
        if not settings.DEBUG and request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Additional security headers
        response['X-Permitted-Cross-Domain-Policies'] = 'none'
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # API-specific headers
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            # Prevent API responses from being embedded
            response['X-Frame-Options'] = 'DENY'
            # Don't override CSP for API responses, it's already set above
        
        # Authentication endpoint specific headers
        if any(request.path.startswith(path) for path in ['/api/auth/', '/admin/']):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            # Only apply Clear-Site-Data to logout endpoints to avoid CORS issues
            if 'logout' in request.path:
                response['Clear-Site-Data'] = '"cache", "cookies", "storage", "executionContexts"'
        
        return response


class RequestIDMiddleware(MiddlewareMixin):
    """Add unique request ID to each request for tracking"""
    
    def process_request(self, request):
        request.id = str(uuid.uuid4())
        request.META['HTTP_X_REQUEST_ID'] = request.id
    
    def process_response(self, request, response):
        if hasattr(request, 'id'):
            response['X-Request-ID'] = request.id
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Global rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False  # Required for Django middleware
        # Configure rate limits
        self.rate_limits = {
            'default': (100, 60),  # 100 requests per minute
            'api': (1000, 60),     # 1000 API requests per minute
            'auth': (10, 60),      # 10 auth attempts per minute
        }
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_request(self, request):
        # Skip rate limiting in DEBUG mode
        if settings.DEBUG:
            return None
        
        # Determine rate limit type
        path = request.path
        if path.startswith('/api/auth/'):
            limit_type = 'auth'
        elif path.startswith('/api/'):
            limit_type = 'api'
        else:
            limit_type = 'default'
        
        # Get rate limit config
        max_requests, window = self.rate_limits[limit_type]
        
        # Get client identifier
        client_ip = self.get_client_ip(request)
        if request.user.is_authenticated:
            client_id = f"user_{request.user.id}"
        else:
            client_id = f"ip_{client_ip}"
        
        # Create cache key
        cache_key = f"rate_limit:{limit_type}:{client_id}"
        
        # Check rate limit
        current_requests = cache.get(cache_key, 0)
        if current_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_id} on {limit_type}")
            return HttpResponseForbidden("Rate limit exceeded. Please try again later.")
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, window)
        
        return None


class AuditLogMiddleware(MiddlewareMixin):
    """Log all sensitive operations for audit trail"""
    
    SENSITIVE_OPERATIONS = [
        '/api/banking/connect/',
        '/api/banking/sync/',
        '/api/banking/transactions/',
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/companies/subscription/',
        '/api/payments/',
    ]
    
    def process_request(self, request):
        request._start_time = time.time()
    
    def process_response(self, request, response):
        # Check if this is a sensitive operation
        for path in self.SENSITIVE_OPERATIONS:
            if request.path.startswith(path):
                self._log_audit_event(request, response)
                break
        
        return response
    
    def _log_audit_event(self, request, response):
        """Log audit event"""
        duration = time.time() - getattr(request, '_start_time', 0)
        
        audit_data = {
            'timestamp': time.time(),
            'request_id': getattr(request, 'id', 'unknown'),
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': duration,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Log to audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.info(f"AUDIT: {audit_data}")
        
        # In production, also send to audit storage (e.g., dedicated database)
        if not settings.DEBUG:
            self._store_audit_event(audit_data)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _store_audit_event(self, audit_data):
        """Store audit event in persistent storage"""
        # TODO: Implement audit storage (e.g., separate database, S3, etc.)
        pass


class IPWhitelistMiddleware(MiddlewareMixin):
    """IP whitelist for admin and sensitive endpoints"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get whitelist from settings
        self.whitelist = getattr(settings, 'IP_WHITELIST', [])
        self.protected_paths = [
            '/admin/',
            '/api/admin/',
            '/api/banking/webhook/',
            '/api/payments/webhook/',
        ]
    
    def process_request(self, request):
        # Skip in DEBUG mode
        if settings.DEBUG:
            return None
        
        # Check if path needs protection
        needs_protection = any(
            request.path.startswith(path) 
            for path in self.protected_paths
        )
        
        if not needs_protection:
            return None
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check whitelist
        if client_ip not in self.whitelist:
            logger.warning(f"Blocked access from {client_ip} to {request.path}")
            return HttpResponseForbidden("Access denied")
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def sanitize_user_input(data: dict) -> dict:
    """Sanitize user input to prevent XSS and injection attacks"""
    import bleach
    
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    allowed_attributes = {}
    
    def clean_value(value):
        if isinstance(value, str):
            # Remove any HTML tags except allowed ones
            return bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        elif isinstance(value, dict):
            return sanitize_user_input(value)
        elif isinstance(value, list):
            return [clean_value(item) for item in value]
        else:
            return value
    
    return {key: clean_value(value) for key, value in data.items()}


def validate_cpf(cpf: str) -> bool:
    """Validate Brazilian CPF - wrapper for common validator"""
    from .common_validators import validate_cpf as _validate_cpf
    return _validate_cpf(cpf)


def validate_cnpj(cnpj: str) -> bool:
    """Validate Brazilian CNPJ - wrapper for common validator"""
    from .common_validators import validate_cnpj as _validate_cnpj
    try:
        _validate_cnpj(cnpj)
        return True
    except:
        return False


# Security Monitoring and Alerting System
class SecurityMonitor:
    """Real-time security monitoring and threat detection"""
    
    def __init__(self):
        self.alert_thresholds = {
            'failed_logins': 5,  # Failed logins per IP in 10 minutes
            'suspicious_requests': 10,  # Suspicious requests per user in 5 minutes
            'api_abuse': 100,  # API requests per IP in 1 minute
            'admin_access': 3,  # Failed admin access attempts in 1 hour
        }
        self.monitoring_logger = logging.getLogger('security.monitoring')
    
    def detect_brute_force(self, ip_address: str, user_email: str = None) -> dict:
        """Detect brute force attacks based on failed login patterns"""
        cache_key = f"failed_logins:{ip_address}"
        cache_key_user = f"failed_logins_user:{user_email}" if user_email else None
        
        # Check IP-based attacks
        ip_failures = cache.get(cache_key, 0)
        user_failures = cache.get(cache_key_user, 0) if cache_key_user else 0
        
        threat_level = 'low'
        if ip_failures >= 10 or user_failures >= 8:
            threat_level = 'critical'
        elif ip_failures >= 5 or user_failures >= 5:
            threat_level = 'high'
        elif ip_failures >= 3 or user_failures >= 3:
            threat_level = 'medium'
        
        return {
            'threat_detected': threat_level != 'low',
            'threat_level': threat_level,
            'ip_failures': ip_failures,
            'user_failures': user_failures,
            'recommended_action': self._get_recommended_action(threat_level)
        }
    
    def detect_suspicious_patterns(self, request, user=None) -> dict:
        """Detect suspicious request patterns"""
        patterns = []
        threat_level = 'low'
        
        # Check for rapid API calls
        if self._check_rapid_requests(request):
            patterns.append('rapid_api_calls')
            threat_level = 'medium'
        
        # Check for unusual access patterns
        if user and self._check_unusual_access(request, user):
            patterns.append('unusual_access_pattern')
            threat_level = 'medium'
        
        # Check for known attack patterns in requests
        if self._check_attack_patterns(request):
            patterns.append('attack_signature')
            threat_level = 'high'
        
        # Check for geographic anomalies (if IP geolocation is available)
        if self._check_geographic_anomaly(request, user):
            patterns.append('geographic_anomaly')
            threat_level = 'medium'
        
        return {
            'threat_detected': len(patterns) > 0,
            'threat_level': threat_level,
            'patterns': patterns,
            'recommended_action': self._get_recommended_action(threat_level)
        }
    
    def alert_security_team(self, incident_type: str, severity: str, details: dict):
        """Send alert to security team"""
        alert_data = {
            'timestamp': time.time(),
            'incident_type': incident_type,
            'severity': severity,
            'details': details,
            'alert_id': str(uuid.uuid4())
        }
        
        # Log the alert
        self.monitoring_logger.critical(
            f"SECURITY ALERT: {incident_type} - {severity}",
            extra=alert_data
        )
        
        # In production, send to monitoring service (e.g., Sentry, PagerDuty)
        if not settings.DEBUG:
            self._send_external_alert(alert_data)
    
    def _check_rapid_requests(self, request) -> bool:
        """Check for rapid successive requests from same IP"""
        client_ip = self._get_client_ip(request)
        cache_key = f"request_count:{client_ip}"
        
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, 60)  # 1 minute window
        
        return current_count > 50  # More than 50 requests per minute
    
    def _check_unusual_access(self, request, user) -> bool:
        """Check for unusual access patterns for the user"""
        # Check if accessing from new IP
        last_ip = getattr(user, 'last_login_ip', None)
        current_ip = self._get_client_ip(request)
        
        if last_ip and last_ip != current_ip:
            # Log IP change for monitoring
            self.monitoring_logger.info(
                f"User {user.id} accessing from new IP: {current_ip} (previous: {last_ip})"
            )
            return True
        
        return False
    
    def _check_attack_patterns(self, request) -> bool:
        """Check for known attack patterns in request"""
        attack_patterns = [
            'union select', 'drop table', '<script', 'javascript:',
            '../../../', 'eval(', 'exec(', 'system(', 'cmd.exe'
        ]
        
        # Check URL and query parameters
        full_path = request.get_full_path().lower()
        for pattern in attack_patterns:
            if pattern in full_path:
                return True
        
        # Check POST data if available
        if hasattr(request, 'body') and request.body:
            try:
                body_str = request.body.decode('utf-8', errors='ignore').lower()
                for pattern in attack_patterns:
                    if pattern in body_str:
                        return True
            except:
                pass
        
        return False
    
    def _check_geographic_anomaly(self, request, user) -> bool:
        """Check for geographic anomalies (placeholder for IP geolocation)"""
        # In production, implement IP geolocation checking
        # For now, return False as this requires external service
        return False
    
    def _get_recommended_action(self, threat_level: str) -> str:
        """Get recommended action based on threat level"""
        actions = {
            'low': 'monitor',
            'medium': 'increase_monitoring',
            'high': 'block_temporarily',
            'critical': 'block_immediately'
        }
        return actions.get(threat_level, 'monitor')
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _send_external_alert(self, alert_data):
        """Send alert to external monitoring service"""
        # Implement integration with external services
        # Examples: Sentry, PagerDuty, Slack, Email
        pass


class ThreatDetector:
    """Advanced threat detection and analysis"""
    
    def __init__(self):
        self.detector_logger = logging.getLogger('security.threats')
        self.known_threat_ips = set()  # In production, load from threat intelligence feeds
        self.threat_patterns = self._load_threat_patterns()
    
    def analyze_request_threat(self, request) -> dict:
        """Comprehensive threat analysis of incoming request"""
        threats = []
        risk_score = 0.0
        
        # Check against known malicious IPs
        if self._check_malicious_ip(request):
            threats.append('malicious_ip')
            risk_score += 0.8
        
        # Check request headers for suspicious patterns
        header_threats = self._analyze_headers(request)
        threats.extend(header_threats)
        risk_score += len(header_threats) * 0.2
        
        # Check payload for malicious content
        payload_threats = self._analyze_payload(request)
        threats.extend(payload_threats)
        risk_score += len(payload_threats) * 0.3
        
        # Check user agent patterns
        if self._check_suspicious_user_agent(request):
            threats.append('suspicious_user_agent')
            risk_score += 0.4
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        return {
            'threats_detected': threats,
            'risk_score': risk_score,
            'threat_level': self._calculate_threat_level(risk_score),
            'recommended_action': self._get_threat_action(risk_score)
        }
    
    def _load_threat_patterns(self) -> dict:
        """Load threat patterns for detection"""
        return {
            'sql_injection': [
                'union select', 'drop table', 'insert into', 'delete from',
                'update set', 'alter table', 'exec(', 'execute('
            ],
            'xss': [
                '<script', 'javascript:', 'onerror=', 'onload=',
                'alert(', 'document.cookie', 'window.location'
            ],
            'path_traversal': [
                '../', '..\\', '/etc/passwd', '/etc/shadow',
                'c:\\windows', 'boot.ini'
            ],
            'command_injection': [
                'system(', 'exec(', 'eval(', 'cmd.exe',
                '/bin/sh', '/bin/bash', 'powershell'
            ]
        }
    
    def _check_malicious_ip(self, request) -> bool:
        """Check if request comes from known malicious IP"""
        client_ip = self._get_client_ip(request)
        return client_ip in self.known_threat_ips
    
    def _analyze_headers(self, request) -> list:
        """Analyze request headers for threats"""
        threats = []
        suspicious_headers = ['x-forwarded-for', 'x-real-ip', 'user-agent', 'referer']
        
        for header in suspicious_headers:
            header_value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}', '')
            if header_value:
                for threat_type, patterns in self.threat_patterns.items():
                    for pattern in patterns:
                        if pattern.lower() in header_value.lower():
                            threats.append(f'header_{threat_type}')
                            break
        
        return threats
    
    def _analyze_payload(self, request) -> list:
        """Analyze request payload for malicious content"""
        threats = []
        
        # Check query parameters
        for key, value in request.GET.items():
            for threat_type, patterns in self.threat_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in value.lower():
                        threats.append(f'query_{threat_type}')
                        break
        
        # Check POST data
        if hasattr(request, 'body') and request.body:
            try:
                body_str = request.body.decode('utf-8', errors='ignore').lower()
                for threat_type, patterns in self.threat_patterns.items():
                    for pattern in patterns:
                        if pattern in body_str:
                            threats.append(f'payload_{threat_type}')
                            break
            except:
                pass
        
        return threats
    
    def _check_suspicious_user_agent(self, request) -> bool:
        """Check for suspicious user agent strings"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
            'burpsuite', 'curl', 'wget', 'python-requests'
        ]
        
        return any(agent in user_agent for agent in suspicious_agents)
    
    def _calculate_threat_level(self, risk_score: float) -> str:
        """Calculate threat level based on risk score"""
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _get_threat_action(self, risk_score: float) -> str:
        """Get recommended action based on risk score"""
        if risk_score >= 0.8:
            return 'block_immediately'
        elif risk_score >= 0.6:
            return 'challenge_user'
        elif risk_score >= 0.3:
            return 'increase_logging'
        else:
            return 'monitor'
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityThreatMiddleware(MiddlewareMixin):
    """Middleware for real-time threat detection and mitigation"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_monitor = SecurityMonitor()
        self.threat_detector = ThreatDetector()
        self.threat_logger = logging.getLogger('security.threats')
    
    def process_request(self, request):
        # Skip threat detection in DEBUG mode for development
        if settings.DEBUG:
            return None
        
        # Analyze request for threats
        threat_analysis = self.threat_detector.analyze_request_threat(request)
        
        if threat_analysis['risk_score'] >= 0.8:
            # Critical threat - block immediately
            self.threat_logger.critical(
                f"CRITICAL THREAT BLOCKED: {threat_analysis['threats_detected']}",
                extra={
                    'client_ip': self.threat_detector._get_client_ip(request),
                    'path': request.path,
                    'method': request.method,
                    'risk_score': threat_analysis['risk_score'],
                    'threats': threat_analysis['threats_detected'],
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
            
            # Alert security team
            self.security_monitor.alert_security_team(
                'critical_threat_blocked',
                'critical',
                {
                    'client_ip': self.threat_detector._get_client_ip(request),
                    'threats': threat_analysis['threats_detected'],
                    'risk_score': threat_analysis['risk_score']
                }
            )
            
            return HttpResponseForbidden("Request blocked for security reasons")
        
        elif threat_analysis['risk_score'] >= 0.3:
            # Medium/High threat - log and monitor
            self.threat_logger.warning(
                f"THREAT DETECTED: {threat_analysis['threats_detected']}",
                extra={
                    'client_ip': self.threat_detector._get_client_ip(request),
                    'path': request.path,
                    'method': request.method,
                    'risk_score': threat_analysis['risk_score'],
                    'threats': threat_analysis['threats_detected'],
                }
            )
        
        # Store threat analysis in request for later use
        request.threat_analysis = threat_analysis
        
        return None
    
    def process_response(self, request, response):
        # Log successful requests from medium-risk sources
        if hasattr(request, 'threat_analysis'):
            analysis = request.threat_analysis
            if analysis['risk_score'] >= 0.3:
                self.threat_logger.info(
                    f"Request completed with threat level {analysis['threat_level']}",
                    extra={
                        'client_ip': self.threat_detector._get_client_ip(request),
                        'status_code': response.status_code,
                        'risk_score': analysis['risk_score']
                    }
                )
        
        return response