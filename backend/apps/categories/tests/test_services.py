"""
Comprehensive tests for Categories app AI services
Tests for AICategorizationService, RuleBasedCategorizationService,
CategoryAnalyticsService, and BulkCategorizationService
"""
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from apps.authentication.models import User
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.categories.models import (AITrainingData, CategorizationLog,
                                    CategoryRule, CategorySuggestion)
from apps.categories.services import (AICategorizationService,
                                      BulkCategorizationService,
                                      CategoryAnalyticsService,
                                      RuleBasedCategorizationService)
from apps.companies.models import Company, SubscriptionPlan
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone


class BaseCategoryTestCase(TestCase):
    """Base test case with common setup for category tests"""
    
    def setUp(self):
        """Common setup for all test cases"""
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=Decimal('49.90'),
            price_yearly=Decimal('499.00'),
            max_transactions=1000,
            max_bank_accounts=2,
            max_users=3
        )
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001'
        )


class TestAICategorizationService(BaseCategoryTestCase):
    """Test AICategorizationService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Call parent setUp
        super().setUp()
        
        # Create test user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678000123',
            owner=self.user,
            subscription_plan=self.subscription_plan
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_number='12345',
            agency='0001',
            account_type='checking'
        )
        
        # Create test categories
        self.food_category = TransactionCategory.objects.create(
            name='Alimentação',
            slug='alimentacao',
            category_type='expense',
            icon='food',
            is_system=True,
            keywords='restaurante,lanchonete,comida,alimento'
        )
        
        self.transport_category = TransactionCategory.objects.create(
            name='Transporte',
            slug='transporte',
            category_type='expense',
            icon='car',
            is_system=True,
            keywords='uber,taxi,combustivel,gasolina,onibus'
        )
        
        self.income_category = TransactionCategory.objects.create(
            name='Receitas',
            slug='receitas',
            category_type='income',
            icon='money',
            is_system=True,
            keywords='pagamento,salario,venda'
        )
        
        self.default_expense = TransactionCategory.objects.create(
            name='Outros',
            slug='outros-despesas',
            category_type='expense',
            icon='other',
            is_system=True
        )
        
        self.default_income = TransactionCategory.objects.create(
            name='Outras Receitas',
            slug='outros-receitas',
            category_type='income',
            icon='other',
            is_system=True
        )
        
        # Create test transaction
        self.transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='TEST123',
            amount=Decimal('-50.00'),
            description='IFOOD RESTAURANTE XYZ',
            transaction_type='expense',
            counterpart_name='IFOOD',
            transaction_date=timezone.now()
        )
        
        # Initialize service with mocked OpenAI key
        with override_settings(OPENAI_API_KEY='test-key'):
            self.service = AICategorizationService()
            # Mock the OpenAI client to prevent real API calls
            self.service.client = MagicMock()
    
    def test_init_without_api_key(self):
        """Test initialization without OpenAI API key raises error"""
        with override_settings(OPENAI_API_KEY=''):
            with self.assertRaises(ValueError) as context:
                AICategorizationService()
            self.assertIn('OPENAI_API_KEY must be configured', str(context.exception))
    
    def test_categorize_transaction_with_rule_match(self):
        """Test categorization when rule matches"""
        # Create a matching rule
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.food_category,
            name='Food Rule',
            rule_type='keyword',
            conditions={'keywords': ['ifood', 'restaurante']},
            priority=1,
            confidence_threshold=0.85
        )
        
        result = self.service.categorize_transaction(self.transaction)
        
        self.assertEqual(result['category'], self.food_category)
        self.assertEqual(result['confidence'], 0.85)
        self.assertEqual(result['method'], 'rule')
        self.assertEqual(result['rule'], rule)
        
        # Check that rule match count was incremented
        rule.refresh_from_db()
        self.assertEqual(rule.match_count, 1)
        
        # Check categorization log was created
        log = CategorizationLog.objects.filter(
            transaction=self.transaction,
            method='rule'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.method, 'rule')
        self.assertEqual(log.suggested_category, self.food_category)
        self.assertEqual(log.confidence_score, 0.85)
        self.assertEqual(log.rule_used, rule)
    
    @patch('apps.categories.services.OpenAI')
    def test_categorize_transaction_with_ai_fallback(self, mock_openai_class):
        """Test AI categorization when no rules match"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
        CATEGORIA: Transporte
        CONFIANÇA: 0.9
        MOTIVO: Transação com Uber indica serviço de transporte
        """
        mock_client.chat.completions.create.return_value = mock_response
        
        # Update transaction to not match any rules
        self.transaction.description = 'UBER DO BRASIL'
        self.transaction.counterpart_name = 'UBER'
        self.transaction.save()
        
        # Use the existing service with mocked client
        self.service.client = mock_client
        
        result = self.service.categorize_transaction(self.transaction)
        
        self.assertEqual(result['category'], self.transport_category)
        self.assertEqual(result['confidence'], 0.9)
        self.assertEqual(result['method'], 'ai')
        self.assertEqual(result['reason'], 'Transação com Uber indica serviço de transporte')
        
        # Check API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs['model'], 'gpt-4o-mini')
        self.assertEqual(call_args.kwargs['temperature'], 0.1)
        
        # Check categorization log
        log = CategorizationLog.objects.filter(
            transaction=self.transaction,
            method='ai'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.method, 'ai')
        self.assertEqual(log.ai_model_version, 'gpt-4o-mini')
    
    def test_categorize_transaction_default_fallback(self):
        """Test default category fallback when no matches"""
        # No rules and AI returns low confidence
        with patch.object(self.service, '_ai_categorize', return_value={'confidence': 0.5}):
            result = self.service.categorize_transaction(self.transaction)
        
        self.assertEqual(result['category'], self.default_expense)
        self.assertEqual(result['confidence'], 0.1)
        self.assertEqual(result['method'], 'default')
        self.assertEqual(result['reason'], 'Categoria padrão')
    
    def test_categorize_transaction_error_handling(self):
        """Test error handling during categorization"""
        # Mock an error in rule application
        with patch.object(self.service, '_apply_rules', side_effect=Exception('Test error')):
            result = self.service.categorize_transaction(self.transaction)
        
        # Should return default category
        self.assertEqual(result['category'], self.default_expense)
        self.assertEqual(result['confidence'], 0.1)
        self.assertEqual(result['method'], 'default')
    
    def test_rule_matches_keyword(self):
        """Test keyword rule matching"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.food_category,
            name='Food Keywords',
            rule_type='keyword',
            conditions={'keywords': ['restaurante', 'comida', 'lanche']}
        )
        
        self.assertTrue(self.service._rule_matches(rule, self.transaction))
        
        # Test non-matching
        self.transaction.description = 'UBER VIAGEM'
        self.assertFalse(self.service._rule_matches(rule, self.transaction))
    
    def test_rule_matches_amount_range(self):
        """Test amount range rule matching"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.food_category,
            name='Small Expenses',
            rule_type='amount_range',
            conditions={'min_amount': 10, 'max_amount': 100}
        )
        
        self.assertTrue(self.service._rule_matches(rule, self.transaction))
        
        # Test outside range
        self.transaction.amount = Decimal('-200.00')
        self.assertFalse(self.service._rule_matches(rule, self.transaction))
    
    def test_rule_matches_counterpart(self):
        """Test counterpart rule matching"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.food_category,
            name='Food Delivery',
            rule_type='counterpart',
            conditions={'counterparts': ['IFOOD', 'RAPPI', 'UBER EATS']}
        )
        
        self.assertTrue(self.service._rule_matches(rule, self.transaction))
        
        # Test non-matching
        self.transaction.counterpart_name = 'AMAZON'
        self.assertFalse(self.service._rule_matches(rule, self.transaction))
    
    def test_rule_matches_pattern(self):
        """Test regex pattern rule matching"""
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.transport_category,
            name='Transport Pattern',
            rule_type='pattern',
            conditions={'pattern': r'(UBER|TAXI|99)\s+(VIAGEM|CORRIDA)'}
        )
        
        self.transaction.description = 'UBER VIAGEM SAO PAULO'
        self.assertTrue(self.service._rule_matches(rule, self.transaction))
        
        # Test non-matching
        self.transaction.description = 'IFOOD PEDIDO'
        self.assertFalse(self.service._rule_matches(rule, self.transaction))
        
        # Test invalid regex
        rule.conditions = {'pattern': '[invalid(regex'}
        self.assertFalse(self.service._rule_matches(rule, self.transaction))
    
    def test_parse_ai_response(self):
        """Test parsing of AI response"""
        categories = TransactionCategory.objects.all()
        
        # Valid response
        response = """
        CATEGORIA: Alimentação
        CONFIANÇA: 0.85
        MOTIVO: Transação com IFOOD indica pedido de comida
        """
        result = self.service._parse_ai_response(response, categories)
        
        self.assertEqual(result['category'], self.food_category)
        self.assertEqual(result['confidence'], 0.85)
        self.assertEqual(result['reason'], 'Transação com IFOOD indica pedido de comida')
        
        # Invalid response format
        response = "Invalid format response"
        result = self.service._parse_ai_response(response, categories)
        self.assertIsNone(result)
        
        # Non-existent category
        response = """
        CATEGORIA: Categoria Inexistente
        CONFIANÇA: 0.9
        MOTIVO: Test
        """
        result = self.service._parse_ai_response(response, categories)
        self.assertIsNone(result)
    
    def test_get_default_category(self):
        """Test default category selection"""
        # Test expense
        result = self.service._get_default_category(self.transaction)
        self.assertEqual(result['category'], self.default_expense)
        
        # Test income
        self.transaction.is_income = True
        self.transaction.transaction_type = 'income'
        result = self.service._get_default_category(self.transaction)
        self.assertEqual(result['category'], self.default_income)
    
    def test_learn_from_feedback(self):
        """Test learning from user feedback"""
        self.service.learn_from_feedback(
            self.transaction,
            self.food_category,
            self.user
        )
        
        # Check training data was created
        training_data = AITrainingData.objects.get(
            company=self.company,
            description=self.transaction.description
        )
        self.assertEqual(training_data.category, self.food_category)
        self.assertTrue(training_data.is_verified)
        self.assertEqual(training_data.verification_source, 'user_feedback')
        self.assertEqual(training_data.verified_by, self.user)
        
        # Check extracted features
        features = training_data.extracted_features
        self.assertIn('description_length', features)
        self.assertIn('amount_range', features)
        self.assertIn('has_counterpart', features)
    
    def test_extract_features(self):
        """Test feature extraction from transaction"""
        features = self.service._extract_features(self.transaction)
        
        self.assertEqual(features['description_length'], len(self.transaction.description))
        self.assertEqual(features['amount_range'], 'low')  # 50 is in low range
        self.assertEqual(features['transaction_day'], self.transaction.transaction_date.day)
        self.assertTrue(features['has_counterpart'])
        self.assertGreater(features['description_words'], 0)
        self.assertGreater(features['amount_log'], 0)
    
    def test_get_amount_range(self):
        """Test amount range categorization"""
        test_cases = [
            (Decimal('30'), 'very_low'),
            (Decimal('100'), 'low'),
            (Decimal('300'), 'medium'),
            (Decimal('700'), 'high'),
            (Decimal('2000'), 'very_high'),
        ]
        
        for amount, expected_range in test_cases:
            result = self.service._get_amount_range(amount)
            self.assertEqual(result, expected_range, f"Amount {amount} should be {expected_range}")


