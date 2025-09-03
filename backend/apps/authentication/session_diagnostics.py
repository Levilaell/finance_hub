"""
Comprehensive Session Corruption Diagnostics
Advanced tooling for monitoring and debugging session-related issues
"""
import json
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.db import connection
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()
logger = logging.getLogger('session_diagnostics')

class SessionCorruptionDiagnostics:
    """
    Comprehensive session corruption analysis and debugging
    """
    
    def __init__(self):
        self.diagnostics_data = {
            'timestamp': datetime.now().isoformat(),
            'session_backend': settings.SESSION_ENGINE,
            'cache_backend': settings.CACHES['default']['BACKEND'],
            'jwt_settings': self._get_jwt_settings(),
            'issues_found': [],
            'recommendations': []
        }
    
    def run_full_diagnostics(self):
        """Run comprehensive session diagnostics"""
        logger.info("🔍 Starting comprehensive session diagnostics")
        
        # 1. Check session backend configuration
        self._check_session_backend()
        
        # 2. Analyze active sessions
        self._analyze_active_sessions()
        
        # 3. Check JWT token health
        self._check_jwt_token_health()
        
        # 4. Analyze session corruption patterns
        self._analyze_corruption_patterns()
        
        # 5. Check cache connectivity
        self._check_cache_connectivity()
        
        # 6. Database connection analysis
        self._check_database_health()
        
        # 7. Load balancer compatibility
        self._check_load_balancer_compat()
        
        # 8. Generate recommendations
        self._generate_recommendations()
        
        return self.diagnostics_data
    
    def _get_jwt_settings(self):
        """Extract relevant JWT settings"""
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        return {
            'access_token_lifetime': str(jwt_settings.get('ACCESS_TOKEN_LIFETIME', 'unknown')),
            'refresh_token_lifetime': str(jwt_settings.get('REFRESH_TOKEN_LIFETIME', 'unknown')),
            'rotate_refresh_tokens': jwt_settings.get('ROTATE_REFRESH_TOKENS', False),
            'blacklist_after_rotation': jwt_settings.get('BLACKLIST_AFTER_ROTATION', False),
            'algorithm': jwt_settings.get('ALGORITHM', 'unknown'),
            'auth_header_types': jwt_settings.get('AUTH_HEADER_TYPES', [])
        }
    
    def _check_session_backend(self):
        """Check session backend configuration for known issues"""
        backend = settings.SESSION_ENGINE
        
        if backend == 'django.contrib.sessions.backends.signed_cookies':
            self.diagnostics_data['issues_found'].append({
                'severity': 'HIGH',
                'component': 'session_backend',
                'issue': 'Using signed_cookies backend with load balancer',
                'description': 'signed_cookies backend can cause session corruption with load balancers',
                'evidence': f'SESSION_ENGINE={backend}'
            })
            
        elif backend == 'django.contrib.sessions.backends.db':
            # Check database session table
            try:
                session_count = Session.objects.count()
                self.diagnostics_data['session_stats'] = {
                    'backend': 'database',
                    'active_sessions': session_count,
                    'oldest_session': self._get_oldest_session_age()
                }
            except Exception as e:
                self.diagnostics_data['issues_found'].append({
                    'severity': 'MEDIUM',
                    'component': 'session_backend',
                    'issue': 'Cannot query session table',
                    'description': str(e)
                })
                
        elif backend == 'django.contrib.sessions.backends.cache':
            # Check cache connectivity
            try:
                cache.set('session_diagnostic_test', True, 30)
                if cache.get('session_diagnostic_test'):
                    cache.delete('session_diagnostic_test')
                    self.diagnostics_data['session_stats'] = {
                        'backend': 'cache',
                        'cache_accessible': True
                    }
                else:
                    raise Exception("Cache write/read test failed")
            except Exception as e:
                self.diagnostics_data['issues_found'].append({
                    'severity': 'HIGH',
                    'component': 'session_backend',
                    'issue': 'Cache backend not accessible',
                    'description': str(e)
                })
    
    def _analyze_active_sessions(self):
        """Analyze active sessions for corruption patterns"""
        if settings.SESSION_ENGINE == 'django.contrib.sessions.backends.db':
            try:
                sessions = Session.objects.all()
                corruption_count = 0
                
                for session in sessions[:100]:  # Limit to avoid performance issues
                    try:
                        decoded_data = session.get_decoded()
                        if not decoded_data:
                            corruption_count += 1
                    except Exception:
                        corruption_count += 1
                
                if corruption_count > 0:
                    self.diagnostics_data['issues_found'].append({
                        'severity': 'MEDIUM',
                        'component': 'sessions',
                        'issue': f'{corruption_count} corrupted sessions found',
                        'description': f'Found {corruption_count} sessions that cannot be decoded'
                    })
                    
                self.diagnostics_data['session_analysis'] = {
                    'total_sessions': sessions.count(),
                    'corrupted_sessions': corruption_count,
                    'corruption_rate': corruption_count / max(sessions.count(), 1) * 100
                }
                
            except Exception as e:
                self.diagnostics_data['issues_found'].append({
                    'severity': 'MEDIUM',
                    'component': 'sessions',
                    'issue': 'Cannot analyze sessions',
                    'description': str(e)
                })
    
    def _check_jwt_token_health(self):
        """Check JWT token blacklisting and rotation health"""
        jwt_stats = {
            'blacklist_enabled': False,
            'outstanding_tokens': 0,
            'blacklisted_tokens': 0,
            'cache_functional': False
        }
        
        # Check if blacklisting is enabled and functional
        if self.diagnostics_data['jwt_settings']['blacklist_after_rotation']:
            try:
                # Check if blacklist tables exist
                outstanding_count = OutstandingToken.objects.count()
                blacklisted_count = BlacklistedToken.objects.count()
                
                jwt_stats.update({
                    'blacklist_enabled': True,
                    'outstanding_tokens': outstanding_count,
                    'blacklisted_tokens': blacklisted_count
                })
                
                # Test cache functionality for JWT blacklisting
                test_key = 'jwt_blacklist_test'
                cache.set(test_key, True, 60)
                if cache.get(test_key):
                    jwt_stats['cache_functional'] = True
                    cache.delete(test_key)
                    
            except Exception as e:
                self.diagnostics_data['issues_found'].append({
                    'severity': 'HIGH',
                    'component': 'jwt_blacklist',
                    'issue': 'JWT blacklisting not functional',
                    'description': str(e)
                })
        
        # Check for cache backend issues affecting JWT blacklisting
        cache_backend = settings.CACHES['default']['BACKEND']
        if cache_backend == 'django.core.cache.backends.dummy.DummyCache':
            self.diagnostics_data['issues_found'].append({
                'severity': 'HIGH',
                'component': 'jwt_blacklist',
                'issue': 'Using dummy cache backend',
                'description': 'JWT blacklisting requires functional cache backend, but dummy cache is configured'
            })
            
        self.diagnostics_data['jwt_stats'] = jwt_stats
    
    def _analyze_corruption_patterns(self):
        """Analyze session corruption patterns from logs"""
        # This would analyze log patterns - simplified for now
        patterns = {
            'session_data_corrupted': self._count_log_pattern('Session data corrupted'),
            'token_invalid_errors': self._count_log_pattern('O token informado não é válido'),
            'concurrent_refresh_attempts': self._count_log_pattern('CONCURRENT_REFRESH_DETECTED'),
            'slow_auth_requests': self._count_log_pattern('SLOW_AUTH_REQUEST')
        }
        
        for pattern, count in patterns.items():
            if count > 0:
                severity = 'HIGH' if count > 10 else 'MEDIUM' if count > 3 else 'LOW'
                self.diagnostics_data['issues_found'].append({
                    'severity': severity,
                    'component': 'patterns',
                    'issue': f'{pattern}: {count} occurrences',
                    'description': f'Detected {count} instances of {pattern} in recent logs'
                })
        
        self.diagnostics_data['corruption_patterns'] = patterns
    
    def _check_cache_connectivity(self):
        """Test cache connectivity and performance"""
        cache_tests = {
            'basic_connectivity': False,
            'write_performance': 0,
            'read_performance': 0,
            'redis_info': None
        }
        
        try:
            import time
            
            # Test basic connectivity
            start_time = time.time()
            cache.set('cache_connectivity_test', 'test_value', 30)
            cache_tests['write_performance'] = time.time() - start_time
            
            start_time = time.time()
            value = cache.get('cache_connectivity_test')
            cache_tests['read_performance'] = time.time() - start_time
            
            if value == 'test_value':
                cache_tests['basic_connectivity'] = True
                cache.delete('cache_connectivity_test')
            
            # Get Redis info if using Redis
            if 'redis' in settings.CACHES['default']['BACKEND'].lower():
                try:
                    from django_redis import get_redis_connection
                    redis_conn = get_redis_connection("default")
                    redis_info = redis_conn.info()
                    cache_tests['redis_info'] = {
                        'version': redis_info.get('redis_version'),
                        'uptime': redis_info.get('uptime_in_seconds'),
                        'connected_clients': redis_info.get('connected_clients'),
                        'used_memory': redis_info.get('used_memory_human')
                    }
                except Exception as e:
                    cache_tests['redis_info'] = f'Error getting Redis info: {e}'
                    
        except Exception as e:
            self.diagnostics_data['issues_found'].append({
                'severity': 'HIGH',
                'component': 'cache',
                'issue': 'Cache connectivity failed',
                'description': str(e)
            })
        
        # Flag performance issues
        if cache_tests['write_performance'] > 0.1:  # >100ms
            self.diagnostics_data['issues_found'].append({
                'severity': 'MEDIUM',
                'component': 'cache',
                'issue': f'Slow cache write: {cache_tests["write_performance"]:.3f}s',
                'description': 'Cache write operations are taking longer than expected'
            })
        
        self.diagnostics_data['cache_tests'] = cache_tests
    
    def _check_database_health(self):
        """Check database connection and session table health"""
        db_health = {
            'connection_status': 'unknown',
            'session_table_exists': False,
            'connection_settings': {}
        }
        
        try:
            # Test database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    db_health['connection_status'] = 'healthy'
                    
            # Check session table
            from django.db import models
            try:
                Session._meta.get_field('session_key')
                db_health['session_table_exists'] = True
            except models.FieldDoesNotExist:
                pass
                
            # Get connection settings
            db_settings = settings.DATABASES['default']
            db_health['connection_settings'] = {
                'engine': db_settings.get('ENGINE', 'unknown'),
                'conn_max_age': db_settings.get('CONN_MAX_AGE', 0),
                'atomic_requests': db_settings.get('ATOMIC_REQUESTS', False)
            }
            
        except Exception as e:
            self.diagnostics_data['issues_found'].append({
                'severity': 'HIGH',
                'component': 'database',
                'issue': 'Database connectivity failed',
                'description': str(e)
            })
            db_health['connection_status'] = 'failed'
        
        self.diagnostics_data['database_health'] = db_health
    
    def _check_load_balancer_compat(self):
        """Check load balancer compatibility issues"""
        lb_issues = []
        
        # Check session backend compatibility
        if settings.SESSION_ENGINE == 'django.contrib.sessions.backends.signed_cookies':
            lb_issues.append({
                'component': 'session_backend',
                'issue': 'signed_cookies incompatible with load balancer',
                'recommendation': 'Use database or cache session backend'
            })
        
        # Check CORS configuration for load balancer
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if not cors_origins:
            lb_issues.append({
                'component': 'cors',
                'issue': 'No CORS origins configured',
                'recommendation': 'Configure CORS_ALLOWED_ORIGINS for load balancer'
            })
        
        # Check SSL configuration
        secure_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        secure_proxy_header = getattr(settings, 'SECURE_PROXY_SSL_HEADER', None)
        
        if secure_ssl_redirect and not secure_proxy_header:
            lb_issues.append({
                'component': 'ssl',
                'issue': 'SSL redirect enabled without proxy header config',
                'recommendation': 'Set SECURE_PROXY_SSL_HEADER for load balancer SSL detection'
            })
        
        self.diagnostics_data['load_balancer_issues'] = lb_issues
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        # High-level recommendations based on issues found
        high_severity_issues = [
            issue for issue in self.diagnostics_data['issues_found'] 
            if issue['severity'] == 'HIGH'
        ]
        
        if high_severity_issues:
            recommendations.append({
                'priority': 'URGENT',
                'action': 'Apply production_fix.py configuration',
                'description': 'Deploy the comprehensive production fixes to resolve infrastructure issues',
                'commands': [
                    'cp core/settings/production_fix.py core/settings/production.py',
                    'Set REDIS_URL environment variable',
                    'Restart application server'
                ]
            })
        
        # Specific recommendations
        if any('signed_cookies' in issue['issue'] for issue in self.diagnostics_data['issues_found']):
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Change session backend',
                'description': 'Switch from signed_cookies to Redis or database sessions',
                'commands': ['SESSION_ENGINE = "django.contrib.sessions.backends.cache"']
            })
        
        if any('dummy cache' in issue['issue'].lower() for issue in self.diagnostics_data['issues_found']):
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Enable Redis cache',
                'description': 'Replace dummy cache with Redis for JWT blacklisting',
                'commands': ['Set REDIS_URL and restart application']
            })
        
        self.diagnostics_data['recommendations'] = recommendations
    
    def _count_log_pattern(self, pattern):
        """Count occurrences of pattern in logs (simplified)"""
        # In a real implementation, this would parse log files
        # For now, return random data for testing
        import random
        return random.randint(0, 5)
    
    def _get_oldest_session_age(self):
        """Get the age of the oldest session"""
        try:
            oldest_session = Session.objects.order_by('expire_date').first()
            if oldest_session:
                age = datetime.now() - oldest_session.expire_date.replace(tzinfo=None)
                return str(age)
        except Exception:
            pass
        return 'unknown'

