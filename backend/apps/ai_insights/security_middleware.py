"""
Security Middleware for AI Insights
Provides security headers, CORS configuration, and request validation
"""
import logging
import json
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds comprehensive security headers to all AI Insights responses
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Security headers configuration
        self.security_headers = {
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # XSS protection
            'X-XSS-Protection': '1; mode=block',
            
            # Content type sniffing protection
            'X-Content-Type-Options': 'nosniff',
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions policy (formerly Feature Policy)
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), encrypted-media=()',
            
            # Content Security Policy (restrictive for AI Insights)
            'Content-Security-Policy': self._build_csp_header(),
            
            # Strict Transport Security (HTTPS only)
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        }
    
    def _build_csp_header(self) -> str:
        """Build Content Security Policy header"""
        # Get allowed origins from settings
        allowed_origins = getattr(settings, 'AI_INSIGHTS_ALLOWED_ORIGINS', [])
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        # Parse frontend domain
        frontend_domain = urlparse(frontend_url).netloc
        
        csp_directives = [
            "default-src 'self'",
            f"connect-src 'self' {frontend_url} wss://{frontend_domain} ws://{frontend_domain}",
            "script-src 'self' 'unsafe-inline'",  # Allow inline scripts for JSON responses
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "font-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        
        # Add allowed origins
        if allowed_origins:
            origins_str = ' '.join(allowed_origins)
            csp_directives[1] += f" {origins_str}"
        
        return '; '.join(csp_directives)
    
    def process_response(self, request, response):
        """Add security headers to response"""
        # Only add headers to AI Insights endpoints
        if not request.path.startswith('/api/ai-insights/'):
            return response
        
        # Add security headers
        for header, value in self.security_headers.items():
            response[header] = value
        
        # Add cache control for sensitive endpoints
        if any(sensitive in request.path for sensitive in ['/health/', '/metrics/', '/monitor/']):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class CORSMiddleware(MiddlewareMixin):
    """
    Enhanced CORS middleware specifically for AI Insights WebSocket and API endpoints
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Get CORS settings from Django settings
        self.allowed_origins = getattr(settings, 'AI_INSIGHTS_ALLOWED_ORIGINS', [
            'http://localhost:3000',
            'https://localhost:3000',
        ])
        
        self.allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
        self.allowed_headers = [
            'Accept',
            'Authorization',
            'Content-Type',
            'X-Requested-With',
            'X-CSRFToken',
            'Origin',
            'User-Agent',
            'DNT',
            'Cache-Control',
            'X-Mx-ReqToken',
            'Keep-Alive',
            'If-Modified-Since',
        ]
        
        self.exposed_headers = [
            'Content-Length',
            'X-RateLimit-Remaining',
            'X-RateLimit-Limit',
            'X-RateLimit-Reset',
        ]
        
        self.max_age = 86400  # 24 hours
    
    def process_request(self, request):
        """Handle preflight OPTIONS requests"""
        if request.method == 'OPTIONS' and request.path.startswith('/api/ai-insights/'):
            return self._handle_preflight(request)
        
        return None
    
    def process_response(self, request, response):
        """Add CORS headers to response"""
        # Only process AI Insights endpoints
        if not request.path.startswith('/api/ai-insights/') and not request.path.startswith('/ws/ai-chat/'):
            return response
        
        origin = request.META.get('HTTP_ORIGIN')
        
        # Check if origin is allowed
        if origin and self._is_origin_allowed(origin):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Expose-Headers'] = ', '.join(self.exposed_headers)
            
            # Add Vary header to prevent cache poisoning
            response['Vary'] = 'Origin'
        
        return response
    
    def _handle_preflight(self, request):
        """Handle CORS preflight request"""
        origin = request.META.get('HTTP_ORIGIN')
        
        if not origin or not self._is_origin_allowed(origin):
            return HttpResponse(status=403)
        
        # Create preflight response
        response = HttpResponse(status=200)
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        response['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = str(self.max_age)
        response['Vary'] = 'Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list"""
        # Allow all origins in development
        if settings.DEBUG and origin.startswith(('http://localhost:', 'http://127.0.0.1:')):
            return True
        
        return origin in self.allowed_origins


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for AI Insights endpoints
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Rate limit configuration
        self.rate_limits = {
            '/api/ai-insights/conversations/': {'rate': 60, 'period': 60},  # 60 requests per minute
            '/api/ai-insights/credits/': {'rate': 30, 'period': 60},        # 30 requests per minute
            '/api/ai-insights/insights/': {'rate': 100, 'period': 60},      # 100 requests per minute
            '/api/ai-insights/analysis/': {'rate': 10, 'period': 60},       # 10 requests per minute
        }
    
    def process_request(self, request):
        """Check rate limits for incoming requests"""
        # Skip non-AI insights endpoints
        if not request.path.startswith('/api/ai-insights/'):
            return None
        
        # Get client identifier (IP + user if authenticated)
        client_id = self._get_client_id(request)
        
        # Check rate limit for this endpoint
        for endpoint, limits in self.rate_limits.items():
            if request.path.startswith(endpoint):
                if not self._check_rate_limit(client_id, endpoint, limits):
                    return HttpResponse(
                        json.dumps({
                            'error': 'Rate limit exceeded',
                            'retry_after': limits['period']
                        }),
                        status=429,
                        content_type='application/json'
                    )
        
        return None
    
    def _get_client_id(self, request) -> str:
        """Get unique client identifier"""
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        # Include user ID if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"{ip}-{request.user.id}"
        
        return ip
    
    def _check_rate_limit(self, client_id: str, endpoint: str, limits: Dict) -> bool:
        """Check if client has exceeded rate limit"""
        cache_key = f"rate_limit:{endpoint}:{client_id}"
        current_time = int(time.time())
        window_start = current_time - limits['period']
        
        # Get request timestamps
        timestamps = cache.get(cache_key, [])
        
        # Remove old timestamps
        timestamps = [ts for ts in timestamps if ts > window_start]
        
        # Check if limit exceeded
        if len(timestamps) >= limits['rate']:
            return False
        
        # Add current timestamp
        timestamps.append(current_time)
        cache.set(cache_key, timestamps, timeout=limits['period'] + 60)
        
        return True


class RequestValidationMiddleware(MiddlewareMixin):
    """
    Validates incoming requests for security threats
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Malicious patterns to detect
        self.malicious_patterns = [
            # SQL injection
            r'(?i)(union.*select|select.*from|insert.*into|update.*set|delete.*from)',
            # XSS
            r'(?i)(<script|javascript:|vbscript:|onload=|onerror=)',
            # Path traversal
            r'(\.\./|\.\.\\\|%2e%2e%2f|%2e%2e%5c)',
            # Command injection
            r'(?i)(;|\||&|`|\$\(|\${)',
        ]
    
    def process_request(self, request):
        """Validate incoming request"""
        # Only validate AI Insights endpoints
        if not request.path.startswith('/api/ai-insights/'):
            return None
        
        # Check for suspicious patterns in various request components
        suspicious_detected = False
        
        # Check query parameters
        for key, value in request.GET.items():
            if self._contains_malicious_pattern(value):
                suspicious_detected = True
                break
        
        # Check POST data if present
        if request.method == 'POST' and hasattr(request, 'body'):
            try:
                body_content = request.body.decode('utf-8')
                if self._contains_malicious_pattern(body_content):
                    suspicious_detected = True
            except UnicodeDecodeError:
                pass
        
        # Check headers
        for header, value in request.META.items():
            if header.startswith('HTTP_') and self._contains_malicious_pattern(value):
                suspicious_detected = True
                break
        
        if suspicious_detected:
            logger.warning(f"Malicious request detected from {request.META.get('REMOTE_ADDR')}: {request.path}")
            return HttpResponse(
                json.dumps({'error': 'Request blocked for security reasons'}),
                status=400,
                content_type='application/json'
            )
        
        return None
    
    def _contains_malicious_pattern(self, text: str) -> bool:
        """Check if text contains malicious patterns"""
        import re
        
        if not isinstance(text, str):
            return False
        
        for pattern in self.malicious_patterns:
            if re.search(pattern, text):
                return True
        
        return False


# Production security configuration
AI_INSIGHTS_SECURITY_CONFIG = {
    'MIDDLEWARE': [
        'apps.ai_insights.security_middleware.SecurityHeadersMiddleware',
        'apps.ai_insights.security_middleware.CORSMiddleware',
        'apps.ai_insights.security_middleware.RateLimitMiddleware',
        'apps.ai_insights.security_middleware.RequestValidationMiddleware',
    ],
    
    'ALLOWED_ORIGINS': [
        # Add your production frontend URLs here
        'https://yourdomain.com',
        'https://www.yourdomain.com',
    ],
    
    'SECURITY_HEADERS': {
        'STRICT_TRANSPORT_SECURITY': True,
        'CONTENT_TYPE_OPTIONS': True,
        'XSS_PROTECTION': True,
        'FRAME_OPTIONS': 'DENY',
        'REFERRER_POLICY': 'strict-origin-when-cross-origin',
    },
    
    'RATE_LIMITS': {
        'GLOBAL': '1000/hour',
        'CONVERSATION': '60/minute',
        'ANALYSIS': '10/minute',
        'CREDITS': '30/minute',
    }
}