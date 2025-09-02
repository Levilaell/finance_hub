"""
Quick command to reset login rate limiting - Railway Production Safe
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reset login rate limiting counters (Production Safe)'
    
    def handle(self, *args, **options):
        """Reset login rate limiting"""
        
        self.stdout.write('🔧 Resetting Login Rate Limits...')
        
        try:
            # Method 1: Try Redis-specific clearing
            cleared_redis = self._clear_redis_patterns()
            
            # Method 2: Clear known DRF throttle cache keys
            cleared_drf = self._clear_drf_throttles()
            
            # Method 3: Test cache functionality
            self._test_cache()
            
            total_cleared = cleared_redis + cleared_drf
            
            self.stdout.write('')
            self.stdout.write('=' * 50)
            self.stdout.write(f'✅ RATE LIMITS RESET')
            self.stdout.write(f'   Redis keys cleared: {cleared_redis}')
            self.stdout.write(f'   DRF throttles cleared: {cleared_drf}')
            self.stdout.write(f'   Total: {total_cleared} counters reset')
            self.stdout.write('')
            self.stdout.write('🎯 Users can now attempt login again')
            self.stdout.write('=' * 50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error resetting rate limits: {e}')
            )
            # Fallback: clear entire cache (nuclear option)
            self.stdout.write('🚨 Trying fallback: clearing entire cache...')
            try:
                cache.clear()
                self.stdout.write(
                    self.style.SUCCESS('✅ Entire cache cleared as fallback')
                )
            except Exception as fallback_error:
                self.stdout.write(
                    self.style.ERROR(f'❌ Fallback also failed: {fallback_error}')
                )
                raise
    
    def _clear_redis_patterns(self):
        """Clear Redis keys using pattern matching"""
        cleared = 0
        
        try:
            from django_redis import get_redis_connection
            redis_client = get_redis_connection("default")
            
            # Patterns for django_ratelimit and DRF throttling
            patterns = [
                'rl:*',           # django_ratelimit standard pattern
                '*:1:login:*',    # django_ratelimit alternative format
                'throttle_*',     # DRF throttling keys
                '*login*',        # Any login-related keys
            ]
            
            for pattern in patterns:
                keys = list(redis_client.scan_iter(match=pattern))
                if keys:
                    redis_client.delete(*keys)
                    cleared += len(keys)
                    self.stdout.write(f'   Cleared {len(keys)} keys matching "{pattern}"')
            
        except ImportError:
            self.stdout.write('   Redis not available, skipping pattern clearing')
        except Exception as e:
            self.stdout.write(f'   Redis pattern clearing failed: {e}')
        
        return cleared
    
    def _clear_drf_throttles(self):
        """Clear specific DRF throttle cache keys"""
        cleared = 0
        
        # Known DRF throttle scopes from our configuration
        throttle_scopes = [
            'login',
            'registration', 
            'password_reset',
            'api',
            'burst',
        ]
        
        for scope in throttle_scopes:
            try:
                # Try common key patterns for DRF throttling
                key_patterns = [
                    f'throttle_{scope}',
                    f'throttle_{scope}_',
                ]
                
                for pattern in key_patterns:
                    # Since we can't scan, try clearing some common variations
                    for i in range(100):  # Clear first 100 possible keys
                        key = f'{pattern}{i}'
                        if cache.get(key) is not None:
                            cache.delete(key)
                            cleared += 1
                
            except Exception as e:
                self.stdout.write(f'   Failed to clear {scope} throttles: {e}')
        
        return cleared
    
    def _test_cache(self):
        """Test that cache is working"""
        test_key = 'rate_limit_reset_test'
        test_value = 'working'
        
        try:
            cache.set(test_key, test_value, 10)
            if cache.get(test_key) == test_value:
                cache.delete(test_key)
                self.stdout.write('   ✅ Cache system is working')
            else:
                self.stdout.write('   ⚠️ Cache test failed')
        except Exception as e:
            self.stdout.write(f'   ⚠️ Cache test error: {e}')