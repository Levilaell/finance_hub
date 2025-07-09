"""
Comprehensive tests for Banking app models
Testing model validation, business logic, and relationships
"""
import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.banking.models import (
    BankProvider,
    BankAccount,
    TransactionCategory,
    Transaction,
    RecurringTransaction,
    Budget,
    FinancialGoal,
    BankSync,
    BankConnection
)
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class BankingModelsTestCase(TestCase):
    """Base test case for banking models"""
    
    def setUp(self):
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Basic',
            price=Decimal('29.90'),
            max_accounts=5,
            max_transactions=1000
        )
        
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            document_number='12345678000199',
            subscription_plan=self.subscription_plan,
            owner=self.user
        )
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='TEST001'
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense',
            is_system=True
        )


class BankProviderModelTest(BankingModelsTestCase):
    """Test BankProvider model functionality"""
    
    def test_bank_provider_creation(self):
        """Test creating a bank provider with valid data"""
        provider_data = {
            'name': 'Banco do Brasil',
            'code': 'BB001',
            'color': '#FFD700',
            'is_open_banking': True,
            'api_endpoint': 'https://api.bancodobrasil.com.br',
            'is_active': True,
            'requires_agency': True,
            'requires_account': True,
            'supports_pix': True,
            'supports_ted': True,
            'supports_doc': True,
        }
        provider = BankProvider.objects.create(**provider_data)
        
        self.assertEqual(provider.name, 'Banco do Brasil')
        self.assertEqual(provider.code, 'BB001')
        self.assertTrue(provider.is_active)
        self.assertTrue(provider.supports_pix)
        self.assertEqual(str(provider), 'Banco do Brasil (BB001)')
    
    def test_bank_provider_code_uniqueness(self):
        """Test that bank code must be unique"""
        BankProvider.objects.create(name='Bank 1', code='UNIQUE001')
        
        # Try to create another provider with same code
        with self.assertRaises(IntegrityError):
            BankProvider.objects.create(name='Bank 2', code='UNIQUE001')
    
    def test_bank_provider_defaults(self):
        """Test default values for optional fields"""
        provider = BankProvider.objects.create(name='Test Bank', code='TEST123')
        
        self.assertTrue(provider.is_open_banking)
        self.assertTrue(provider.is_active)
        self.assertTrue(provider.requires_agency)
        self.assertTrue(provider.requires_account)
        self.assertTrue(provider.supports_pix)
        self.assertTrue(provider.supports_ted)
        self.assertTrue(provider.supports_doc)
        self.assertEqual(provider.color, '#000000')
    
    def test_bank_provider_ordering(self):
        """Test that providers are ordered by name"""
        BankProvider.objects.create(name='Zebra Bank', code='ZEB')
        BankProvider.objects.create(name='Alpha Bank', code='ALP')
        BankProvider.objects.create(name='Beta Bank', code='BET')
        
        providers = list(BankProvider.objects.all())
        names = [p.name for p in providers]
        
        # Should include our setup provider 'Test Bank' and be alphabetically ordered
        self.assertIn('Alpha Bank', names)
        self.assertIn('Beta Bank', names)
        self.assertIn('Test Bank', names)
        self.assertIn('Zebra Bank', names)