class TestRuleBasedCategorizationService(BaseCategoryTestCase):
    """Test RuleBasedCategorizationService functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678000123',
            owner=self.user
        )
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense',
            icon='test'
        )
        self.service = RuleBasedCategorizationService()
        
        # Create bank account for transactions
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_number='12345',
            agency='0001',
            account_type='checking'
        )
    
    def test_create_keyword_rule(self):
        """Test creating keyword-based rule"""
        keywords = ['pizza', 'hamburger', 'restaurante']
        rule = self.service.create_keyword_rule(
            self.company,
            self.category,
            keywords,
            'Food Keywords Rule'
        )
        
        self.assertEqual(rule.company, self.company)
        self.assertEqual(rule.category, self.category)
        self.assertEqual(rule.name, 'Food Keywords Rule')
        self.assertEqual(rule.rule_type, 'keyword')
        self.assertEqual(rule.conditions['keywords'], keywords)
        self.assertEqual(rule.priority, 1)
        self.assertTrue(rule.is_active)
    
    def test_create_amount_rule(self):
        """Test creating amount range rule"""
        rule = self.service.create_amount_rule(
            self.company,
            self.category,
            Decimal('100.00'),
            Decimal('500.00'),
            'Medium Expenses Rule'
        )
        
        self.assertEqual(rule.rule_type, 'amount_range')
        self.assertEqual(rule.conditions['min_amount'], 100.0)
        self.assertEqual(rule.conditions['max_amount'], 500.0)
        self.assertEqual(rule.priority, 2)
    
    def test_create_counterpart_rule(self):
        """Test creating counterpart-based rule"""
        counterparts = ['UBER', 'CABIFY', '99 TAXI']
        rule = self.service.create_counterpart_rule(
            self.company,
            self.category,
            counterparts,
            'Transport Services Rule'
        )
        
        self.assertEqual(rule.rule_type, 'counterpart')
        self.assertEqual(rule.conditions['counterparts'], counterparts)
        self.assertEqual(rule.priority, 3)
    
    def test_suggest_rules_from_patterns(self):
        """Test suggesting rules from transaction patterns"""
        # Create repeated transactions with same description
        for i in range(5):
            Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'TEST{i}',
                amount=Decimal('-50.00'),
                description='NETFLIX ASSINATURA MENSAL',
                transaction_type='expense',
                counterpart_name='NETFLIX',
                transaction_date=timezone.now(),
                category=self.category
            )
        
        # Create other transactions
        Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='OTHER1',
            amount=Decimal('-30.00'),
            description='RANDOM EXPENSE',
            transaction_type='expense',
            counterpart_name='OTHER',
            transaction_date=timezone.now(),
            category=self.category
        )
        
        suggestions = self.service.suggest_rules_from_patterns(self.company)
        
        self.assertGreater(len(suggestions), 0)
        
        # Check Netflix suggestion
        netflix_suggestion = next(
            (s for s in suggestions if 'netflix' in str(s['keywords']).lower()),
            None
        )
        self.assertIsNotNone(netflix_suggestion)
        self.assertEqual(netflix_suggestion['type'], 'keyword')
        self.assertEqual(netflix_suggestion['frequency'], 5)
        self.assertIn('netflix', [k.lower() for k in netflix_suggestion['keywords']])
    
    def test_extract_keywords(self):
        """Test keyword extraction from description"""
        test_cases = [
            (
                'PIX TRANSFERENCIA BANCO ITAU CONTA 12345',
                []  # All common words should be filtered
            ),
            (
                'NETFLIX ASSINATURA MENSAL STREAMING',
                ['netflix', 'assinatura', 'mensal']
            ),
            (
                'UBER VIAGEM AEROPORTO GUARULHOS',
                ['viagem', 'aeroporto', 'guarulhos']
            ),
        ]
        
        for description, expected in test_cases:
            keywords = self.service._extract_keywords(description)
            # Compare lowercase versions
            keywords_lower = [k.lower() for k in keywords]
            expected_lower = [e.lower() for e in expected]
            
            for expected_keyword in expected_lower:
                self.assertIn(
                    expected_keyword,
                    keywords_lower,
                    f"Expected '{expected_keyword}' in keywords for '{description}'"
                )


class TestCategoryAnalyticsService(BaseCategoryTestCase):
    """Test CategoryAnalyticsService functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678000123',
            owner=self.user
        )
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense',
            icon='test'
        )
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_number='12345',
            agency='0001',
            account_type='checking'
        )
        self.service = CategoryAnalyticsService()
    
    def test_calculate_accuracy_metrics_empty(self):
        """Test accuracy metrics with no data"""
        metrics = self.service.calculate_accuracy_metrics(self.company, 30)
        
        self.assertEqual(metrics['total_categorizations'], 0)
        self.assertEqual(metrics['accuracy'], 0.0)
        self.assertEqual(metrics['ai_accuracy'], 0.0)
        self.assertEqual(metrics['rule_accuracy'], 0.0)
        self.assertEqual(metrics['method_breakdown'], {})
    
    def test_calculate_accuracy_metrics_with_data(self):
        """Test accuracy metrics with categorization logs"""
        # Create test transactions
        transactions = []
        for i in range(10):
            transaction = Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'TEST{i}',
                amount=Decimal('-50.00'),
                description=f'Test Transaction {i}',
                transaction_type='expense',
                transaction_date=timezone.now()
            )
            transactions.append(transaction)
        
        # Create categorization logs with different methods
        # AI categorizations: 5 total, 4 correct
        for i in range(5):
            CategorizationLog.objects.create(
                transaction=transactions[i],
                method='ai',
                suggested_category=self.category,
                confidence_score=0.8,
                was_accepted=(i < 4),  # 4 correct, 1 incorrect
                processing_time_ms=100
            )
        
        # Rule categorizations: 3 total, 3 correct
        for i in range(5, 8):
            CategorizationLog.objects.create(
                transaction=transactions[i],
                method='rule',
                suggested_category=self.category,
                confidence_score=0.9,
                was_accepted=True,
                processing_time_ms=50
            )
        
        # Manual categorizations: 2 total, 1 correct
        for i in range(8, 10):
            CategorizationLog.objects.create(
                transaction=transactions[i],
                method='manual',
                suggested_category=self.category,
                confidence_score=1.0,
                was_accepted=(i == 8),  # 1 correct, 1 incorrect
                processing_time_ms=0
            )
        
        metrics = self.service.calculate_accuracy_metrics(self.company, 30)
        
        self.assertEqual(metrics['total_categorizations'], 10)
        self.assertEqual(metrics['accuracy'], 0.8)  # 8/10 correct
        self.assertEqual(metrics['ai_accuracy'], 0.8)  # 4/5 correct
        self.assertEqual(metrics['rule_accuracy'], 1.0)  # 3/3 correct
        self.assertEqual(metrics['period_days'], 30)
        
        # Check method breakdown
        self.assertEqual(metrics['method_breakdown']['ai']['total'], 5)
        self.assertEqual(metrics['method_breakdown']['ai']['correct'], 4)
        self.assertEqual(metrics['method_breakdown']['rule']['total'], 3)
        self.assertEqual(metrics['method_breakdown']['rule']['correct'], 3)
        self.assertEqual(metrics['method_breakdown']['manual']['total'], 2)
        self.assertEqual(metrics['method_breakdown']['manual']['correct'], 1)
    
    def test_get_category_insights(self):
        """Test category usage insights"""
        # Create transactions with categories
        food_category = TransactionCategory.objects.create(
            name='Food',
            slug='food',
            category_type='expense',
            icon='food'
        )
        
        # Create 10 food transactions
        for i in range(10):
            transaction = Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'FOOD{i}',
                amount=Decimal('-30.00'),
                description=f'Restaurant {i}',
                transaction_type='expense',
                transaction_date=timezone.now(),
                category=food_category,
                ai_category_confidence=0.85
            )
            
            # Create categorization logs (8 correct, 2 incorrect)
            CategorizationLog.objects.create(
                transaction=transaction,
                method='ai',
                suggested_category=food_category,
                confidence_score=0.85,
                was_accepted=(i < 8)
            )
        
        insights = self.service.get_category_insights(self.company)
        
        self.assertEqual(len(insights), 1)
        
        food_insight = insights[0]
        self.assertEqual(food_insight['category'], 'Food')
        self.assertEqual(food_insight['icon'], 'food')
        self.assertEqual(food_insight['type'], 'expense')
        self.assertEqual(food_insight['transaction_count'], 10)
        self.assertAlmostEqual(food_insight['avg_confidence'], 0.85, places=2)
        self.assertEqual(food_insight['accuracy'], 0.8)  # 8/10
        self.assertFalse(food_insight['needs_attention'])  # accuracy >= 0.7
    
    def test_suggest_improvements(self):
        """Test improvement suggestions"""
        # Create category with low accuracy
        low_accuracy_category = TransactionCategory.objects.create(
            name='Low Accuracy Category',
            slug='low-accuracy',
            category_type='expense',
            icon='warning'
        )
        
        # Create 25 transactions with this category
        for i in range(25):
            transaction = Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'LOW{i}',
                amount=Decimal('-100.00'),
                description=f'Unclear Transaction {i}',
                transaction_type='expense',
                transaction_date=timezone.now(),
                category=low_accuracy_category,
                ai_category_confidence=0.5
            )
            
            # Create logs with low accuracy (only 10 correct out of 25)
            CategorizationLog.objects.create(
                transaction=transaction,
                method='ai',
                suggested_category=low_accuracy_category,
                confidence_score=0.5,
                was_accepted=(i < 10)
            )
        
        # Create uncategorized repeated transactions
        for i in range(5):
            Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'UNCAT{i}',
                amount=Decimal('-200.00'),
                description='RECURRING PAYMENT XYZ',
                transaction_type='expense',
                transaction_date=timezone.now(),
                category=None
            )
        
        suggestions = self.service.suggest_improvements(self.company)
        
        # Check accuracy improvement suggestion
        accuracy_suggestions = [s for s in suggestions if s['type'] == 'accuracy_improvement']
        self.assertGreater(len(accuracy_suggestions), 0)
        
        low_accuracy_suggestion = accuracy_suggestions[0]
        self.assertEqual(low_accuracy_suggestion['category'], 'Low Accuracy Category')
        self.assertEqual(low_accuracy_suggestion['current_accuracy'], 0.4)  # 10/25
        self.assertEqual(low_accuracy_suggestion['priority'], 'high')  # >20 transactions
        
        # Check rule creation suggestion
        rule_suggestions = [s for s in suggestions if s['type'] == 'rule_creation']
        self.assertGreater(len(rule_suggestions), 0)
        
        recurring_suggestion = rule_suggestions[0]
        self.assertEqual(recurring_suggestion['description'], 'RECURRING PAYMENT XYZ')
        self.assertEqual(recurring_suggestion['frequency'], 5)
        self.assertEqual(recurring_suggestion['priority'], 'medium')


