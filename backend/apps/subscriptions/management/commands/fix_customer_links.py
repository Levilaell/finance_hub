"""
Management command to fix customer-user linkage and sync subscriptions
"""
from django.core.management.base import BaseCommand
from apps.authentication.models import User
from djstripe.models import Customer, Subscription
import stripe
from django.conf import settings


class Command(BaseCommand):
    help = 'Fix customer-user linkage and sync subscriptions from Stripe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Fix specific user by email',
        )
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help='Sync all subscriptions from Stripe',
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_SECRET_KEY

        email = options.get('email')
        sync_all = options.get('sync_all')

        if email:
            self.fix_user_customer(email)
        elif sync_all:
            self.sync_all_subscriptions()
        else:
            self.fix_all_users()

    def fix_user_customer(self, email):
        """Fix customer linkage for specific user"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {email} not found'))
            return

        self.stdout.write(self.style.HTTP_INFO(f'\nFixing customer linkage for: {user.email}'))

        # Find all customers with this email
        customers = Customer.objects.filter(email=user.email)
        self.stdout.write(f'Found {customers.count()} customers with email {user.email}')

        if customers.count() == 0:
            self.stdout.write(self.style.WARNING('No customers found'))
            return

        # Find customer with active subscription
        customer_with_sub = None
        for customer in customers:
            subs = Subscription.objects.filter(customer=customer, status__in=['active', 'trialing'])
            if subs.exists():
                customer_with_sub = customer
                self.stdout.write(self.style.SUCCESS(f'Found customer with active subscription: {customer.id}'))
                break

        # If no active subscription, use the first customer
        if not customer_with_sub:
            customer_with_sub = customers.first()
            self.stdout.write(self.style.WARNING(f'No active subscription found, using first customer: {customer_with_sub.id}'))

        # Link customer to user
        if customer_with_sub.subscriber != user:
            customer_with_sub.subscriber = user
            customer_with_sub.save()
            self.stdout.write(self.style.SUCCESS(f'Linked customer {customer_with_sub.id} to user {user.email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Customer {customer_with_sub.id} already linked to user'))

        # Unlink other customers
        for customer in customers:
            if customer.id != customer_with_sub.id and customer.subscriber == user:
                customer.subscriber = None
                customer.save()
                self.stdout.write(f'Unlinked duplicate customer {customer.id}')

        # Show final status
        subs = Subscription.objects.filter(customer__subscriber=user)
        self.stdout.write(self.style.SUCCESS(f'\nFinal status:'))
        self.stdout.write(f'  User: {user.email}')
        self.stdout.write(f'  Active subscription: {user.has_active_subscription}')
        self.stdout.write(f'  Subscriptions count: {subs.count()}')

    def fix_all_users(self):
        """Fix customer linkage for all users"""
        self.stdout.write(self.style.SUCCESS('\n=== Fixing customer linkage for all users ===\n'))

        users = User.objects.all()
        fixed_count = 0

        for user in users:
            customers = Customer.objects.filter(email=user.email)
            if customers.count() > 1 or (customers.exists() and customers.first().subscriber != user):
                self.stdout.write(f'\nFixing: {user.email}')
                self.fix_user_customer(user.email)
                fixed_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n\nFixed {fixed_count} users'))

    def sync_all_subscriptions(self):
        """Sync all subscriptions from Stripe"""
        self.stdout.write(self.style.SUCCESS('\n=== Syncing all subscriptions from Stripe ===\n'))

        try:
            # Get all subscriptions from Stripe
            subscriptions = stripe.Subscription.list(limit=100)

            synced_count = 0
            for stripe_sub in subscriptions.auto_paging_iter():
                try:
                    sub = Subscription.sync_from_stripe_data(stripe_sub)
                    self.stdout.write(f'Synced: {sub.id} (status: {sub.status})')
                    synced_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error syncing {stripe_sub.id}: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(f'\n\nSynced {synced_count} subscriptions'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error syncing subscriptions: {str(e)}'))
