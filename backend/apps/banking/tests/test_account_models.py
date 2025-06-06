"""
Tests for bank account models
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.authentication.models import User
from apps.companies.models import Company
from apps.banking.models import BankAccount, BankProvider


class BankAccountModelTestCase(TestCase):
    """Test cases for BankAccount model"""
    
    def setUp(self):
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
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
    
    def test_create_bank_account(self):
        """Test creating a bank account"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678',
            account_digit='9',
            current_balance=Decimal('1000.00'),
            available_balance=Decimal('950.00'),
            nickname='Main Account'
        )
        
        self.assertEqual(account.company, self.company)
        self.assertEqual(account.bank_provider, self.bank_provider)
        self.assertEqual(account.account_type, 'checking')
        self.assertEqual(account.agency, '1234')
        self.assertEqual(account.account_number, '12345678')
        self.assertEqual(account.account_digit, '9')
        self.assertEqual(account.current_balance, Decimal('1000.00'))
        self.assertEqual(account.nickname, 'Main Account')
        self.assertEqual(account.status, 'pending')  # Default status
        self.assertTrue(account.is_active)  # Default is_active
    
    def test_bank_account_str_representation(self):
        """Test string representation of bank account"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678'
        )
        
        expected_str = f"{self.bank_provider.name} - 1234/12345678"
        self.assertEqual(str(account), expected_str)
    
    def test_masked_account_property(self):
        """Test masked account property"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678'
        )
        
        self.assertEqual(account.masked_account, '****5678')
        
        # Test with short account number
        account.account_number = '123'
        account.save()
        self.assertEqual(account.masked_account, '123')
    
    def test_display_name_property_with_nickname(self):
        """Test display name property with nickname"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678',
            nickname='Main Account'
        )
        
        expected_display = f"Main Account ({self.bank_provider.name})"
        self.assertEqual(account.display_name, expected_display)
    
    def test_display_name_property_without_nickname(self):
        """Test display name property without nickname"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678'
        )
        
        expected_display = f"{self.bank_provider.name} - ****5678"
        self.assertEqual(account.display_name, expected_display)
    
    def test_unique_constraint(self):
        """Test unique constraint on company, bank_provider, agency, account_number"""
        # Create first account
        BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678'
        )
        
        # Try to create duplicate account
        with self.assertRaises(Exception):  # Should raise IntegrityError
            BankAccount.objects.create(
                company=self.company,
                bank_provider=self.bank_provider,
                account_type='savings',  # Different type, but same other fields
                agency='1234',
                account_number='12345678'
            )
    
    def test_account_type_choices(self):
        """Test account type choices"""
        valid_types = ['checking', 'savings', 'business', 'digital']
        
        for account_type in valid_types:
            account = BankAccount.objects.create(
                company=self.company,
                bank_provider=self.bank_provider,
                account_type=account_type,
                agency=f'123{account_type[0]}',
                account_number=f'1234567{account_type[0]}'
            )
            self.assertEqual(account.account_type, account_type)
    
    def test_status_choices(self):
        """Test status choices"""
        valid_statuses = ['active', 'inactive', 'pending', 'error', 'expired']
        
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678'
        )
        
        for status_choice in valid_statuses:
            account.status = status_choice
            account.save()
            account.refresh_from_db()
            self.assertEqual(account.status, status_choice)
    
    def test_decimal_fields_precision(self):
        """Test decimal fields precision"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678',
            current_balance=Decimal('12345.67'),
            available_balance=Decimal('12300.45')
        )
        
        self.assertEqual(account.current_balance, Decimal('12345.67'))
        self.assertEqual(account.available_balance, Decimal('12300.45'))
    
    def test_meta_options(self):
        """Test model meta options"""
        self.assertEqual(BankAccount._meta.db_table, 'bank_accounts')
        self.assertEqual(str(BankAccount._meta.verbose_name), 'Bank Account')
        self.assertEqual(str(BankAccount._meta.verbose_name_plural), 'Bank Accounts')
    
    def test_default_values(self):
        """Test default values"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='12345678'
        )
        
        self.assertEqual(account.current_balance, Decimal('0.00'))
        self.assertEqual(account.available_balance, Decimal('0.00'))
        self.assertEqual(account.status, 'pending')
        self.assertTrue(account.is_active)
        self.assertFalse(account.is_primary)
        self.assertEqual(account.sync_frequency, 4)


class BankProviderModelTestCase(TestCase):
    """Test cases for BankProvider model"""
    
    def test_create_bank_provider(self):
        """Test creating a bank provider"""
        provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            color='#FF0000',
            is_open_banking=True,
            api_endpoint='https://api.testbank.com',
            supports_pix=True,
            supports_ted=True,
            supports_doc=False
        )
        
        self.assertEqual(provider.name, 'Test Bank')
        self.assertEqual(provider.code, '001')
        self.assertEqual(provider.color, '#FF0000')
        self.assertTrue(provider.is_open_banking)
        self.assertEqual(provider.api_endpoint, 'https://api.testbank.com')
        self.assertTrue(provider.supports_pix)
        self.assertTrue(provider.supports_ted)
        self.assertFalse(provider.supports_doc)
    
    def test_bank_provider_str_representation(self):
        """Test string representation of bank provider"""
        provider = BankProvider.objects.create(
            name='Test Bank',
            code='001'
        )
        
        expected_str = "Test Bank (001)"
        self.assertEqual(str(provider), expected_str)
    
    def test_unique_code_constraint(self):
        """Test unique constraint on bank code"""
        BankProvider.objects.create(name='Bank One', code='001')
        
        with self.assertRaises(Exception):  # Should raise IntegrityError
            BankProvider.objects.create(name='Bank Two', code='001')
    
    def test_default_values(self):
        """Test default values for bank provider"""
        provider = BankProvider.objects.create(
            name='Test Bank',
            code='001'
        )
        
        self.assertEqual(provider.color, '#000000')
        self.assertTrue(provider.is_open_banking)
        self.assertTrue(provider.is_active)
        self.assertTrue(provider.requires_agency)
        self.assertTrue(provider.requires_account)
        self.assertTrue(provider.supports_pix)
        self.assertTrue(provider.supports_ted)
        self.assertTrue(provider.supports_doc)
    
    def test_meta_options(self):
        """Test model meta options"""
        self.assertEqual(BankProvider._meta.db_table, 'bank_providers')
        self.assertEqual(str(BankProvider._meta.verbose_name), 'Bank Provider')
        self.assertEqual(str(BankProvider._meta.verbose_name_plural), 'Bank Providers')
        self.assertEqual(BankProvider._meta.ordering, ['name'])