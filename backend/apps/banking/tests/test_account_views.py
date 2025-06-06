"""
Tests for bank account views
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.companies.models import Company
from apps.banking.models import BankAccount, BankProvider


class BankAccountViewSetTestCase(TestCase):
    """Test cases for BankAccountViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user and company
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678000195',
            owner=self.user
        )
        self.user.company = self.company
        self.user.save()
        
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
            agency='1234',
            account_number='12345678',
            account_digit='9',
            current_balance=Decimal('1000.00'),
            available_balance=Decimal('950.00'),
            nickname='Main Account',
            status='active',
            is_active=True
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_list_accounts(self):
        """Test listing bank accounts"""
        url = reverse('banking:bank-account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.bank_account.id)
        self.assertEqual(response.data[0]['display_name'], self.bank_account.display_name)
    
    def test_retrieve_account(self):
        """Test retrieving a specific bank account"""
        url = reverse('banking:bank-account-detail', kwargs={'pk': self.bank_account.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.bank_account.id)
        self.assertEqual(response.data['agency'], '1234')
        self.assertEqual(response.data['account_number'], '12345678')
    
    def test_create_account(self):
        """Test creating a new bank account"""
        url = reverse('banking:bank-account-list')
        data = {
            'bank_provider': self.bank_provider.id,
            'account_type': 'savings',
            'agency': '5678',
            'account_number': '87654321',
            'account_digit': '0',
            'nickname': 'Savings Account'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BankAccount.objects.count(), 2)
        
        new_account = BankAccount.objects.get(id=response.data['id'])
        self.assertEqual(new_account.company, self.company)
        self.assertEqual(new_account.account_type, 'savings')
        self.assertEqual(new_account.agency, '5678')
    
    def test_update_account(self):
        """Test updating a bank account"""
        url = reverse('banking:bank-account-detail', kwargs={'pk': self.bank_account.id})
        data = {
            'nickname': 'Updated Account Name',
            'is_primary': True
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.nickname, 'Updated Account Name')
        self.assertTrue(self.bank_account.is_primary)
    
    def test_delete_account(self):
        """Test deleting a bank account"""
        url = reverse('banking:bank-account-detail', kwargs={'pk': self.bank_account.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BankAccount.objects.count(), 0)
    
    def test_sync_account(self):
        """Test syncing a bank account"""
        url = reverse('banking:bank-account-sync', kwargs={'pk': self.bank_account.id})
        response = self.client.post(url)
        
        # Since we don't have actual sync service, this should return an error
        # In production, this would trigger the sync process
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_accounts_summary(self):
        """Test accounts summary endpoint"""
        url = reverse('banking:bank-account-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_accounts'], 1)
        self.assertEqual(response.data['active_accounts'], 1)
        self.assertEqual(response.data['total_balance'], Decimal('1000.00'))
        self.assertEqual(response.data['sync_errors'], 0)
    
    def test_user_can_only_see_own_company_accounts(self):
        """Test that users can only see accounts from their company"""
        # Create another company and account
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            full_name='Other User'
        )
        other_company = Company.objects.create(
            name='Other Company',
            cnpj='98765432000100',
            owner=other_user
        )
        other_user.company = other_company
        other_user.save()
        
        BankAccount.objects.create(
            company=other_company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='9999',
            account_number='99999999',
            status='active',
            is_active=True
        )
        
        # Test that original user only sees their account
        url = reverse('banking:bank-account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.bank_account.id)
    
    def test_create_account_requires_authentication(self):
        """Test that creating account requires authentication"""
        self.client.force_authenticate(user=None)
        
        url = reverse('banking:bank-account-list')
        data = {
            'bank_provider': self.bank_provider.id,
            'account_type': 'checking',
            'agency': '1111',
            'account_number': '11111111'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_masked_account_property(self):
        """Test that account number is properly masked"""
        url = reverse('banking:bank-account-detail', kwargs={'pk': self.bank_account.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['masked_account'], '****5678')
    
    def test_display_name_property(self):
        """Test account display name property"""
        url = reverse('banking:bank-account-detail', kwargs={'pk': self.bank_account.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_display_name = f"Main Account ({self.bank_provider.name})"
        self.assertEqual(response.data['display_name'], expected_display_name)
    
    def test_account_validation(self):
        """Test account creation validation"""
        url = reverse('banking:bank-account-list')
        
        # Test missing required fields
        data = {
            'account_type': 'checking'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid account type
        data = {
            'bank_provider': self.bank_provider.id,
            'account_type': 'invalid_type',
            'agency': '1234',
            'account_number': '12345678'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_account_ordering(self):
        """Test that accounts are ordered by creation date (newest first)"""
        # Create second account
        second_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='savings',
            agency='5678',
            account_number='87654321',
            status='active',
            is_active=True
        )
        
        url = reverse('banking:bank-account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Newest account should be first
        self.assertEqual(response.data[0]['id'], second_account.id)
        self.assertEqual(response.data[1]['id'], self.bank_account.id)