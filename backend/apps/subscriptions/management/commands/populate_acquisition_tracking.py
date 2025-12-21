"""
Populate AcquisitionTracking for existing users with subscriptions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from djstripe.models import Subscription
from apps.authentication.models import User
from apps.subscriptions.models import AcquisitionTracking


class Command(BaseCommand):
    help = 'Populate AcquisitionTracking for existing users with subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        # Get all subscriptions
        subscriptions = Subscription.objects.select_related(
            'customer', 'customer__subscriber'
        ).order_by('-created')

        created_count = 0
        skipped_count = 0
        error_count = 0

        for sub in subscriptions:
            if not sub.customer or not sub.customer.subscriber:
                self.stdout.write(
                    self.style.WARNING(f'Skipping subscription {sub.id}: no subscriber')
                )
                skipped_count += 1
                continue

            user = sub.customer.subscriber

            # Check if already exists
            if AcquisitionTracking.objects.filter(user=user).exists():
                self.stdout.write(f'Skipping {user.email}: already has tracking')
                skipped_count += 1
                continue

            # Get acquisition_angle from user
            acquisition_angle = user.acquisition_angle or 'unknown'
            valid_angles = ['time', 'price', 'delay', 'visibility', 'organic']
            if acquisition_angle not in valid_angles:
                acquisition_angle = 'unknown'

            # Determine conversion status
            converted_at = None
            canceled_at = None

            if sub.status == 'active' and sub.trial_end:
                # User converted from trial
                converted_at = sub.trial_end

            if sub.status == 'canceled':
                canceled_at = sub.canceled_at or sub.ended_at or timezone.now()

            self.stdout.write(
                f'User: {user.email}\n'
                f'  - Angle: {acquisition_angle}\n'
                f'  - Status: {sub.status}\n'
                f'  - Trial: {sub.trial_start} -> {sub.trial_end}\n'
                f'  - Converted: {converted_at}\n'
                f'  - Canceled: {canceled_at}'
            )

            if not dry_run:
                try:
                    AcquisitionTracking.objects.create(
                        user=user,
                        acquisition_angle=acquisition_angle,
                        signup_price_id=user.signup_price_id,
                        subscription_status=sub.status,
                        stripe_subscription_id=sub.id,
                        trial_started_at=sub.trial_start,
                        trial_ended_at=sub.trial_end if sub.status != 'trialing' else None,
                        converted_at=converted_at,
                        canceled_at=canceled_at,
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  -> Created!'))
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  -> Error: {e}'))
            else:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  -> Would create'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        if error_count:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
