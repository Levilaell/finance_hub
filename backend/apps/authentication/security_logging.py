"""
Security logging for authentication events
"""
import logging
from django.utils import timezone
from django.conf import settings

# Create dedicated security logger
security_logger = logging.getLogger('security')


class SecurityEvent:
    """Security event types"""
    LOGIN_SUCCESS = 'login_success'
    LOGIN_FAILED = 'login_failed'
    LOGOUT = 'logout'
    PASSWORD_CHANGED = 'password_changed'
    ACCOUNT_LOCKED = 'account_locked'
    TOKEN_REFRESHED = 'token_refreshed'
    TOKEN_REFRESH_FAILED = 'token_refresh_failed'
    SESSION_INVALIDATED = 'session_invalidated'
    ACCOUNT_CREATED = 'account_created'
    ACCOUNT_DELETED = 'account_deleted'


def log_security_event(event_type, user=None, request=None, extra_data=None):
    """
    Log security events with structured data
    """
    event_data = {
        'event_type': event_type,
        'timestamp': timezone.now().isoformat(),
        'user_id': getattr(user, 'id', None) if user else None,
        'username': getattr(user, 'email', None) if user else None,
    }
    
    if request:
        event_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
            'session_key': getattr(request.session, 'session_key', None),
        })
    
    if extra_data:
        event_data.update(extra_data)
    
    # Log based on event severity
    if event_type in [SecurityEvent.LOGIN_FAILED, SecurityEvent.ACCOUNT_LOCKED]:
        security_logger.warning(f"Security Event: {event_type}", extra={'security_event': event_data})
    elif event_type in [SecurityEvent.PASSWORD_CHANGED, SecurityEvent.SESSION_INVALIDATED]:
        security_logger.info(f"Security Event: {event_type}", extra={'security_event': event_data})
    else:
        security_logger.info(f"Security Event: {event_type}", extra={'security_event': event_data})
    
    # In production, you might also want to:
    # - Send to SIEM system
    # - Store in dedicated security database
    # - Trigger alerts for suspicious patterns
    
    return event_data


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LoginAttemptTracker:
    """
    Track login attempts for security monitoring
    """
    
    @staticmethod
    def track_failed_attempt(email, ip_address):
        """Track failed login attempt"""
        from django.core.cache import cache
        
        # Track by email
        email_key = f'login_attempts:email:{email}'
        email_attempts = cache.get(email_key, 0)
        cache.set(email_key, email_attempts + 1, 3600)  # 1 hour
        
        # Track by IP
        ip_key = f'login_attempts:ip:{ip_address}'
        ip_attempts = cache.get(ip_key, 0)
        cache.set(ip_key, ip_attempts + 1, 3600)  # 1 hour
        
        # Check if we should lock the account
        if email_attempts >= getattr(settings, 'AUTH_MAX_LOGIN_ATTEMPTS', 5):
            return True, email_attempts
        
        return False, email_attempts
    
    @staticmethod
    def reset_attempts(email, ip_address=None):
        """Reset login attempts on successful login"""
        from django.core.cache import cache
        
        cache.delete(f'login_attempts:email:{email}')
        if ip_address:
            cache.delete(f'login_attempts:ip:{ip_address}')
    
    @staticmethod
    def is_locked(email):
        """Check if account is locked"""
        from django.core.cache import cache
        
        email_key = f'login_attempts:email:{email}'
        attempts = cache.get(email_key, 0)
        return attempts >= getattr(settings, 'AUTH_MAX_LOGIN_ATTEMPTS', 5)


class SessionManager:
    """
    Manage user sessions for security
    """
    
    @staticmethod
    def invalidate_all_sessions(user):
        """
        Invalidate all sessions for a user (e.g., after password change)
        """
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        # Get all non-expired sessions
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        invalidated_count = 0
        
        # Check each session for the user
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                session.delete()
                invalidated_count += 1
        
        # Also invalidate JWT tokens if using token blacklist
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            # Get all outstanding tokens for the user
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            token_count = outstanding_tokens.count()
            
            # Blacklist all tokens
            for token in outstanding_tokens:
                try:
                    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
                    BlacklistedToken.objects.get_or_create(token=token)
                except Exception:
                    # If blacklist model doesn't exist, delete the token
                    token.delete()
            
            # Log the event with counts
            log_security_event(
                SecurityEvent.SESSION_INVALIDATED,
                user=user,
                extra_data={
                    'reason': 'all_sessions_invalidated',
                    'sessions_invalidated': invalidated_count,
                    'tokens_invalidated': token_count
                }
            )
        except ImportError:
            # Token blacklist not available, log without token count
            log_security_event(
                SecurityEvent.SESSION_INVALIDATED,
                user=user,
                extra_data={
                    'reason': 'all_sessions_invalidated',
                    'sessions_invalidated': invalidated_count
                }
            )
    
    
    @staticmethod
    def get_active_session_count(user):
        """Get count of active sessions for a user"""
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        count = 0
        
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                count += 1
        
        return count
    
    
