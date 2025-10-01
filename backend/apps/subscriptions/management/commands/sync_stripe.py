"""
Management command to sync Stripe data and fix Plan vs Price issues
"""
from django.core.management.base import BaseCommand
from djstripe.models import Product, Price, Plan, Customer, Subscription
from djstripe import utils
import stripe
from django.conf import settings


class Command(BaseCommand):
    help = 'Sync Stripe data and clean up deprecated Plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean all djstripe data before syncing',
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

        if options['clean']:
            self.stdout.write('🗑️  Limpando dados antigos...')
            Plan.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Plans removidos'))

        self.stdout.write('\n📦 Sincronizando Products...')
        products = stripe.Product.list(limit=100)
        for product_data in products.auto_paging_iter():
            try:
                product = Product.sync_from_stripe_data(product_data)
                self.stdout.write(f'  ✓ {product.name}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ✗ {product_data.id}: {e}'))

        self.stdout.write('\n💰 Sincronizando Prices...')
        prices = stripe.Price.list(limit=100)
        for price_data in prices.auto_paging_iter():
            try:
                price = Price.sync_from_stripe_data(price_data)
                amount = price.unit_amount / 100 if price.unit_amount else 0
                self.stdout.write(f'  ✓ R$ {amount:.2f} - {price.product.name if price.product else "N/A"}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ✗ {price_data.id}: {e}'))

        self.stdout.write('\n👥 Sincronizando Customers...')
        customers = stripe.Customer.list(limit=100)
        for customer_data in customers.auto_paging_iter():
            try:
                customer = Customer.sync_from_stripe_data(customer_data)
                self.stdout.write(f'  ✓ {customer.email or customer.id}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ✗ {customer_data.id}: {e}'))

        self.stdout.write('\n📋 Sincronizando Subscriptions...')
        subscriptions = stripe.Subscription.list(limit=100)
        for sub_data in subscriptions.auto_paging_iter():
            try:
                sub = Subscription.sync_from_stripe_data(sub_data)
                self.stdout.write(f'  ✓ {sub.id} - {sub.status}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ✗ {sub_data.id}: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Sincronização completa!'))
