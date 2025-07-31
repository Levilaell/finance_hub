"""
Advanced session management and device tracking
"""
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import secrets
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from user_agents import parse
import logging

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages device identification and tracking
    """
    
    def __init__(self):
        self.device_cache_timeout = 86400 * 30  # 30 days
    
    def generate_device_id(self, request) -> str:
        """Generate unique device identifier"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        # Create composite fingerprint
        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
        device_id = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
        
        return device_id
    
    def get_device_info(self, request) -> Dict:
        """Extract device information from request"""
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_string)
        
        return {
            'device_id': self.generate_device_id(request),
            'user_agent': user_agent_string,
            'browser': {
                'family': user_agent.browser.family,
                'version': user_agent.browser.version_string,
            },
            'os': {
                'family': user_agent.os.family,
                'version': user_agent.os.version_string,
            },
            'device': {
                'family': user_agent.device.family,
                'brand': user_agent.device.brand,
                'model': user_agent.device.model,
            },
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_pc': user_agent.is_pc,
            'is_bot': user_agent.is_bot,
        }
    
    def get_device_name(self, device_info: Dict) -> str:
        """Generate human-readable device name"""
        browser = device_info['browser']['family']
        os = device_info['os']['family']
        
        if device_info['is_mobile']:
            device_type = 'Mobile'
        elif device_info['is_tablet']:
            device_type = 'Tablet'
        else:
            device_type = 'Desktop'
        
        if device_info['device']['brand']:
            return f"{device_info['device']['brand']} {device_type} - {browser}"
        else:
            return f"{os} {device_type} - {browser}"
    
    def is_device_trusted(self, user, device_id: str) -> bool:
        """Check if device is in user's trusted devices"""
        if not user or not hasattr(user, 'trusted_devices'):
            return False
        
        trusted_devices = user.trusted_devices or []
        
        for device in trusted_devices:
            if device.get('id') == device_id:
                # Check if trust hasn't expired
                trusted_at = device.get('trusted_at')
                if trusted_at:
                    try:
                        if isinstance(trusted_at, str):
                            trusted_at = timezone.datetime.fromisoformat(trusted_at.replace('Z', '+00:00'))
                        
                        # Trust expires after 30 days
                        trust_expires = trusted_at + timezone.timedelta(days=30)
                        return timezone.now() < trust_expires
                    except Exception:
                        pass
        
        return False
    
    def add_trusted_device(self, user, device_info: Dict):
        """Add device to user's trusted devices"""
        if not user:
            return
        
        device_record = {
            'id': device_info['device_id'],
            'name': self.get_device_name(device_info),
            'user_agent': device_info['user_agent'],
            'browser': device_info['browser'],
            'os': device_info['os'],
            'device': device_info['device'],
            'trusted_at': timezone.now().isoformat(),
            'last_used': timezone.now().isoformat(),
        }
        
        trusted_devices = user.trusted_devices or []
        
        # Remove existing entry for this device
        trusted_devices = [d for d in trusted_devices if d.get('id') != device_info['device_id']]
        
        # Add new entry
        trusted_devices.append(device_record)
        
        # Keep only last 10 trusted devices
        trusted_devices = trusted_devices[-10:]
        
        user.trusted_devices = trusted_devices
        user.save()
    
    def remove_trusted_device(self, user, device_id: str):
        """Remove device from trusted devices"""
        if not user or not hasattr(user, 'trusted_devices'):
            return
        
        trusted_devices = user.trusted_devices or []
        user.trusted_devices = [d for d in trusted_devices if d.get('id') != device_id]
        user.save()
    
    def update_device_last_used(self, user, device_id: str):
        """Update last used timestamp for device"""
        if not user or not hasattr(user, 'trusted_devices'):
            return
        
        trusted_devices = user.trusted_devices or []
        
        for device in trusted_devices:
            if device.get('id') == device_id:
                device['last_used'] = timezone.now().isoformat()
                break
        
        user.trusted_devices = trusted_devices
        user.save()


