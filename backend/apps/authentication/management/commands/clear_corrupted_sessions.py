"""
Management command to clear corrupted sessions causing login issues
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.sessions.models import Session
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clear corrupted sessions causing login/logout issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleared without actually clearing',
        )
    
    def handle(self, *args, **options):
        """Clear corrupted sessions"""
        
        dry_run = options['dry_run']
        
        self.stdout.write('🧹 Clearing Corrupted Sessions...')
        self.stdout.write('=' * 50)
        
        cleared_count = 0
        
        try:
            # Method 1: Clear cache-based sessions
            if dry_run:
                self.stdout.write('DRY RUN: Would clear cache-based sessions')
            else:
                # Clear session-related cache keys
                try:
                    from django_redis import get_redis_connection
                    redis_client = get_redis_connection("default")
                    
                    # Find session keys
                    session_keys = list(redis_client.scan_iter(match="*session*"))
                    if session_keys:
                        redis_client.delete(*session_keys)
                        cleared_count += len(session_keys)
                        self.stdout.write(f'   Cleared {len(session_keys)} Redis session keys')
                    else:
                        self.stdout.write('   No Redis session keys found')
                        
                except ImportError:
                    self.stdout.write('   Redis not available, using Django cache')
                    # Fallback to Django cache clear
                    cache.clear()
                    self.stdout.write('   Cleared entire Django cache')
                    cleared_count += 1
            
            # Method 2: Clear database sessions (if using database backend)
            try:
                if dry_run:
                    session_count = Session.objects.count()
                    self.stdout.write(f'DRY RUN: Would clear {session_count} database sessions')
                else:
                    deleted = Session.objects.all().delete()
                    if deleted[0] > 0:
                        cleared_count += deleted[0]
                        self.stdout.write(f'   Cleared {deleted[0]} database sessions')
                    else:
                        self.stdout.write('   No database sessions found')
            except Exception as e:
                self.stdout.write(f'   Database session clearing failed: {e}')
            
            # Summary
            self.stdout.write('')
            self.stdout.write('=' * 50)
            if dry_run:
                self.stdout.write('🔍 DRY RUN COMPLETE')
                self.stdout.write('   No actual changes made')
            else:
                self.stdout.write(f'✅ SESSION CLEANUP COMPLETE')
                self.stdout.write(f'   Total items cleared: {cleared_count}')
                self.stdout.write('')
                self.stdout.write('🎯 Benefits:')
                self.stdout.write('   - Login/logout issues should be resolved')
                self.stdout.write('   - "Session data corrupted" warnings eliminated')
                self.stdout.write('   - Users will need to login again (expected)')
            self.stdout.write('=' * 50)
            
        except Exception as e:
            logger.error(f"Failed to clear sessions: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'❌ Error clearing sessions: {e}')
            )