class BankAccountModelTest(BankingModelsTestCase):
    """Test BankAccount model functionality"""
    
    def test_bank_account_creation(self):
        """Test creating a bank account with valid data"""
        account_data = {
            'company': self.company,
            'bank_provider': self.bank_provider,
            'account_type': 'checking',
            'agency': '1234',
            'account_number': '567890',
            'account_digit': '1',
            'external_account_id': 'ext_123',
            'status': 'active',
            'current_balance': Decimal('1000.00'),
            'available_balance': Decimal('950.00'),
            'nickname': 'Main Account'
        }
        account = BankAccount.objects.create(**account_data)
        
        self.assertEqual(account.company, self.company)
        self.assertEqual(account.bank_provider, self.bank_provider)
        self.assertEqual(account.account_type, 'checking')
        self.assertEqual(account.agency, '1234')
        self.assertEqual(account.account_number, '567890')
        self.assertEqual(account.current_balance, Decimal('1000.00'))
        self.assertTrue(account.is_active)
    
    def test_bank_account_string_representation(self):
        """Test string representation of bank account"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890'
        )
        expected = f"{self.bank_provider.name} - 1234/567890"
        self.assertEqual(str(account), expected)
    
    def test_masked_account_property(self):
        """Test account number masking for security"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890'
        )
        self.assertEqual(account.masked_account, '****7890')
        
        # Test short account number
        account.account_number = '123'
        self.assertEqual(account.masked_account, '123')
    
    def test_display_name_property(self):
        """Test display name property"""
        # With nickname
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890',
            nickname='Main Account'
        )
        expected_with_nickname = f"Main Account ({self.bank_provider.name})"
        self.assertEqual(account.display_name, expected_with_nickname)
        
        # Without nickname
        account.nickname = ''
        account.save()
        expected_without_nickname = f"{self.bank_provider.name} - ****7890"
        self.assertEqual(account.display_name, expected_without_nickname)
    
    def test_brazilian_agency_validation(self):
        """Test Brazilian agency format validation"""
        account = BankAccount(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            account_number='567890'
        )
        
        # Valid agency formats
        valid_agencies = ['1234', '0001', '12345', '1234-5']
        for agency in valid_agencies:
            account.agency = agency
            try:
                account.clean()  # Should not raise ValidationError
            except ValidationError:
                self.fail(f"Valid agency '{agency}' raised ValidationError")
        
        # Invalid agency formats
        invalid_agencies = ['', '12', '123456', 'ABC', '12-34-56']
        for agency in invalid_agencies:
            account.agency = agency
            with self.assertRaises(ValidationError):
                account.clean()
    
    def test_brazilian_account_validation(self):
        """Test Brazilian account number format validation"""
        account = BankAccount(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234'
        )
        
        # Valid account formats
        valid_accounts = ['123456', '1234567', '123456-7', '123456X', '12345678901']
        for account_number in valid_accounts:
            account.account_number = account_number
            try:
                account.clean()  # Should not raise ValidationError
            except ValidationError:
                self.fail(f"Valid account '{account_number}' raised ValidationError")
        
        # Invalid account formats
        invalid_accounts = ['', '123', '1234567890123', 'ABC123', '12-34-56']
        for account_number in invalid_accounts:
            account.account_number = account_number
            with self.assertRaises(ValidationError):
                account.clean()
    
    def test_unique_together_constraint(self):
        """Test unique together constraint"""
        account_data = {
            'company': self.company,
            'bank_provider': self.bank_provider,
            'account_type': 'checking',
            'agency': '1234',
            'account_number': '567890'
        }
        BankAccount.objects.create(**account_data)
        
        # Try to create duplicate account
        with self.assertRaises(IntegrityError):
            BankAccount.objects.create(**account_data)
    
    def test_account_defaults(self):
        """Test default values for optional fields"""
        minimal_data = {
            'company': self.company,
            'bank_provider': self.bank_provider,
            'account_type': 'checking',
            'agency': '1234',
            'account_number': '567890'
        }
        account = BankAccount.objects.create(**minimal_data)
        
        self.assertEqual(account.status, 'pending')
        self.assertEqual(account.current_balance, Decimal('0.00'))
        self.assertEqual(account.available_balance, Decimal('0.00'))
        self.assertFalse(account.is_primary)
        self.assertTrue(account.is_active)
        self.assertEqual(account.sync_frequency, 4)


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


