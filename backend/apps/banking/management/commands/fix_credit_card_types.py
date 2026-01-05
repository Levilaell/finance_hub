"""
Django management command to fix credit card account types.

This command identifies credit card accounts that were incorrectly saved as CHECKING
(due to the missing 'CREDIT' -> 'CREDIT_CARD' mapping) and corrects their type.

Usage:
    python manage.py fix_credit_card_types
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.banking.models import BankAccount


class Command(BaseCommand):
    help = 'Fix credit card accounts that were incorrectly saved as CHECKING'

    def handle(self, *args, **options):
        self.stdout.write('Searching for credit card accounts with incorrect type...')

        # Find accounts that have credit card fields but wrong type
        # Credit cards have credit_limit or available_credit_limit filled
        credit_cards = BankAccount.objects.filter(
            Q(credit_limit__isnull=False) | Q(available_credit_limit__isnull=False)
        ).exclude(type='CREDIT_CARD')

        count = credit_cards.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No accounts need correction'))
            return

        self.stdout.write(f'Found {count} credit card account(s) with incorrect type:')

        for account in credit_cards:
            self.stdout.write(
                f'  - {account.name} (ID: {account.id}) - '
                f'Current: {account.type} → Will change to: CREDIT_CARD'
            )

        # Update all at once
        updated = credit_cards.update(type='CREDIT_CARD')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully updated {updated} credit card account(s)'
            )
        )
