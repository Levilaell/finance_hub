"""
Banking models tests
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class BankingModelsTestCase(TestCase):
    """Base test case for banking models"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=29.90,
            price_yearly=299.00
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan
        )
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            color='#000000'
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense',
            is_system=True
        )


class BankAccountModelTest(BankingModelsTestCase):
    """Test BankAccount model"""
    
    def test_create_bank_account(self):
        """Test creating a bank account"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890',
            account_digit='1'
        )
        
        self.assertEqual(str(account), 'Test Bank - 1234/567890')
        self.assertEqual(account.masked_account, '****7890')
        self.assertEqual(account.display_name, 'Test Bank - ****7890')
    
    def test_bank_account_with_nickname(self):
        """Test bank account with nickname"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890',
            nickname='Main Account'
        )
        
        self.assertEqual(account.display_name, 'Main Account (Test Bank)')
    
    def test_unique_constraint(self):
        """Test unique constraint on bank account"""
        BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890'
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            BankAccount.objects.create(
                company=self.company,
                bank_provider=self.bank_provider,
                account_type='checking',
                agency='1234',
                account_number='567890'
            )


class TransactionModelTest(BankingModelsTestCase):
    """Test Transaction model"""
    
    def setUp(self):
        super().setUp()
        # Create bank account
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890'
        )
    
    def test_create_income_transaction(self):
        """Test creating income transaction"""
        transaction = Transaction.objects.create(
            bank_account=self.account,
            transaction_type='credit',
            amount=Decimal('1000.00'),
            description='Sales revenue',
            transaction_date='2024-01-15 10:00:00',
            category=self.category
        )
        
        self.assertTrue(transaction.is_income)
        self.assertFalse(transaction.is_expense)
        self.assertEqual(transaction.formatted_amount, 'R$ 1.000,00')
        self.assertEqual(transaction.amount_with_sign, Decimal('1000.00'))
    
    def test_create_expense_transaction(self):
        """Test creating expense transaction"""
        transaction = Transaction.objects.create(
            bank_account=self.account,
            transaction_type='debit',
            amount=Decimal('-500.00'),
            description='Office supplies',
            transaction_date='2024-01-15 14:00:00',
            category=self.category
        )
        
        self.assertFalse(transaction.is_income)
        self.assertTrue(transaction.is_expense)
        self.assertEqual(transaction.formatted_amount, 'R$ 500,00')
        self.assertEqual(transaction.amount_with_sign, Decimal('-500.00'))
    
    def test_transaction_categorization(self):
        """Test transaction AI categorization fields"""
        transaction = Transaction.objects.create(
            bank_account=self.account,
            transaction_type='debit',
            amount=Decimal('-150.00'),
            description='Restaurant payment',
            transaction_date='2024-01-15 12:30:00',
            category=self.category,
            ai_category_confidence=0.85,
            is_ai_categorized=True
        )
        
        self.assertEqual(transaction.ai_category_confidence, 0.85)
        self.assertTrue(transaction.is_ai_categorized)
        self.assertFalse(transaction.is_manually_reviewed)


class TransactionCategoryModelTest(BankingModelsTestCase):
    """Test TransactionCategory model"""
    
    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
        parent_category = TransactionCategory.objects.create(
            name='Parent Category',
            slug='parent-category',
            category_type='expense',
            is_system=True
        )
        
        child_category = TransactionCategory.objects.create(
            name='Child Category',
            slug='child-category',
            category_type='expense',
            parent=parent_category,
            is_system=True
        )
        
        self.assertEqual(str(child_category), 'Parent Category > Child Category')
        self.assertEqual(child_category.full_name, 'Parent Category > Child Category')
        self.assertEqual(parent_category.subcategories.count(), 1)
    
    def test_category_keywords(self):
        """Test category keywords for AI"""
        category = TransactionCategory.objects.create(
            name='Food & Dining',
            slug='food-dining',
            category_type='expense',
            keywords=['restaurant', 'food', 'lunch', 'dinner'],
            is_system=True
        )
        
        self.assertIn('restaurant', category.keywords)
        self.assertEqual(len(category.keywords), 4)