"""
Smart anomaly detection for authentication security
"""
from django.utils import timezone
from django.conf import settings
from geopy.distance import geodesic
import geoip2.database
import geoip2.errors
from typing import Dict, List, Optional, Tuple
import math
import logging
from ..models_enhanced import SecurityEvent, AuthenticationAuditLog
import hashlib

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalous authentication patterns
    """
    
    def __init__(self):
        self.geoip_db_path = getattr(settings, 'GEOIP_PATH', None)
        self.geoip_reader = None
        
        if self.geoip_db_path:
            try:
                self.geoip_reader = geoip2.database.Reader(self.geoip_db_path)
            except Exception as e:
                logger.warning(f"Could not initialize GeoIP reader: {e}")
    
    def analyze_login_attempt(self, user, request, success: bool) -> Dict:
        """
        Analyze a login attempt for anomalies
        Returns anomaly analysis results
        """
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        location = self._get_location_from_ip(ip_address)
        
        anomalies = {
            'risk_score': 0.0,
            'anomalies': [],
            'location': location,
            'device_fingerprint': self._generate_device_fingerprint(request),
        }
        
        # Check for new device
        if self._is_new_device(user, user_agent):
            anomalies['anomalies'].append('new_device')
            anomalies['risk_score'] += 0.3
        
        # Check for new location
        if location and self._is_new_location(user, location):
            anomalies['anomalies'].append('new_location')
            anomalies['risk_score'] += 0.4
        
        # Check for impossible travel
        if location and self._check_impossible_travel(user, location):
            anomalies['anomalies'].append('impossible_travel')
            anomalies['risk_score'] += 0.8
        
        # Check for suspicious timing patterns
        if self._check_suspicious_timing(user):
            anomalies['anomalies'].append('suspicious_timing')
            anomalies['risk_score'] += 0.2
        
        # Check for TOR/VPN usage
        if self._check_tor_vpn(ip_address, user_agent):
            anomalies['anomalies'].append('tor_vpn_usage')
            anomalies['risk_score'] += 0.3
        
        # Check for brute force patterns
        if not success and self._check_brute_force_pattern(ip_address):
            anomalies['anomalies'].append('brute_force_attempt')
            anomalies['risk_score'] += 0.5
        
        # Account-specific checks
        if user:
            # Check account age
            account_age_days = (timezone.now() - user.created_at).days
            if account_age_days < 1:
                anomalies['risk_score'] += 0.2
            elif account_age_days < 7:
                anomalies['risk_score'] += 0.1
            
            # Check password age
            if user.password_changed_at:
                password_age_days = (timezone.now() - user.password_changed_at).days
                if password_age_days > 90:
                    anomalies['risk_score'] += 0.1
        
        # Normalize risk score
        anomalies['risk_score'] = min(anomalies['risk_score'], 1.0)
        
        # Log high-risk events
        if anomalies['risk_score'] > 0.7:
            self._create_security_event(user, 'suspicious_pattern', 'high', {
                'anomalies': anomalies['anomalies'],
                'risk_score': anomalies['risk_score'],
                'ip_address': ip_address,
                'location': location,
            })
        
        return anomalies
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _get_location_from_ip(self, ip_address: str) -> Optional[Dict]:
        """Get geographic location from IP address"""
        if not self.geoip_reader or not ip_address:
            return None
        
        try:
            response = self.geoip_reader.city(ip_address)
            return {
                'country': response.country.iso_code,
                'country_name': response.country.name,
                'city': response.city.name,
                'latitude': float(response.location.latitude) if response.location.latitude else None,
                'longitude': float(response.location.longitude) if response.location.longitude else None,
            }
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception as e:
            logger.error(f"GeoIP lookup error: {e}")
            return None
    
    def _generate_device_fingerprint(self, request) -> str:
        """Generate device fingerprint from request headers"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def _is_new_device(self, user, user_agent: str) -> bool:
        """Check if this is a new device for the user"""
        if not user or not user_agent:
            return False
        
        # Simple check based on user agent
        recent_logins = AuthenticationAuditLog.objects.filter(
            user=user,
            event_type='login_success',
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        ).values_list('data', flat=True)
        
        for login_data in recent_logins:
            if isinstance(login_data, dict):
                if login_data.get('user_agent') == user_agent:
                    return False
        
        return True
    
    def _is_new_location(self, user, location: Dict) -> bool:
        """Check if this is a new location for the user"""
        if not user or not location or not location.get('country'):
            return False
        
        # Check known countries from successful logins
        known_countries = AuthenticationAuditLog.objects.filter(
            user=user,
            event_type='login_success',
            timestamp__gte=timezone.now() - timezone.timedelta(days=90)
        ).values_list('country', flat=True).distinct()
        
        return location['country'] not in known_countries
    
    def _check_impossible_travel(self, user, current_location: Dict) -> bool:
        """Check for impossible travel between locations"""
        if not user or not current_location:
            return False
        
        # Get last known location within 6 hours
        recent_login = AuthenticationAuditLog.objects.filter(
            user=user,
            event_type='login_success',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=6),
            latitude__isnull=False,
            longitude__isnull=False
        ).order_by('-timestamp').first()
        
        if not recent_login:
            return False
        
        # Calculate distance and time
        last_location = (recent_login.latitude, recent_login.longitude)
        current_pos = (current_location.get('latitude'), current_location.get('longitude'))
        
        if not all([last_location[0], last_location[1], current_pos[0], current_pos[1]]):
            return False
        
        try:
            distance_km = geodesic(last_location, current_pos).kilometers
            time_hours = (timezone.now() - recent_login.timestamp).total_seconds() / 3600
            
            # Maximum reasonable travel speed: 1000 km/h (commercial flight)
            max_speed_kmh = 1000
            
            if time_hours > 0 and distance_km / time_hours > max_speed_kmh:
                logger.warning(
                    f"Impossible travel detected for user {user.email}: "
                    f"{distance_km:.0f}km in {time_hours:.1f}h "
                    f"({distance_km/time_hours:.0f} km/h)"
                )
                return True
        
        except Exception as e:
            logger.error(f"Error calculating travel distance: {e}")
        
        return False
    
    def _check_suspicious_timing(self, user) -> bool:
        """Check for suspicious timing patterns"""
        if not user:
            return False
        
        # Check for login attempts at unusual hours
        current_hour = timezone.now().hour
        
        # Get user's typical login hours from history
        recent_logins = AuthenticationAuditLog.objects.filter(
            user=user,
            event_type='login_success',
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        ).values_list('timestamp', flat=True)
        
        if len(recent_logins) < 5:
            return False  # Not enough data
        
        typical_hours = [login.hour for login in recent_logins]
        
        # Calculate if current hour is unusual (outside of typical +/- 3 hours)
        typical_range = set()
        for hour in set(typical_hours):
            for offset in range(-3, 4):
                typical_range.add((hour + offset) % 24)
        
        return current_hour not in typical_range
    
    def _check_tor_vpn(self, ip_address: str, user_agent: str) -> bool:
        """Check for TOR/VPN usage indicators"""
        # Simple heuristics - in production, use specialized services
        tor_indicators = [
            'tor browser',
            'torbrowser',
        ]
        
        vpn_indicators = [
            'nordvpn',
            'expressvpn',
            'surfshark',
        ]
        
        user_agent_lower = user_agent.lower()
        
        for indicator in tor_indicators + vpn_indicators:
            if indicator in user_agent_lower:
                return True
        
        # TODO: Integrate with TOR exit node lists and VPN IP ranges
        return False
    
    def _check_brute_force_pattern(self, ip_address: str) -> bool:
        """Check for brute force attack patterns"""
        # Check for multiple failed attempts from same IP
        recent_failures = AuthenticationAuditLog.objects.filter(
            ip_address=ip_address,
            event_type='login_failure',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        
        # Also check for attempts against multiple accounts
        distinct_users = AuthenticationAuditLog.objects.filter(
            ip_address=ip_address,
            event_type='login_failure',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=1)
        ).values('user').distinct().count()
        
        # Indicators of brute force
        if recent_failures > 10 or distinct_users > 5:
            return True
        
        return False
    
    def _create_security_event(self, user, event_type: str, severity: str, data: Dict):
        """Create a security event record"""
        SecurityEvent.objects.create(
            user=user,
            event_type=event_type,
            severity=severity,
            data=data,
            ip_address=data.get('ip_address')
        )


