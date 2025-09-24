"""
Sync Pluggy connectors from API
"""

from django.core.management.base import BaseCommand
from apps.banking.services import ConnectorService


class Command(BaseCommand):
    help = 'Sync Pluggy connectors from API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--country',
            type=str,
            default='BR',
            help='Country code (default: BR)'
        )
        parser.add_argument(
            '--sandbox',
            action='store_true',
            help='Include sandbox connectors'
        )

    def handle(self, *args, **options):
        country = options['country']
        sandbox = options['sandbox']

        self.stdout.write(f"Syncing connectors for {country} (sandbox: {sandbox})...")

        service = ConnectorService()
        try:
            count = service.sync_connectors(country=country, sandbox=sandbox)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully synced {count} connectors')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error syncing connectors: {e}')
            )