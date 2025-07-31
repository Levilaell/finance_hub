"""
Comprehensive audit logging system for authentication events
"""
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import logging
import json
from typing import Dict, Optional, Any
from ..models_enhanced import AuthenticationAuditLog, SecurityEvent, EnhancedUser
from .anomaly_detection import AnomalyDetector

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Centralized audit logging for all authentication events
    """
    
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.enabled = getattr(settings, 'AUDIT_LOGGING_ENABLED', True)
        self.log_successful_events = getattr(settings, 'LOG_SUCCESSFUL_AUTH_EVENTS', True)
        self.log_failed_events = getattr(settings, 'LOG_FAILED_AUTH_EVENTS', True)
        self.retention_days = getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 365)
    
    def log_authentication_event(self,
                                event_type: str,
                                user: Optional[EnhancedUser] = None,
                                request=None,
                                success: bool = True,
                                error_message: str = '',
                                additional_data: Dict = None) -> Optional[AuthenticationAuditLog]:
        """
        Log an authentication event with comprehensive details
        """
        if not self.enabled:
            return None
        
        # Skip logging based on configuration
        if success and not self.log_successful_events:
            return None
        if not success and not self.log_failed_events:
            return None
        
        try:
            with transaction.atomic():
                # Extract request information
                ip_address = None
                user_agent = ''
                location_data = {}
                
                if request:
                    ip_address = self._get_client_ip(request)
                    user_agent = request.META.get('HTTP_USER_AGENT', '')
                    location_data = self._get_location_data(ip_address)
                
                # Prepare audit log data
                audit_data = {
                    'user': user,
                    'event_type': event_type,
                    'timestamp': timezone.now(),
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'success': success,
                    'error_message': error_message,
                    'data': additional_data or {},
                }
                
                # Add location data
                if location_data:
                    audit_data.update({
                        'country': location_data.get('country'),
                        'city': location_data.get('city'),
                        'latitude': location_data.get('latitude'),
                        'longitude': location_data.get('longitude'),
                    })
                
                # Perform risk assessment
                if user and request:
                    anomaly_result = self.anomaly_detector.analyze_login_attempt(
                        user, request, success
                    )
                    audit_data['risk_score'] = anomaly_result['risk_score']
                    audit_data['flagged'] = anomaly_result['risk_score'] > 0.7
                    
                    # Add anomaly data
                    if anomaly_result['anomalies']:
                        audit_data['data']['anomalies'] = anomaly_result['anomalies']
                
                # Create audit log entry
                audit_log = AuthenticationAuditLog.objects.create(**audit_data)
                
                # Log to standard logger as well
                self._log_to_standard_logger(audit_log)
                
                # Create security events for high-risk activities
                if audit_log.flagged:
                    self._create_security_event(audit_log)
                
                # Trigger alerts if necessary
                if audit_log.risk_score > 0.8:
                    self._trigger_security_alert(audit_log)
                
                return audit_log
                
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}", exc_info=True)
            return None
    
    def log_login_success(self, user: EnhancedUser, request, additional_data: Dict = None):
        """Log successful login"""
        return self.log_authentication_event(
            event_type='login_success',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_login_failure(self, user: Optional[EnhancedUser], request, 
                         error_message: str, additional_data: Dict = None):
        """Log failed login attempt"""
        return self.log_authentication_event(
            event_type='login_failure',
            user=user,
            request=request,
            success=False,
            error_message=error_message,
            additional_data=additional_data
        )
    
    def log_logout(self, user: EnhancedUser, request, additional_data: Dict = None):
        """Log user logout"""
        return self.log_authentication_event(
            event_type='logout',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_password_reset_request(self, user: EnhancedUser, request, 
                                  additional_data: Dict = None):
        """Log password reset request"""
        return self.log_authentication_event(
            event_type='password_reset_request',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_password_reset_complete(self, user: EnhancedUser, request, 
                                   additional_data: Dict = None):
        """Log completed password reset"""
        return self.log_authentication_event(
            event_type='password_reset_complete',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_password_change(self, user: EnhancedUser, request, 
                           additional_data: Dict = None):
        """Log password change"""
        return self.log_authentication_event(
            event_type='password_change',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_2fa_enable(self, user: EnhancedUser, request, additional_data: Dict = None):
        """Log 2FA activation"""
        return self.log_authentication_event(
            event_type='2fa_enable',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_2fa_disable(self, user: EnhancedUser, request, additional_data: Dict = None):
        """Log 2FA deactivation"""
        return self.log_authentication_event(
            event_type='2fa_disable',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_2fa_success(self, user: EnhancedUser, request, additional_data: Dict = None):
        """Log successful 2FA verification"""
        return self.log_authentication_event(
            event_type='2fa_success',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_2fa_failure(self, user: EnhancedUser, request, error_message: str, 
                       additional_data: Dict = None):
        """Log failed 2FA verification"""
        return self.log_authentication_event(
            event_type='2fa_failure',
            user=user,
            request=request,
            success=False,
            error_message=error_message,
            additional_data=additional_data
        )
    
    def log_account_locked(self, user: EnhancedUser, request, reason: str, 
                          additional_data: Dict = None):
        """Log account lockout"""
        data = additional_data or {}
        data['lock_reason'] = reason
        
        return self.log_authentication_event(
            event_type='account_locked',
            user=user,
            request=request,
            success=True,
            additional_data=data
        )
    
    def log_account_unlocked(self, user: EnhancedUser, request, method: str, 
                           additional_data: Dict = None):
        """Log account unlock"""
        data = additional_data or {}
        data['unlock_method'] = method
        
        return self.log_authentication_event(
            event_type='account_unlocked',
            user=user,
            request=request,
            success=True,
            additional_data=data
        )
    
    def log_email_verified(self, user: EnhancedUser, request, additional_data: Dict = None):
        """Log email verification"""
        return self.log_authentication_event(
            event_type='email_verified',
            user=user,
            request=request,
            success=True,
            additional_data=additional_data
        )
    
    def log_device_trusted(self, user: EnhancedUser, request, device_info: Dict, 
                          additional_data: Dict = None):
        """Log device being marked as trusted"""
        data = additional_data or {}
        data['device_info'] = device_info
        
        return self.log_authentication_event(
            event_type='device_trusted',
            user=user,
            request=request,
            success=True,
            additional_data=data
        )
    
    def log_session_expired(self, user: EnhancedUser, session_key: str, reason: str,
                           additional_data: Dict = None):
        """Log session expiration"""
        data = additional_data or {}
        data.update({
            'session_key': session_key,
            'expiration_reason': reason
        })
        
        return self.log_authentication_event(
            event_type='session_expired',
            user=user,
            request=None,
            success=True,
            additional_data=data
        )
    
    def log_oauth_login(self, user: EnhancedUser, request, provider: str, 
                       provider_user_id: str, additional_data: Dict = None):
        """Log OAuth login"""
        data = additional_data or {}
        data.update({
            'oauth_provider': provider,
            'provider_user_id': provider_user_id
        })
        
        return self.log_authentication_event(
            event_type='oauth_login',
            user=user,
            request=request,
            success=True,
            additional_data=data
        )
    
    def log_suspicious_activity(self, user: Optional[EnhancedUser], request, 
                               activity_type: str, details: Dict):
        """Log suspicious activity"""
        data = {
            'activity_type': activity_type,
            'details': details
        }
        
        return self.log_authentication_event(
            event_type='suspicious_activity',
            user=user,
            request=request,
            success=False,
            additional_data=data
        )
    
    def get_user_audit_trail(self, user: EnhancedUser, days: int = 30) -> list:
        """Get audit trail for a specific user"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        return AuthenticationAuditLog.objects.filter(
            user=user,
            timestamp__gte=start_date
        ).order_by('-timestamp')
    
    def get_security_events(self, user: Optional[EnhancedUser] = None, 
                           days: int = 7) -> list:
        """Get recent security events"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        query = SecurityEvent.objects.filter(timestamp__gte=start_date)
        
        if user:
            query = query.filter(user=user)
        
        return query.order_by('-timestamp')
    
    def cleanup_old_logs(self):
        """Clean up old audit logs based on retention policy"""
        cutoff_date = timezone.now() - timezone.timedelta(days=self.retention_days)
        
        # Delete old audit logs
        audit_count = AuthenticationAuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if audit_count > 0:
            AuthenticationAuditLog.objects.filter(
                timestamp__lt=cutoff_date
            ).delete()
            
            logger.info(f"Cleaned up {audit_count} old audit log entries")
        
        # Delete old security events (keep for longer)
        security_cutoff = timezone.now() - timezone.timedelta(days=self.retention_days * 2)
        security_count = SecurityEvent.objects.filter(
            timestamp__lt=security_cutoff
        ).count()
        
        if security_count > 0:
            SecurityEvent.objects.filter(
                timestamp__lt=security_cutoff
            ).delete()
            
            logger.info(f"Cleaned up {security_count} old security event entries")
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _get_location_data(self, ip_address: str) -> Dict:
        """Get location data from IP address"""
        if not ip_address:
            return {}
        
        # Use the same GeoIP functionality as anomaly detector
        location = self.anomaly_detector._get_location_from_ip(ip_address)
        return location or {}
    
    def _log_to_standard_logger(self, audit_log: AuthenticationAuditLog):
        """Log to standard Python logger"""
        log_level = logging.WARNING if not audit_log.success or audit_log.flagged else logging.INFO
        
        log_message = (
            f"AUTH_EVENT: {audit_log.event_type} - "
            f"User: {audit_log.user.email if audit_log.user else 'Unknown'} - "
            f"IP: {audit_log.ip_address} - "
            f"Success: {audit_log.success} - "
            f"Risk: {audit_log.risk_score:.2f}"
        )
        
        extra_data = {
            'event_type': audit_log.event_type,
            'user_id': audit_log.user.id if audit_log.user else None,
            'ip_address': audit_log.ip_address,
            'success': audit_log.success,
            'risk_score': audit_log.risk_score,
            'flagged': audit_log.flagged,
            'timestamp': audit_log.timestamp.isoformat(),
        }
        
        logger.log(log_level, log_message, extra=extra_data)
    
    def _create_security_event(self, audit_log: AuthenticationAuditLog):
        """Create security event for high-risk audit logs"""
        try:
            # Determine event type and severity
            event_type = 'suspicious_pattern'
            severity = 'medium'
            
            if audit_log.risk_score > 0.9:
                severity = 'critical'
            elif audit_log.risk_score > 0.8:
                severity = 'high'
            
            # Check for specific anomaly types
            anomalies = audit_log.data.get('anomalies', [])
            if 'impossible_travel' in anomalies:
                event_type = 'impossible_travel'
                severity = 'high'
            elif 'brute_force_attempt' in anomalies:
                event_type = 'brute_force'
                severity = 'high'
            elif 'new_location' in anomalies:
                event_type = 'new_location'
            elif 'new_device' in anomalies:
                event_type = 'new_device'
            
            SecurityEvent.objects.create(
                user=audit_log.user,
                event_type=event_type,
                severity=severity,
                timestamp=audit_log.timestamp,
                ip_address=audit_log.ip_address,
                data={
                    'audit_log_id': audit_log.id,
                    'risk_score': audit_log.risk_score,
                    'anomalies': anomalies,
                    'event_details': audit_log.data,
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create security event: {str(e)}")
    
    def _trigger_security_alert(self, audit_log: AuthenticationAuditLog):
        """Trigger security alerts for critical events"""
        try:
            # This would integrate with your alerting system
            # Examples: email, SMS, Slack, PagerDuty, etc.
            
            alert_data = {
                'event_type': audit_log.event_type,
                'user': audit_log.user.email if audit_log.user else 'Unknown',
                'ip_address': audit_log.ip_address,
                'risk_score': audit_log.risk_score,
                'timestamp': audit_log.timestamp.isoformat(),
                'anomalies': audit_log.data.get('anomalies', []),
            }
            
            # Log critical alert
            logger.critical(
                f"SECURITY_ALERT: High-risk authentication event detected",
                extra=alert_data
            )
            
            # TODO: Implement actual alerting mechanisms
            # - Send email to security team
            # - Post to Slack security channel
            # - Create incident in monitoring system
            # - Send SMS to on-call personnel
            
        except Exception as e:
            logger.error(f"Failed to trigger security alert: {str(e)}")


class SecurityReporter:
    """
    Generate security reports from audit logs
    """
    
    def __init__(self):
        self.audit_logger = AuditLogger()
    
    def generate_user_security_report(self, user: EnhancedUser, days: int = 30) -> Dict:
        """Generate security report for a specific user"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get user's audit logs
        logs = AuthenticationAuditLog.objects.filter(
            user=user,
            timestamp__gte=start_date
        )
        
        # Calculate statistics
        total_events = logs.count()
        successful_logins = logs.filter(event_type='login_success').count()
        failed_logins = logs.filter(event_type='login_failure').count()
        high_risk_events = logs.filter(risk_score__gte=0.7).count()
        
        # Get unique locations and devices
        unique_countries = logs.exclude(country='').values_list('country', flat=True).distinct()
        unique_ips = logs.exclude(ip_address__isnull=True).values_list('ip_address', flat=True).distinct()
        
        # Get recent security events
        security_events = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=start_date
        ).order_by('-timestamp')[:10]
        
        return {
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.full_name,
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'days': days,
            },
            'statistics': {
                'total_events': total_events,
                'successful_logins': successful_logins,
                'failed_logins': failed_logins,
                'high_risk_events': high_risk_events,
                'unique_countries': len(unique_countries),
                'unique_ip_addresses': len(unique_ips),
            },
            'risk_assessment': {
                'average_risk_score': logs.aggregate(
                    avg_risk=models.Avg('risk_score')
                )['avg_risk'] or 0.0,
                'max_risk_score': logs.aggregate(
                    max_risk=models.Max('risk_score')
                )['max_risk'] or 0.0,
            },
            'security_events': [
                {
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'timestamp': event.timestamp.isoformat(),
                    'resolved': event.resolved,
                }
                for event in security_events
            ],
            'locations': list(unique_countries),
            'recommendations': self._generate_security_recommendations(user, logs),
        }
    
    def generate_system_security_report(self, days: int = 7) -> Dict:
        """Generate system-wide security report"""
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get system-wide statistics
        total_events = AuthenticationAuditLog.objects.filter(
            timestamp__gte=start_date
        ).count()
        
        failed_logins = AuthenticationAuditLog.objects.filter(
            event_type='login_failure',
            timestamp__gte=start_date
        ).count()
        
        high_risk_events = AuthenticationAuditLog.objects.filter(
            risk_score__gte=0.7,
            timestamp__gte=start_date
        ).count()
        
        # Get security events by severity
        security_events = SecurityEvent.objects.filter(
            timestamp__gte=start_date
        ).values('severity').annotate(count=models.Count('id'))
        
        # Get top attacking IPs
        top_attack_ips = AuthenticationAuditLog.objects.filter(
            event_type='login_failure',
            timestamp__gte=start_date
        ).values('ip_address').annotate(
            attempt_count=models.Count('id')
        ).order_by('-attempt_count')[:10]
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'days': days,
            },
            'statistics': {
                'total_events': total_events,
                'failed_logins': failed_logins,
                'high_risk_events': high_risk_events,
                'security_events_by_severity': {
                    event['severity']: event['count']
                    for event in security_events
                },
            },
            'threats': {
                'top_attacking_ips': [
                    {
                        'ip_address': ip['ip_address'],
                        'attempt_count': ip['attempt_count'],
                    }
                    for ip in top_attack_ips
                ],
            },
            'recommendations': self._generate_system_recommendations(),
        }
    
    def _generate_security_recommendations(self, user: EnhancedUser, logs) -> List[str]:
        """Generate personalized security recommendations"""
        recommendations = []
        
        # Check 2FA status
        if not user.is_two_factor_enabled:
            recommendations.append("Enable two-factor authentication for enhanced security")
        
        # Check for recent failed logins
        recent_failures = logs.filter(
            event_type='login_failure',
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        if recent_failures > 5:
            recommendations.append("Consider changing your password due to recent failed login attempts")
        
        # Check password age
        if user.password_changed_at:
            password_age = (timezone.now() - user.password_changed_at).days
            if password_age > 90:
                recommendations.append("Consider updating your password (current password is over 90 days old)")
        
        # Check for multiple locations
        unique_countries = logs.exclude(country='').values_list('country', flat=True).distinct()
        if len(unique_countries) > 3:
            recommendations.append("Review recent login locations and remove any unrecognized trusted devices")
        
        return recommendations
    
    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-wide security recommendations"""
        recommendations = [
            "Review and investigate high-risk authentication events",
            "Monitor top attacking IP addresses and consider blocking repeat offenders",
            "Ensure all users are encouraged to enable two-factor authentication",
            "Review security event patterns for potential coordinated attacks",
        ]
        
        return recommendations


# Global instances
audit_logger = AuditLogger()
security_reporter = SecurityReporter()