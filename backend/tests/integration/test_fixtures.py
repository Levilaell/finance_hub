"""
Common fixtures and utilities for integration tests
"""
from apps.companies.models import SubscriptionPlan
from apps.banking.models import TransactionCategory


def create_default_subscription_plans():
    """Create default subscription plans for tests"""
    plans = []
    
    # Starter plan
    starter, _ = SubscriptionPlan.objects.get_or_create(
        slug='starter',
        defaults={
            'name': 'Starter',
            'plan_type': 'starter',
            'price_monthly': 29.00,
            'price_yearly': 290.00,
            'max_users': 3,
            'max_bank_accounts': 2,
            'max_transactions': 500,
            'has_ai_categorization': False,
            'has_advanced_reports': False,
            'has_api_access': False,
            'has_accountant_access': False
        }
    )
    plans.append(starter)
    
    # Pro plan
    pro, _ = SubscriptionPlan.objects.get_or_create(
        slug='pro',
        defaults={
            'name': 'Pro',
            'plan_type': 'pro',
            'price_monthly': 99.00,
            'price_yearly': 990.00,
            'max_users': 10,
            'max_bank_accounts': 5,
            'max_transactions': 2000,
            'has_ai_categorization': True,
            'has_advanced_reports': True,
            'has_api_access': False,
            'has_accountant_access': False
        }
    )
    plans.append(pro)
    
    # Enterprise plan
    enterprise, _ = SubscriptionPlan.objects.get_or_create(
        slug='enterprise',
        defaults={
            'name': 'Enterprise',
            'plan_type': 'enterprise',
            'price_monthly': 299.00,
            'price_yearly': 2990.00,
            'max_users': 100,
            'max_bank_accounts': 100,
            'max_transactions': 10000,
            'has_ai_categorization': True,
            'has_advanced_reports': True,
            'has_api_access': True,
            'has_accountant_access': True
        }
    )
    plans.append(enterprise)
    
    return plans


def create_default_categories():
    """Create default transaction categories for tests"""
    categories = []
    
    # Income categories
    income_categories = [
        ('sales', 'Sales', 'income'),
        ('services', 'Services', 'income'),
        ('other-income', 'Other Income', 'income'),
    ]
    
    # Expense categories
    expense_categories = [
        ('food-dining', 'Food & Dining', 'expense'),
        ('transportation', 'Transportation', 'expense'),
        ('utilities', 'Utilities', 'expense'),
        ('office', 'Office', 'expense'),
        ('operations', 'Operations', 'expense'),
        ('groceries', 'Groceries', 'expense'),
        ('restaurants', 'Restaurants', 'expense'),
        ('test-expense', 'Test', 'expense'),
    ]
    
    for slug, name, cat_type in income_categories + expense_categories:
        category, _ = TransactionCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'category_type': cat_type}
        )
        categories.append(category)
    
    return categories