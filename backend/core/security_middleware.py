"""
Security middleware for Finance Hub
Implements comprehensive security headers
"""
from django.conf import settings
from django.http import HttpResponse


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Content Security Policy
        self.csp_directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net", "https://unpkg.com"],
            "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"],
            "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
            "img-src": ["'self'", "data:", "https:", "blob:"],
            "connect-src": ["'self'", "https://api.stripe.com", "wss:", "ws:"],
            "frame-src": ["'self'", "https://js.stripe.com", "https://hooks.stripe.com"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": [],
        }
        
        # Build CSP string
        self.csp = "; ".join(
            f"{directive} {' '.join(values)}" if values else directive
            for directive, values in self.csp_directives.items()
        )
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add headers to HTML responses
        if isinstance(response, HttpResponse):
            content_type = response.get('Content-Type', '')
            
            # Security headers for all responses
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # HSTS (only in production)
            if not settings.DEBUG:
                response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # CSP for HTML responses
            if 'text/html' in content_type:
                # Use Report-Only in development for testing
                if settings.DEBUG:
                    response['Content-Security-Policy-Report-Only'] = self.csp
                else:
                    response['Content-Security-Policy'] = self.csp
            
            # Additional headers for API responses
            if 'application/json' in content_type:
                response['X-API-Version'] = getattr(settings, 'API_VERSION', '1.0')
        
        return response


class CORSSecurityMiddleware:
    """
    Middleware to handle CORS with security in mind
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        self.allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
        self.allowed_headers = [
            'Accept',
            'Accept-Language',
            'Content-Language',
            'Content-Type',
            'Authorization',
            'X-Requested-With',
            'X-CSRFToken',
        ]
        self.max_age = 86400  # 24 hours
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Get origin from request
        origin = request.META.get('HTTP_ORIGIN')
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Content-Length'] = '0'
        
        # Only add CORS headers if origin is allowed
        if origin and (origin in self.allowed_origins or settings.DEBUG):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
            response['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
            response['Access-Control-Max-Age'] = str(self.max_age)
            
            # Expose specific headers
            response['Access-Control-Expose-Headers'] = 'X-API-Version, X-RateLimit-Remaining'
        
        return response