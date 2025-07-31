"""
Enhanced security middleware for authentication protection
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging
import time
import json

from .security.rate_limiting import IPBasedRateLimiter, get_client_ip
from .security.anomaly_detection import AnomalyDetector
from .security.audit_logger import SecurityAuditLogger

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware with multiple protection layers
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limiter = IPBasedRateLimiter('api_request', window_seconds=60, max_requests=100)
        self.auth_rate_limiter = IPBasedRateLimiter('auth_request', window_seconds=60, max_requests=20)
        self.anomaly_detector = AnomalyDetector()
        self.audit_logger = SecurityAuditLogger()
        self.start_time = time.time()
    
    def process_request(self, request):
        """
        Process incoming request for security checks
        """
        request.security_start_time = time.time()
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Skip security checks for health checks and static files
        if self._should_skip_security_check(request):
            return None
        
        # Check general API rate limiting
        allowed, retry_after = self.rate_limiter.check_rate_limit(client_ip, 'api')
        if not allowed:
            self.audit_logger.log_security_event(
                event_type='rate_limit_exceeded',
                ip_address=client_ip,
                user_agent=user_agent,
                data={'endpoint': request.path, 'retry_after': retry_after},
                severity='medium'
            )
            
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': retry_after
            }, status=429)
        
        # Enhanced rate limiting for authentication endpoints
        if self._is_auth_endpoint(request.path):
            auth_allowed, auth_retry_after = self.auth_rate_limiter.check_rate_limit(client_ip, 'auth')
            if not auth_allowed:
                self.audit_logger.log_security_event(
                    event_type='auth_rate_limit_exceeded',
                    ip_address=client_ip,
                    user_agent=user_agent,
                    data={'endpoint': request.path, 'retry_after': auth_retry_after},
                    severity='high'
                )
                
                return JsonResponse({
                    'error': 'Authentication rate limit exceeded',
                    'retry_after': auth_retry_after
                }, status=429)
        
        # Request anomaly detection
        if hasattr(settings, 'ENABLE_ANOMALY_DETECTION') and settings.ENABLE_ANOMALY_DETECTION:
            anomaly_score = self.anomaly_detector.calculate_risk_score(request)
            
            if anomaly_score > 0.8:  # High anomaly score
                self.audit_logger.log_security_event(
                    event_type='suspicious_request',
                    ip_address=client_ip,
                    user_agent=user_agent,
                    data={
                        'endpoint': request.path,
                        'method': request.method,
                        'anomaly_score': anomaly_score
                    },
                    severity='high'
                )
                
                # Consider blocking request or requiring additional verification
                logger.warning(f"High anomaly score request: {anomaly_score} from {client_ip}")
        
        return None
    
    def process_response(self, request, response):
        """
        Process response and update security metrics
        """
        if self._should_skip_security_check(request):
            return response
        
        client_ip = get_client_ip(request)
        
        # Record the request for rate limiting
        self.rate_limiter.record_request(client_ip, 'api')
        
        if self._is_auth_endpoint(request.path):
            self.auth_rate_limiter.record_request(client_ip, 'auth')
        
        # Add security headers
        response = self._add_security_headers(response, request)
        
        # Log slow requests
        if hasattr(request, 'security_start_time'):
            request_time = time.time() - request.security_start_time
            if request_time > 5.0:  # Requests taking more than 5 seconds
                logger.warning(
                    f"Slow request detected: {request.path} took {request_time:.2f}s from {client_ip}"
                )
        
        return response
    
    def process_exception(self, request, exception):
        """
        Log security-relevant exceptions
        """
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Log security-relevant exceptions
        if isinstance(exception, (PermissionError, ValueError)):
            self.audit_logger.log_security_event(
                event_type='suspicious_exception',
                ip_address=client_ip,
                user_agent=user_agent,
                data={
                    'endpoint': request.path,
                    'exception': str(exception),
                    'exception_type': type(exception).__name__
                },
                severity='medium'
            )
        
        return None
    
    def _should_skip_security_check(self, request):
        """
        Check if security checks should be skipped for this request
        """
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _is_auth_endpoint(self, path):
        """
        Check if path is an authentication endpoint
        """
        auth_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/refresh/',
            '/api/auth/password-reset/',
            '/api/auth/2fa/',
        ]
        
        return any(path.startswith(auth_path) for auth_path in auth_paths)
    
    def _add_security_headers(self, response, request):
        """
        Add security headers to response
        """
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'DENY'
        
        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy for API responses
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'"
        
        # Cache control for sensitive endpoints
        if self._is_auth_endpoint(request.path):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced session security middleware
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.audit_logger = SecurityAuditLogger()
    
    def process_request(self, request):
        """
        Validate session security
        """
        if not request.user.is_authenticated:
            return None
        
        user = request.user
        client_ip = get_client_ip(request)
        
        # Check for session hijacking indicators
        if hasattr(user, 'last_login_ip') and user.last_login_ip:
            if user.last_login_ip != client_ip:
                # IP address changed - potential session hijacking
                if getattr(settings, 'VALIDATE_SESSION_IP', False):
                    self.audit_logger.log_security_event(
                        event_type='session_ip_change',
                        user=user,
                        ip_address=client_ip,
                        data={'previous_ip': user.last_login_ip},
                        severity='high'
                    )
                    
                    # In strict mode, invalidate session
                    if getattr(settings, 'STRICT_SESSION_IP_VALIDATION', False):
                        request.session.flush()
                        return JsonResponse({
                            'error': 'Session security violation'
                        }, status=401)
        
        # Update user's last activity
        if hasattr(user, 'last_login_ip'):
            user.last_login_ip = client_ip
            user.save(update_fields=['last_login_ip'])
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log requests for security monitoring
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.audit_logger = SecurityAuditLogger()
    
    def process_request(self, request):
        """
        Log request details for security monitoring
        """
        # Skip logging for non-security relevant requests
        if self._should_skip_logging(request):
            return None
        
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Log authentication attempts
        if request.path.startswith('/api/auth/'):
            self.audit_logger.log_request(
                request=request,
                user=getattr(request, 'user', None),
                ip_address=client_ip,
                user_agent=user_agent
            )
        
        return None
    
    def _should_skip_logging(self, request):
        """
        Check if request logging should be skipped
        """
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/api/status/',
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)


class APIKeyMiddleware(MiddlewareMixin):
    """
    Middleware for API key authentication
    """
    
    def process_request(self, request):
        """
        Check for API key authentication
        """
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if api_key:
            from .backends import APIKeyAuthenticationBackend
            backend = APIKeyAuthenticationBackend()
            user = backend.authenticate(request, api_key=api_key)
            
            if user:
                request.user = user
                request.auth_method = 'api_key'
            else:
                return JsonResponse({
                    'error': 'Invalid API key'
                }, status=401)
        
        return None