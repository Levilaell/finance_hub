"""
Management command to assign categories to existing transactions.
This command creates categories from Pluggy category data and assigns them to transactions.

Usage:
    python manage.py assign_categories
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.banking.models import Transaction, Category
from apps.banking.services import get_or_create_category


class Command(BaseCommand):
    help = 'Assign categories to existing transactions based on Pluggy category data'

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

        # Get all transactions without user_category assigned
        transactions_to_update = Transaction.objects.filter(
            user_category__isnull=True
        ).select_related('account__connection__user')

        total_count = transactions_to_update.count()
        self.stdout.write(f'Found {total_count} transactions without categories')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('All transactions already have categories assigned!'))
            return

        updated_count = 0
        skipped_count = 0
        created_categories = set()

        with transaction.atomic():
            for tx in transactions_to_update:
                # Skip if no pluggy_category
                if not tx.pluggy_category or not tx.pluggy_category.strip():
                    skipped_count += 1
                    continue

                # Get user from the account connection
                user = tx.account.connection.user

                # Get or create category
                category = get_or_create_category(user, tx.pluggy_category, tx.type)

                if category:
                    if not dry_run:
                        tx.user_category = category
                        tx.save(update_fields=['user_category'])

                    updated_count += 1

                    # Track created categories for reporting
                    category_key = f"{user.id}:{category.name}:{category.type}"
                    if category_key not in created_categories:
                        created_categories.add(category_key)
                        self.stdout.write(
                            f'  Created/Found category: {category.name} ({category.type}) for user {user.email}'
                        )
                else:
                    skipped_count += 1

            if dry_run:
                # Rollback the transaction in dry-run mode
                transaction.set_rollback(True)

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Total transactions processed: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'Transactions updated: {updated_count}'))
        self.stdout.write(f'Transactions skipped (no category): {skipped_count}')
        self.stdout.write(f'Unique categories created/found: {len(created_categories)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\nSuccessfully assigned categories to transactions!'))
