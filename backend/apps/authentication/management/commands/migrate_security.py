"""
Management command to migrate from basic to enhanced authentication security
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate from basic to enhanced authentication security'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to process in each batch'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if enhanced models are not ready'
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.batch_size = options['batch_size']
        self.force = options['force']
        
        self.stdout.write(self.style.SUCCESS('🔄 Starting Security Migration'))
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
        
        # Migrate users
        self._migrate_users()
        
        # Update settings
        self._update_settings()
        
        # Clean up old data
        if not self.dry_run:
            self._cleanup_old_data()
        
        self.stdout.write(self.style.SUCCESS('✅ Security migration completed'))
    
    def _check_prerequisites(self):
        """Check if migration prerequisites are met"""
        self.stdout.write('📋 Checking prerequisites...')
        
        # Check if enhanced models are available
        try:
            from apps.authentication.models_enhanced import EnhancedUser
            self.stdout.write('   ✅ Enhanced models available')
        except ImportError:
            if not self.force:
                self.stdout.write(
                    self.style.ERROR('❌ Enhanced models not available. Use --force to skip this check.')
                )
                return False
            self.stdout.write('   ⚠️  Enhanced models not available (forced)')
        
        # Check database migrations
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='auth_enhanced_users';"
                )
                if cursor.fetchone():
                    self.stdout.write('   ✅ Enhanced user table exists')
                else:
                    self.stdout.write('   ⚠️  Enhanced user table not found')
        except Exception as e:
            self.stdout.write(f'   ⚠️  Could not check database: {e}')
        
        # Check for existing security components
        security_components = [
            'apps.authentication.security.rate_limiting',
            'apps.authentication.security.password_policies',
            'apps.authentication.security.session_management',
        ]
        
        for component in security_components:
            try:
                __import__(component)
                self.stdout.write(f'   ✅ {component.split(".")[-1]}')
            except ImportError:
                if not self.force:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {component} not available')
                    )
                    return False
                self.stdout.write(f'   ⚠️  {component} not available (forced)')
        
        return True
    
    def _migrate_users(self):
        """Migrate user accounts to enhanced security"""
        self.stdout.write('👥 Migrating user accounts...')
        
        total_users = User.objects.count()
        self.stdout.write(f'   Found {total_users} users to migrate')
        
        migrated_count = 0
        error_count = 0
        
        # Process users in batches
        for offset in range(0, total_users, self.batch_size):
            users = User.objects.all()[offset:offset + self.batch_size]
            
            for user in users:
                try:
                    if self.dry_run:
                        self.stdout.write(f'   Would migrate: {user.email}')
                    else:
                        self._migrate_single_user(user)
                    
                    migrated_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f'Failed to migrate user {user.email}: {e}')
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Failed to migrate {user.email}: {e}')
                    )
        
        self.stdout.write(f'📊 Migration summary:')
        self.stdout.write(f'   ✅ Successfully migrated: {migrated_count}')
        if error_count > 0:
            self.stdout.write(f'   ❌ Errors: {error_count}')
    
    @transaction.atomic
    def _migrate_single_user(self, user):
        """Migrate a single user to enhanced security"""
        
        # Initialize security fields
        if not hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
        
        if not hasattr(user, 'last_failed_login'):
            user.last_failed_login = None
        
        if not hasattr(user, 'is_locked'):
            user.is_locked = False
        
        if not hasattr(user, 'locked_until'):
            user.locked_until = None
        
        if not hasattr(user, 'password_changed_at'):
            user.password_changed_at = user.date_joined or timezone.now()
        
        if not hasattr(user, 'password_history'):
            user.password_history = []
        
        if not hasattr(user, 'active_sessions'):
            user.active_sessions = {}
        
        if not hasattr(user, 'trusted_devices'):
            user.trusted_devices = []
        
        if not hasattr(user, 'risk_score'):
            user.risk_score = 0.0
        
        # Initialize 2FA fields if not present
        if not hasattr(user, 'is_two_factor_enabled'):
            user.is_two_factor_enabled = False
        
        if not hasattr(user, 'two_factor_secret'):
            user.two_factor_secret = ''
        
        if not hasattr(user, 'backup_codes'):
            user.backup_codes = []
        
        # Save changes
        user.save()
        
        # Create initial audit log entry
        self._create_migration_audit_log(user)
    
    def _create_migration_audit_log(self, user):
        """Create audit log entry for migration"""
        try:
            from apps.authentication.models_enhanced import AuthenticationAuditLog
            
            AuthenticationAuditLog.objects.create(
                user=user,
                event_type='account_migrated',
                timestamp=timezone.now(),
                ip_address='127.0.0.1',
                data={'migrated_to': 'enhanced_security'},
                success=True
            )
        except ImportError:
            # Enhanced models not available
            pass
        except Exception as e:
            logger.warning(f'Could not create audit log for user {user.email}: {e}')
    
    def _update_settings(self):
        """Update Django settings for enhanced security"""
        self.stdout.write('⚙️  Updating settings...')
        
        settings_updates = {
            'AUTHENTICATION_BACKENDS': [
                'apps.authentication.backends.EnhancedAuthenticationBackend',
                'django.contrib.auth.backends.ModelBackend',
            ],
            'MIDDLEWARE_UPDATES': [
                'apps.authentication.middleware.SecurityMiddleware',
                'apps.authentication.middleware.SessionSecurityMiddleware',
                'apps.authentication.middleware.RequestLoggingMiddleware',
            ],
            'SIMPLE_JWT_UPDATES': {
                'ALGORITHM': 'RS256',
                'ACCESS_TOKEN_LIFETIME': '30 minutes',
                'REFRESH_TOKEN_LIFETIME': '3 days',
            }
        }
        
        settings_file_path = settings.BASE_DIR / 'core' / 'settings' / 'enhanced_security.py'
        
        if not self.dry_run:
            try:
                with open(settings_file_path, 'w') as f:
                    f.write('# Enhanced Security Settings\n')
                    f.write('# Generated by migrate_security command\n')
                    f.write(f'# Generated on: {timezone.now()}\n\n')
                    
                    f.write('# Enhanced Authentication Backend\n')
                    f.write('AUTHENTICATION_BACKENDS = [\n')
                    for backend in settings_updates['AUTHENTICATION_BACKENDS']:
                        f.write(f'    "{backend}",\n')
                    f.write(']\n\n')
                    
                    f.write('# Security Middleware (add to MIDDLEWARE list)\n')
                    f.write('SECURITY_MIDDLEWARE = [\n')
                    for middleware in settings_updates['MIDDLEWARE_UPDATES']:
                        f.write(f'    "{middleware}",\n')
                    f.write(']\n\n')
                    
                    f.write('# Enhanced JWT Settings\n')
                    f.write('from datetime import timedelta\n')
                    f.write('SIMPLE_JWT.update({\n')
                    f.write('    "ALGORITHM": "RS256",\n')
                    f.write('    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),\n')
                    f.write('    "REFRESH_TOKEN_LIFETIME": timedelta(days=3),\n')
                    f.write('})\n\n')
                    
                    f.write('# Enhanced Security Settings\n')
                    f.write('AUTH_MAX_LOGIN_ATTEMPTS = 3\n')
                    f.write('AUTH_LOCKOUT_DURATION = 3600  # 1 hour\n')
                    f.write('MAX_SESSIONS_PER_USER = 3\n')
                    f.write('VALIDATE_SESSION_IP = False\n')
                
                self.stdout.write(f'   Created: {settings_file_path}')
                self.stdout.write('   ⚠️  Import this file in your settings to activate enhanced security')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create settings file: {e}')
                )
        else:
            self.stdout.write(f'   Would create: {settings_file_path}')
    
    def _cleanup_old_data(self):
        """Clean up old authentication data"""
        self.stdout.write('🧹 Cleaning up old data...')
        
        cleanup_tasks = [
            ('Expired password reset tokens', self._cleanup_expired_tokens),
            ('Expired email verification tokens', self._cleanup_expired_verifications),
            ('Old session data', self._cleanup_old_sessions),
        ]
        
        for task_name, task_func in cleanup_tasks:
            try:
                cleaned_count = task_func()
                self.stdout.write(f'   ✅ {task_name}: {cleaned_count} items cleaned')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {task_name}: {e}')
                )
    
    def _cleanup_expired_tokens(self):
        """Clean up expired password reset tokens"""
        from apps.authentication.models import PasswordReset
        
        expired_count = PasswordReset.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        if not self.dry_run:
            PasswordReset.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
        
        return expired_count
    
    def _cleanup_expired_verifications(self):
        """Clean up expired email verification tokens"""
        from apps.authentication.models import EmailVerification
        
        expired_count = EmailVerification.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        if not self.dry_run:
            EmailVerification.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
        
        return expired_count
    
    def _cleanup_old_sessions(self):
        """Clean up old session data"""
        from django.contrib.sessions.models import Session
        
        expired_count = Session.objects.filter(
            expire_date__lt=timezone.now()
        ).count()
        
        if not self.dry_run:
            Session.objects.filter(
                expire_date__lt=timezone.now()
            ).delete()
        
        return expired_count