class RecurringTransactionModelTest(BankingModelsTestCase):
    """Test RecurringTransaction model functionality"""
    
    def setUp(self):
        super().setUp()
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890'
        )
    
    def test_recurring_transaction_creation(self):
        """Test creating a recurring transaction"""
        recurring_data = {
            'bank_account': self.bank_account,
            'name': 'Monthly Salary',
            'description_pattern': 'SALARY PAYMENT',
            'expected_amount': Decimal('3000.00'),
            'amount_tolerance': Decimal('5.00'),
            'frequency': 'monthly',
            'next_expected_date': timezone.now().date() + timedelta(days=30),
            'day_tolerance': 3,
            'category': self.category,
            'is_active': True
        }
        recurring = RecurringTransaction.objects.create(**recurring_data)
        
        self.assertEqual(recurring.name, 'Monthly Salary')
        self.assertEqual(recurring.expected_amount, Decimal('3000.00'))
        self.assertEqual(recurring.frequency, 'monthly')
        self.assertTrue(recurring.is_active)
    
    def test_recurring_transaction_string_representation(self):
        """Test string representation"""
        recurring = RecurringTransaction.objects.create(
            bank_account=self.bank_account,
            name='Weekly Expense',
            description_pattern='WEEKLY PAYMENT',
            expected_amount=Decimal('100.00'),
            frequency='weekly',
            next_expected_date=timezone.now().date()
        )
        expected = f"{recurring.name} - {recurring.frequency}"
        self.assertEqual(str(recurring), expected)
    
    def test_recurring_transaction_defaults(self):
        """Test default values"""
        recurring = RecurringTransaction.objects.create(
            bank_account=self.bank_account,
            name='Test Recurring',
            description_pattern='TEST',
            expected_amount=Decimal('100.00'),
            frequency='monthly',
            next_expected_date=timezone.now().date()
        )
        
        self.assertEqual(recurring.amount_tolerance, Decimal('5.00'))
        self.assertEqual(recurring.day_tolerance, 3)
        self.assertTrue(recurring.is_active)
        self.assertTrue(recurring.auto_categorize)
        self.assertTrue(recurring.send_alerts)
        self.assertEqual(recurring.total_occurrences, 0)
        self.assertEqual(recurring.accuracy_rate, 0.0)


