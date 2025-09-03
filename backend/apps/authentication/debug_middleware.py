"""
Comprehensive Authentication Debugging Middleware
Provides detailed logging and monitoring for JWT authentication issues
"""
import json
import time
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

logger = logging.getLogger('auth_debug')

class AuthenticationDebugMiddleware(MiddlewareMixin):
    """
    Comprehensive middleware for debugging authentication issues
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
    def process_request(self, request):
        """Log authentication-related requests with detailed context"""
        
        # Only process authentication-related endpoints
        if not self._is_auth_related(request.path):
            return None
            
        # Start timing
        request._auth_debug_start = time.time()
        
        # Extract authentication context
        auth_context = self._extract_auth_context(request)
        
        # Log request details
        logger.info(
            f"AUTH_REQUEST: {request.method} {request.path}",
            extra={
                'request_id': getattr(request, 'id', 'unknown'),
                'ip': self._get_client_ip(request),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'auth_context': auth_context,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Check for potential race conditions
        if request.path.endswith('/refresh/'):
            self._check_concurrent_refresh(request, auth_context)
            
        return None
        
    def process_response(self, request, response):
        """Log authentication responses with timing and success metrics"""
        
        if not self._is_auth_related(request.path):
            return response
            
        # Calculate processing time
        processing_time = 0
        if hasattr(request, '_auth_debug_start'):
            processing_time = time.time() - request._auth_debug_start
            
        # Extract response context
        response_context = self._extract_response_context(response)
        
        # Log response details
        logger.info(
            f"AUTH_RESPONSE: {request.method} {request.path} -> {response.status_code}",
            extra={
                'request_id': getattr(request, 'id', 'unknown'),
                'ip': self._get_client_ip(request),
                'status_code': response.status_code,
                'processing_time': processing_time,
                'response_context': response_context,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Track authentication metrics
        self._track_auth_metrics(request, response, processing_time)
        
        # Check for JWT-specific errors
        if response.status_code == 401 and request.path.endswith('/refresh/'):
            self._analyze_token_refresh_failure(request, response)
            
        return response
        
    def _is_auth_related(self, path):
        """Check if path is authentication related"""
        auth_paths = [
            '/api/auth/login/',
            '/api/auth/refresh/',
            '/api/auth/logout/',
            '/api/auth/register/',
            '/api/auth/verify-email/',
            '/api/auth/password-reset/',
            '/api/auth/2fa/',
        ]
        return any(path.startswith(auth_path) for auth_path in auth_paths)
        
    def _get_client_ip(self, request):
        """Extract client IP considering load balancers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
        
    def _extract_auth_context(self, request):
        """Extract authentication context from request"""
        context = {
            'has_authorization': bool(request.headers.get('Authorization')),
            'content_type': request.content_type,
            'content_length': len(getattr(request, 'body', b'')),
        }
        
        # Analyze Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            context['auth_type'] = 'Bearer' if auth_header.startswith('Bearer ') else 'Other'
            context['token_preview'] = auth_header[:20] + '...' if len(auth_header) > 20 else auth_header
            
        # For refresh requests, analyze the refresh token
        if request.path.endswith('/refresh/') and hasattr(request, 'data'):
            refresh_token = request.data.get('refresh', '')
            if refresh_token:
                context['refresh_token_analysis'] = self._analyze_token(refresh_token)
                
        return context
        
    def _extract_response_context(self, response):
        """Extract authentication context from response"""
        context = {
            'has_tokens': False,
            'error_message': None
        }
        
        # Parse JSON response safely
        try:
            if hasattr(response, 'data'):
                data = response.data
            else:
                content = getattr(response, 'content', b'')
                if content:
                    data = json.loads(content.decode('utf-8'))
                else:
                    data = {}
                    
            # Check for token presence
            if 'access' in data or 'refresh' in data:
                context['has_tokens'] = True
                context['token_types'] = []
                if 'access' in data:
                    context['token_types'].append('access')
                    context['access_token_analysis'] = self._analyze_token(data['access'])
                if 'refresh' in data:
                    context['token_types'].append('refresh')
                    
            # Extract error messages
            if 'error' in data:
                context['error_message'] = data['error']
                
        except (json.JSONDecodeError, AttributeError, KeyError):
            pass
            
        return context
        
    def _analyze_token(self, token_string):
        """Analyze JWT token for debugging"""
        if not token_string:
            return {'status': 'empty'}
            
        try:
            # For refresh tokens
            try:
                token = RefreshToken(token_string)
                payload = token.payload
                return {
                    'status': 'valid_refresh',
                    'user_id': payload.get('user_id'),
                    'exp': payload.get('exp'),
                    'iat': payload.get('iat'),
                    'jti': payload.get('jti'),
                    'token_type': payload.get('token_type'),
                    'is_expired': token.check_exp() if hasattr(token, 'check_exp') else False
                }
            except (TokenError, InvalidToken):
                pass
                
            # For access tokens
            try:
                token = AccessToken(token_string)
                payload = token.payload
                return {
                    'status': 'valid_access',
                    'user_id': payload.get('user_id'),
                    'exp': payload.get('exp'),
                    'iat': payload.get('iat'),
                    'token_type': payload.get('token_type'),
                    'is_expired': token.check_exp() if hasattr(token, 'check_exp') else False
                }
            except (TokenError, InvalidToken):
                pass
                
            return {'status': 'invalid', 'error': 'Token validation failed'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
            
    def _check_concurrent_refresh(self, request, auth_context):
        """Check for concurrent refresh token usage"""
        refresh_token = request.data.get('refresh', '') if hasattr(request, 'data') else ''
        if not refresh_token:
            return
            
        # Create a cache key based on token hash
        cache_key = f"refresh_in_progress:{hash(refresh_token)}"
        
        # Check if this token is already being processed
        if cache.get(cache_key):
            logger.warning(
                "CONCURRENT_REFRESH_DETECTED: Same refresh token used simultaneously",
                extra={
                    'ip': self._get_client_ip(request),
                    'token_hash': hash(refresh_token),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        # Mark this token as in progress (expire after 30 seconds)
        cache.set(cache_key, True, 30)
        
    def _track_auth_metrics(self, request, response, processing_time):
        """Track authentication metrics for monitoring"""
        metric_key = f"auth_metrics:{request.path}:{response.status_code}"
        
        # Get current metrics
        metrics = cache.get(metric_key, {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'last_updated': datetime.now().isoformat()
        })
        
        # Update metrics
        metrics['count'] += 1
        metrics['total_time'] += processing_time
        metrics['avg_time'] = metrics['total_time'] / metrics['count']
        metrics['last_updated'] = datetime.now().isoformat()
        
        # Store for 1 hour
        cache.set(metric_key, metrics, 3600)
        
        # Log slow requests
        if processing_time > 2.0:  # More than 2 seconds
            logger.warning(
                f"SLOW_AUTH_REQUEST: {request.method} {request.path} took {processing_time:.2f}s",
                extra={
                    'ip': self._get_client_ip(request),
                    'processing_time': processing_time,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
    def _analyze_token_refresh_failure(self, request, response):
        """Analyze failed token refresh attempts"""
        refresh_token = request.data.get('refresh', '') if hasattr(request, 'data') else ''
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'ip': self._get_client_ip(request),
            'refresh_token_provided': bool(refresh_token),
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
        
        if refresh_token:
            analysis['token_analysis'] = self._analyze_token(refresh_token)
            
        try:
            if hasattr(response, 'data'):
                error_data = response.data
            else:
                content = getattr(response, 'content', b'')
                if content:
                    error_data = json.loads(content.decode('utf-8'))
                else:
                    error_data = {}
                    
            analysis['error_response'] = error_data
            
        except (json.JSONDecodeError, AttributeError):
            pass
            
        logger.error(
            "TOKEN_REFRESH_FAILURE_ANALYSIS",
            extra={
                'analysis': analysis
            }
        )

class AuthMetricsView:
    """
    View to expose authentication metrics for monitoring
    """
    
    def get_auth_metrics(self):
        """Get authentication metrics from cache"""
        metrics = {}
        
        # Get all auth metric keys
        auth_paths = [
            '/api/auth/login/',
            '/api/auth/refresh/', 
            '/api/auth/logout/',
            '/api/auth/register/'
        ]
        
        for path in auth_paths:
            for status_code in [200, 201, 400, 401, 403, 500]:
                metric_key = f"auth_metrics:{path}:{status_code}"
                metric_data = cache.get(metric_key)
                if metric_data:
                    metrics[f"{path}_{status_code}"] = metric_data
                    
        return metrics
        
    def get_concurrent_refresh_stats(self):
        """Get statistics about concurrent refresh attempts"""
        # This would require more sophisticated tracking
        # For now, return placeholder data
        return {
            'total_concurrent_detections': 0,
            'last_detection': None,
            'most_concurrent_ip': None
        }