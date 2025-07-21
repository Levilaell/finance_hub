"""
Django management command to fix webhook sync issues
"""
from django.core.management.base import BaseCommand
from django.db import transaction
import re


class Command(BaseCommand):
    help = 'Fix webhook sync method call issue'

    def handle(self, *args, **options):
        """Fix the webhook sync issue"""
        
        self.stdout.write("Fixing webhook sync method call...")
        
        # Read the file
        file_path = '/Users/levilaell/Desktop/finance_hub/backend/apps/banking/pluggy_views.py'
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if the issue exists
            if 'await sync_service.sync_account(account.id)' in content:
                # Fix the method call
                fixed_content = content.replace(
                    'await sync_service.sync_account(account.id)',
                    'await sync_service.sync_account_transactions(account)'
                )
                
                # Write back
                with open(file_path, 'w') as f:
                    f.write(fixed_content)
                
                self.stdout.write(self.style.SUCCESS('✅ Fixed webhook sync method call'))
                self.stdout.write('Changed: sync_account(account.id) -> sync_account_transactions(account)')
            else:
                self.stdout.write(self.style.WARNING('Issue not found or already fixed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fixing webhook: {e}'))