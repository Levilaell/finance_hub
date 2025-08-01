"""
Management command to rotate JWT keys
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.security import rotate_jwt_keys
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rotate JWT keys (generate new RSA keypair)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force key rotation without confirmation in production',
        )
    
    def handle(self, *args, **options):
        """Handle the key rotation command"""
        
        # Safety check for production
        if not settings.DEBUG and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    'This will invalidate all existing JWT tokens. '
                    'Use --force to confirm in production.'
                )
            )
            return
        
        try:
            self.stdout.write('Starting JWT key rotation...')
            
            # Perform key rotation
            rotate_jwt_keys()
            
            self.stdout.write(
                self.style.SUCCESS(
                    'JWT keys rotated successfully. '
                    'All existing tokens will be invalid and users will need to re-login.'
                )
            )
            
            # Log the key rotation for audit
            logger.info("JWT keys rotated via management command")
            
        except Exception as e:
            logger.error(f"JWT key rotation failed: {str(e)}")
            raise CommandError(f'Key rotation failed: {str(e)}')