class SessionManager:
    """
    Advanced session management with security features
    """
    
    def __init__(self):
        self.max_sessions_per_user = getattr(settings, 'MAX_SESSIONS_PER_USER', 5)
        self.session_timeout = getattr(settings, 'SESSION_TIMEOUT', 86400)  # 24 hours
        self.absolute_timeout = getattr(settings, 'SESSION_ABSOLUTE_TIMEOUT', 86400 * 7)  # 7 days
    
    def create_session(self, user, request, remember_me=False) -> str:
        """Create a new session for user"""
        from django.contrib.sessions.backends.db import SessionStore
        
        session = SessionStore()
        
        # Basic session data
        session['_auth_user_id'] = str(user.pk)
        session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        session['_auth_user_hash'] = user.get_session_auth_hash()
        
        # Enhanced session data
        device_manager = DeviceManager()
        device_info = device_manager.get_device_info(request)
        
        session['device_info'] = device_info
        session['ip_address'] = self._get_client_ip(request)
        session['created_at'] = timezone.now().isoformat()
        session['last_activity'] = timezone.now().isoformat()
        session['remember_me'] = remember_me
        
        # Set session expiry
        if remember_me:
            session.set_expiry(self.absolute_timeout)
        else:
            session.set_expiry(self.session_timeout)
        
        session.save()
        
        # Update user's active sessions
        self._add_active_session(user, session.session_key, device_info, request)
        
        # Cleanup old sessions
        self._cleanup_old_sessions(user)
        
        return session.session_key
    
    def validate_session(self, session_key: str, request) -> Tuple[bool, Optional[Dict]]:
        """Validate session and check for anomalies"""
        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()
        except Session.DoesNotExist:
            return False, {'error': 'Session not found'}
        
        # Check if session has expired
        if session.expire_date < timezone.now():
            return False, {'error': 'Session expired'}
        
        # Check IP address consistency (optional)
        if getattr(settings, 'VALIDATE_SESSION_IP', False):
            session_ip = session_data.get('ip_address')
            current_ip = self._get_client_ip(request)
            
            if session_ip and session_ip != current_ip:
                logger.warning(f"Session IP mismatch: {session_ip} vs {current_ip}")
                # In production, you might want to invalidate the session
                # return False, {'error': 'IP address mismatch'}
        
        # Check session timeout
        last_activity = session_data.get('last_activity')
        if last_activity:
            try:
                last_activity_dt = timezone.datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                if timezone.now() - last_activity_dt > timezone.timedelta(seconds=self.session_timeout):
                    return False, {'error': 'Session timed out due to inactivity'}
            except Exception:
                pass
        
        # Check absolute timeout
        created_at = session_data.get('created_at')
        if created_at:
            try:
                created_dt = timezone.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if timezone.now() - created_dt > timezone.timedelta(seconds=self.absolute_timeout):
                    return False, {'error': 'Session absolute timeout exceeded'}
            except Exception:
                pass
        
        return True, session_data
    
    def update_session_activity(self, session_key: str):
        """Update session last activity timestamp"""
        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()
            session_data['last_activity'] = timezone.now().isoformat()
            session.session_data = session.encode(session_data)
            session.save()
        except Session.DoesNotExist:
            pass
    
    def invalidate_session(self, session_key: str, user=None):
        """Invalidate a specific session"""
        try:
            Session.objects.filter(session_key=session_key).delete()
            
            if user:
                self._remove_active_session(user, session_key)
                
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
    
    def invalidate_all_sessions(self, user):
        """Invalidate all sessions for a user"""
        # Get all sessions for the user
        user_sessions = Session.objects.filter(
            session_data__contains=f'"_auth_user_id":"{user.pk}"'
        )
        
        session_keys = list(user_sessions.values_list('session_key', flat=True))
        
        # Delete sessions
        user_sessions.delete()
        
        # Clear user's active sessions
        if hasattr(user, 'active_sessions'):
            user.active_sessions = {}
            user.save()
        
        logger.info(f"Invalidated {len(session_keys)} sessions for user {user.pk}")
        
        return len(session_keys)
    
    def get_user_sessions(self, user) -> List[Dict]:
        """Get all active sessions for a user"""
        sessions = []
        
        if not hasattr(user, 'active_sessions'):
            return sessions
        
        active_sessions = user.active_sessions or {}
        
        for session_key, session_info in active_sessions.items():
            # Verify session still exists
            try:
                session = Session.objects.get(session_key=session_key)
                
                sessions.append({
                    'session_key': session_key,
                    'device_name': session_info.get('device_name', 'Unknown Device'),
                    'ip_address': session_info.get('ip_address'),
                    'created_at': session_info.get('created_at'),
                    'last_activity': session_info.get('last_activity'),
                    'current': session_key == getattr(user, '_current_session_key', None),
                })
            except Session.DoesNotExist:
                # Remove invalid session from user's active sessions
                self._remove_active_session(user, session_key)
        
        return sessions
    
    def _add_active_session(self, user, session_key: str, device_info: Dict, request):
        """Add session to user's active sessions"""
        device_manager = DeviceManager()
        device_name = device_manager.get_device_name(device_info)
        
        session_info = {
            'device_name': device_name,
            'device_id': device_info['device_id'],
            'ip_address': self._get_client_ip(request),
            'user_agent': device_info['user_agent'],
            'created_at': timezone.now().isoformat(),
            'last_activity': timezone.now().isoformat(),
        }
        
        if not hasattr(user, 'active_sessions'):
            user.active_sessions = {}
        
        if user.active_sessions is None:
            user.active_sessions = {}
        
        user.active_sessions[session_key] = session_info
        user.save()
    
    def _remove_active_session(self, user, session_key: str):
        """Remove session from user's active sessions"""
        if hasattr(user, 'active_sessions') and user.active_sessions:
            if session_key in user.active_sessions:
                del user.active_sessions[session_key]
                user.save()
    
    def _cleanup_old_sessions(self, user):
        """Remove old sessions if user has too many"""
        if not hasattr(user, 'active_sessions'):
            return
        
        active_sessions = user.active_sessions or {}
        
        if len(active_sessions) > self.max_sessions_per_user:
            # Sort by last activity and remove oldest
            sessions_by_activity = sorted(
                active_sessions.items(),
                key=lambda x: x[1].get('last_activity', ''),
                reverse=True
            )
            
            # Keep most recent sessions
            sessions_to_keep = dict(sessions_by_activity[:self.max_sessions_per_user])
            sessions_to_remove = [
                k for k, v in sessions_by_activity[self.max_sessions_per_user:]
            ]
            
            # Remove old sessions
            for session_key in sessions_to_remove:
                self.invalidate_session(session_key)
            
            user.active_sessions = sessions_to_keep
            user.save()
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class RememberMeManager:
    """
    Manages "Remember Me" functionality with secure tokens
    """
    
    def __init__(self):
        self.token_lifetime = getattr(settings, 'REMEMBER_ME_LIFETIME', 86400 * 30)  # 30 days
    
    def create_remember_token(self, user, request) -> str:
        """Create a remember me token"""
        from ..models_enhanced import RememberMeToken
        
        device_manager = DeviceManager()
        device_info = device_manager.get_device_info(request)
        
        # Clean up old tokens
        self._cleanup_old_tokens(user)
        
        # Create new token
        remember_token = RememberMeToken(
            user=user,
            device_id=device_info['device_id'],
            device_name=device_manager.get_device_name(device_info),
            expires_at=timezone.now() + timezone.timedelta(seconds=self.token_lifetime),
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        token_string = remember_token.generate_token()
        remember_token.save()
        
        return token_string
    
    def validate_remember_token(self, token_string: str) -> Tuple[Optional[object], bool]:
        """Validate remember me token and return user"""
        from ..models_enhanced import RememberMeToken
        
        if ':' not in token_string:
            return None, False
        
        selector, validator = token_string.split(':', 1)
        
        try:
            remember_token = RememberMeToken.objects.get(
                selector=selector,
                is_active=True
            )
            
            if not remember_token.is_valid():
                remember_token.is_active = False
                remember_token.save()
                return None, False
            
            if not remember_token.verify_validator(validator):
                # Invalid validator - possible attack
                logger.warning(f"Invalid remember me validator for selector {selector}")
                remember_token.is_active = False
                remember_token.save()
                return None, False
            
            # Update last used
            remember_token.update_last_used()
            
            return remember_token.user, True
            
        except RememberMeToken.DoesNotExist:
            return None, False
    
    def invalidate_remember_token(self, user, device_id: str = None):
        """Invalidate remember me tokens"""
        from ..models_enhanced import RememberMeToken
        
        query = RememberMeToken.objects.filter(user=user, is_active=True)
        
        if device_id:
            query = query.filter(device_id=device_id)
        
        count = query.update(is_active=False)
        logger.info(f"Invalidated {count} remember me tokens for user {user.pk}")
        
        return count
    
    def _cleanup_old_tokens(self, user):
        """Clean up expired tokens"""
        from ..models_enhanced import RememberMeToken
        
        expired_count = RememberMeToken.objects.filter(
            user=user,
            expires_at__lt=timezone.now()
        ).update(is_active=False)
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired remember tokens for user {user.pk}")
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class ConcurrentSessionLimiter:
    """
    Limits concurrent sessions per user
    """
    
    def __init__(self, max_sessions=5):
        self.max_sessions = max_sessions
    
    def check_session_limit(self, user) -> Tuple[bool, int]:
        """
        Check if user has reached session limit
        Returns: (can_create_session, current_session_count)
        """
        active_sessions = user.active_sessions or {}
        current_count = len(active_sessions)
        
        return current_count < self.max_sessions, current_count
    
    def enforce_session_limit(self, user):
        """Enforce session limit by removing oldest sessions"""
        session_manager = SessionManager()
        session_manager._cleanup_old_sessions(user)


# Global instances
device_manager = DeviceManager()
session_manager = SessionManager()
remember_me_manager = RememberMeManager()
session_limiter = ConcurrentSessionLimiter()