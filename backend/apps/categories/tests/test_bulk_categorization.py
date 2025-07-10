"""
Tests for bulk categorization functionality
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import TransactionCategory, BankAccount, BankProvider, Transaction
from apps.categories.models import CategoryRule


User = get_user_model()


class BulkCategorizationTestCase(TestCase):
    """Test cases for bulk categorization operations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=Decimal('29.90'),
            price_yearly=Decimal('299.00')
        )
        
        # Create test company
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=self.subscription_plan
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='0001',
            account_number='12345',
            account_digit='6'
        )
        
        # Create categories
        self.food_category = TransactionCategory.objects.create(
            name='Food',
            slug='food',
            category_type='expense',
            icon='🍔',
            color='#f59e0b'
        )
        
        self.transport_category = TransactionCategory.objects.create(
            name='Transport',
            slug='transport',
            category_type='expense',
            icon='🚗',
            color='#3b82f6'
        )
        
        # Create category rules
        self.food_rule = CategoryRule.objects.create(
            company=self.company,
            category=self.food_category,
            name='Food Keywords',
            rule_type='keyword',
            conditions={
                'field': 'description',
                'keywords': ['restaurant', 'food', 'lunch', 'dinner']
            },
            priority=10,
            created_by=self.user
        )
        
        self.transport_rule = CategoryRule.objects.create(
            company=self.company,
            category=self.transport_category,
            name='Transport Keywords',
            rule_type='keyword',
            conditions={
                'field': 'description',
                'keywords': ['uber', 'taxi', 'gas', 'fuel']
            },
            priority=10,
            created_by=self.user
        )
    
    def test_bulk_categorize_uncategorized(self):
        """Test bulk categorization of uncategorized transactions"""
        # Create uncategorized transactions
        transactions = []
        for i in range(5):
            if i < 3:
                desc = f'Restaurant payment {i}'
            else:
                desc = f'Uber ride {i}'
                
            trans = Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=Decimal('50.00'),
                description=desc,
                transaction_date=timezone.now(),
                category=None  # Uncategorized
            )
            transactions.append(trans)
        
        url = reverse('categories:bulk-categorization')
        data = {
            'operation': 'categorize_uncategorized',
            'limit': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['operation'], 'categorize_uncategorized')
        
        # Verify transactions were categorized
        for trans in transactions[:3]:
            trans.refresh_from_db()
            self.assertEqual(trans.category, self.food_category)
            
        for trans in transactions[3:]:
            trans.refresh_from_db()
            self.assertEqual(trans.category, self.transport_category)
    
    def test_bulk_recategorize_low_confidence(self):
        """Test recategorization of low confidence transactions"""
        # Create transactions with low confidence scores
        transactions = []
        for i in range(3):
            trans = Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=Decimal('75.00'),
                description=f'Ambiguous payment {i}',
                transaction_date=timezone.now(),
                category=self.food_category,
                ai_category_confidence=0.3,  # Low confidence
                is_ai_categorized=True
            )
            transactions.append(trans)
        
        url = reverse('categories:bulk-categorization')
        data = {
            'operation': 'recategorize_low_confidence',
            'confidence_threshold': 0.5
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['operation'], 'recategorize_low_confidence')
    
    def test_invalid_bulk_operation(self):
        """Test invalid bulk operation"""
        url = reverse('categories:bulk-categorization')
        data = {
            'operation': 'invalid_operation'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Operação não suportada')
    
    def test_category_rule_application(self):
        """Test applying category rules to transactions"""
        # Create a transaction that matches food rule
        transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='debit',
            amount=Decimal('45.00'),
            description='Lunch at restaurant downtown',
            transaction_date=timezone.now(),
            category=None
        )
        
        # Apply rules via bulk categorization
        url = reverse('categories:bulk-categorization')
        data = {
            'operation': 'categorize_uncategorized',
            'limit': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaction was categorized correctly
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, self.food_category)
    
    def test_bulk_categorization_with_transaction_ids(self):
        """Test bulk categorization with specific transaction IDs"""
        # Create specific transactions
        trans1 = Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='debit',
            amount=Decimal('30.00'),
            description='Food delivery',
            transaction_date=timezone.now(),
            category=None
        )
        
        trans2 = Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='debit',
            amount=Decimal('25.00'),
            description='Taxi ride',
            transaction_date=timezone.now(),
            category=None
        )
        
        # This one should not be categorized
        trans3 = Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='debit',
            amount=Decimal('100.00'),
            description='Random purchase',
            transaction_date=timezone.now(),
            category=None
        )
        
        url = reverse('categories:bulk-categorization')
        data = {
            'operation': 'categorize_uncategorized',
            'transaction_ids': [str(trans1.id), str(trans2.id)]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only specified transactions were categorized
        trans1.refresh_from_db()
        trans2.refresh_from_db()
        trans3.refresh_from_db()
        
        self.assertEqual(trans1.category, self.food_category)
        self.assertEqual(trans2.category, self.transport_category)
        self.assertIsNone(trans3.category)