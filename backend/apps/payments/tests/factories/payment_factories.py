"""
Factory classes for payment models
"""
import factory
from factory.django import DjangoModelFactory
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from apps.payments.models import (
    SubscriptionPlan,
    Subscription,
    PaymentMethod,
    Payment,
    UsageRecord,
    FailedWebhook,
)
from apps.companies.tests.factories import CompanyFactory


class SubscriptionPlanFactory(DjangoModelFactory):
    """Factory for SubscriptionPlan model"""
    class Meta:
        model = SubscriptionPlan
    
    name = factory.Iterator(['starter', 'professional', 'enterprise'])
    display_name = factory.Faker('catch_phrase')
    price_monthly = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    price_yearly = factory.LazyAttribute(lambda obj: obj.price_monthly * 10)  # 2 months discount
    max_transactions = factory.Faker('random_int', min=100, max=10000)
    max_bank_accounts = factory.Faker('random_int', min=1, max=10)
    max_ai_requests = factory.Faker('random_int', min=10, max=1000)
    features = factory.Dict({
        'ai_insights': factory.Faker('boolean'),
        'advanced_reports': factory.Faker('boolean'),
        'priority_support': factory.Faker('boolean'),
        'api_access': factory.Faker('boolean'),
    })
    is_active = True


class SubscriptionFactory(DjangoModelFactory):
    """Factory for Subscription model"""
    class Meta:
        model = Subscription
    
    company = factory.SubFactory(CompanyFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    status = factory.Faker('random_element', elements=['trial', 'active', 'cancelled', 'expired', 'past_due'])
    billing_period = factory.Faker('random_element', elements=['monthly', 'yearly'])
    
    trial_ends_at = factory.LazyAttribute(
        lambda obj: timezone.now() + timedelta(days=14) if obj.status == 'trial' else None
    )
    current_period_start = factory.LazyFunction(timezone.now)
    current_period_end = factory.LazyAttribute(
        lambda obj: obj.current_period_start + timedelta(days=30 if obj.billing_period == 'monthly' else 365)
    )
    cancelled_at = factory.LazyAttribute(
        lambda obj: timezone.now() if obj.status == 'cancelled' else None
    )
    
    stripe_subscription_id = factory.Faker('uuid4')
    stripe_customer_id = factory.Sequence(lambda n: f"cus_{n:010d}")
    
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class PaymentMethodFactory(DjangoModelFactory):
    """Factory for PaymentMethod model"""
    class Meta:
        model = PaymentMethod
    
    company = factory.SubFactory(CompanyFactory)
    type = factory.Faker('random_element', elements=['card', 'bank_account', 'pix'])
    is_default = False
    brand = factory.Faker('random_element', elements=['visa', 'mastercard', 'amex', 'discover'])
    last4 = factory.Faker('numerify', text='####')
    exp_month = factory.Faker('random_int', min=1, max=12)
    exp_year = factory.Faker('random_int', min=2024, max=2030)
    display_name = factory.LazyAttribute(lambda obj: f"{obj.brand} ****{obj.last4}")
    
    stripe_payment_method_id = factory.Faker('uuid4')
    metadata = factory.Dict({})
    
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class PaymentFactory(DjangoModelFactory):
    """Factory for Payment model"""
    class Meta:
        model = Payment
    
    company = factory.SubFactory(CompanyFactory)
    subscription = factory.SubFactory(SubscriptionFactory)
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    currency = 'BRL'
    status = factory.Faker('random_element', elements=['pending', 'processing', 'succeeded', 'failed', 'cancelled', 'refunded'])
    description = factory.Faker('sentence')
    gateway = 'stripe'
    payment_method = factory.SubFactory(PaymentMethodFactory)
    
    stripe_payment_intent_id = factory.Sequence(lambda n: f"pi_{n:010d}")
    stripe_invoice_id = factory.Sequence(lambda n: f"in_{n:010d}")
    
    paid_at = factory.LazyAttribute(
        lambda obj: timezone.now() if obj.status == 'succeeded' else None
    )
    
    metadata = factory.Dict({
        'customer_ip': factory.Faker('ipv4'),
        'user_agent': factory.Faker('user_agent'),
    })
    
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class UsageRecordFactory(DjangoModelFactory):
    """Factory for UsageRecord model"""
    class Meta:
        model = UsageRecord
    
    company = factory.SubFactory(CompanyFactory)
    type = factory.Faker('random_element', elements=['transaction', 'bank_account', 'ai_request'])
    count = factory.Faker('random_int', min=0, max=1000)
    period_start = factory.LazyFunction(lambda: timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    period_end = factory.LazyAttribute(
        lambda obj: (obj.period_start.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
    )
    
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class FailedWebhookFactory(DjangoModelFactory):
    """Factory for FailedWebhook model"""
    class Meta:
        model = FailedWebhook
    
    event_id = factory.Sequence(lambda n: f"evt_{n:010d}")
    event_type = factory.Faker('random_element', elements=[
        'checkout.session.completed',
        'invoice.payment_succeeded',
        'invoice.payment_failed',
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
    ])
    
    event_data = factory.LazyFunction(lambda: {
        'object': {
            'id': 'obj_test_123456',
            'amount': 2999,
            'currency': 'brl',
        }
    })
    
    error_message = factory.Faker('sentence')
    retry_count = 0
    max_retries = 5
    next_retry_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=5))
    
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)