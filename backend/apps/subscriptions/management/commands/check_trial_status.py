"""
Management command to check trial usage status for users
"""
from django.core.management.base import BaseCommand
from apps.authentication.models import User
from apps.subscriptions.models import TrialUsageTracking
from djstripe.models import Subscription


class Command(BaseCommand):
    help = 'Check trial usage status for all users or specific email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Check specific user by email',
        )

    def handle(self, *args, **options):
        email = options.get('email')

        if email:
            # Check specific user
            try:
                user = User.objects.get(email=email)
                self.print_user_trial_status(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        else:
            # Check all users
            self.stdout.write(self.style.SUCCESS('\n=== Trial Usage Status for All Users ===\n'))
            users = User.objects.all().order_by('email')
            for user in users:
                self.print_user_trial_status(user)
                self.stdout.write('')

    def print_user_trial_status(self, user):
        # Get trial tracking
        trial_tracking, created = TrialUsageTracking.objects.get_or_create(user=user)

        # Get subscriptions
        subscriptions = Subscription.objects.filter(
            customer__subscriber=user
        ).order_by('-created')

        self.stdout.write(self.style.HTTP_INFO(f'User: {user.email}'))
        self.stdout.write(f'  Name: {user.first_name} {user.last_name}')
        self.stdout.write(f'  Has used trial: {trial_tracking.has_used_trial}')
        self.stdout.write(f'  First trial at: {trial_tracking.first_trial_at}')
        self.stdout.write(f'  Subscriptions count: {subscriptions.count()}')

        if subscriptions.exists():
            for idx, sub in enumerate(subscriptions, 1):
                self.stdout.write(f'  Subscription {idx}:')
                self.stdout.write(f'    Status: {sub.status}')
                self.stdout.write(f'    Created: {sub.created}')
                if sub.trial_end:
                    self.stdout.write(f'    Trial end: {sub.trial_end}')
