"""
Management command to fix items stuck in UPDATING status
when they actually have SUCCESS execution status
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.banking.models import PluggyItem
from apps.banking.integrations.pluggy.client import PluggyClient, PluggyError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix items stuck in UPDATING status with SUCCESS execution'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--sync-with-api',
            action='store_true',
            help='Sync status with Pluggy API before fixing'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        sync_with_api = options['sync_with_api']
        
        self.stdout.write(self.style.SUCCESS('=== Fixing Stuck UPDATING Status ==='))
        
        # Find items stuck in UPDATING status
        stuck_items = PluggyItem.objects.filter(
            status='UPDATING'
        ).select_related('connector')
        
        self.stdout.write(f"Found {stuck_items.count()} items with UPDATING status")
        
        fixed_count = 0
        error_count = 0
        
        for item in stuck_items:
            try:
                self.stdout.write(f"\nChecking item {item.pluggy_item_id} ({item.connector.name}):")
                self.stdout.write(f"  Current status: {item.status}")
                self.stdout.write(f"  Execution status: {item.execution_status}")
                self.stdout.write(f"  Last update: {item.pluggy_updated_at}")
                
                # If sync with API is requested, get latest status
                if sync_with_api:
                    try:
                        with PluggyClient() as client:
                            item_data = client.get_item(item.pluggy_item_id)
                            
                            # Update from API
                            item.status = item_data['status']
                            item.execution_status = item_data.get('executionStatus', '')
                            item.pluggy_updated_at = item_data.get('updatedAt')
                            
                            if not dry_run:
                                item.save()
                            
                            self.stdout.write(f"  API status: {item_data['status']}")
                            self.stdout.write(f"  API execution: {item_data.get('executionStatus', 'N/A')}")
                            
                    except PluggyError as e:
                        self.stdout.write(self.style.ERROR(f"  Failed to sync with API: {e}"))
                
                # Check if should be fixed
                should_fix = False
                reason = ""
                
                if item.execution_status == 'SUCCESS':
                    should_fix = True
                    reason = "Execution status is SUCCESS"
                elif item.execution_status == 'PARTIAL_SUCCESS':
                    should_fix = True
                    reason = "Execution status is PARTIAL_SUCCESS"
                elif item.last_successful_update and item.last_successful_update > timezone.now() - timedelta(hours=24):
                    should_fix = True
                    reason = "Had successful update in last 24 hours"
                
                if should_fix:
                    self.stdout.write(self.style.WARNING(f"  Should fix: {reason}"))
                    
                    if not dry_run:
                        old_status = item.status
                        item.status = 'UPDATED'
                        item.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"  Fixed: {old_status} -> UPDATED"))
                        fixed_count += 1
                    else:
                        self.stdout.write(self.style.WARNING("  Would fix (dry run)"))
                else:
                    self.stdout.write("  No fix needed")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
                error_count += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        self.stdout.write(f"Total items checked: {stuck_items.count()}")
        self.stdout.write(f"Items fixed: {fixed_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes were made"))
            self.stdout.write("Run without --dry-run to apply fixes")