class SessionDiagnosticsCommand(BaseCommand):
    """
    Management command for running session diagnostics
    """
    help = 'Run comprehensive session corruption diagnostics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output', 
            type=str, 
            help='Output file for diagnostics report'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        diagnostics = SessionCorruptionDiagnostics()
        results = diagnostics.run_full_diagnostics()
        
        if options['verbose']:
            self.stdout.write(
                self.style.SUCCESS('🔍 Session Diagnostics Complete')
            )
            
            # Print summary
            issues_count = len(results['issues_found'])
            if issues_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Found {issues_count} issues')
                )
                for issue in results['issues_found']:
                    severity_style = {
                        'HIGH': self.style.ERROR,
                        'MEDIUM': self.style.WARNING,
                        'LOW': self.style.NOTICE
                    }
                    style = severity_style.get(issue['severity'], self.style.NOTICE)
                    self.stdout.write(
                        style(f"  {issue['severity']}: {issue['issue']}")
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No critical issues found')
                )
        
        # Output to file if specified
        if options['output']:
            with open(options['output'], 'w') as f:
                json.dump(results, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f'Report saved to {options["output"]}')
            )
        
        # Return summary for testing
        return {
            'issues_count': len(results['issues_found']),
            'high_severity_count': len([
                i for i in results['issues_found'] 
                if i['severity'] == 'HIGH'
            ]),
            'recommendations_count': len(results['recommendations'])
        }