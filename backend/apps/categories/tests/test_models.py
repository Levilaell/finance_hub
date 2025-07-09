"""
Comprehensive tests for Categories app models.
Testing AI categorization models, rules, training data, and performance tracking.
"""
import json
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.utils import IntegrityError
from django.db import models

from apps.banking.models import BankAccount, Transaction, TransactionCategory, BankProvider
from apps.companies.models import Company, SubscriptionPlan
from apps.categories.models import (
    CategoryRule, AITrainingData, CategorySuggestion, 
    CategoryPerformance, CategorizationLog
)

User = get_user_model()


class CategoryRuleModelTest(TestCase):
    """Test CategoryRule model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Utilities',
            slug='utilities',
            category_type='expense',
            icon='utilities'
        )
    
    def test_create_keyword_rule(self):
        """Test creating a keyword-based rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Utilities Keywords',
            rule_type='keyword',
            conditions={'keywords': ['electricity', 'water', 'gas']},
            priority=10,
            is_active=True
        )
        
        self.assertEqual(rule.rule_type, 'keyword')
        self.assertEqual(rule.priority, 10)
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.match_count, 0)
        self.assertEqual(rule.accuracy_rate, 0.0)
        self.assertIsInstance(rule.conditions, dict)
        self.assertIn('keywords', rule.conditions)
    
    def test_create_amount_range_rule(self):
        """Test creating an amount range rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Medium Amount Range',
            rule_type='amount_range',
            conditions={
                'min_amount': '100.00',
                'max_amount': '500.00'
            },
            priority=5
        )
        
        self.assertEqual(rule.rule_type, 'amount_range')
        self.assertEqual(rule.conditions['min_amount'], '100.00')
        self.assertEqual(rule.conditions['max_amount'], '500.00')
    
    def test_create_counterpart_rule(self):
        """Test creating a counterpart-based rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Ride Services',
            rule_type='counterpart',
            conditions={'counterparts': ['UBER', 'CABIFY', '99TAXI']},
            priority=8
        )
        
        self.assertEqual(rule.rule_type, 'counterpart')
        self.assertIn('counterparts', rule.conditions)
        self.assertEqual(len(rule.conditions['counterparts']), 3)
    
    def test_create_pattern_rule(self):
        """Test creating a regex pattern rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Salary Pattern',
            rule_type='pattern',
            conditions={'pattern': r'PIX.*SALARIO'},
            priority=15
        )
        
        self.assertEqual(rule.rule_type, 'pattern')
        self.assertEqual(rule.conditions['pattern'], r'PIX.*SALARIO')
    
    def test_create_ai_prediction_rule(self):
        """Test creating an AI prediction threshold rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='High Confidence AI',
            rule_type='ai_prediction',
            conditions={'min_confidence': 0.85},
            priority=1
        )
        
        self.assertEqual(rule.rule_type, 'ai_prediction')
        self.assertEqual(rule.conditions['min_confidence'], 0.85)
    
    def test_rule_string_representation(self):
        """Test string representation of rule"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Test utilities rule',
            rule_type='keyword',
            conditions={'keywords': ['test']}
        )
        
        expected = f"Test utilities rule → {self.category.name}"
        self.assertEqual(str(rule), expected)
    
    def test_rule_ordering(self):
        """Test rules are ordered by priority descending"""
        rule1 = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Low Priority Rule',
            rule_type='keyword',
            conditions={'keywords': ['test1']},
            priority=5
        )
        
        rule2 = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='High Priority Rule',
            rule_type='keyword',
            conditions={'keywords': ['test2']},
            priority=10
        )
        
        rules = CategoryRule.objects.all()
        self.assertEqual(rules[0], rule2)  # Higher priority first
        self.assertEqual(rules[1], rule1)
    
    def test_rule_company_isolation(self):
        """Test rules are isolated by company"""
        # Create another company
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        other_company = Company.objects.create(
            owner=other_user,
            name='Other Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create rules for both companies
        rule1 = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Company 1 Rule',
            rule_type='keyword',
            conditions={'keywords': ['test']}
        )
        
        rule2 = CategoryRule.objects.create(
            company=other_company,
            category=self.category,
            name='Company 2 Rule',
            rule_type='keyword',
            conditions={'keywords': ['test']}
        )
        
        # Verify isolation
        company_rules = CategoryRule.objects.filter(company=self.company)
        self.assertEqual(company_rules.count(), 1)
        self.assertEqual(company_rules.first(), rule1)
    
    def test_rule_statistics_update(self):
        """Test updating rule match statistics"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Test Rule',
            rule_type='keyword',
            conditions={'keywords': ['test']}
        )
        
        # Update match count
        rule.match_count = 10
        rule.accuracy_rate = 0.85
        rule.save()
        
        rule.refresh_from_db()
        self.assertEqual(rule.match_count, 10)
        self.assertEqual(rule.accuracy_rate, 0.85)


