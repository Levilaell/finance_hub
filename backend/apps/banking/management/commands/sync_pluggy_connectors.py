"""
Sync Pluggy connectors (banks) command
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.banking.models import PluggyConnector
from apps.banking.integrations.pluggy.client import PluggyClient, PluggyError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync connectors (banks) from Pluggy API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-sandbox',
            action='store_true',
            help='Include sandbox connectors',
        )

    def handle(self, *args, **options):
        include_sandbox = options.get('include_sandbox', False)
        
        self.stdout.write('Starting Pluggy connectors sync...')
        
        try:
            with PluggyClient() as client:
                # Get connectors from Pluggy
                self.stdout.write('Fetching connectors from Pluggy API...')
                connectors = client.get_connectors()
                
                self.stdout.write(f'Found {len(connectors)} connectors')
                
                # Update or create connectors
                created = 0
                updated = 0
                skipped = 0
                
                with transaction.atomic():
                    for connector_data in connectors:
                        # Skip sandbox if not requested
                        if connector_data.get('sandbox', False) and not include_sandbox:
                            skipped += 1
                            continue
                        
                        obj, was_created = PluggyConnector.objects.update_or_create(
                            pluggy_id=connector_data['id'],
                            defaults={
                                'name': connector_data['name'],
                                'institution_url': connector_data.get('institutionUrl', ''),
                                'image_url': connector_data.get('imageUrl', ''),
                                'primary_color': connector_data.get('primaryColor', '#000000'),
                                'type': connector_data['type'],
                                'country': connector_data.get('country', 'BR'),
                                'has_mfa': connector_data.get('hasMFA', False),
                                'has_oauth': connector_data.get('oauth', False),
                                'is_open_finance': connector_data.get('isOpenFinance', False),
                                'is_sandbox': connector_data.get('sandbox', False),
                                'products': connector_data.get('products', []),
                                'credentials': connector_data.get('credentials', [])
                            }
                        )
                        
                        if was_created:
                            created += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created: {connector_data["name"]}')
                            )
                        else:
                            updated += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSync completed successfully!\n'
                        f'Created: {created}\n'
                        f'Updated: {updated}\n'
                        f'Skipped (sandbox): {skipped}\n'
                        f'Total processed: {created + updated}'
                    )
                )
                
        except PluggyError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to sync connectors: {e}')
            )
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
            raise