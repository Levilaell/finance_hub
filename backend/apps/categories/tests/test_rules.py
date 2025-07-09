"""
Test category rules functionality
Tests for CategoryRuleViewSet and rule-based categorization
"""
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.categories.models import CategoryRule, CategorizationLog
from apps.categories.services import AICategorizationService
from apps.companies.models import Company, SubscriptionPlan
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import Mock, patch
import json
import uuid

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CategoryRuleViewSetTests(TestCase):
    """Test category rule management and application"""
    
    def setUp(self):
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00,
            max_users=5,
            max_bank_accounts=5
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-bank',
            is_active=True
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='0001',
            account_number='12345',
            current_balance=1000.00
        )
        
        # Create categories
        self.food_category = TransactionCategory.objects.create(
            name='Alimentação',
            slug='alimentacao',
            category_type='expense'
        )
        self.transport_category = TransactionCategory.objects.create(
            name='Transporte',
            slug='transporte',
            category_type='expense'
        )
        self.income_category = TransactionCategory.objects.create(
            name='Salário',
            slug='salario',
            category_type='income'
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('categories:category-rule-list')
    
    def test_create_keyword_rule(self):
        """Test creating a keyword-based category rule"""
        data = {
            'name': 'Uber Rule',
            'category': self.transport_category.id,
            'rule_type': 'keyword',
            'conditions': {
                'keywords': ['uber', 'taxi', '99']
            },
            'priority': 10,
            'is_active': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Uber Rule')
        self.assertEqual(response.data['rule_type'], 'keyword')
        
        # Verify rule was created
        rule = CategoryRule.objects.get(id=response.data['id'])
        self.assertEqual(rule.company, self.company)
        self.assertEqual(rule.created_by, self.user)
        self.assertEqual(rule.category, self.transport_category)
    
    def test_create_amount_range_rule(self):
        """Test creating an amount range rule"""
        data = {
            'name': 'High Value Rule',
            'category': self.income_category.id,
            'rule_type': 'amount_range',
            'conditions': {
                'min_amount': 5000.00,
                'max_amount': 10000.00
            },
            'priority': 5,
            'is_active': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rule_type'], 'amount_range')
        self.assertEqual(response.data['conditions']['min_amount'], 5000.00)
    
    def test_create_pattern_rule(self):
        """Test creating a regex pattern rule"""
        data = {
            'name': 'Restaurant Pattern',
            'category': self.food_category.id,
            'rule_type': 'pattern',
            'conditions': {
                'pattern': r'(?i)(restaurante|lanchonete|padaria)'
            },
            'priority': 8,
            'is_active': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rule_type'], 'pattern')
    
    def test_list_company_rules(self):
        """Test listing rules for the company"""
        # Create some rules
        CategoryRule.objects.create(
            company=self.company,
            name='Rule 1',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['food']},
            created_by=self.user
        )
        CategoryRule.objects.create(
            company=self.company,
            name='Rule 2',
            category=self.transport_category,
            rule_type='keyword',
            conditions={'keywords': ['uber']},
            created_by=self.user
        )
        
        # Create rule for another company (should not appear)
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        other_company = Company.objects.create(
            name='Other Company',
            cnpj='22333444000195',
            owner=other_user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        CategoryRule.objects.create(
            company=other_company,
            name='Other Rule',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['other']},
            created_by=self.user
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        rule_names = [r['name'] for r in response.data['results']]
        self.assertIn('Rule 1', rule_names)
        self.assertIn('Rule 2', rule_names)
        self.assertNotIn('Other Rule', rule_names)
    
    def test_update_rule(self):
        """Test updating a category rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            name='Original Rule',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['old']},
            created_by=self.user
        )
        
        url = reverse('categories:category-rule-detail', args=[rule.id])
        data = {
            'name': 'Updated Rule',
            'conditions': {'keywords': ['new', 'updated']},
            'priority': 15
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Rule')
        self.assertEqual(response.data['priority'], 15)
        
        # Verify update
        rule.refresh_from_db()
        self.assertEqual(rule.name, 'Updated Rule')
        self.assertEqual(rule.conditions['keywords'], ['new', 'updated'])
    
    def test_delete_rule(self):
        """Test deleting a category rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            name='Rule to Delete',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['delete']},
            created_by=self.user
        )
        
        url = reverse('categories:category-rule-detail', args=[rule.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CategoryRule.objects.filter(id=rule.id).exists())
    
    def test_test_rule_action(self):
        """Test the test_rule action"""
        rule = CategoryRule.objects.create(
            company=self.company,
            name='Test Rule',
            category=self.transport_category,
            rule_type='keyword',
            conditions={'keywords': ['uber', 'taxi']},
            created_by=self.user
        )
        
        # Create test transactions
        for i in range(5):
            Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'test_{i}',
                amount=-50.00,
                description=f'Uber ride {i}' if i < 3 else f'Food delivery {i}',
                transaction_date=timezone.now(),
                transaction_type='debit'
            )
        
        # Mock rule matching
        def mock_rule_matches(rule, transaction):
            return 'uber' in transaction.description.lower()
        
        url = reverse('categories:category-rule-test-rule', args=[rule.id])
        
        with patch.object(AICategorizationService, '_rule_matches', side_effect=mock_rule_matches):
            response = self.client.post(url, {'limit': 10}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['matches_found'], 3)
        self.assertEqual(response.data['total_tested'], 5)
        self.assertAlmostEqual(response.data['match_rate'], 0.6)
        self.assertLessEqual(len(response.data['matches']), 20)
    
    def test_apply_to_existing_action(self):
        """Test applying rule to existing transactions"""
        rule = CategoryRule.objects.create(
            company=self.company,
            name='Apply Rule',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['restaurant']},
            created_by=self.user
        )
        
        # Mock bulk service
        mock_results = {
            'processed': 25,
            'categorized': 20,
            'failed': 5
        }
        
        url = reverse('categories:category-rule-apply-to-existing', args=[rule.id])
        
        with patch('apps.categories.services.BulkCategorizationService.apply_rule_to_existing_transactions', 
                  return_value=mock_results) as mock_apply:
            response = self.client.post(url, {'limit': 100}, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['results'], mock_results)
            mock_apply.assert_called_once_with(rule, 100)
    
    def test_invalid_rule_type(self):
        """Test creating rule with invalid type"""
        data = {
            'name': 'Invalid Rule',
            'category': self.food_category.id,
            'rule_type': 'invalid_type',
            'conditions': {},
            'priority': 10
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_authentication_required(self):
        """Test authentication requirement"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_rule_priority_ordering(self):
        """Test that rules are returned ordered by priority"""
        # Create rules with different priorities
        CategoryRule.objects.create(
            company=self.company,
            name='Low Priority',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['low']},
            priority=1,
            created_by=self.user
        )
        CategoryRule.objects.create(
            company=self.company,
            name='High Priority',
            category=self.transport_category,
            rule_type='keyword',
            conditions={'keywords': ['high']},
            priority=10,
            created_by=self.user
        )
        CategoryRule.objects.create(
            company=self.company,
            name='Medium Priority',
            category=self.income_category,
            rule_type='keyword',
            conditions={'keywords': ['medium']},
            priority=5,
            created_by=self.user
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rules = response.data['results']
        
        # Verify ordering by priority (descending)
        self.assertEqual(rules[0]['priority'], 10)
        self.assertEqual(rules[1]['priority'], 5)
        self.assertEqual(rules[2]['priority'], 1)
    
    def test_rule_activation_deactivation(self):
        """Test activating and deactivating rules"""
        rule = CategoryRule.objects.create(
            company=self.company,
            name='Toggle Rule',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['toggle']},
            is_active=True,
            created_by=self.user
        )
        
        url = reverse('categories:category-rule-detail', args=[rule.id])
        
        # Deactivate rule
        response = self.client.patch(url, {'is_active': False}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        
        # Verify in database
        rule.refresh_from_db()
        self.assertFalse(rule.is_active)
        
        # Reactivate rule
        response = self.client.patch(url, {'is_active': True}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])
    
    def test_cannot_access_other_company_rules(self):
        """Test that users cannot access rules from other companies"""
        # Create another user and company
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        other_company = Company.objects.create(
            name='Other Company',
            cnpj='22333444000195',
            owner=other_user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create rule for other company
        other_rule = CategoryRule.objects.create(
            company=other_company,
            name='Other Company Rule',
            category=self.food_category,
            rule_type='keyword',
            conditions={'keywords': ['other']},
            created_by=other_user
        )
        
        # Try to access other company's rule
        url = reverse('categories:category-rule-detail', args=[other_rule.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)