"""
Management command to translate existing categories from English to Portuguese.
Uses the pluggy_categories.json file for translations.

Usage:
    python manage.py translate_categories
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.banking.models import Category
from apps.banking.services import get_category_translations


class Command(BaseCommand):
    help = 'Translate existing categories from English to Portuguese'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run command without making changes (preview only)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Load translations
        translations = get_category_translations()

        if not translations:
            self.stdout.write(self.style.ERROR('Failed to load translations!'))
            return

        self.stdout.write(f'Loaded {len(translations)} translations')

        # Get all categories
        categories = Category.objects.all()
        total_count = categories.count()

        self.stdout.write(f'Found {total_count} categories to process')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No categories to translate!'))
            return

        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for category in categories:
                # Check if category name is in English (exists in translations)
                if category.name in translations:
                    translated_name = translations[category.name]

                    old_name = category.name
                    if not dry_run:
                        category.name = translated_name
                        category.save(update_fields=['name'])

                    self.stdout.write(
                        f'  {old_name} -> {translated_name} ({category.type})'
                    )
                    updated_count += 1
                else:
                    # Already translated or custom category
                    skipped_count += 1

            if dry_run:
                # Rollback the transaction in dry-run mode
                transaction.set_rollback(True)

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Total categories: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'Categories translated: {updated_count}'))
        self.stdout.write(f'Categories skipped (already translated or custom): {skipped_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\nSuccessfully translated all categories!'))
