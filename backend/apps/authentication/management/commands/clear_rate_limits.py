"""
Management command to clear rate limiting counters
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.core.cache.utils import make_key
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clear rate limiting counters from cache'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleared without actually clearing',
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Clear only keys matching this pattern (e.g., "rl:" for django_ratelimit)',
            default=None,
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all cache (WARNING: affects sessions, etc.)',
        )
    
    def handle(self, *args, **options):
        """Handle the clear rate limits command"""
        
        dry_run = options['dry_run']
        pattern = options['pattern']
        clear_all = options['all']
        
        self.stdout.write('🔧 Rate Limit Counter Cleaner')
        self.stdout.write('=' * 50)
        
        if clear_all:
            self.stdout.write(
                self.style.WARNING(
                    'WARNING: This will clear ALL cache including sessions!'
                )
            )
            if not dry_run:
                confirm = input('Are you sure? (type "yes" to confirm): ')
                if confirm != 'yes':
                    self.stdout.write('Operation cancelled.')
                    return
        
        try:
            if clear_all:
                if dry_run:
                    self.stdout.write('DRY RUN: Would clear entire cache')
                else:
                    cache.clear()
                    self.stdout.write(
                        self.style.SUCCESS('✅ Entire cache cleared')
                    )
            else:
                # Clear specific rate limiting patterns
                patterns_to_clear = []
                
                if pattern:
                    patterns_to_clear.append(pattern)
                else:
                    # Default patterns for rate limiting
                    patterns_to_clear = [
                        'rl:',          # django_ratelimit keys
                        'throttle_',    # DRF throttle keys
                        ':1:login:',    # Alternative django_ratelimit format
                    ]
                
                cleared_count = 0
                
                for pattern_str in patterns_to_clear:
                    if dry_run:
                        self.stdout.write(f'DRY RUN: Would clear keys matching "{pattern_str}"')
                    else:
                        count = self._clear_keys_by_pattern(pattern_str)
                        cleared_count += count
                        self.stdout.write(f'Cleared {count} keys matching "{pattern_str}"')
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Total keys cleared: {cleared_count}')
                    )
            
            # Test cache functionality
            test_key = 'rate_limit_cleaner_test'
            cache.set(test_key, 'test_value', 60)
            if cache.get(test_key) == 'test_value':
                cache.delete(test_key)
                self.stdout.write('✅ Cache is working properly')
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Cache test failed - may not be working')
                )
            
            if not dry_run:
                self.stdout.write('')
                self.stdout.write('Rate limiting counters have been reset.')
                self.stdout.write('Users should now be able to attempt login again.')
            
        except Exception as e:
            logger.error(f"Failed to clear rate limits: {str(e)}")
            raise CommandError(f'Failed to clear rate limits: {str(e)}')
    
    def _clear_keys_by_pattern(self, pattern):
        """
        Clear cache keys matching a pattern
        Note: This is a simplified version as Redis pattern matching 
        requires specific cache backend features
        """
        cleared_count = 0
        
        try:
            # Try to get the Redis client if using django_redis
            from django_redis import get_redis_connection
            redis_client = get_redis_connection("default")
            
            # Use Redis SCAN to find keys
            keys = redis_client.scan_iter(match=f"*{pattern}*")
            keys_list = list(keys)
            
            if keys_list:
                redis_client.delete(*keys_list)
                cleared_count = len(keys_list)
            
        except ImportError:
            # Fallback for non-Redis cache backends
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Pattern matching not available for this cache backend. '
                    f'Use --all to clear entire cache.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Pattern matching failed: {e}. '
                    f'Use --all to clear entire cache.'
                )
            )
        
        return cleared_count