class LocationTracker:
    """
    Tracks and validates user locations
    """
    
    def __init__(self):
        self.detector = AnomalyDetector()
    
    def update_user_location(self, user, location: Dict):
        """Update user's known locations"""
        if not location or not user:
            return
        
        # Add to known networks if not already there
        known_networks = user.known_networks or []
        
        location_key = f"{location.get('country')}:{location.get('city')}"
        if location_key not in known_networks:
            known_networks.append(location_key)
            user.known_networks = known_networks
            user.save()
    
    def is_trusted_location(self, user, location: Dict) -> bool:
        """Check if this is a trusted location for the user"""
        if not location or not user:
            return False
        
        location_key = f"{location.get('country')}:{location.get('city')}"
        return location_key in (user.known_networks or [])


class BehaviorAnalyzer:
    """
    Analyzes user behavior patterns for anomalies
    """
    
    def analyze_login_pattern(self, user) -> Dict:
        """Analyze user's login patterns"""
        if not user:
            return {'risk_score': 0.0, 'patterns': []}
        
        # Get login history
        logins = AuthenticationAuditLog.objects.filter(
            user=user,
            event_type='login_success',
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-timestamp')[:50]
        
        patterns = {
            'risk_score': 0.0,
            'patterns': [],
            'frequency': self._analyze_frequency(logins),
            'timing': self._analyze_timing(logins),
            'locations': self._analyze_locations(logins),
        }
        
        return patterns
    
    def _analyze_frequency(self, logins) -> Dict:
        """Analyze login frequency patterns"""
        if len(logins) < 7:
            return {'status': 'insufficient_data'}
        
        # Calculate average daily logins
        days = (logins[0].timestamp - logins[-1].timestamp).days or 1
        avg_daily = len(logins) / days
        
        return {
            'avg_daily_logins': avg_daily,
            'total_logins': len(logins),
            'period_days': days,
        }
    
    def _analyze_timing(self, logins) -> Dict:
        """Analyze login timing patterns"""
        if len(logins) < 5:
            return {'status': 'insufficient_data'}
        
        hours = [login.timestamp.hour for login in logins]
        
        return {
            'common_hours': list(set(hours)),
            'hour_distribution': {hour: hours.count(hour) for hour in set(hours)},
        }
    
    def _analyze_locations(self, logins) -> Dict:
        """Analyze location patterns"""
        countries = [login.country for login in logins if login.country]
        cities = [login.city for login in logins if login.city]
        
        return {
            'countries': list(set(countries)),
            'cities': list(set(cities)),
            'location_count': len(set(countries + cities)),
        }


# Utility functions
def calculate_risk_score(factors: Dict) -> float:
    """Calculate overall risk score from various factors"""
    base_score = 0.0
    
    # Weight different factors
    weights = {
        'new_device': 0.3,
        'new_location': 0.4,
        'impossible_travel': 0.8,
        'suspicious_timing': 0.2,
        'tor_vpn_usage': 0.3,
        'brute_force_attempt': 0.5,
        'account_age_new': 0.2,
        'password_age_old': 0.1,
    }
    
    for factor, weight in weights.items():
        if factors.get(factor):
            base_score += weight
    
    return min(base_score, 1.0)


def should_require_additional_verification(risk_score: float, user=None) -> bool:
    """Determine if additional verification is required"""
    thresholds = {
        'low': 0.3,
        'medium': 0.5,
        'high': 0.7,
    }
    
    if risk_score >= thresholds['high']:
        return True
    
    if risk_score >= thresholds['medium'] and user:
        # Additional checks for medium risk
        if not user.is_two_factor_enabled:
            return True
    
    return False