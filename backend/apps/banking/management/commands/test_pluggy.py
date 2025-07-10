"""
Django management command to test Pluggy integration
"""
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.banking.pluggy_client import PluggyClient


class Command(BaseCommand):
    help = 'Test Pluggy API connection and list available banks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-token',
            action='store_true',
            help='Create a connect token'
        )
        parser.add_argument(
            '--item-id',
            type=str,
            help='Test with specific item ID'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Pluggy integration...'))
        
        # Check configuration
        if not all([
            getattr(settings, 'PLUGGY_CLIENT_ID', None),
            getattr(settings, 'PLUGGY_CLIENT_SECRET', None)
        ]):
            self.stdout.write(
                self.style.ERROR(
                    'Missing Pluggy credentials. Please set PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET'
                )
            )
            return
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.test_pluggy(options))
        finally:
            loop.close()
    
    async def test_pluggy(self, options):
        """Test Pluggy API"""
        async with PluggyClient() as client:
            # Test authentication
            self.stdout.write('Testing authentication...')
            try:
                await client._ensure_authenticated()
                self.stdout.write(
                    self.style.SUCCESS('✓ Authentication successful')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Authentication failed: {e}')
                )
                return
            
            # Get connectors
            self.stdout.write('\nFetching available banks...')
            try:
                connectors = await client.get_connectors()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Found {len(connectors)} connectors')
                )
                
                # Show banks
                banks = [c for c in connectors if c.get('type') == 'PERSONAL_BANK']
                self.stdout.write(f'\nAvailable banks ({len(banks)}):')
                
                for bank in banks[:10]:  # Show first 10
                    status = bank.get('health', {}).get('status', 'UNKNOWN')
                    status_color = (
                        self.style.SUCCESS if status == 'ONLINE'
                        else self.style.WARNING if status == 'UNSTABLE'
                        else self.style.ERROR
                    )
                    
                    self.stdout.write(
                        f"  - {bank['name']} (ID: {bank['id']}) "
                        f"[{status_color(status)}]"
                    )
                
                if len(banks) > 10:
                    self.stdout.write(f'  ... and {len(banks) - 10} more')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to get connectors: {e}')
                )
                return
            
            # Create connect token if requested
            if options['create_token']:
                self.stdout.write('\nCreating connect token...')
                try:
                    token_data = await client.create_connect_token(
                        options.get('item_id')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('✓ Connect token created:')
                    )
                    self.stdout.write(
                        f"  Token: {token_data.get('accessToken', 'N/A')[:30]}..."
                    )
                    self.stdout.write(
                        f"  Connect URL: {getattr(settings, 'PLUGGY_CONNECT_URL', 'https://connect.pluggy.ai')}"
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to create token: {e}')
                    )
            
            # Test specific item if provided
            if options['item_id']:
                self.stdout.write(f'\nTesting item {options["item_id"]}...')
                try:
                    # Get item
                    item = await client.get_item(options['item_id'])
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Item found: {item.get("connector", {}).get("name")}')
                    )
                    
                    # Get accounts
                    accounts = await client.get_accounts(options['item_id'])
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Found {len(accounts)} accounts')
                    )
                    
                    for acc in accounts:
                        self.stdout.write(
                            f"  - {acc.get('name', 'N/A')} "
                            f"({acc.get('type', 'N/A')}) "
                            f"Balance: {acc.get('balance', 0)}"
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to get item: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Pluggy integration test completed!')
            )