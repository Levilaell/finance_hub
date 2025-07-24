"""
Test Pluggy integration
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.banking.pluggy_client import PluggyClient
import json


class Command(BaseCommand):
    help = 'Test Pluggy API integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-banks',
            action='store_true',
            help='List available banks'
        )
        parser.add_argument(
            '--create-token',
            action='store_true',
            help='Create a connect token'
        )
        parser.add_argument(
            '--sandbox',
            action='store_true',
            default=True,
            help='Use sandbox mode'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Pluggy integration...'))
        
        # Check configuration
        if not settings.PLUGGY_CLIENT_ID or not settings.PLUGGY_CLIENT_SECRET:
            self.stdout.write(
                self.style.ERROR(
                    'PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET must be set in environment variables'
                )
            )
            return
        
        try:
            client = PluggyClient()
            
            if options['list_banks']:
                self.stdout.write(self.style.SUCCESS('\nFetching available banks...'))
                connectors = client.get_connectors(
                    country='BR',
                    sandbox=options['sandbox']
                )
                
                self.stdout.write(f'\nFound {len(connectors)} connectors:')
                
                # Filter only bank connectors
                banks = [c for c in connectors if c.get('type') == 'PERSONAL_BANK']
                
                for bank in banks[:10]:  # Show first 10
                    self.stdout.write(
                        f"\n{bank['name']} (ID: {bank['id']})"
                        f"\n  Sandbox: {bank.get('sandbox', False)}"
                        f"\n  OAuth: {bank.get('oauth', False)}"
                        f"\n  Open Finance: {bank.get('openFinance', False)}"
                    )
                
                if len(banks) > 10:
                    self.stdout.write(f'\n... and {len(banks) - 10} more banks')
            
            if options['create_token']:
                self.stdout.write(self.style.SUCCESS('\nCreating connect token...'))
                token_data = client.create_connect_token()
                
                self.stdout.write(
                    f"\n✅ Connect token created successfully!"
                    f"\n\nToken: {token_data['accessToken'][:20]}..."
                    f"\n\nConnect URL: {token_data['connectUrl']}"
                )
                
                if settings.PLUGGY_USE_SANDBOX:
                    self.stdout.write(
                        self.style.WARNING(
                            '\n⚠️  Sandbox mode is enabled. Use these test credentials:'
                            '\n  User: user-ok'
                            '\n  Password: password-ok'
                            '\n  2FA Token: 123456'
                        )
                    )
            
            # Test API key creation
            if not options['list_banks'] and not options['create_token']:
                self.stdout.write('\nTesting API authentication...')
                api_key = client._get_api_key()
                self.stdout.write(self.style.SUCCESS('✅ API authentication successful!'))
                
                self.stdout.write(
                    f"\nPluggy configuration:"
                    f"\n  Base URL: {client.base_url}"
                    f"\n  Sandbox: {client.use_sandbox}"
                    f"\n  Client ID: {client.client_id[:10]}..."
                )
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
            
            # Additional debug info
            import traceback
            self.stdout.write(self.style.ERROR('\nTraceback:'))
            self.stdout.write(traceback.format_exc())