class AITrainingDataModelTest(TestCase):
    """Test AITrainingData model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create bank account
        self.provider = BankProvider.objects.create(
            code='001',
            name='Test Bank'
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            agency='0001',
            account_number='12345-6'
        )
        
        # Create default categories
        TransactionCategory.objects.create(
            name='Outros Despesas',
            slug='outros-despesas',
            category_type='expense',
            is_system=True,
            icon='outros'
        )
        
        TransactionCategory.objects.create(
            name='Outros Receitas',
            slug='outros-receitas',
            category_type='income',
            is_system=True,
            icon='outros'
        )
        
        # Create categories
        self.category = TransactionCategory.objects.create(
            name='Food',
            slug='food',
            category_type='expense',
            icon='food'
        )
        
        # Create transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.account,
            amount=Decimal('-50.00'),
            transaction_type='debit',
            description='RESTAURANTE XYZ',
            transaction_date=timezone.now().date(),
            category=self.category
        )
    
    def test_create_training_data(self):
        """Test creating AI training data"""
        training_data = AITrainingData.objects.create(
            company=self.company,
            description='RESTAURANTE XYZ',
            amount=Decimal('-50.00'),
            transaction_type='debit',
            counterpart_name='RESTAURANTE XYZ LTDA',
            category=self.category,
            is_verified=True,
            verification_source='manual',
            verified_by=self.user,
            extracted_features={
                'description_keywords': ['restaurante', 'xyz'],
                'amount_range': 'low',
                'transaction_type': 'expense',
                'time_features': {
                    'hour': 12,
                    'day_of_week': 5,
                    'is_weekend': True
                }
            }
        )
        
        self.assertEqual(training_data.company, self.company)
        self.assertEqual(training_data.description, 'RESTAURANTE XYZ')
        self.assertEqual(training_data.amount, Decimal('-50.00'))
        self.assertEqual(training_data.transaction_type, 'debit')
        self.assertEqual(training_data.category, self.category)
        self.assertTrue(training_data.is_verified)
        self.assertEqual(training_data.verification_source, 'manual')
        self.assertEqual(training_data.verified_by, self.user)
        self.assertIsInstance(training_data.extracted_features, dict)
        self.assertIn('description_keywords', training_data.extracted_features)
    
    def test_training_data_sources(self):
        """Test different verification sources"""
        sources = ['manual', 'user_feedback', 'rule_based', 'ai_confident']
        
        for i, source in enumerate(sources):
            training_data = AITrainingData.objects.create(
                company=self.company,
                description=f'Test {source}',
                amount=Decimal(f'-{10 + i}.00'),
                transaction_type='debit',
                counterpart_name=f'Test Company {i}',
                category=self.category,
                verification_source=source,
                is_verified=True
            )
            self.assertEqual(training_data.verification_source, source)
    
    def test_training_data_string_representation(self):
        """Test string representation of training data"""
        training_data = AITrainingData.objects.create(
            company=self.company,
            description='SUPERMERCADO XYZ LTDA',
            amount=Decimal('-150.00'),
            transaction_type='debit',
            category=self.category,
            verification_source='manual'
        )
        
        expected = f"SUPERMERCADO XYZ LTDA → {self.category.name}"
        self.assertEqual(str(training_data), expected)
    
    def test_training_data_subcategory(self):
        """Test training data with subcategory"""
        # Create a subcategory
        subcategory = TransactionCategory.objects.create(
            name='Restaurantes',
            slug='restaurantes',
            category_type='expense',
            parent=self.category
        )
        
        training_data = AITrainingData.objects.create(
            company=self.company,
            description='RESTAURANTE ITALIANO',
            amount=Decimal('-200.00'),
            transaction_type='debit',
            category=self.category,
            subcategory=subcategory,
            verification_source='manual'
        )
        
        self.assertEqual(training_data.category, self.category)
        self.assertEqual(training_data.subcategory, subcategory)
    
    def test_training_data_company_isolation(self):
        """Test training data is isolated by company"""
        # Create another company
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        other_company = Company.objects.create(
            owner=other_user,
            name='Other Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create training data for both companies
        data1 = AITrainingData.objects.create(
            company=self.company,
            description='Test Company Data',
            amount=Decimal('-100.00'),
            transaction_type='debit',
            category=self.category,
            verification_source='manual'
        )
        
        data2 = AITrainingData.objects.create(
            company=other_company,
            description='Other Company Data',
            amount=Decimal('-200.00'),
            transaction_type='debit',
            category=self.category,
            verification_source='manual'
        )
        
        # Verify isolation
        company_data = AITrainingData.objects.filter(company=self.company)
        self.assertEqual(company_data.count(), 1)
        self.assertEqual(company_data.first(), data1)


class CategorySuggestionModelTest(TestCase):
    """Test CategorySuggestion model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create bank account
        self.provider = BankProvider.objects.create(
            code='001',
            name='Test Bank'
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            agency='0001',
            account_number='12345-6'
        )
        
        # Create default categories
        TransactionCategory.objects.create(
            name='Outros Despesas',
            slug='outros-despesas',
            category_type='expense',
            is_system=True,
            icon='outros'
        )
        
        TransactionCategory.objects.create(
            name='Outros Receitas',
            slug='outros-receitas',
            category_type='income',
            is_system=True,
            icon='outros'
        )
        
        # Create categories
        self.category1 = TransactionCategory.objects.create(
            name='Transport',
            slug='transport',
            category_type='expense',
            icon='transport'
        )
        
        self.category2 = TransactionCategory.objects.create(
            name='Entertainment',
            slug='entertainment',
            category_type='expense',
            icon='entertainment'
        )
        
        # Create transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.account,
            amount=Decimal('-25.00'),
            transaction_type='debit',
            description='UBER TRIP',
            transaction_date=timezone.now().date()
        )
    
    def test_create_category_suggestion(self):
        """Test creating a category suggestion"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.category1,
            confidence_score=0.92,
            model_version='gpt-4o-mini',
            alternative_suggestions=[
                {'category_id': str(self.category2.id), 'score': 0.75},
                {'category_id': 'other_id', 'score': 0.60}
            ],
            features_used=['description', 'amount', 'counterpart']
        )
        
        self.assertEqual(suggestion.transaction, self.transaction)
        self.assertEqual(suggestion.suggested_category, self.category1)
        self.assertEqual(suggestion.confidence_score, 0.92)
        self.assertEqual(suggestion.model_version, 'gpt-4o-mini')
        self.assertFalse(suggestion.is_accepted)
        self.assertFalse(suggestion.is_rejected)
        self.assertEqual(suggestion.user_feedback, '')
        self.assertIsInstance(suggestion.alternative_suggestions, list)
        self.assertEqual(len(suggestion.alternative_suggestions), 2)
    
    def test_suggestion_acceptance(self):
        """Test accepting a suggestion"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.category1,
            confidence_score=0.85,
            model_version='gpt-4o-mini'
        )
        
        # Accept suggestion
        suggestion.is_accepted = True
        suggestion.reviewed_at = timezone.now()
        suggestion.reviewed_by = self.user
        suggestion.save()
        
        suggestion.refresh_from_db()
        self.assertTrue(suggestion.is_accepted)
        self.assertFalse(suggestion.is_rejected)
        self.assertIsNotNone(suggestion.reviewed_at)
        self.assertEqual(suggestion.reviewed_by, self.user)
    
    def test_suggestion_rejection_with_feedback(self):
        """Test rejecting a suggestion with feedback"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.category1,
            confidence_score=0.75,
            model_version='gpt-4o-mini'
        )
        
        # Reject with feedback
        suggestion.is_rejected = True
        suggestion.user_feedback = 'Esta transação deveria ser categorizada como Entretenimento'
        suggestion.reviewed_at = timezone.now()
        suggestion.reviewed_by = self.user
        suggestion.save()
        
        suggestion.refresh_from_db()
        self.assertTrue(suggestion.is_rejected)
        self.assertFalse(suggestion.is_accepted)
        self.assertEqual(suggestion.user_feedback, 'Esta transação deveria ser categorizada como Entretenimento')
        self.assertIsNotNone(suggestion.reviewed_at)
    
    def test_suggestion_model_versions(self):
        """Test different AI model versions"""
        versions = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o-mini']
        
        for i, version in enumerate(versions):
            transaction = Transaction.objects.create(
                bank_account=self.account,
                amount=Decimal(f'-{10 + i}.00'),
                transaction_type='debit',
                description=f'Test {version}',
                transaction_date=timezone.now().date()
            )
            
            suggestion = CategorySuggestion.objects.create(
                transaction=transaction,
                suggested_category=self.category1,
                confidence_score=0.80,
                model_version=version
            )
            
            self.assertEqual(suggestion.model_version, version)
    
    def test_suggestion_string_representation(self):
        """Test string representation of suggestion"""
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.category1,
            confidence_score=0.88,
            model_version='gpt-4o-mini'
        )
        
        expected = f"UBER TRIP → {self.category1.name} (0.88)"
        self.assertEqual(str(suggestion), expected)
    
    def test_suggestion_unique_transaction(self):
        """Test that each transaction can only have one suggestion"""
        CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.category1,
            confidence_score=0.90,
            model_version='gpt-4o-mini'
        )
        
        # Try to create another suggestion for same transaction
        with self.assertRaises(IntegrityError):
            CategorySuggestion.objects.create(
                transaction=self.transaction,
                suggested_category=self.category2,
                confidence_score=0.85,
                model_version='gpt-4'
            )
    
    def test_suggestion_features_used(self):
        """Test tracking features used for categorization"""
        features = ['description', 'amount', 'transaction_type', 'counterpart', 'date_patterns']
        
        suggestion = CategorySuggestion.objects.create(
            transaction=self.transaction,
            suggested_category=self.category1,
            confidence_score=0.91,
            model_version='gpt-4o-mini',
            features_used=features
        )
        
        self.assertIsInstance(suggestion.features_used, list)
        self.assertEqual(len(suggestion.features_used), 5)
        self.assertIn('description', suggestion.features_used)
        self.assertIn('amount', suggestion.features_used)


class CategoryPerformanceModelTest(TestCase):
    """Test CategoryPerformance model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Shopping',
            slug='shopping',
            category_type='expense',
            icon='shopping'
        )
    
    def test_create_performance_metrics(self):
        """Test creating performance metrics"""
        from datetime import date
        
        performance = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            total_predictions=100,
            correct_predictions=85,
            false_positives=10,
            false_negatives=5,
            accuracy=0.85,
            precision=0.88,
            recall=0.82,
            f1_score=0.85
        )
        
        self.assertEqual(performance.company, self.company)
        self.assertEqual(performance.category, self.category)
        self.assertEqual(performance.period_start, date(2024, 1, 1))
        self.assertEqual(performance.period_end, date(2024, 1, 31))
        self.assertEqual(performance.total_predictions, 100)
        self.assertEqual(performance.correct_predictions, 85)
        self.assertEqual(performance.accuracy, 0.85)
    
    def test_update_metrics_method(self):
        """Test the update_metrics method"""
        from datetime import date
        
        performance = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            total_predictions=100,
            correct_predictions=85,
            false_positives=10,
            false_negatives=5
        )
        
        # Call update_metrics to recalculate
        performance.update_metrics()
        
        performance.refresh_from_db()
        self.assertEqual(performance.accuracy, 0.85)  # 85/100
        self.assertAlmostEqual(performance.precision, 0.8947, 4)  # 85/(85+10)
        self.assertAlmostEqual(performance.recall, 0.9444, 4)  # 85/(85+5)
        self.assertAlmostEqual(performance.f1_score, 0.9189, 4)  # 2*precision*recall/(precision+recall)
    
    def test_performance_string_representation(self):
        """Test string representation of performance"""
        from datetime import date
        
        performance = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            accuracy=0.92
        )
        
        expected = f"{self.category.name} - 92.00% accuracy"
        self.assertEqual(str(performance), expected)
    
    def test_performance_unique_constraint(self):
        """Test unique constraint on company, category, period"""
        from datetime import date
        
        CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )
        
        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            CategoryPerformance.objects.create(
                company=self.company,
                category=self.category,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31)
            )
    
    def test_performance_different_periods(self):
        """Test performance metrics for different periods"""
        from datetime import date
        
        perf1 = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            accuracy=0.85
        )
        
        perf2 = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 2, 1),
            period_end=date(2024, 2, 29),
            accuracy=0.90
        )
        
        # Both should exist without conflict
        performances = CategoryPerformance.objects.filter(company=self.company, category=self.category)
        self.assertEqual(performances.count(), 2)
        self.assertIn(perf1, performances)
        self.assertIn(perf2, performances)
    
    def test_performance_company_isolation(self):
        """Test performance metrics are isolated by company"""
        # Create another company
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        other_company = Company.objects.create(
            owner=other_user,
            name='Other Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create performance metrics for both companies
        from datetime import date
        
        perf1 = CategoryPerformance.objects.create(
            company=self.company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )
        
        perf2 = CategoryPerformance.objects.create(
            company=other_company,
            category=self.category,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )
        
        # Verify isolation
        company_perfs = CategoryPerformance.objects.filter(company=self.company)
        self.assertEqual(company_perfs.count(), 1)
        self.assertEqual(company_perfs.first(), perf1)


class CategorizationLogModelTest(TestCase):
    """Test CategorizationLog model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        
        # Create bank account
        self.provider = BankProvider.objects.create(
            code='001',
            name='Test Bank'
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            agency='0001',
            account_number='12345-6'
        )
        
        # Create default categories
        self.default_expense_category = TransactionCategory.objects.create(
            name='Outros Despesas',
            slug='outros-despesas',
            category_type='expense',
            is_system=True,
            icon='outros'
        )
        
        self.default_income_category = TransactionCategory.objects.create(
            name='Outros Receitas',
            slug='outros-receitas',
            category_type='income',
            is_system=True,
            icon='outros'
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Groceries',
            slug='groceries',
            category_type='expense',
            icon='groceries'
        )
        
        # Create transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.account,
            amount=Decimal('-150.00'),
            transaction_type='debit',
            description='SUPERMERCADO ABC',
            transaction_date=timezone.now().date()
        )
    
    def test_create_categorization_log(self):
        """Test creating a categorization log entry"""
        log = CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.category,
            confidence_score=0.94,
            processing_time_ms=235,
            ai_model_version='gpt-4o-mini',
            was_accepted=True,
            final_category=self.category
        )
        
        self.assertEqual(log.transaction, self.transaction)
        self.assertEqual(log.method, 'ai')
        self.assertEqual(log.suggested_category, self.category)
        self.assertEqual(log.confidence_score, 0.94)
        self.assertEqual(log.processing_time_ms, 235)
        self.assertEqual(log.ai_model_version, 'gpt-4o-mini')
        self.assertTrue(log.was_accepted)
        self.assertEqual(log.final_category, self.category)
    
    def test_categorization_methods(self):
        """Test different categorization methods"""
        methods = ['ai', 'rule', 'manual', 'bulk', 'recurring']
        
        for method in methods:
            log = CategorizationLog.objects.create(
                transaction=Transaction.objects.create(
                    bank_account=self.account,
                    amount=Decimal('-10.00'),
                    transaction_type='debit',
                    description=f'Test {method}',
                    transaction_date=timezone.now().date()
                ),
                method=method,
                suggested_category=self.category,
                confidence_score=0.85
            )
            self.assertEqual(log.method, method)
    
    def test_categorization_with_rule(self):
        """Test categorization log with rule reference"""
        # Create a rule
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Supermercado Rule',
            rule_type='keyword',
            conditions={'keywords': ['supermercado', 'mercado']}
        )
        
        log = CategorizationLog.objects.create(
            transaction=self.transaction,
            method='rule',
            suggested_category=self.category,
            confidence_score=0.95,
            rule_used=rule,
            was_accepted=True
        )
        
        self.assertEqual(log.method, 'rule')
        self.assertEqual(log.rule_used, rule)
        self.assertEqual(log.confidence_score, 0.95)
        self.assertTrue(log.was_accepted)
    
    def test_log_string_representation(self):
        """Test string representation of log"""
        log = CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.category,
            confidence_score=0.88
        )
        
        expected = f"ai - {self.category.name} (0.88)"
        self.assertEqual(str(log), expected)
    
    def test_log_ordering(self):
        """Test logs are ordered by timestamp descending"""
        # Clear any existing logs
        CategorizationLog.objects.all().delete()
        
        log1 = CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.category,
            confidence_score=0.85
        )
        
        # Create another log entry
        transaction2 = Transaction.objects.create(
            bank_account=self.account,
            amount=Decimal('-50.00'),
            transaction_type='debit',
            description='Test 2',
            transaction_date=timezone.now().date()
        )
        
        log2 = CategorizationLog.objects.create(
            transaction=transaction2,
            method='rule',
            suggested_category=self.category,
            confidence_score=0.90
        )
        
        logs = CategorizationLog.objects.all().order_by('-created_at')
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)
    
    def test_log_final_category_different(self):
        """Test when final category differs from suggested"""
        # Create another category
        other_category = TransactionCategory.objects.create(
            name='Restaurants',
            slug='restaurants',
            category_type='expense',
            icon='restaurant'
        )
        
        log = CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.category,  # Suggested Groceries
            confidence_score=0.75,
            was_accepted=False,
            final_category=other_category  # User chose Restaurants
        )
        
        self.assertEqual(log.suggested_category, self.category)
        self.assertEqual(log.final_category, other_category)
        self.assertFalse(log.was_accepted)
        self.assertNotEqual(log.suggested_category, log.final_category)
    
    def test_log_processing_time(self):
        """Test tracking processing time"""
        log = CategorizationLog.objects.create(
            transaction=self.transaction,
            method='ai',
            suggested_category=self.category,
            confidence_score=0.92,
            processing_time_ms=150,  # 150 milliseconds
            ai_model_version='gpt-4o-mini'
        )
        
        self.assertEqual(log.processing_time_ms, 150)
        
    def test_log_statistics_aggregation(self):
        """Test gathering statistics from logs"""
        # Create multiple log entries
        for i in range(10):
            was_accepted = i < 8  # 80% acceptance rate
            CategorizationLog.objects.create(
                transaction=Transaction.objects.create(
                    bank_account=self.account,
                    amount=Decimal(f'-{10 + i}.00'),
                    transaction_type='debit',
                    description=f'Transaction {i}',
                    transaction_date=timezone.now().date()
                ),
                method='ai' if i < 5 else 'rule',
                suggested_category=self.category,
                confidence_score=0.70 + (i * 0.02),
                processing_time_ms=100 + (i * 50),
                was_accepted=was_accepted
            )
        
        # Verify we can query statistics
        from django.db.models import Avg, Count
        
        stats = CategorizationLog.objects.aggregate(
            total=Count('id'),
            accepted=Count('id', filter=models.Q(was_accepted=True)),
            avg_confidence=Avg('confidence_score'),
            avg_processing_time=Avg('processing_time_ms')
        )
        
        self.assertEqual(stats['total'], 10)
        self.assertEqual(stats['accepted'], 8)
        self.assertAlmostEqual(stats['avg_confidence'], 0.79, 2)
        self.assertEqual(stats['avg_processing_time'], 325.0)