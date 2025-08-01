"""
Test factories for companies app using factory_boy for better test data management
"""
import factory
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.companies.models import Company, SubscriptionPlan, ResourceUsage

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users"""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    is_active = True
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class SubscriptionPlanFactory(factory.django.DjangoModelFactory):
    """Factory for creating test subscription plans"""
    
    class Meta:
        model = SubscriptionPlan
    
    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())
    price_monthly = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    price_yearly = factory.LazyAttribute(lambda obj: obj.price_monthly * Decimal('10'))  # 10x monthly for testing
    max_transactions = factory.Faker('random_int', min=100, max=10000)
    max_bank_accounts = factory.Faker('random_int', min=1, max=10)
    max_ai_requests = factory.Faker('random_int', min=10, max=1000)
    has_ai_insights = factory.Faker('boolean')
    has_advanced_reports = factory.Faker('boolean')
    stripe_price_id_monthly = factory.Faker('uuid4')
    stripe_price_id_yearly = factory.Faker('uuid4')
    is_active = True
    display_order = factory.Sequence(lambda n: n)


class CompanyFactory(factory.django.DjangoModelFactory):
    """Factory for creating test companies"""
    
    class Meta:
        model = Company
    
    owner = factory.SubFactory(UserFactory)
    name = factory.Faker('company')
    subscription_plan = factory.SubFactory(SubscriptionPlanFactory)
    subscription_status = 'trial'
    billing_cycle = 'monthly'
    trial_ends_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=14))
    current_month_transactions = 0
    current_month_ai_requests = 0
    is_active = True


class ResourceUsageFactory(factory.django.DjangoModelFactory):
    """Factory for creating test resource usage records"""
    
    class Meta:
        model = ResourceUsage
    
    company = factory.SubFactory(CompanyFactory)
    month = factory.LazyFunction(lambda: timezone.now().replace(day=1).date())
    transactions_count = factory.Faker('random_int', min=0, max=1000)
    ai_requests_count = factory.Faker('random_int', min=0, max=100)


# Trait factories for common scenarios
class TrialCompanyFactory(CompanyFactory):
    """Factory for companies in trial period"""
    subscription_status = 'trial'
    trial_ends_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))


class ActiveCompanyFactory(CompanyFactory):
    """Factory for companies with active subscriptions"""
    subscription_status = 'active'
    subscription_id = factory.Faker('uuid4')
    trial_ends_at = None


class ExpiredTrialCompanyFactory(CompanyFactory):
    """Factory for companies with expired trials"""
    subscription_status = 'trial'
    trial_ends_at = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))


class BasicPlanFactory(SubscriptionPlanFactory):
    """Factory for basic subscription plan"""
    name = 'Basic'
    slug = 'basic'
    price_monthly = Decimal('9.99')
    price_yearly = Decimal('99.99')
    max_transactions = 500
    max_bank_accounts = 2
    max_ai_requests = 50
    has_ai_insights = False
    has_advanced_reports = False


class PremiumPlanFactory(SubscriptionPlanFactory):
    """Factory for premium subscription plan"""
    name = 'Premium'
    slug = 'premium'
    price_monthly = Decimal('19.99')
    price_yearly = Decimal('199.99')
    max_transactions = 2000
    max_bank_accounts = 5
    max_ai_requests = 200
    has_ai_insights = True
    has_advanced_reports = True


class EnterprisePlanFactory(SubscriptionPlanFactory):
    """Factory for enterprise subscription plan"""
    name = 'Enterprise'
    slug = 'enterprise'
    price_monthly = Decimal('49.99')
    price_yearly = Decimal('499.99')
    max_transactions = 10000
    max_bank_accounts = 20
    max_ai_requests = 1000
    has_ai_insights = True
    has_advanced_reports = True