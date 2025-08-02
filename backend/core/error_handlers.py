"""
Comprehensive error handling for production
"""
import logging
import traceback
import uuid
from typing import Dict, Any, Optional

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import (
    APIException, AuthenticationFailed, NotAuthenticated,
    PermissionDenied as DRFPermissionDenied, Throttled, ValidationError as DRFValidationError
)

# Open banking errors will be added when the module is created
class OpenBankingError(Exception):
    pass

class AuthenticationError(OpenBankingError):
    pass

class APIError(OpenBankingError):
    pass

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


class FinanceAppError(APIException):
    """Base exception for finance app specific errors"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'An error occurred in the finance application.'
    default_code = 'finance_error'


class InsufficientFundsError(FinanceAppError):
    """Insufficient funds for transaction"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Insufficient funds for this transaction.'
    default_code = 'insufficient_funds'


class BankAccountConnectionError(FinanceAppError):
    """Bank connection/integration error"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Unable to connect to bank service.'
    default_code = 'bank_connection_error'


class AICategorizationError(FinanceAppError):
    """AI categorization service error"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'AI categorization service is temporarily unavailable.'
    default_code = 'ai_service_error'


class InvalidAccountError(FinanceAppError):
    """Invalid bank account error"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid bank account information.'
    default_code = 'invalid_account'


class TokenExpiredError(FinanceAppError):
    """Banking token expired error"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Banking authentication token has expired.'
    default_code = 'token_expired'


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict] = None,
    field_errors: Optional[Dict] = None
) -> Dict[str, Any]:
    """Format standardized error response"""
    response = {
        'error': {
            'code': error_code,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
    }
    
    if details:
        response['error']['details'] = details
    
    if field_errors:
        response['error']['field_errors'] = field_errors
    
    # Add request ID if available
    if hasattr(settings, 'REQUEST_ID_HEADER'):
        # In production, you'd get this from request context
        pass
    
    return response


def sanitize_error_message(error: Exception, user_facing: bool = True, error_type: str = None) -> str:
    """Sanitize error messages for user consumption and prevent information disclosure"""
    if not user_facing or settings.DEBUG:
        return str(error)
    
    # In production, return generic messages based on error type to prevent information disclosure
    if error_type:
        generic_messages = {
            'authentication': 'Authentication failed. Please check your credentials.',
            'authorization': 'Access denied. You do not have permission to perform this action.',
            'validation': 'Invalid input data provided.',
            'not_found': 'The requested resource was not found.',
            'server_error': 'Internal server error. Please try again later.',
            'rate_limit': 'Rate limit exceeded. Please wait before trying again.',
            'database': 'Data processing error. Please try again later.',
            'external_api': 'External service unavailable. Please try again later.',
            'security': 'Request rejected for security reasons.',
            'csrf': 'CSRF verification failed. Please refresh the page and try again.',
            'suspicious': 'Suspicious activity detected. Request blocked.',
        }
        
        return generic_messages.get(error_type, 'An error occurred. Please try again later.')
    
    # Map internal errors to user-friendly messages (legacy support)
    error_mappings = {
        'Connection refused': 'Service is temporarily unavailable. Please try again later.',
        'Timeout': 'Request timed out. Please try again.',
        'Invalid token': 'Your session has expired. Please log in again.',
        'Insufficient funds': 'Insufficient funds for this transaction.',
        'Invalid account': 'Bank account information is invalid.',
        'Rate limit': 'Too many requests. Please wait before trying again.',
        'csrf': 'CSRF verification failed. Please refresh the page.',
        'permission': 'Access denied.',
        'authentication': 'Authentication failed.',
    }
    
    error_str = str(error).lower()
    for key, message in error_mappings.items():
        if key.lower() in error_str:
            return message
    
    return 'An unexpected error occurred. Please try again later.'


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_security_error(request, error, error_type='unknown'):
    """
    Log security-related errors with full context
    """
    client_ip = get_client_ip(request)
    user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
    
    security_logger.error(
        f"Security error: {error_type}",
        extra={
            'error_type': error_type,
            'error_message': str(error),
            'client_ip': client_ip,
            'user_id': user_id,
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'timestamp': timezone.now().isoformat(),
            'stack_trace': traceback.format_exc() if settings.DEBUG else None
        }
    )


def handle_suspicious_operation(request, message="Suspicious operation detected", block_request=True):
    """
    Handle suspicious operations with logging and appropriate response
    """
    client_ip = get_client_ip(request)
    user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
    
    security_logger.critical(
        f"SUSPICIOUS ACTIVITY from {client_ip}: {message}",
        extra={
            'event_type': 'suspicious_activity',
            'client_ip': client_ip,
            'user_id': user_id,
            'path': request.path,
            'method': request.method,
            'message': message,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'post_data': dict(request.POST) if request.method == 'POST' and not any(field in request.POST for field in ['password', 'token']) else 'REDACTED',
            'get_params': dict(request.GET),
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    if block_request:
        return Response(
            format_error_response(
                'security_violation',
                sanitize_error_message(Exception(message), error_type='security')
            ),
            status=status.HTTP_403_FORBIDDEN
        )
    
    return None


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    def __init__(self, message, error_type='security', should_block=True):
        super().__init__(message)
        self.error_type = error_type
        self.should_block = should_block


def custom_exception_handler(exc, context):
    """Custom exception handler for the entire application with security logging"""
    
    # Get the request object
    request = context.get('request')
    view = context.get('view')
    
    # Handle security errors first
    if isinstance(exc, SecurityError):
        if request:
            log_security_error(request, exc, exc.error_type)
            if exc.should_block:
                return handle_suspicious_operation(request, str(exc))
    
    # Determine if this is a security-related error
    security_exceptions = [
        'authentication', 'permission', 'authorization', 'invalid token', 
        'csrf', 'forbidden', 'unauthorized', 'access denied'
    ]
    
    is_security_error = any(
        keyword in str(exc).lower() 
        for keyword in security_exceptions
    )
    
    # Log the exception with context
    if is_security_error:
        if request:
            log_security_error(request, exc, 'authentication' if 'auth' in str(exc).lower() else 'authorization')
        logger.warning(
            f"Security exception in {view.__class__.__name__ if view else 'unknown'} for user {getattr(request.user, 'id', 'anonymous') if request else 'unknown'}: {exc}",
            extra={
                'exception_type': exc.__class__.__name__,
                'view': view.__class__.__name__ if view else None,
                'user_id': getattr(request.user, 'id', None) if request else None,
                'path': getattr(request, 'path', None) if request else None,
                'method': getattr(request, 'method', None) if request else None,
                'client_ip': get_client_ip(request) if request else None,
                'is_security_error': True,
            },
            exc_info=settings.DEBUG  # Only include stack trace in debug mode
        )
    else:
        logger.error(
            f"Exception in {view.__class__.__name__ if view else 'unknown'} for user {getattr(request.user, 'id', 'anonymous') if request else 'unknown'}: {exc}",
            extra={
                'exception_type': exc.__class__.__name__,
                'view': view.__class__.__name__ if view else None,
                'user_id': getattr(request.user, 'id', None) if request else None,
                'path': getattr(request, 'path', None) if request else None,
                'method': getattr(request, 'method', None) if request else None,
                'is_security_error': False,
            },
            exc_info=True
        )
    
    # Handle specific Open Banking errors
    if isinstance(exc, OpenBankingError):
        if isinstance(exc, AuthenticationError):
            return Response(
                format_error_response(
                    'bank_auth_error',
                    'Bank authentication failed. Please reconnect your account.',
                    {'type': 'authentication'}
                ),
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, APIError):
            return Response(
                format_error_response(
                    'bank_api_error',
                    'Bank service is temporarily unavailable.',
                    {'type': 'api_error'}
                ),
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    # Handle custom finance app errors
    if isinstance(exc, FinanceAppError):
        return Response(
            format_error_response(
                exc.default_code,
                sanitize_error_message(exc),
                {'type': 'finance_error'}
            ),
            status=exc.status_code
        )
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        field_errors = {}
        if hasattr(exc, 'message_dict'):
            field_errors = exc.message_dict
        elif hasattr(exc, 'messages'):
            field_errors = {'non_field_errors': exc.messages}
        
        return Response(
            format_error_response(
                'validation_error',
                'Validation failed.',
                field_errors=field_errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle DRF validation errors
    if isinstance(exc, DRFValidationError):
        return Response(
            format_error_response(
                'validation_error',
                'Erro de validação nos dados fornecidos.',
                field_errors=exc.detail
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle permission errors
    if isinstance(exc, (PermissionDenied, DRFPermissionDenied)):
        return Response(
            format_error_response(
                'permission_denied',
                'You do not have permission to perform this action.'
            ),
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Handle authentication errors
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return Response(
            format_error_response(
                'authentication_required',
                'Authentication required.'
            ),
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Handle throttling
    if isinstance(exc, Throttled):
        return Response(
            format_error_response(
                'rate_limited',
                f'Rate limit exceeded. Try again in {exc.wait} seconds.',
                {'wait_time': exc.wait}
            ),
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Handle 404 errors
    if isinstance(exc, Http404):
        return Response(
            format_error_response(
                'not_found',
                'The requested resource was not found.'
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Call DRF's default exception handler for other cases
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # Customize DRF's default response format
        custom_response_data = format_error_response(
            'api_error',
            sanitize_error_message(exc),
            {'original_error': response.data}
        )
        response.data = custom_response_data
        return response
    
    # Handle unexpected errors
    if not settings.DEBUG:
        # In production, don't expose internal errors
        logger.critical(
            f"Unhandled exception: {exc}",
            extra={'traceback': traceback.format_exc()},
            exc_info=True
        )
        
        return Response(
            format_error_response(
                'internal_error',
                'An internal server error occurred. Please contact support if the problem persists.',
                {'error_id': str(uuid.uuid4())}  # For tracking
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # In debug mode, let Django handle it
    return None


class SecurityErrorMiddleware:
    """Middleware specifically for handling security-related errors and threats"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except SecurityError as exc:
            # Handle security errors with specialized logging and blocking
            log_security_error(request, exc, exc.error_type)
            if exc.should_block:
                return handle_suspicious_operation(request, str(exc))
            else:
                # Log but don't block
                return Response(
                    format_error_response(
                        'security_warning',
                        sanitize_error_message(exc, error_type='security')
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception as exc:
            # Check if this is a security-related exception
            security_keywords = [
                'csrf', 'xss', 'injection', 'unauthorized', 'forbidden',
                'authentication', 'permission', 'token', 'session'
            ]
            
            is_security_related = any(
                keyword in str(exc).lower() 
                for keyword in security_keywords
            )
            
            if is_security_related:
                log_security_error(request, exc, 'security')
                return Response(
                    format_error_response(
                        'security_error',
                        sanitize_error_message(exc, error_type='security')
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Not a security error, let other middleware handle it
            return self.get_response(request)
    
    def process_exception(self, request, exception):
        """Process security exceptions that occur during view processing"""
        if isinstance(exception, SecurityError):
            log_security_error(request, exception, exception.error_type)
            return handle_suspicious_operation(request, str(exception))
        
        # Check for security-related exceptions
        security_exceptions = [
            'authentication', 'permission', 'authorization', 'csrf',
            'xss', 'injection', 'suspicious', 'rate limit'
        ]
        
        is_security_exception = any(
            keyword in str(exception).lower() 
            for keyword in security_exceptions
        )
        
        if is_security_exception:
            log_security_error(request, exception, 'security')
            return Response(
                format_error_response(
                    'security_exception',
                    sanitize_error_message(exception, error_type='security')
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return None to let other middleware handle non-security exceptions
        return None


class ErrorHandlingMiddleware:
    """Middleware to catch and handle errors not caught by DRF"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            logger.error(
                f"Unhandled exception in middleware: {exc}",
                extra={
                    'path': request.path,
                    'method': request.method,
                    'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                },
                exc_info=True
            )
            
            # Re-raise the exception to let Django handle it
            raise
    
    def process_exception(self, request, exception):
        """Process exceptions that occur during view processing"""
        logger.error(
            f"Exception during view processing: {exception}",
            extra={
                'path': request.path,
                'method': request.method,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            },
            exc_info=True
        )
        
        # Return None to let Django's default exception handling take over
        return None


# Specific error handlers for common scenarios
def handle_database_error(exc, context):
    """Handle database-related errors"""
    logger.error(f"Database error: {exc}", exc_info=True)
    
    return Response(
        format_error_response(
            'database_error',
            'Database service is temporarily unavailable.'
        ),
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )


def handle_external_api_error(exc, context):
    """Handle external API errors (banks, AI services, etc.)"""
    logger.error(f"External API error: {exc}", exc_info=True)
    
    return Response(
        format_error_response(
            'external_service_error',
            'External service is temporarily unavailable.'
        ),
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )


def handle_business_logic_error(exc, context):
    """Handle business logic errors"""
    logger.warning(f"Business logic error: {exc}")
    
    return Response(
        format_error_response(
            'business_error',
            sanitize_error_message(exc)
        ),
        status=status.HTTP_400_BAD_REQUEST
    )