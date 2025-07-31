"""
Management command to clean up old audit logs
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.authentication.models_enhanced import AuthenticationAuditLog, SecurityEvent
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old authentication audit logs and security events'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 365),
            help='Number of days to retain audit logs (default: 365)',
        )
        parser.add_argument(
            '--security-days',
            type=int,
            default=getattr(settings, 'SECURITY_EVENT_RETENTION_DAYS', 730),
            help='Number of days to retain security events (default: 730)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to delete in each batch',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        security_days = options['security_days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        audit_cutoff = timezone.now() - timezone.timedelta(days=days)
        security_cutoff = timezone.now() - timezone.timedelta(days=security_days)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting cleanup (dry_run={dry_run})'
            )
        )
        self.stdout.write(f'Audit log cutoff: {audit_cutoff}')
        self.stdout.write(f'Security event cutoff: {security_cutoff}')
        
        # Clean up audit logs
        audit_total = self.cleanup_audit_logs(audit_cutoff, dry_run, batch_size)
        
        # Clean up security events
        security_total = self.cleanup_security_events(security_cutoff, dry_run, batch_size)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleanup completed: {audit_total} audit logs, {security_total} security events'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no records were actually deleted')
            )
    
    def cleanup_audit_logs(self, cutoff_date, dry_run, batch_size):
        """Clean up old audit logs"""
        self.stdout.write('Cleaning up audit logs...')
        
        # Count total records to delete
        total_count = AuthenticationAuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if total_count == 0:
            self.stdout.write('No old audit logs to clean up')
            return 0
        
        self.stdout.write(f'Found {total_count} audit logs to delete')
        
        if dry_run:
            return total_count
        
        # Delete in batches to avoid memory issues
        deleted_total = 0
        
        while True:
            # Get batch of IDs to delete
            ids_to_delete = list(
                AuthenticationAuditLog.objects.filter(
                    timestamp__lt=cutoff_date
                ).values_list('id', flat=True)[:batch_size]
            )
            
            if not ids_to_delete:
                break
            
            # Delete batch
            deleted_count = AuthenticationAuditLog.objects.filter(
                id__in=ids_to_delete
            ).delete()[0]
            
            deleted_total += deleted_count
            
            self.stdout.write(f'Deleted {deleted_total}/{total_count} audit logs')
            
            # Break if we deleted fewer than batch size (last batch)
            if len(ids_to_delete) < batch_size:
                break
        
        return deleted_total
    
    def cleanup_security_events(self, cutoff_date, dry_run, batch_size):
        """Clean up old security events"""
        self.stdout.write('Cleaning up security events...')
        
        # Count total records to delete (keep unresolved events longer)
        total_count = SecurityEvent.objects.filter(
            timestamp__lt=cutoff_date,
            resolved=True  # Only delete resolved events
        ).count()
        
        if total_count == 0:
            self.stdout.write('No old security events to clean up')
            return 0
        
        self.stdout.write(f'Found {total_count} resolved security events to delete')
        
        if dry_run:
            return total_count
        
        # Delete in batches
        deleted_total = 0
        
        while True:
            # Get batch of IDs to delete
            ids_to_delete = list(
                SecurityEvent.objects.filter(
                    timestamp__lt=cutoff_date,
                    resolved=True
                ).values_list('id', flat=True)[:batch_size]
            )
            
            if not ids_to_delete:
                break
            
            # Delete batch
            deleted_count = SecurityEvent.objects.filter(
                id__in=ids_to_delete
            ).delete()[0]
            
            deleted_total += deleted_count
            
            self.stdout.write(f'Deleted {deleted_total}/{total_count} security events')
            
            # Break if we deleted fewer than batch size (last batch)
            if len(ids_to_delete) < batch_size:
                break
        
        return deleted_total