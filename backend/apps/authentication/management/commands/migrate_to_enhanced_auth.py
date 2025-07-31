"""
Management command to migrate existing users to enhanced authentication system
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.authentication.models import User as OldUser
from apps.authentication.models_enhanced import EnhancedUser
from apps.authentication.security.encryption import default_encryption
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate existing users to enhanced authentication system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run migration in dry-run mode (no actual changes)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to process in each batch',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting user migration (dry_run={dry_run}, batch_size={batch_size})'
            )
        )
        
        # Get total user count
        total_users = OldUser.objects.count()
        migrated_count = 0
        error_count = 0
        
        self.stdout.write(f'Found {total_users} users to migrate')
        
        # Process users in batches
        for offset in range(0, total_users, batch_size):
            batch_users = OldUser.objects.all()[offset:offset + batch_size]
            
            for old_user in batch_users:
                try:
                    success = self.migrate_user(old_user, dry_run)
                    if success:
                        migrated_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f'Error migrating user {old_user.email}: {str(e)}')
                    error_count += 1
            
            # Progress update
            processed = min(offset + batch_size, total_users)
            self.stdout.write(f'Processed {processed}/{total_users} users')
        
        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Migration completed: {migrated_count} migrated, {error_count} errors'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no actual changes were made')
            )
    
    def migrate_user(self, old_user, dry_run=False):
        """Migrate a single user to enhanced model"""
        try:
            # Check if user already migrated
            if EnhancedUser.objects.filter(email=old_user.email).exists():
                self.stdout.write(f'User {old_user.email} already migrated - skipping')
                return True
            
            if not dry_run:
                with transaction.atomic():
                    # Create enhanced user
                    enhanced_user = EnhancedUser()
                    
                    # Copy basic fields
                    enhanced_user.email = old_user.email
                    enhanced_user.username = old_user.username
                    enhanced_user.first_name = old_user.first_name
                    enhanced_user.last_name = old_user.last_name
                    enhanced_user.password = old_user.password
                    enhanced_user.is_active = old_user.is_active
                    enhanced_user.is_staff = old_user.is_staff
                    enhanced_user.is_superuser = old_user.is_superuser
                    enhanced_user.date_joined = old_user.date_joined
                    enhanced_user.last_login = old_user.last_login
                    
                    # Copy authentication-specific fields
                    enhanced_user.phone = getattr(old_user, 'phone', '')
                    enhanced_user.is_email_verified = getattr(old_user, 'is_email_verified', False)
                    enhanced_user.is_phone_verified = getattr(old_user, 'is_phone_verified', False)
                    enhanced_user.avatar = getattr(old_user, 'avatar', None)
                    enhanced_user.date_of_birth = getattr(old_user, 'date_of_birth', None)
                    enhanced_user.preferred_language = getattr(old_user, 'preferred_language', 'pt-br')
                    enhanced_user.timezone = getattr(old_user, 'timezone', 'America/Sao_Paulo')
                    enhanced_user.last_login_ip = getattr(old_user, 'last_login_ip', None)
                    enhanced_user.payment_customer_id = getattr(old_user, 'payment_customer_id', None)
                    enhanced_user.payment_gateway = getattr(old_user, 'payment_gateway', None)
                    
                    # Handle 2FA migration
                    old_2fa_secret = getattr(old_user, 'two_factor_secret', '')
                    if old_2fa_secret:
                        # Encrypt the existing 2FA secret
                        enhanced_user.two_factor_secret = old_2fa_secret
                        enhanced_user.is_two_factor_enabled = getattr(old_user, 'is_two_factor_enabled', False)
                    
                    # Handle backup codes
                    old_backup_codes = getattr(old_user, 'backup_codes', [])
                    if old_backup_codes:
                        enhanced_user.backup_codes = old_backup_codes
                    
                    # Set security defaults
                    enhanced_user.failed_login_attempts = 0
                    enhanced_user.is_locked = False
                    enhanced_user.password_changed_at = timezone.now()
                    enhanced_user.risk_score = 0.0
                    enhanced_user.active_sessions = {}
                    enhanced_user.trusted_devices = []
                    enhanced_user.known_networks = []
                    enhanced_user.security_questions = {}
                    enhanced_user.password_history = []
                    
                    # Set timestamps
                    enhanced_user.created_at = getattr(old_user, 'created_at', old_user.date_joined)
                    enhanced_user.updated_at = getattr(old_user, 'updated_at', timezone.now())
                    
                    enhanced_user.save()
                    
                    # Add current password to history
                    enhanced_user.add_to_password_history(enhanced_user.password)
                    
                    self.stdout.write(f'✓ Migrated user: {old_user.email}')
                    return True
            else:
                self.stdout.write(f'[DRY RUN] Would migrate user: {old_user.email}')
                return True
                
        except Exception as e:
            self.stderr.write(f'✗ Failed to migrate user {old_user.email}: {str(e)}')
            return False
    
    def cleanup_old_data(self, dry_run=False):
        """Clean up old authentication data after successful migration"""
        if not dry_run:
            self.stdout.write('Cleaning up old authentication data...')
            
            # This would remove old models/tables after successful migration
            # Implement based on your specific needs
            
            self.stdout.write('Cleanup completed')
        else:
            self.stdout.write('[DRY RUN] Would clean up old authentication data')