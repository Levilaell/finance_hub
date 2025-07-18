"""
Management command to create test performance data for development
This command creates realistic categorization logs and performance metrics for testing
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create test performance data for development and testing'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                'Command deprecated: Categorization is now handled automatically by Pluggy'
            )
        )