class TestBulkCategorizationService(BaseCategoryTestCase):
    """Test BulkCategorizationService functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678000123',
            owner=self.user
        )
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense',
            icon='test'
        )
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_number='12345',
            agency='0001',
            account_type='checking'
        )
        
        # Mock OpenAI API key
        with override_settings(OPENAI_API_KEY='test-key'):
            self.service = BulkCategorizationService()
    
    @patch('apps.categories.services.AICategorizationService.categorize_transaction')
    def test_categorize_uncategorized_transactions(self, mock_categorize):
        """Test bulk categorization of uncategorized transactions"""
        # Create uncategorized transactions
        transactions = []
        for i in range(10):
            transaction = Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'UNCAT{i}',
                amount=Decimal('-50.00'),
                description=f'Uncategorized Transaction {i}',
                transaction_type='expense',
                transaction_date=timezone.now(),
                category=None,
                is_ai_categorized=False
            )
            transactions.append(transaction)
        
        # Mock categorization results
        def mock_categorize_side_effect(transaction):
            # Simulate different confidence levels
            if 'Transaction 0' in transaction.description:
                return None  # Failed
            elif 'Transaction 1' in transaction.description:
                return {'category': self.category, 'confidence': 0.9, 'method': 'ai'}
            elif 'Transaction 2' in transaction.description:
                return {'category': self.category, 'confidence': 0.6, 'method': 'ai'}
            else:
                return {'category': self.category, 'confidence': 0.85, 'method': 'ai'}
        
        mock_categorize.side_effect = mock_categorize_side_effect
        
        results = self.service.categorize_uncategorized_transactions(self.company, limit=5)
        
        self.assertEqual(results['total_processed'], 5)
        self.assertEqual(results['categorized'], 4)  # All except transaction 0
        self.assertEqual(results['failed'], 1)
        self.assertEqual(results['high_confidence'], 3)  # confidence >= 0.8
        self.assertEqual(results['low_confidence'], 1)  # confidence < 0.8
        
        # Check that transactions were updated
        transaction1 = Transaction.objects.get(description='Uncategorized Transaction 1')
        self.assertEqual(transaction1.category, self.category)
        self.assertEqual(transaction1.ai_category_confidence, 0.9)
        self.assertTrue(transaction1.is_ai_categorized)
    
    def test_apply_rule_to_existing_transactions(self):
        """Test applying a rule to existing transactions"""
        # Create a rule
        rule = CategoryRule.objects.create(
            company=self.company,
            category=self.category,
            name='Test Rule',
            rule_type='keyword',
            conditions={'keywords': ['payment', 'recurring']},
            confidence_threshold=0.85
        )
        
        # Create matching and non-matching transactions
        matching_transactions = []
        for i in range(5):
            transaction = Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'MATCH{i}',
                amount=Decimal('-100.00'),
                description=f'RECURRING PAYMENT SERVICE {i}',
                transaction_type='expense',
                transaction_date=timezone.now(),
                category=None
            )
            matching_transactions.append(transaction)
        
        # Already categorized transaction
        Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='ALREADY_CAT',
            amount=Decimal('-100.00'),
            description='RECURRING PAYMENT ALREADY CATEGORIZED',
            transaction_type='expense',
            transaction_date=timezone.now(),
            category=self.category
        )
        
        # Non-matching transaction
        Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='NO_MATCH',
            amount=Decimal('-100.00'),
            description='OTHER EXPENSE',
            transaction_type='expense',
            transaction_date=timezone.now(),
            category=None
        )
        
        results = self.service.apply_rule_to_existing_transactions(rule, limit=10)
        
        self.assertEqual(results['total_checked'], 7)
        self.assertEqual(results['matches_found'], 6)  # 5 uncategorized + 1 already categorized
        self.assertEqual(results['categorized'], 5)
        self.assertEqual(results['already_categorized'], 1)
        
        # Check that matching transactions were categorized
        for transaction in matching_transactions:
            transaction.refresh_from_db()
            self.assertEqual(transaction.category, self.category)
            self.assertEqual(transaction.ai_category_confidence, 0.85)
            self.assertTrue(transaction.is_ai_categorized)
        
        # Check rule match count was updated
        rule.refresh_from_db()
        self.assertEqual(rule.match_count, 6)
        
        # Check categorization logs were created
        logs = CategorizationLog.objects.filter(rule_used=rule)
        self.assertEqual(logs.count(), 5)
    
    @patch('apps.categories.services.AICategorizationService.categorize_transaction')
    def test_recategorize_low_confidence_transactions(self, mock_categorize):
        """Test recategorizing transactions with low confidence"""
        # Create low confidence transactions
        low_conf_transactions = []
        for i in range(5):
            transaction = Transaction.objects.create(
                bank_account=self.bank_account,
                external_id=f'LOWCONF{i}',
                amount=Decimal('-75.00'),
                description=f'Low Confidence Transaction {i}',
                transaction_type='expense',
                transaction_date=timezone.now(),
                category=self.category,
                ai_category_confidence=0.4,
                is_ai_categorized=True
            )
            low_conf_transactions.append(transaction)
        
        # Mock improved categorization results
        def mock_categorize_side_effect(transaction):
            if 'Transaction 0' in transaction.description:
                return {'category': self.category, 'confidence': 0.9, 'method': 'ai'}
            elif 'Transaction 1' in transaction.description:
                return {'category': self.category, 'confidence': 0.3, 'method': 'ai'}  # Worse
            else:
                return {'category': self.category, 'confidence': 0.7, 'method': 'ai'}
        
        mock_categorize.side_effect = mock_categorize_side_effect
        
        results = self.service.recategorize_low_confidence_transactions(
            self.company,
            confidence_threshold=0.5
        )
        
        self.assertEqual(results['total_processed'], 5)
        self.assertEqual(results['improved'], 3)  # Transactions 0, 2, 3, 4
        self.assertEqual(results['unchanged'], 2)  # Transaction 1 (worse) + failed to improve
        self.assertEqual(results['failed'], 0)
        
        # Check that improved transactions were updated
        transaction0 = Transaction.objects.get(description='Low Confidence Transaction 0')
        self.assertEqual(transaction0.ai_category_confidence, 0.9)
        
        # Check that worse confidence was not applied
        transaction1 = Transaction.objects.get(description='Low Confidence Transaction 1')
        self.assertEqual(transaction1.ai_category_confidence, 0.4)  # Original value
    
    @patch('apps.categories.services.AICategorizationService.categorize_transaction')
    def test_bulk_categorization_error_handling(self, mock_categorize):
        """Test error handling in bulk operations"""
        # Create test transaction
        transaction = Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='ERROR_TEST',
            amount=Decimal('-50.00'),
            description='Error Transaction',
            transaction_type='expense',
            transaction_date=timezone.now(),
            category=None,
            is_ai_categorized=False
        )
        
        # Mock categorization to raise an exception
        mock_categorize.side_effect = Exception('Test error')
        
        results = self.service.categorize_uncategorized_transactions(self.company, limit=1)
        
        self.assertEqual(results['total_processed'], 0)
        self.assertEqual(results['categorized'], 0)
        self.assertEqual(results['failed'], 1)
        
        # Transaction should remain uncategorized
        transaction.refresh_from_db()
        self.assertIsNone(transaction.category)
        self.assertFalse(transaction.is_ai_categorized)


class TestCompanyIsolation(BaseCategoryTestCase):
    """Test that services respect company boundaries"""
    
    def setUp(self):
        """Set up test data for multiple companies"""
        super().setUp()
        # Create two users and companies
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        self.company1 = Company.objects.create(
            name='Company 1',
            cnpj='12345678000123',
            owner=self.user1,
            subscription_plan=self.subscription_plan
        )
        self.bank_account1 = BankAccount.objects.create(
            company=self.company1,
            bank_provider=self.bank_provider,
            account_number='11111',
            agency='0001',
            account_type='checking'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        self.company2 = Company.objects.create(
            name='Company 2',
            cnpj='98765432000198',
            owner=self.user2,
            subscription_plan=self.subscription_plan
        )
        self.bank_account2 = BankAccount.objects.create(
            company=self.company2,
            bank_provider=self.bank_provider,
            account_number='22222',
            agency='0002',
            account_type='checking'
        )
        
        # Create categories
        self.category = TransactionCategory.objects.create(
            name='Shared Category',
            slug='shared-category',
            category_type='expense',
            icon='shared'
        )
        
        # Create rules for each company
        self.rule1 = CategoryRule.objects.create(
            company=self.company1,
            category=self.category,
            name='Company 1 Rule',
            rule_type='keyword',
            conditions={'keywords': ['company1']},
            priority=1
        )
        
        self.rule2 = CategoryRule.objects.create(
            company=self.company2,
            category=self.category,
            name='Company 2 Rule',
            rule_type='keyword',
            conditions={'keywords': ['company2']},
            priority=1
        )
        
        # Create transactions for each company
        self.transaction1 = Transaction.objects.create(
            bank_account=self.bank_account1,
            external_id='COMP1_TRANS',
            amount=Decimal('-100.00'),
            description='COMPANY1 EXPENSE',
            transaction_type='expense',
            transaction_date=timezone.now()
        )
        
        self.transaction2 = Transaction.objects.create(
            bank_account=self.bank_account2,
            external_id='COMP2_TRANS',
            amount=Decimal('-200.00'),
            description='COMPANY2 EXPENSE',
            transaction_type='expense',
            transaction_date=timezone.now()
        )
    
    @override_settings(OPENAI_API_KEY='test-key')
    def test_ai_categorization_respects_company_rules(self):
        """Test that AI categorization only uses company-specific rules"""
        service = AICategorizationService()
        
        # Company 1 transaction should match Company 1 rule
        result1 = service._apply_rules(self.transaction1)
        self.assertIsNotNone(result1)
        self.assertEqual(result1['rule'], self.rule1)
        
        # Company 2 transaction should match Company 2 rule
        result2 = service._apply_rules(self.transaction2)
        self.assertIsNotNone(result2)
        self.assertEqual(result2['rule'], self.rule2)
        
        # Company 1 transaction should not match Company 2 rule
        self.transaction1.description = 'COMPANY2 EXPENSE'
        result1_wrong = service._apply_rules(self.transaction1)
        self.assertIsNone(result1_wrong)
    
    def test_analytics_service_company_isolation(self):
        """Test that analytics only show company-specific data"""
        service = CategoryAnalyticsService()
        
        # Create categorization logs for each company
        CategorizationLog.objects.create(
            transaction=self.transaction1,
            method='rule',
            suggested_category=self.category,
            confidence_score=0.9,
            was_accepted=True
        )
        
        CategorizationLog.objects.create(
            transaction=self.transaction2,
            method='rule',
            suggested_category=self.category,
            confidence_score=0.9,
            was_accepted=True
        )
        
        # Get metrics for company 1
        metrics1 = service.calculate_accuracy_metrics(self.company1, 30)
        self.assertEqual(metrics1['total_categorizations'], 1)
        
        # Get metrics for company 2
        metrics2 = service.calculate_accuracy_metrics(self.company2, 30)
        self.assertEqual(metrics2['total_categorizations'], 1)
        
        # Each company should only see their own data
        insights1 = service.get_category_insights(self.company1)
        insights2 = service.get_category_insights(self.company2)
        
        # Both should have 1 transaction in the shared category
        self.assertEqual(len(insights1), 1)
        self.assertEqual(len(insights2), 1)
        self.assertEqual(insights1[0]['transaction_count'], 1)
        self.assertEqual(insights2[0]['transaction_count'], 1)
    
    @override_settings(OPENAI_API_KEY='test-key')
    def test_bulk_service_company_isolation(self):
        """Test that bulk operations only affect company-specific data"""
        service = BulkCategorizationService()
        
        # Apply rule to existing transactions
        results1 = service.apply_rule_to_existing_transactions(self.rule1, limit=10)
        
        # Should only check Company 1's transaction
        self.assertEqual(results1['total_checked'], 1)
        self.assertEqual(results1['matches_found'], 1)
        
        # Company 2's transaction should remain unaffected
        self.transaction2.refresh_from_db()
        self.assertIsNone(self.transaction2.category)