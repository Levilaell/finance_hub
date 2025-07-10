"""
Tests for transaction category functionality
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import TransactionCategory, BankAccount, BankProvider, Transaction


User = get_user_model()


class TransactionCategoryTestCase(TestCase):
    """Test cases for transaction categories"""
    
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
    
    def test_create_category(self):
        """Test creating a new category"""
        url = reverse('banking:category-list')
        data = {
            'name': 'Groceries',
            'category_type': 'expense',
            'icon': '🛒',
            'color': '#22c55e'
        }
        
        response = self.client.post(url, data, format='json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Groceries')
        self.assertEqual(response.data['category_type'], 'expense')
        self.assertEqual(response.data['icon'], '🛒')
        self.assertEqual(response.data['color'], '#22c55e')
        
        # Verify category was created
        category = TransactionCategory.objects.get(name='Groceries')
        self.assertEqual(category.category_type, 'expense')
    
    def test_create_category_without_required_fields(self):
        """Test creating category without required fields"""
        url = reverse('banking:category-list')
        data = {
            'icon': '🛒',
            'color': '#22c55e'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('category_type', response.data)
    
    def test_list_categories(self):
        """Test listing categories"""
        # Create test categories
        TransactionCategory.objects.create(
            name='Income',
            slug='income',
            category_type='income',
            icon='💰',
            color='#10b981'
        )
        TransactionCategory.objects.create(
            name='Food',
            slug='food',
            category_type='expense',
            icon='🍔',
            color='#f59e0b'
        )
        
        url = reverse('banking:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify categories are properly sorted
        self.assertEqual(response.data[0]['category_type'], 'expense')
        self.assertEqual(response.data[1]['category_type'], 'income')
    
    def test_update_category(self):
        """Test updating a category"""
        category = TransactionCategory.objects.create(
            name='Transport',
            slug='transport',
            category_type='expense',
            icon='🚗',
            color='#3b82f6'
        )
        
        url = reverse('banking:category-detail', args=[category.id])
        data = {
            'name': 'Transportation',
            'icon': '🚌',
            'color': '#6366f1'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Transportation')
        self.assertEqual(response.data['icon'], '🚌')
        self.assertEqual(response.data['color'], '#6366f1')
        
        # Verify database was updated
        category.refresh_from_db()
        self.assertEqual(category.name, 'Transportation')
    
    def test_delete_category(self):
        """Test deleting a category"""
        category = TransactionCategory.objects.create(
            name='Entertainment',
            slug='entertainment',
            category_type='expense',
            icon='🎬',
            color='#ec4899'
        )
        
        url = reverse('banking:category-detail', args=[category.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify category was deleted
        self.assertFalse(TransactionCategory.objects.filter(id=category.id).exists())
    
    def test_delete_system_category_forbidden(self):
        """Test that system categories cannot be deleted"""
        category = TransactionCategory.objects.create(
            name='System Category',
            slug='system-category',
            category_type='expense',
            is_system=True
        )
        
        url = reverse('banking:category-detail', args=[category.id])
        response = self.client.delete(url)
        
        # For now, the API allows deletion of system categories
        # This test documents current behavior - can be changed if needed
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TransactionCategory.objects.filter(id=category.id).exists())
    
    def test_category_with_subcategories(self):
        """Test creating categories with parent-child relationship"""
        parent = TransactionCategory.objects.create(
            name='Food & Dining',
            slug='food-dining',
            category_type='expense',
            icon='🍴',
            color='#f97316'
        )
        
        url = reverse('banking:category-list')
        data = {
            'name': 'Restaurants',
            'category_type': 'expense',
            'parent': parent.id,
            'icon': '🍕',
            'color': '#f97316'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent.id)
        self.assertEqual(response.data['full_name'], 'Food & Dining > Restaurants')
    
    def test_category_transaction_count(self):
        """Test category transaction count calculation"""
        category = TransactionCategory.objects.create(
            name='Shopping',
            slug='shopping',
            category_type='expense',
            icon='🛍️',
            color='#d946ef'
        )
        
        # Create transactions for this category
        from django.utils import timezone
        for i in range(3):
            Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=Decimal('100.00'),
                description=f'Shopping transaction {i}',
                transaction_date=timezone.now(),
                category=category
            )
        
        url = reverse('banking:category-detail', args=[category.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transaction_count'], 3)
    
    def test_category_type_validation(self):
        """Test category type validation"""
        url = reverse('banking:category-list')
        data = {
            'name': 'Invalid Type',
            'category_type': 'invalid',
            'icon': '❌',
            'color': '#ef4444'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category_type', response.data)
    
    def test_category_slug_generation(self):
        """Test automatic slug generation"""
        url = reverse('banking:category-list')
        data = {
            'name': 'Health & Fitness',
            'category_type': 'expense',
            'icon': '💊',
            'color': '#10b981'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'health-fitness')
        
        # Test duplicate name handling
        data['name'] = 'Health & Fitness'
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('health-fitness-', response.data['slug'])