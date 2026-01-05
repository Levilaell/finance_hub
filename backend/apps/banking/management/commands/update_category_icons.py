"""
Management command to update category icons with appropriate emojis.

Usage:
    python manage.py update_category_icons
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.banking.models import Category
from apps.banking.services import get_category_icon


class Command(BaseCommand):
    help = 'Update category icons with appropriate emojis'

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

        # Get all categories
        categories = Category.objects.all()
        total_count = categories.count()

        self.stdout.write(f'Found {total_count} categories to update')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No categories to update!'))
            return

        updated_count = 0

        with transaction.atomic():
            for category in categories:
                # Get the appropriate icon for this category
                new_icon = get_category_icon(category.name)
                old_icon = category.icon

                # Only update if icon changed
                if old_icon != new_icon:
                    if not dry_run:
                        category.icon = new_icon
                        category.save(update_fields=['icon'])

                    # Use ASCII representation for console output
                    self.stdout.write(
                        f'  {category.name}: [icon updated] ({category.type})'
                    )
                    updated_count += 1

            if dry_run:
                # Rollback the transaction in dry-run mode
                transaction.set_rollback(True)

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Total categories: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'Categories updated: {updated_count}'))
        self.stdout.write(f'Categories unchanged: {total_count - updated_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\nSuccessfully updated all category icons!'))
