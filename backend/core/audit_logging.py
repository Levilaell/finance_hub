"""
Comprehensive audit logging system for Finance Hub
"""
import json
import logging
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest

User = get_user_model()
logger = logging.getLogger('audit')


class AuditLogger:
    """
    Utility class for logging audit events
    """
    
    @staticmethod
    def log(
        event_type: str,
        user: Optional[User] = None,
        company: Optional['Company'] = None,
        request: Optional[HttpRequest] = None,
        obj: Optional[models.Model] = None,
        description: str = '',
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: str = ''
    ) -> AuditLog:
        """
        Log an audit event
        """
        # Extract request information if available
        ip_address = None
        user_agent = ''
        request_method = ''
        request_path = ''
        
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request_method = request.method
            request_path = request.path
            
            # Get user from request if not provided
            if not user and request.user.is_authenticated:
                user = request.user
            
            # Get company from user if not provided
            if not company and user:
                try:
                    company = user.company
                except:
                    pass
        
        # Get content type and object id if object provided
        content_type = None
        object_id = None
        if obj:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = obj.pk
        
        # Create audit log entry
        audit_log = AuditLog.objects.create(
            event_type=event_type,
            user=user,
            company=company,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            content_type=content_type,
            object_id=object_id,
            description=description,
            metadata=metadata or {},
            success=success,
            error_message=error_message
        )
        
        # Also log to standard logger for real-time monitoring
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"AUDIT: {event_type} - User: {user} - IP: {ip_address} - Success: {success}",
            extra={
                'event_type': event_type,
                'user_id': user.id if user else None,
                'company_id': company.id if company else None,
                'ip_address': ip_address,
                'metadata': metadata
            }
        )
        
        return audit_log
    
    @staticmethod
    def log_login(request: HttpRequest, user: User, success: bool = True, reason: str = '') -> AuditLog:
        """Log login attempt"""
        return AuditLogger.log(
            event_type='AUTH_LOGIN' if success else 'AUTH_FAILED_LOGIN',
            user=user if success else None,
            request=request,
            description=f"Login {'successful' if success else 'failed'}" + (f": {reason}" if reason else ""),
            metadata={'email': request.data.get('email', '')},
            success=success,
            error_message=reason
        )
    
    @staticmethod
    def log_payment(payment: 'Payment', event_type: str, request: Optional[HttpRequest] = None) -> AuditLog:
        """Log payment-related events"""
        return AuditLogger.log(
            event_type=event_type,
            user=payment.company.owner if payment.company else None,
            company=payment.company,
            request=request,
            obj=payment,
            description=f"Payment {payment.id} - Amount: {payment.amount} {payment.currency}",
            metadata={
                'amount': str(payment.amount),
                'currency': payment.currency,
                'gateway': payment.gateway,
                'status': payment.status
            }
        )
    
    @staticmethod
    def log_security_event(event_type: str, request: HttpRequest, description: str, severity: str = 'WARNING') -> AuditLog:
        """Log security-related events"""
        return AuditLogger.log(
            event_type='SECURITY_ALERT',
            request=request,
            description=description,
            metadata={
                'severity': severity,
                'event_subtype': event_type
            },
            success=False
        )


class AuditLogMiddleware:
    """
    Middleware to automatically log certain requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Paths that trigger automatic logging
        self.logged_paths = [
            '/api/auth/login/',
            '/api/auth/logout/',
            '/api/auth/register/',
            '/api/payments/',
            '/api/banking/accounts/',
            '/api/banking/sync/',
        ]
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log specific endpoints
        if any(request.path.startswith(path) for path in self.logged_paths):
            # Don't log GET requests to reduce noise
            if request.method != 'GET':
                # Determine event type based on path and method
                event_type = self._get_event_type(request.path, request.method, response.status_code)
                if event_type:
                    AuditLogger.log(
                        event_type=event_type,
                        request=request,
                        success=200 <= response.status_code < 400,
                        metadata={
                            'status_code': response.status_code,
                            'response_size': len(response.content) if hasattr(response, 'content') else 0
                        }
                    )
        
        return response
    
    def _get_event_type(self, path: str, method: str, status_code: int) -> Optional[str]:
        """Determine event type based on request details"""
        # This is a simplified example - expand based on your needs
        if '/auth/login' in path and method == 'POST':
            return 'AUTH_LOGIN' if status_code == 200 else 'AUTH_FAILED_LOGIN'
        elif '/auth/logout' in path:
            return 'AUTH_LOGOUT'
        elif '/auth/register' in path and method == 'POST':
            return 'USER_CREATED' if status_code == 201 else None
        elif '/payments' in path and method == 'POST':
            return 'PAYMENT_CREATED'
        elif '/banking/accounts' in path and method == 'POST':
            return 'BANK_ACCOUNT_CONNECTED'
        elif '/banking/sync' in path and method == 'POST':
            return 'BANK_SYNC_STARTED'
        
        return None