class BudgetModelTest(BankingModelsTestCase):
    """Test Budget model functionality"""
    
    def test_budget_creation(self):
        """Test creating a budget"""
        today = timezone.now().date()
        budget_data = {
            'company': self.company,
            'name': 'Monthly Food Budget',
            'description': 'Budget for food expenses',
            'budget_type': 'monthly',
            'amount': Decimal('500.00'),
            'start_date': today,
            'end_date': today + timedelta(days=30),
            'alert_threshold': 80,
            'created_by': self.user
        }
        budget = Budget.objects.create(**budget_data)
        
        self.assertEqual(budget.company, self.company)
        self.assertEqual(budget.name, 'Monthly Food Budget')
        self.assertEqual(budget.amount, Decimal('500.00'))
        self.assertEqual(budget.budget_type, 'monthly')
        self.assertEqual(budget.status, 'active')
    
    def test_budget_string_representation(self):
        """Test string representation of budget"""
        budget = Budget.objects.create(
            company=self.company,
            name='Test Budget',
            amount=Decimal('1000.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        expected = f"{budget.name} - R$ {budget.amount}"
        self.assertEqual(str(budget), expected)
    
    def test_remaining_amount_property(self):
        """Test remaining amount calculation"""
        budget = Budget.objects.create(
            company=self.company,
            name='Test Budget',
            amount=Decimal('500.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        budget.spent_amount = Decimal('200.00')
        budget.save()
        
        self.assertEqual(budget.remaining_amount, Decimal('300.00'))
    
    def test_spent_percentage_property(self):
        """Test spent percentage calculation"""
        budget = Budget.objects.create(
            company=self.company,
            name='Test Budget',
            amount=Decimal('500.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        budget.spent_amount = Decimal('250.00')
        budget.save()
        
        self.assertEqual(budget.spent_percentage, 50.0)
        
        # Test with zero amount
        budget.amount = Decimal('0.00')
        self.assertEqual(budget.spent_percentage, 0)
    
    def test_is_exceeded_property(self):
        """Test budget exceeded check"""
        budget = Budget.objects.create(
            company=self.company,
            name='Test Budget',
            amount=Decimal('500.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        
        # Not exceeded
        budget.spent_amount = Decimal('400.00')
        self.assertFalse(budget.is_exceeded)
        
        # Exceeded
        budget.spent_amount = Decimal('600.00')
        self.assertTrue(budget.is_exceeded)
    
    def test_is_alert_threshold_reached_property(self):
        """Test alert threshold check"""
        budget = Budget.objects.create(
            company=self.company,
            name='Test Budget',
            amount=Decimal('500.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            alert_threshold=80,
            created_by=self.user
        )
        
        # Below threshold (80%)
        budget.spent_amount = Decimal('300.00')  # 60%
        self.assertFalse(budget.is_alert_threshold_reached)
        
        # At threshold
        budget.spent_amount = Decimal('400.00')  # 80%
        self.assertTrue(budget.is_alert_threshold_reached)
        
        # Above threshold
        budget.spent_amount = Decimal('450.00')  # 90%
        self.assertTrue(budget.is_alert_threshold_reached)


class FinancialGoalModelTest(BankingModelsTestCase):
    """Test FinancialGoal model functionality"""
    
    def test_goal_creation(self):
        """Test creating a financial goal"""
        target_date = timezone.now().date() + timedelta(days=365)
        goal_data = {
            'company': self.company,
            'name': 'Emergency Fund',
            'description': 'Build emergency fund for 6 months expenses',
            'goal_type': 'emergency_fund',
            'target_amount': Decimal('10000.00'),
            'target_date': target_date,
            'created_by': self.user
        }
        goal = FinancialGoal.objects.create(**goal_data)
        
        self.assertEqual(goal.company, self.company)
        self.assertEqual(goal.name, 'Emergency Fund')
        self.assertEqual(goal.target_amount, Decimal('10000.00'))
        self.assertEqual(goal.goal_type, 'emergency_fund')
        self.assertEqual(goal.status, 'active')
    
    def test_goal_string_representation(self):
        """Test string representation of goal"""
        goal = FinancialGoal.objects.create(
            company=self.company,
            name='Vacation Fund',
            goal_type='savings',
            target_amount=Decimal('5000.00'),
            target_date=timezone.now().date() + timedelta(days=180),
            created_by=self.user
        )
        expected = f"{goal.name} - R$ {goal.target_amount}"
        self.assertEqual(str(goal), expected)
    
    def test_progress_percentage_property(self):
        """Test progress percentage calculation"""
        goal = FinancialGoal.objects.create(
            company=self.company,
            name='Test Goal',
            goal_type='savings',
            target_amount=Decimal('10000.00'),
            target_date=timezone.now().date() + timedelta(days=365),
            created_by=self.user
        )
        goal.current_amount = Decimal('2500.00')
        goal.save()
        
        self.assertEqual(goal.progress_percentage, 25.0)
        
        # Test with zero target
        goal.target_amount = Decimal('0.00')
        self.assertEqual(goal.progress_percentage, 0)
    
    def test_remaining_amount_property(self):
        """Test remaining amount calculation"""
        goal = FinancialGoal.objects.create(
            company=self.company,
            name='Test Goal',
            goal_type='savings',
            target_amount=Decimal('10000.00'),
            target_date=timezone.now().date() + timedelta(days=365),
            created_by=self.user
        )
        goal.current_amount = Decimal('3000.00')
        goal.save()
        
        self.assertEqual(goal.remaining_amount, Decimal('7000.00'))
    
    def test_days_remaining_property(self):
        """Test days remaining calculation"""
        future_date = timezone.now().date() + timedelta(days=100)
        goal = FinancialGoal.objects.create(
            company=self.company,
            name='Test Goal',
            goal_type='savings',
            target_amount=Decimal('5000.00'),
            target_date=future_date,
            created_by=self.user
        )
        
        # Should be approximately 100 days
        self.assertGreater(goal.days_remaining, 95)
        self.assertLess(goal.days_remaining, 105)


class BankSyncModelTest(BankingModelsTestCase):
    """Test BankSync model functionality"""
    
    def setUp(self):
        super().setUp()
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890'
        )
    
    def test_bank_sync_creation(self):
        """Test creating a bank sync log"""
        today = timezone.now().date()
        sync_data = {
            'bank_account': self.bank_account,
            'status': 'completed',
            'transactions_found': 50,
            'transactions_new': 10,
            'transactions_updated': 5,
            'sync_from_date': today - timedelta(days=30),
            'sync_to_date': today
        }
        sync = BankSync.objects.create(**sync_data)
        
        self.assertEqual(sync.bank_account, self.bank_account)
        self.assertEqual(sync.status, 'completed')
        self.assertEqual(sync.transactions_found, 50)
        self.assertEqual(sync.transactions_new, 10)
        self.assertEqual(sync.transactions_updated, 5)
    
    def test_bank_sync_string_representation(self):
        """Test string representation of bank sync"""
        sync = BankSync.objects.create(
            bank_account=self.bank_account,
            sync_from_date=timezone.now().date(),
            sync_to_date=timezone.now().date()
        )
        date_str = sync.started_at.strftime('%d/%m/%Y %H:%M')
        expected = f"Sync {sync.bank_account} - {sync.status} ({date_str})"
        self.assertEqual(str(sync), expected)
    
    def test_duration_property(self):
        """Test sync duration calculation"""
        sync = BankSync.objects.create(
            bank_account=self.bank_account,
            sync_from_date=timezone.now().date(),
            sync_to_date=timezone.now().date()
        )
        
        # Set completed time
        sync.completed_at = sync.started_at + timedelta(minutes=5)
        sync.save()
        
        duration = sync.duration
        self.assertEqual(duration.total_seconds(), 300)  # 5 minutes
        
        # Test without completed time
        sync.completed_at = None
        sync.save()
        self.assertIsNone(sync.duration)


class BankConnectionModelTest(BankingModelsTestCase):
    """Test BankConnection model functionality"""
    
    def test_connection_creation(self):
        """Test creating a bank connection"""
        connection_data = {
            'belvo_id': 'belvo_123456',
            'institution': 'test_bank',
            'display_name': 'Test Bank Connection',
            'company': self.company,
            'status': 'valid',
            'last_access_mode': 'recurrent',
            'created_by': self.user,
            'belvo_created_at': timezone.now(),
            'belvo_created_by': 'api_user',
            'external_id': 'ext_123',
            'credentials_stored': True,
            'metadata': {'test': 'data'}
        }
        connection = BankConnection.objects.create(**connection_data)
        
        self.assertEqual(connection.belvo_id, 'belvo_123456')
        self.assertEqual(connection.institution, 'test_bank')
        self.assertEqual(connection.company, self.company)
        self.assertEqual(connection.status, 'valid')
        self.assertTrue(isinstance(connection.id, uuid.UUID))
    
    def test_connection_string_representation(self):
        """Test string representation of connection"""
        connection = BankConnection.objects.create(
            belvo_id='belvo_123',
            institution='test_bank',
            display_name='Test Bank',
            company=self.company,
            created_by=self.user
        )
        expected = f"{connection.institution} - {connection.display_name} ({connection.status})"
        self.assertEqual(str(connection), expected)
    
    def test_is_active_method(self):
        """Test is_active method"""
        connection = BankConnection.objects.create(
            belvo_id='belvo_123',
            institution='test_bank',
            company=self.company,
            created_by=self.user
        )
        
        # Valid status
        connection.status = 'valid'
        self.assertTrue(connection.is_active())
        
        # Invalid status
        connection.status = 'invalid'
        self.assertFalse(connection.is_active())
    
    def test_needs_token_renewal_method(self):
        """Test needs_token_renewal method"""
        connection = BankConnection.objects.create(
            belvo_id='belvo_123',
            institution='test_bank',
            company=self.company,
            created_by=self.user
        )
        
        # Token renewal required
        connection.status = 'token_renewal_required'
        self.assertTrue(connection.needs_token_renewal())
        
        # Valid status
        connection.status = 'valid'
        self.assertFalse(connection.needs_token_renewal())
    
    def test_belvo_id_uniqueness(self):
        """Test that belvo_id must be unique"""
        BankConnection.objects.create(
            belvo_id='unique_belvo_123',
            institution='test_bank',
            company=self.company,
            created_by=self.user
        )
        
        # Try to create another connection with same belvo_id
        with self.assertRaises(IntegrityError):
            BankConnection.objects.create(
                belvo_id='unique_belvo_123',
                institution='another_bank',
                company=self.company,
                created_by=self.user
            )