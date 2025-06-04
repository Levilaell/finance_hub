"""
Categories app services
AI-powered categorization and rule-based matching
"""
import json
import logging
import math
import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from apps.banking.models import Transaction, TransactionCategory
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone

from .models import (AITrainingData, CategorizationLog, CategoryRule,
                     CategorySuggestion)

logger = logging.getLogger(__name__)


class AICategorizationService:
    """
    AI-powered transaction categorization service
    Uses OpenAI API and custom rules for intelligent categorization
    """
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_version = "gpt-4o-mini"
        self.confidence_threshold = 0.7
    
    def categorize_transaction(self, transaction: Transaction) -> Dict:
        """
        Categorize a transaction using AI and rules
        
        Args:
            transaction: Transaction instance to categorize
            
        Returns:
            Dict with categorization results
        """
        start_time = timezone.now()
        
        try:
            # First try rule-based categorization
            rule_result = self._apply_rules(transaction)
            if rule_result and rule_result['confidence'] >= self.confidence_threshold:
                self._log_categorization(
                    transaction, 
                    'rule', 
                    rule_result,
                    processing_time_ms=self._calculate_processing_time(start_time)
                )
                return rule_result
            
            # Try AI categorization if rules don't match
            ai_result = self._ai_categorize(transaction)
            if ai_result and ai_result['confidence'] >= self.confidence_threshold:
                self._log_categorization(
                    transaction, 
                    'ai', 
                    ai_result,
                    processing_time_ms=self._calculate_processing_time(start_time)
                )
                return ai_result
            
            # Fallback to default category
            default_result = self._get_default_category(transaction)
            self._log_categorization(
                transaction, 
                'default', 
                default_result,
                processing_time_ms=self._calculate_processing_time(start_time)
            )
            
            return default_result
            
        except Exception as e:
            logger.error(f"Error categorizing transaction {transaction.id}: {e}")
            return self._get_default_category(transaction)
    
    def _apply_rules(self, transaction: Transaction) -> Optional[Dict]:
        """
        Apply rule-based categorization
        """
        rules = CategoryRule.objects.filter(
            company=transaction.bank_account.company,
            is_active=True
        ).order_by('-priority')
        
        for rule in rules:
            if self._rule_matches(rule, transaction):
                rule.match_count += 1
                rule.save()
                
                return {
                    'category': rule.category,
                    'confidence': rule.confidence_threshold,
                    'method': 'rule',
                    'rule_id': rule.id,
                    'rule_name': rule.name
                }
        
        return None
    
    def _rule_matches(self, rule: CategoryRule, transaction: Transaction) -> bool:
        """
        Check if a rule matches a transaction
        """
        conditions = rule.conditions
        
        if rule.rule_type == 'keyword':
            keywords = conditions.get('keywords', [])
            description_lower = transaction.description.lower()
            return any(keyword.lower() in description_lower for keyword in keywords)
        
        elif rule.rule_type == 'amount_range':
            min_amount = Decimal(str(conditions.get('min_amount', 0)))
            max_amount = Decimal(str(conditions.get('max_amount', 999999999)))
            return min_amount <= abs(transaction.amount) <= max_amount
        
        elif rule.rule_type == 'counterpart':
            counterparts = conditions.get('counterparts', [])
            counterpart_lower = transaction.counterpart_name.lower()
            return any(cp.lower() in counterpart_lower for cp in counterparts)
        
        elif rule.rule_type == 'pattern':
            pattern = conditions.get('pattern', '')
            try:
                return bool(re.search(pattern, transaction.description, re.IGNORECASE))
            except re.error:
                return False
        
        return False
    
    def _ai_categorize(self, transaction: Transaction) -> Optional[Dict]:
        """
        Use OpenAI API for transaction categorization
        """
        try:
            # Get available categories for this company
            categories = TransactionCategory.objects.filter(
                Q(is_system=True) | Q(company=transaction.bank_account.company),
                is_active=True
            )
            
            category_list = [
                f"- {cat.name}: {cat.keywords}" 
                for cat in categories 
                if cat.keywords
            ]
            
            # Prepare prompt
            prompt = self._build_ai_prompt(transaction, category_list)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um especialista em categorização de transações financeiras para empresas brasileiras."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            # Parse response
            ai_response = response.choices[0].message.content.strip()
            return self._parse_ai_response(ai_response, categories)
            
        except Exception as e:
            logger.error(f"AI categorization error for transaction {transaction.id}: {e}")
            return None
    
    def _build_ai_prompt(self, transaction: Transaction, category_list: List[str]) -> str:
        """
        Build prompt for AI categorization
        """
        return f"""
        Categorize esta transação financeira:

        Descrição: {transaction.description}
        Valor: R$ {transaction.amount}
        Tipo: {transaction.transaction_type}
        Contrapartida: {transaction.counterpart_name}
        Data: {transaction.transaction_date.strftime('%d/%m/%Y')}

        Categorias disponíveis:
        {chr(10).join(category_list)}

        Responda APENAS com o formato:
        CATEGORIA: [nome da categoria]
        CONFIANÇA: [0.0 a 1.0]
        MOTIVO: [breve explicação]
        """
    
    def _parse_ai_response(self, response: str, categories) -> Optional[Dict]:
        """
        Parse AI response and find matching category
        """
        try:
            lines = response.strip().split('\n')
            category_name = None
            confidence = 0.0
            reason = ""
            
            for line in lines:
                if line.startswith('CATEGORIA:'):
                    category_name = line.replace('CATEGORIA:', '').strip()
                elif line.startswith('CONFIANÇA:'):
                    confidence = float(line.replace('CONFIANÇA:', '').strip())
                elif line.startswith('MOTIVO:'):
                    reason = line.replace('MOTIVO:', '').strip()
            
            if category_name:
                # Find matching category
                category = categories.filter(
                    name__icontains=category_name
                ).first()
                
                if category:
                    return {
                        'category': category,
                        'confidence': confidence,
                        'method': 'ai',
                        'reason': reason
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _get_default_category(self, transaction: Transaction) -> Dict:
        """
        Get default category based on transaction type
        """
        if transaction.is_income:
            category = TransactionCategory.objects.filter(
                category_type='income',
                is_system=True,
                slug='outros-receitas'
            ).first()
        else:
            category = TransactionCategory.objects.filter(
                category_type='expense',
                is_system=True,
                slug='outros-despesas'
            ).first()
        
        return {
            'category': category,
            'confidence': 0.1,
            'method': 'default',
            'reason': 'Categoria padrão'
        }
    
    def _log_categorization(self, transaction: Transaction, method: str, result: Dict, processing_time_ms: int):
        """
        Log categorization attempt
        """
        CategorizationLog.objects.create(
            transaction=transaction,
            method=method,
            suggested_category=result['category'],
            confidence_score=result['confidence'],
            processing_time_ms=processing_time_ms,
            rule_used=result.get('rule_id'),
            ai_model_version=self.model_version if method == 'ai' else ''
        )
    
    def _calculate_processing_time(self, start_time) -> int:
        """
        Calculate processing time in milliseconds
        """
        return int((timezone.now() - start_time).total_seconds() * 1000)
    
    def learn_from_feedback(self, transaction: Transaction, correct_category: TransactionCategory, user: 'User'):
        """
        Learn from user feedback to improve AI
        """
        # Create training data
        AITrainingData.objects.create(
            company=transaction.bank_account.company,
            description=transaction.description,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            counterpart_name=transaction.counterpart_name,
            category=correct_category,
            is_verified=True,
            verification_source='user_feedback',
            verified_by=user,
            extracted_features=self._extract_features(transaction)
        )
        
        # Update categorization log
        log = CategorizationLog.objects.filter(
            transaction=transaction
        ).order_by('-created_at').first()
        
        if log:
            log.final_category = correct_category
            log.was_accepted = (log.suggested_category == correct_category)
            log.save()
    
    def _extract_features(self, transaction: Transaction) -> Dict:
        """
        Extract features from transaction for ML training
        """
        return {
            'description_length': len(transaction.description),
            'amount_range': self._get_amount_range(transaction.amount),
            'transaction_day': transaction.transaction_date.day,
            'transaction_weekday': transaction.transaction_date.weekday(),
            'has_counterpart': bool(transaction.counterpart_name),
            'description_words': len(transaction.description.split()),
            'amount_log': math.log(float(abs(transaction.amount))) if transaction.amount > 0 else 0
        }
    
    def _get_amount_range(self, amount: Decimal) -> str:
        """
        Get amount range category
        """
        abs_amount = abs(amount)
        
        if abs_amount < 50:
            return 'very_low'
        elif abs_amount < 200:
            return 'low'
        elif abs_amount < 500:
            return 'medium'
        elif abs_amount < 1000:
            return 'high'
        else:
            return 'very_high'


class RuleBasedCategorizationService:
    """
    Rule-based categorization system
    Manages and applies categorization rules
    """
    
    def create_keyword_rule(self, company, category, keywords: List[str], name: str) -> CategoryRule:
        """
        Create a keyword-based categorization rule
        """
        return CategoryRule.objects.create(
            company=company,
            category=category,
            name=name,
            rule_type='keyword',
            conditions={'keywords': keywords},
            priority=1
        )
    
    def create_amount_rule(self, company, category, min_amount: Decimal, max_amount: Decimal, name: str) -> CategoryRule:
        """
        Create an amount range categorization rule
        """
        return CategoryRule.objects.create(
            company=company,
            category=category,
            name=name,
            rule_type='amount_range',
            conditions={
                'min_amount': float(min_amount),
                'max_amount': float(max_amount)
            },
            priority=2
        )
    
    def create_counterpart_rule(self, company, category, counterparts: List[str], name: str) -> CategoryRule:
        """
        Create a counterpart-based categorization rule
        """
        return CategoryRule.objects.create(
            company=company,
            category=category,
            name=name,
            rule_type='counterpart',
            conditions={'counterparts': counterparts},
            priority=3
        )
    
    def suggest_rules_from_patterns(self, company) -> List[Dict]:
        """
        Analyze transactions and suggest new rules
        """
        suggestions = []
        
        # Analyze frequent descriptions
        from apps.banking.models import Transaction
        from django.db.models import Count
        
        frequent_descriptions = Transaction.objects.filter(
            bank_account__company=company,
            category__isnull=False
        ).values(
            'description', 'category__name'
        ).annotate(
            count=Count('id')
        ).filter(count__gte=3).order_by('-count')[:20]
        
        for item in frequent_descriptions:
            # Extract keywords from description
            keywords = self._extract_keywords(item['description'])
            if keywords:
                suggestions.append({
                    'type': 'keyword',
                    'category': item['category__name'],
                    'keywords': keywords,
                    'frequency': item['count'],
                    'confidence': min(0.9, item['count'] / 10)
                })
        
        return suggestions
    
    def _extract_keywords(self, description: str) -> List[str]:
       """
       Extract meaningful keywords from transaction description
       """
       # Remove common words and extract meaningful terms
       common_words = {
           'pix', 'ted', 'doc', 'transferencia', 'pagamento', 'compra', 
           'debito', 'credito', 'saque', 'deposito', 'taxa', 'tarifa',
           'banco', 'caixa', 'conta', 'cartao', 'de', 'do', 'da', 'para',
           'em', 'com', 'por', 'ate', 'desde', 'ltda', 'me', 'eireli'
       }
       
       words = re.findall(r'\b[a-zA-Z]{3,}\b', description.lower())
       keywords = [word for word in words if word not in common_words]
       
       # Return most relevant keywords (max 3)
       return keywords[:3]
    


class CategoryAnalyticsService:
   """
   Analytics service for categorization performance
   """
   
   def calculate_accuracy_metrics(self, company, period_days: int = 30) -> Dict:
       """
       Calculate categorization accuracy metrics
       """
       from datetime import timedelta
       
       end_date = timezone.now().date()
       start_date = end_date - timedelta(days=period_days)
       
       # Get categorization logs for the period
       logs = CategorizationLog.objects.filter(
           transaction__bank_account__company=company,
           created_at__date__gte=start_date,
           created_at__date__lte=end_date
       )
       
       total_categorizations = logs.count()
       if total_categorizations == 0:
           return {
               'total_categorizations': 0,
               'accuracy': 0.0,
               'ai_accuracy': 0.0,
               'rule_accuracy': 0.0,
               'method_breakdown': {}
           }
       
       # Calculate overall accuracy
       correct_categorizations = logs.filter(was_accepted=True).count()
       overall_accuracy = correct_categorizations / total_categorizations
       
       # Method breakdown
       method_stats = {}
       for method in ['ai', 'rule', 'manual', 'default']:
           method_logs = logs.filter(method=method)
           method_total = method_logs.count()
           method_correct = method_logs.filter(was_accepted=True).count()
           
           method_stats[method] = {
               'total': method_total,
               'correct': method_correct,
               'accuracy': method_correct / method_total if method_total > 0 else 0.0
           }
       
       return {
           'total_categorizations': total_categorizations,
           'accuracy': overall_accuracy,
           'ai_accuracy': method_stats['ai']['accuracy'],
           'rule_accuracy': method_stats['rule']['accuracy'],
           'method_breakdown': method_stats,
           'period_days': period_days
       }
   
   def get_category_insights(self, company) -> List[Dict]:
       """
       Get insights about category usage and accuracy
       """
       from apps.banking.models import Transaction
       from django.db.models import Avg, Count

       # Category usage statistics
       category_stats = Transaction.objects.filter(
           bank_account__company=company,
           category__isnull=False
       ).values(
           'category__name',
           'category__icon',
           'category__category_type'
       ).annotate(
           transaction_count=Count('id'),
           avg_confidence=Avg('ai_category_confidence')
       ).order_by('-transaction_count')[:10]
       
       insights = []
       for stat in category_stats:
           # Get accuracy for this category
           category_logs = CategorizationLog.objects.filter(
               transaction__category__name=stat['category__name'],
               transaction__bank_account__company=company
           )
           
           total_logs = category_logs.count()
           correct_logs = category_logs.filter(was_accepted=True).count()
           accuracy = correct_logs / total_logs if total_logs > 0 else 0.0
           
           insights.append({
               'category': stat['category__name'],
               'icon': stat['category__icon'],
               'type': stat['category__category_type'],
               'transaction_count': stat['transaction_count'],
               'avg_confidence': stat['avg_confidence'] or 0.0,
               'accuracy': accuracy,
               'needs_attention': accuracy < 0.7 and stat['transaction_count'] > 5
           })
       
       return insights
   
   def suggest_improvements(self, company) -> List[Dict]:
       """
       Suggest improvements for categorization system
       """
       suggestions = []
       
       # Get categories with low accuracy
       insights = self.get_category_insights(company)
       low_accuracy_categories = [
           insight for insight in insights 
           if insight['accuracy'] < 0.7 and insight['transaction_count'] > 5
       ]
       
       for category in low_accuracy_categories:
           suggestions.append({
               'type': 'accuracy_improvement',
               'category': category['category'],
               'current_accuracy': category['accuracy'],
               'transaction_count': category['transaction_count'],
               'suggestion': f"Revisar e corrigir categorizações para '{category['category']}' - precisão baixa ({category['accuracy']:.1%})",
               'priority': 'high' if category['transaction_count'] > 20 else 'medium'
           })
       
       # Suggest rule creation for frequent uncategorized transactions
       from apps.banking.models import Transaction
       
       uncategorized = Transaction.objects.filter(
           bank_account__company=company,
           category__isnull=True
       ).values('description').annotate(
           count=Count('id')
       ).filter(count__gte=3).order_by('-count')[:5]
       
       for item in uncategorized:
           suggestions.append({
               'type': 'rule_creation',
               'description': item['description'],
               'frequency': item['count'],
               'suggestion': f"Criar regra para '{item['description']}' - aparece {item['count']} vezes",
               'priority': 'medium'
           })
       
       return suggestions


class BulkCategorizationService:
   """
   Service for bulk categorization operations
   """
   
   def __init__(self):
       self.ai_service = AICategorizationService()
   
   def categorize_uncategorized_transactions(self, company, limit: int = 100) -> Dict:
       """
       Categorize all uncategorized transactions for a company
       """
       from apps.banking.models import Transaction
       
       uncategorized = Transaction.objects.filter(
           bank_account__company=company,
           category__isnull=True,
           is_ai_categorized=False
       ).order_by('-transaction_date')[:limit]
       
       results = {
           'total_processed': 0,
           'categorized': 0,
           'failed': 0,
           'high_confidence': 0,
           'low_confidence': 0
       }
       
       for transaction in uncategorized:
           try:
               result = self.ai_service.categorize_transaction(transaction)
               
               if result and result.get('category'):
                   transaction.category = result['category']
                   transaction.ai_category_confidence = result['confidence']
                   transaction.is_ai_categorized = True
                   transaction.save()
                   
                   results['categorized'] += 1
                   
                   if result['confidence'] >= 0.8:
                       results['high_confidence'] += 1
                   else:
                       results['low_confidence'] += 1
               else:
                   results['failed'] += 1
               
               results['total_processed'] += 1
               
           except Exception as e:
               logger.error(f"Error categorizing transaction {transaction.id}: {e}")
               results['failed'] += 1
       
       return results
   
   def apply_rule_to_existing_transactions(self, rule: CategoryRule, limit: int = 1000) -> Dict:
       """
       Apply a categorization rule to existing transactions
       """
       from apps.banking.models import Transaction

       # Get transactions that match the rule
       transactions = Transaction.objects.filter(
           bank_account__company=rule.company
       ).order_by('-transaction_date')[:limit]
       
       results = {
           'total_checked': 0,
           'matches_found': 0,
           'categorized': 0,
           'already_categorized': 0
       }
       
       ai_service = AICategorizationService()
       
       for transaction in transactions:
           results['total_checked'] += 1
           
           if ai_service._rule_matches(rule, transaction):
               results['matches_found'] += 1
               
               if not transaction.category:
                   transaction.category = rule.category
                   transaction.ai_category_confidence = rule.confidence_threshold
                   transaction.is_ai_categorized = True
                   transaction.save()
                   
                   # Log the categorization
                   CategorizationLog.objects.create(
                       transaction=transaction,
                       method='rule',
                       suggested_category=rule.category,
                       confidence_score=rule.confidence_threshold,
                       rule_used=rule,
                       was_accepted=True
                   )
                   
                   results['categorized'] += 1
               else:
                   results['already_categorized'] += 1
       
       # Update rule statistics
       rule.match_count += results['matches_found']
       rule.save()
       
       return results
   
   def recategorize_low_confidence_transactions(self, company, confidence_threshold: float = 0.5) -> Dict:
       """
       Recategorize transactions with low confidence scores
       """
       from apps.banking.models import Transaction
       
       low_confidence = Transaction.objects.filter(
           bank_account__company=company,
           ai_category_confidence__lt=confidence_threshold,
           is_ai_categorized=True
       ).order_by('-transaction_date')[:100]
       
       results = {
           'total_processed': 0,
           'improved': 0,
           'unchanged': 0,
           'failed': 0
       }
       
       for transaction in low_confidence:
           try:
               old_confidence = transaction.ai_category_confidence
               result = self.ai_service.categorize_transaction(transaction)
               
               if result and result.get('confidence', 0) > old_confidence:
                   transaction.category = result['category']
                   transaction.ai_category_confidence = result['confidence']
                   transaction.save()
                   results['improved'] += 1
               else:
                   results['unchanged'] += 1
               
               results['total_processed'] += 1
               
           except Exception as e:
               logger.error(f"Error recategorizing transaction {transaction.id}: {e}")
               results['failed'] += 1
       
       return results