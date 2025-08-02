"""
Unit tests for banking model managers
"""
from django.test import TestCase
from django.utils import timezone

from apps.banking.models import Transaction
from apps.banking.tests.factories.banking_factories import (
    TransactionFactory,
    BankAccountFactory
)
from apps.companies.tests.factories import CompanyFactory


class ActiveTransactionManagerTest(TestCase):
    """Test cases for ActiveTransactionManager"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.account = BankAccountFactory(company=self.company)
        
        # Create active transactions with explicit types
        self.active_trans1 = TransactionFactory(
            account=self.account,
            company=self.company,
            type='DEBIT',
            is_deleted=False
        )
        self.active_trans2 = TransactionFactory(
            account=self.account,
            company=self.company,
            type='DEBIT',
            is_deleted=False
        )
        
        # Create deleted transactions
        self.deleted_trans1 = TransactionFactory(
            account=self.account,
            company=self.company,
            type='DEBIT',
            is_deleted=True,
            deleted_at=timezone.now()
        )
        self.deleted_trans2 = TransactionFactory(
            account=self.account,
            company=self.company,
            type='CREDIT',
            is_deleted=True,
            deleted_at=timezone.now()
        )
    
    def test_active_manager_excludes_deleted(self):
        """Test that active manager excludes deleted transactions"""
        # Default manager should return all
        all_transactions = Transaction.objects.all()
        self.assertEqual(all_transactions.count(), 4)
        
        # Active manager should only return non-deleted
        active_transactions = Transaction.active.all()
        self.assertEqual(active_transactions.count(), 2)
        
        # Check specific transactions
        self.assertIn(self.active_trans1, active_transactions)
        self.assertIn(self.active_trans2, active_transactions)
        self.assertNotIn(self.deleted_trans1, active_transactions)
        self.assertNotIn(self.deleted_trans2, active_transactions)
    
    def test_active_manager_with_filters(self):
        """Test active manager with additional filters"""
        # Create credit and debit transactions
        credit_trans = TransactionFactory(
            account=self.account,
            company=self.company,
            type='CREDIT',
            is_deleted=False
        )
        debit_trans = TransactionFactory(
            account=self.account,
            company=self.company,
            type='DEBIT',
            is_deleted=False
        )
        deleted_credit = TransactionFactory(
            account=self.account,
            company=self.company,
            type='CREDIT',
            is_deleted=True,
            deleted_at=timezone.now()
        )
        
        # Filter active credit transactions
        active_credits = Transaction.active.filter(type='CREDIT')
        self.assertEqual(active_credits.count(), 1)
        self.assertIn(credit_trans, active_credits)
        self.assertNotIn(deleted_credit, active_credits)
    
    def test_active_manager_with_company_filter(self):
        """Test active manager filtering by company"""
        # Create transactions for another company
        other_company = CompanyFactory()
        other_account = BankAccountFactory(company=other_company)
        other_trans = TransactionFactory(
            account=other_account,
            company=other_company,
            is_deleted=False
        )
        
        # Filter by company
        company_transactions = Transaction.active.filter(company=self.company)
        self.assertEqual(company_transactions.count(), 2)
        self.assertNotIn(other_trans, company_transactions)
    
    def test_active_manager_ordering(self):
        """Test that active manager preserves model ordering"""
        # Create transactions with specific dates
        old_trans = TransactionFactory(
            account=self.account,
            company=self.company,
            date=timezone.now() - timezone.timedelta(days=10),
            is_deleted=False
        )
        new_trans = TransactionFactory(
            account=self.account,
            company=self.company,
            date=timezone.now(),
            is_deleted=False
        )
        
        # Check ordering (should be newest first based on model Meta)
        active_ordered = Transaction.active.all()
        first_trans = active_ordered.first()
        self.assertEqual(first_trans.id, new_trans.id)