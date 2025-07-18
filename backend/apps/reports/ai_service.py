"""
Enhanced AI Service for CaixaHub - Advanced financial analysis using OpenAI
CORREÇÕES APLICADAS:
- Tratamento robusto de erros e divisão por zero
- Validação e sanitização de dados antes de enviar para OpenAI
- Cache versionado e com invalidação inteligente
- Rate limiting e controle de custos
- Métricas de qualidade e monitoramento
- Fallback melhorado com insights mais relevantes
"""
import os
import json
import logging
import hashlib
from celery.schedules import crontab
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta, date
from collections import defaultdict
import re
from dotenv import load_dotenv

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from openai import OpenAI
import numpy as np

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# Versão do cache para invalidação automática em updates
CACHE_VERSION = "v2.0"
MAX_API_RETRIES = 3
OPENAI_TIMEOUT = 180  # segundos


class EnhancedAIInsightsService:
    """Enhanced service for generating advanced AI-powered financial insights"""
    
    def __init__(self):
        """Initialize OpenAI client with fallback options"""
        self.client = None
        self.model = "gpt-4o-mini"  # Modelo otimizado para custo-benefício
        self.max_tokens = 2000
        self.temperature = 0.7
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize OpenAI client with multiple fallback options"""
        # Try environment variable first
        api_key = os.getenv('OPENAI_API_KEY')
        
        # Try Django settings
        if not api_key:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        if api_key:
            try:
                self.client = OpenAI(
                    api_key=api_key,
                    timeout=OPENAI_TIMEOUT,
                    max_retries=MAX_API_RETRIES
                )
                # Test connection
                self.client.models.list()
            except Exception as e:
                self.client = None
        else:
            logger.warning("OpenAI API key not found. AI insights will use fallback mode.")
    
    def generate_insights(
        self, 
        financial_data: Dict[str, Any],
        company_name: str = "Empresa",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered insights with caching and error handling
        """
        try:
            # Validate input data
            if not self._validate_financial_data(financial_data):
                logger.warning("Invalid financial data provided")
                return self._generate_enhanced_fallback_insights(financial_data, company_name)
            
            # Generate cache key with version
            cache_key = self._generate_cache_key(financial_data, company_name)
            
            # Check cache unless force refresh
            if not force_refresh:
                cached_result = cache.get(cache_key)
                if cached_result and cached_result.get('version') == CACHE_VERSION:
                    logger.info(f"Returning cached insights for {company_name}")
                    cached_result['from_cache'] = True
                    return cached_result
            
            # Check if AI is available
            if not self.client:
                logger.warning("OpenAI client not available. Using enhanced fallback insights.")
                return self._generate_enhanced_fallback_insights(financial_data, company_name)
            
            # Prepare comprehensive analysis
            analysis_data = self._prepare_comprehensive_analysis(financial_data)
            
            # Sanitize sensitive data before sending to AI
            sanitized_data = self._sanitize_for_ai(analysis_data)
            
            # Create detailed prompt
            prompt = self._create_advanced_analysis_prompt(sanitized_data, company_name)
            
            # Call OpenAI API with error handling
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": self._get_system_prompt()
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # Parse and validate response
                ai_response = response.choices[0].message.content
                insights_data = json.loads(ai_response)
                
                # Validate AI response structure
                if not self._validate_ai_response(insights_data):
                    logger.warning("Invalid AI response structure, using fallback")
                    return self._generate_enhanced_fallback_insights(financial_data, company_name)
                
                # Format and enhance insights
                result = self._format_and_enhance_insights(insights_data, analysis_data)
                
                # Add version for cache invalidation
                result['version'] = CACHE_VERSION
                
                # Cache the result for 24 hours
                cache.set(cache_key, result, 86400)
                
                # Log metrics for monitoring
                self._log_ai_metrics(response, company_name)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                return self._generate_enhanced_fallback_insights(financial_data, company_name)
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return self._generate_enhanced_fallback_insights(financial_data, company_name)
                
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}", exc_info=True)
            return self._generate_enhanced_fallback_insights(financial_data, company_name)
    
    def _validate_financial_data(self, financial_data: Dict[str, Any]) -> bool:
        """Validate financial data structure and content"""
        required_fields = ['income', 'expenses', 'period_days']
        
        for field in required_fields:
            if field not in financial_data:
                return False
            
            # Check for valid numeric values
            if field in ['income', 'expenses']:
                try:
                    value = float(financial_data[field])
                    if not np.isfinite(value):
                        return False
                except (TypeError, ValueError):
                    return False
        
        return True
    
    def _sanitize_for_ai(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information before sending to AI"""
        # Convert Decimals to float for JSON serialization
        import json
        
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
        sanitized = json.loads(json.dumps(data, default=decimal_default))  # Deep copy with Decimal handling
        
        # Remove specific account numbers, names, etc
        sensitive_fields = ['account_number', 'cpf', 'cnpj', 'api_key', 'password']
        
        def remove_sensitive(obj):
            if isinstance(obj, dict):
                return {k: remove_sensitive(v) for k, v in obj.items() 
                       if k.lower() not in sensitive_fields}
            elif isinstance(obj, list):
                return [remove_sensitive(item) for item in obj]
            elif isinstance(obj, str):
                # Mask potential account numbers or IDs
                return re.sub(r'\b\d{4,}\b', 'XXXX', obj)
            return obj
        
        return remove_sensitive(sanitized)
    
    def _validate_ai_response(self, response: Dict[str, Any]) -> bool:
        """Validate AI response has required structure"""
        required_keys = ['insights', 'predictions', 'recommendations', 'key_metrics']
        
        for key in required_keys:
            if key not in response:
                return False
            
        # Validate insights structure
        if not isinstance(response.get('insights'), list):
            return False
            
        # Validate at least one insight
        if len(response['insights']) == 0:
            return False
            
        return True
    
    def _log_ai_metrics(self, response: Any, company_name: str):
        """Log AI usage metrics for monitoring and cost control"""
        try:
            usage = response.usage
            metrics = {
                'company': company_name,
                'model': self.model,
                'prompt_tokens': usage.prompt_tokens,
                'completion_tokens': usage.completion_tokens,
                'total_tokens': usage.total_tokens,
                'estimated_cost': self._estimate_cost(usage),
                'timestamp': timezone.now().isoformat()
            }
            
            # Log to monitoring system
            logger.info(f"AI Usage Metrics: {json.dumps(metrics)}")
            
            # Track daily usage
            daily_key = f"ai_usage_{timezone.now().date()}"
            current_usage = cache.get(daily_key, 0)
            cache.set(daily_key, current_usage + usage.total_tokens, 86400)
            
        except Exception as e:
            logger.error(f"Error logging AI metrics: {e}")
    
    def _estimate_cost(self, usage: Any) -> float:
        """Estimate cost based on token usage"""
        # Preços aproximados para gpt-4o-mini (em USD por 1k tokens)
        input_price = 0.00015  # $0.15 per 1M tokens
        output_price = 0.0006   # $0.60 per 1M tokens
        
        input_cost = (usage.prompt_tokens / 1000) * input_price
        output_cost = (usage.completion_tokens / 1000) * output_price
        
        return round(input_cost + output_cost, 4)
    
    def _generate_cache_key(self, financial_data: Dict[str, Any], company_name: str) -> str:
        """Generate a cache key based on financial data"""
        # Create a simplified version of the data for hashing
        key_data = {
            'company': company_name,
            'period_days': financial_data.get('period_days'),
            'income': round(float(financial_data.get('income', 0)), 2),
            'expenses': round(float(financial_data.get('expenses', 0)), 2),
            'transaction_count': financial_data.get('transaction_count', 0),
            'version': CACHE_VERSION
        }
        
        # Generate hash
        data_str = json.dumps(key_data, sort_keys=True)
        return f"ai_insights_{hashlib.md5(data_str.encode()).hexdigest()}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI analysis"""
        return """Você é um consultor financeiro sênior especializado em análise de dados 
        para pequenas e médias empresas brasileiras. Sua missão é:
        
        1. Analisar profundamente os dados financeiros fornecidos
        2. Identificar padrões, tendências e anomalias importantes
        3. Gerar insights acionáveis e específicos (não genéricos)
        4. Fazer previsões realistas baseadas em tendências históricas
        5. Fornecer recomendações práticas e implementáveis
        6. Destacar oportunidades de economia e crescimento
        7. Alertar sobre riscos potenciais
        
        IMPORTANTE:
        - Seja específico com valores e porcentagens
        - Use linguagem clara e profissional em português brasileiro
        - Foque em insights que agregam valor real ao empresário
        - Evite recomendações óbvias ou genéricas
        - Sempre retorne a resposta em formato JSON válido
        - Priorize insights que levam a ações concretas
        - Considere o contexto brasileiro (impostos, sazonalidade, etc)
        """
    
    def _prepare_comprehensive_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive analysis data for AI processing"""
        
        # Extract base metrics with safe defaults
        income = float(financial_data.get('income', 0))
        expenses = float(financial_data.get('expenses', 0))
        net_flow = float(financial_data.get('net_flow', income - expenses))
        period_days = max(1, financial_data.get('period_days', 30))  # Prevent division by zero
        
        # Calculate advanced metrics with safety checks
        analysis = {
            'basic_metrics': financial_data,
            'calculated_metrics': {
                'profit_margin': self._safe_percentage(net_flow, income),
                'expense_ratio': self._safe_percentage(expenses, income),
                'daily_burn_rate': self._safe_division(expenses, period_days),
                'daily_revenue': self._safe_division(income, period_days),
                'months_of_runway': self._calculate_runway(income, expenses, period_days)
            },
            'patterns': self._analyze_patterns(financial_data),
            'anomalies': self._detect_anomalies(financial_data),
            'growth_metrics': self._calculate_growth_metrics(financial_data),
            'risk_indicators': self._assess_risk_indicators(financial_data)
        }
        
        return analysis
    
    def _safe_division(self, numerator: float, denominator: float, default: float = 0) -> float:
        """Safe division with default value"""
        try:
            numerator = float(numerator)
            denominator = float(denominator)
            
            if denominator == 0 or not np.isfinite(denominator):
                return default
                
            result = numerator / denominator
            return result if np.isfinite(result) else default
        except (TypeError, ValueError):
            return default

    def _safe_percentage(self, part: float, whole: float, default: float = 0) -> float:
        """Calculate percentage safely"""
        return self._safe_division(part * 100, whole, default)
    
    def _calculate_runway(self, income: float, expenses: float, period_days: int) -> float:
        """Calculate months of runway with safety checks"""
        if expenses <= 0 or period_days <= 0:
            return 999  # Infinite runway
        
        daily_burn = expenses / period_days
        monthly_burn = daily_burn * 30
        
        if monthly_burn <= 0:
            return 999
            
        return min(self._safe_division(income, monthly_burn), 999)
    
    def _analyze_patterns(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze spending and income patterns safely"""
        patterns = {
            'weekly_variation': {},
            'category_concentration': {},
            'payment_frequency': {},
            'seasonal_indicators': []
        }
        
        # Analyze weekly patterns
        weekly_data = financial_data.get('weekly_patterns', [])
        if weekly_data and len(weekly_data) > 0:
            incomes = [float(w.get('income', 0)) for w in weekly_data]
            expenses = [float(w.get('expenses', 0)) for w in weekly_data]
            
            if incomes:
                patterns['weekly_variation'] = {
                    'income_volatility': self._calculate_volatility(incomes),
                    'expense_volatility': self._calculate_volatility(expenses),
                    'best_week': max(weekly_data, key=lambda x: float(x.get('net', 0))),
                    'worst_week': min(weekly_data, key=lambda x: float(x.get('net', 0)))
                }
        
        # Analyze category concentration
        categories = financial_data.get('top_expense_categories', [])
        if categories:
            total_categorized = sum(float(cat.get('amount', 0)) for cat in categories)
            patterns['category_concentration'] = {
                'top_3_percentage': sum(float(cat.get('percentage', 0)) for cat in categories[:3]),
                'diversification_score': len([c for c in categories if float(c.get('percentage', 0)) > 5]),
                'dominant_category': categories[0] if categories else None
            }
        
        return patterns
    
    def _detect_anomalies(self, financial_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect financial anomalies with improved logic"""
        anomalies = []
        
        # Safe extraction of values
        expenses = float(financial_data.get('expenses', 0))
        income = float(financial_data.get('income', 0))
        
        # Check for unusual transactions
        largest_expense = financial_data.get('largest_expense', {})
        if largest_expense:
            expense_amount = abs(float(largest_expense.get('amount', 0)))
            if expense_amount > 0 and expenses > 0 and expense_amount > expenses * 0.2:
                anomalies.append({
                    'type': 'large_expense',
                    'description': f"Despesa de R$ {expense_amount:,.2f} representa mais de 20% do total",
                    'transaction': largest_expense.get('description', 'Transação não identificada'),
                    'severity': 'high' if expense_amount > expenses * 0.5 else 'medium'
                })
        
        # Check for spending spikes
        weekly_data = financial_data.get('weekly_patterns', [])
        if len(weekly_data) > 1:
            weekly_expenses = [float(w.get('expenses', 0)) for w in weekly_data]
            avg_weekly_expense = np.mean(weekly_expenses) if weekly_expenses else 0
            
            if avg_weekly_expense > 0:
                for i, week in enumerate(weekly_data):
                    week_expense = float(week.get('expenses', 0))
                    if week_expense > avg_weekly_expense * 1.5:
                        anomalies.append({
                            'type': 'spending_spike',
                            'week': week.get('week_start', f'Semana {i+1}'),
                            'amount': week_expense,
                            'deviation': self._safe_percentage(week_expense - avg_weekly_expense, avg_weekly_expense)
                        })
        
        # Check for negative cash flow
        if income > 0 and expenses > income:
            anomalies.append({
                'type': 'negative_cash_flow',
                'description': f"Despesas superam receitas em {self._safe_percentage(expenses - income, income):.1f}%",
                'severity': 'high'
            })
        
        return anomalies[:5]  # Limit to top 5 anomalies
    
    def _calculate_growth_metrics(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate growth and trend metrics with safety checks"""
        weekly_data = financial_data.get('weekly_patterns', [])
        
        if len(weekly_data) < 2:
            return {
                'trend': 'insufficient_data',
                'message': 'Dados insuficientes para análise de tendência'
            }
        
        # Calculate week-over-week growth safely
        income_growth = []
        expense_growth = []
        
        for i in range(1, len(weekly_data)):
            prev_income = float(weekly_data[i-1].get('income', 0))
            curr_income = float(weekly_data[i].get('income', 0))
            prev_expense = float(weekly_data[i-1].get('expenses', 0))
            curr_expense = float(weekly_data[i].get('expenses', 0))
            
            if prev_income > 0:
                growth = self._safe_percentage(curr_income - prev_income, prev_income)
                if np.isfinite(growth):
                    income_growth.append(growth)
                    
            if prev_expense > 0:
                growth = self._safe_percentage(curr_expense - prev_expense, prev_expense)
                if np.isfinite(growth):
                    expense_growth.append(growth)
        
        avg_income_growth = np.mean(income_growth) if income_growth else 0
        avg_expense_growth = np.mean(expense_growth) if expense_growth else 0
        
        return {
            'income_trend': 'growing' if avg_income_growth > 5 else 'stable' if avg_income_growth > -5 else 'declining',
            'expense_trend': 'growing' if avg_expense_growth > 5 else 'stable' if avg_expense_growth > -5 else 'declining',
            'avg_income_growth': round(avg_income_growth, 1),
            'avg_expense_growth': round(avg_expense_growth, 1),
            'momentum': 'positive' if avg_income_growth > avg_expense_growth else 'negative',
            'consistency': self._calculate_consistency(income_growth)
        }
    
    def _calculate_consistency(self, growth_rates: List[float]) -> str:
        """Calculate growth consistency"""
        if not growth_rates:
            return 'unknown'
        
        std_dev = np.std(growth_rates)
        if std_dev < 10:
            return 'very_consistent'
        elif std_dev < 25:
            return 'consistent'
        elif std_dev < 50:
            return 'variable'
        else:
            return 'highly_variable'
    
    def _assess_risk_indicators(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess financial risk indicators with improved logic"""
        income = float(financial_data.get('income', 0))
        expenses = float(financial_data.get('expenses', 0))
        
        # Cash flow risk assessment
        if income == 0:
            cash_flow_risk = 'critical'
        elif expenses > income:
            cash_flow_risk = 'high'
        elif expenses > income * 0.8:
            cash_flow_risk = 'medium'
        else:
            cash_flow_risk = 'low'
        
        # Category concentration risk
        categories = financial_data.get('top_expense_categories', [])
        concentration_risk = 'low'
        if categories:
            top_category_percentage = float(categories[0].get('percentage', 0))
            if top_category_percentage > 50:
                concentration_risk = 'high'
            elif top_category_percentage > 30:
                concentration_risk = 'medium'
        
        risks = {
            'cash_flow_risk': cash_flow_risk,
            'concentration_risk': concentration_risk,
            'volatility_risk': self._assess_volatility_risk(financial_data),
            'dependency_risk': self._assess_dependency_risk(financial_data),
            'overall_risk_score': self._calculate_overall_risk_score(
                cash_flow_risk, concentration_risk
            )
        }
        
        return risks
    
    def _calculate_overall_risk_score(self, cash_flow_risk: str, concentration_risk: str) -> int:
        """Calculate overall risk score from 1-10"""
        risk_values = {
            'low': 2,
            'medium': 5,
            'high': 8,
            'critical': 10
        }
        
        cf_score = risk_values.get(cash_flow_risk, 5)
        conc_score = risk_values.get(concentration_risk, 5)
        
        return min(10, int((cf_score + conc_score) / 2))
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation) safely"""
        if not values or len(values) < 2:
            return 0
        
        # Filter out non-finite values
        clean_values = [v for v in values if np.isfinite(v)]
        if len(clean_values) < 2:
            return 0
        
        mean = np.mean(clean_values)
        if mean == 0:
            return 0
        
        std_dev = np.std(clean_values)
        cv = (std_dev / abs(mean)) * 100
        
        return min(cv, 200)  # Cap at 200% to avoid extreme values
    
    def _assess_volatility_risk(self, financial_data: Dict[str, Any]) -> str:
        """Assess volatility risk level"""
        weekly_data = financial_data.get('weekly_patterns', [])
        if not weekly_data:
            return 'unknown'
        
        income_values = [float(w.get('income', 0)) for w in weekly_data]
        volatility = self._calculate_volatility(income_values)
        
        if volatility > 50:
            return 'high'
        elif volatility > 25:
            return 'medium'
        return 'low'
    
    def _assess_dependency_risk(self, financial_data: Dict[str, Any]) -> str:
        """Assess customer dependency risk"""
        # Simplified assessment based on category concentration
        top_categories = financial_data.get('top_expense_categories', [])
        if not top_categories:
            return 'unknown'
            
        top_percentage = float(top_categories[0].get('percentage', 0))
        if top_percentage > 40:
            return 'high'
        elif top_percentage > 25:
            return 'medium'
        return 'low'
    
    def _create_advanced_analysis_prompt(self, analysis_data: Dict[str, Any], company_name: str) -> str:
        """Create an advanced analysis prompt with all insights"""
        
        basic = analysis_data['basic_metrics']
        calculated = analysis_data['calculated_metrics']
        patterns = analysis_data['patterns']
        anomalies = analysis_data['anomalies']
        growth = analysis_data['growth_metrics']
        risks = analysis_data['risk_indicators']
        
        # Format numbers safely
        income = float(basic.get('income', 0))
        expenses = float(basic.get('expenses', 0))
        net_flow = float(basic.get('net_flow', 0))
        period_days = basic.get('period_days', 30)
        transaction_count = basic.get('transaction_count', 0)
        
        prompt = f"""
        Analise os dados financeiros detalhados da empresa {company_name}:
        
        MÉTRICAS BÁSICAS ({period_days} dias):
        - Receita Total: R$ {income:,.2f}
        - Despesas Totais: R$ {expenses:,.2f}
        - Resultado Líquido: R$ {net_flow:,.2f}
        - Transações: {transaction_count}
        
        INDICADORES CALCULADOS:
        - Margem de Lucro: {calculated['profit_margin']:.1f}%
        - Taxa de Despesas: {calculated['expense_ratio']:.1f}%
        - Burn Rate Diário: R$ {calculated['daily_burn_rate']:,.2f}
        - Receita Diária: R$ {calculated['daily_revenue']:,.2f}
        - Meses de Runway: {calculated['months_of_runway']:.1f}
        
        PADRÕES IDENTIFICADOS:
        {json.dumps(patterns, ensure_ascii=False, indent=2)}
        
        ANOMALIAS DETECTADAS:
        {json.dumps(anomalies, ensure_ascii=False, indent=2)}
        
        MÉTRICAS DE CRESCIMENTO:
        {json.dumps(growth, ensure_ascii=False, indent=2)}
        
        INDICADORES DE RISCO:
        {json.dumps(risks, ensure_ascii=False, indent=2)}
        
        TOP 5 CATEGORIAS DE GASTOS:
        """
        
        for i, cat in enumerate(basic.get('top_expense_categories', [])[:5], 1):
            amount = float(cat.get('amount', 0))
            percentage = float(cat.get('percentage', 0))
            count = cat.get('count', 0)
            prompt += f"\n{i}. {cat['name']}: R$ {amount:,.2f} ({percentage:.1f}%) - {count} transações"
        
        prompt += """
        
        Com base nesta análise profunda, forneça insights em formato JSON:
        {
            "insights": [
                {
                    "type": "success/warning/danger/info",
                    "title": "Título específico e impactante",
                    "description": "Descrição detalhada com números e contexto",
                    "value": "Valor ou métrica principal",
                    "trend": "up/down/stable",
                    "priority": "high/medium/low",
                    "actionable": true/false
                }
            ],
            "predictions": {
                "next_month_income": valor_numerico,
                "next_month_expenses": valor_numerico,
                "projected_savings": valor_numerico,
                "growth_rate": porcentagem,
                "risk_score": 1-10,
                "opportunities": ["lista de oportunidades identificadas"],
                "threats": ["lista de ameaças identificadas"]
            },
            "recommendations": [
                {
                    "type": "cost_reduction/revenue_growth/risk_mitigation/efficiency",
                    "title": "Ação específica recomendada",
                    "description": "Como implementar e benefícios esperados",
                    "potential_impact": "R$ X.XXX ou X%",
                    "priority": "high/medium/low",
                    "time_to_implement": "imediato/curto_prazo/medio_prazo"
                }
            ],
            "alerts": [
                {
                    "severity": "high/medium/low",
                    "title": "Alerta específico",
                    "description": "Detalhes do que requer atenção",
                    "action_required": "Ação necessária"
                }
            ],
            "key_metrics": {
                "health_score": 1-100,
                "efficiency_score": 1-100,
                "growth_potential": 1-100
            }
        }
        
        REQUISITOS CRÍTICOS:
        1. Seja EXTREMAMENTE específico - use números, porcentagens e comparações
        2. Identifique oportunidades concretas de economia (ex: "Reduza gastos com X em 15% = R$ 500/mês")
        3. Destaque tendências preocupantes antes que se tornem problemas
        4. Sugira ações imediatas e mensuráveis
        5. Compare com benchmarks do setor quando relevante
        6. Identifique os 3 principais riscos e 3 principais oportunidades
        7. Cada insight deve levar a uma ação clara
        8. Considere sazonalidade e contexto brasileiro
        """
        
        return prompt
    
    def _format_and_enhance_insights(self, ai_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and enhance AI insights with additional context"""
        
        # Ensure all required fields exist with safe defaults
        formatted = {
            'insights': [],
            'predictions': {},
            'recommendations': [],
            'alerts': [],
            'key_metrics': {},
            'summary': {},
            'ai_generated': True,
            'generated_at': timezone.now().isoformat(),
            'confidence_level': 'high'  # Add confidence indicator
        }
        
        # Process insights with priority sorting and validation
        insights = ai_data.get('insights', [])
        for insight in insights:
            if isinstance(insight, dict) and 'title' in insight:
                # Validate insight type
                valid_types = ['success', 'warning', 'danger', 'info']
                insight_type = insight.get('type', 'info')
                if insight_type not in valid_types:
                    insight_type = 'info'
                
                formatted_insight = {
                    'type': insight_type,
                    'title': insight.get('title', 'Insight'),
                    'description': insight.get('description', ''),
                    'value': insight.get('value', ''),
                    'trend': insight.get('trend'),
                    'priority': insight.get('priority', 'medium'),
                    'actionable': insight.get('actionable', True),
                    'category': self._categorize_insight(insight)
                }
                formatted['insights'].append(formatted_insight)
        
        # Sort insights by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        formatted['insights'].sort(key=lambda x: priority_order.get(x['priority'], 1))
        
        # Process predictions with validation and bounds
        predictions = ai_data.get('predictions', {})
        formatted['predictions'] = {
            'next_month_income': max(0, float(predictions.get('next_month_income', 0))),
            'next_month_expenses': max(0, float(predictions.get('next_month_expenses', 0))),
            'projected_savings': float(predictions.get('projected_savings', 0)),
            'growth_rate': max(-100, min(100, float(predictions.get('growth_rate', 0)))),
            'risk_score': max(1, min(10, int(predictions.get('risk_score', 5)))),
            'opportunities': predictions.get('opportunities', [])[:5],  # Limit to 5
            'threats': predictions.get('threats', [])[:5],  # Limit to 5
            'confidence': self._calculate_prediction_confidence(analysis_data)
        }
        
        # Process recommendations with impact analysis
        recommendations = ai_data.get('recommendations', [])
        for rec in recommendations[:10]:  # Limit to top 10
            if isinstance(rec, dict) and 'title' in rec:
                formatted_rec = {
                    'type': rec.get('type', 'general'),
                    'title': rec.get('title', 'Recomendação'),
                    'description': rec.get('description', ''),
                    'potential_impact': rec.get('potential_impact', 'A definir'),
                    'priority': rec.get('priority', 'medium'),
                    'time_to_implement': rec.get('time_to_implement', 'curto_prazo'),
                    'difficulty': self._assess_implementation_difficulty(rec)
                }
                formatted['recommendations'].append(formatted_rec)
        
        # Process alerts with severity validation
        alerts = ai_data.get('alerts', [])
        for alert in alerts[:5]:  # Limit alerts
            if isinstance(alert, dict) and 'title' in alert:
                severity = alert.get('severity', 'medium')
                if severity not in ['high', 'medium', 'low']:
                    severity = 'medium'
                    
                formatted['alerts'].append({
                    'severity': severity,
                    'title': alert.get('title', 'Alerta'),
                    'description': alert.get('description', ''),
                    'action_required': alert.get('action_required', ''),
                    'urgency': self._calculate_alert_urgency(alert, analysis_data)
                })
        
        # Add key metrics with bounds
        key_metrics = ai_data.get('key_metrics', {})
        formatted['key_metrics'] = {
            'health_score': max(0, min(100, key_metrics.get('health_score', 70))),
            'efficiency_score': max(0, min(100, key_metrics.get('efficiency_score', 70))),
            'growth_potential': max(0, min(100, key_metrics.get('growth_potential', 70))),
            'overall_grade': self._calculate_overall_grade(key_metrics)
        }
        
        # Generate executive summary
        formatted['summary'] = self._generate_executive_summary(formatted, analysis_data)
        
        return formatted
    
    def _categorize_insight(self, insight: Dict[str, Any]) -> str:
        """Categorize insight for better organization"""
        title_lower = insight.get('title', '').lower()
        desc_lower = insight.get('description', '').lower()
        
        if any(word in title_lower + desc_lower for word in ['receita', 'faturamento', 'vendas']):
            return 'revenue'
        elif any(word in title_lower + desc_lower for word in ['despesa', 'gasto', 'custo']):
            return 'expense'
        elif any(word in title_lower + desc_lower for word in ['fluxo', 'caixa', 'liquidez']):
            return 'cashflow'
        elif any(word in title_lower + desc_lower for word in ['risco', 'alerta', 'atenção']):
            return 'risk'
        else:
            return 'general'
    
    def _calculate_prediction_confidence(self, analysis_data: Dict[str, Any]) -> str:
        """Calculate confidence level for predictions"""
        # Based on data quality and patterns
        growth_metrics = analysis_data.get('growth_metrics', {})
        consistency = growth_metrics.get('consistency', 'unknown')
        
        if consistency == 'very_consistent':
            return 'high'
        elif consistency in ['consistent', 'variable']:
            return 'medium'
        else:
            return 'low'
    
    def _assess_implementation_difficulty(self, recommendation: Dict[str, Any]) -> str:
        """Assess difficulty of implementing recommendation"""
        rec_type = recommendation.get('type', '')
        time_frame = recommendation.get('time_to_implement', '')
        
        if rec_type == 'cost_reduction' and time_frame == 'imediato':
            return 'easy'
        elif rec_type == 'revenue_growth':
            return 'hard'
        else:
            return 'medium'
    
    def _calculate_alert_urgency(self, alert: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
        """Calculate urgency level for alerts"""
        severity = alert.get('severity', 'medium')
        risks = analysis_data.get('risk_indicators', {})
        
        if severity == 'high' and risks.get('cash_flow_risk') == 'high':
            return 'immediate'
        elif severity == 'high':
            return 'urgent'
        elif severity == 'medium':
            return 'soon'
        else:
            return 'monitor'
    
    def _calculate_overall_grade(self, key_metrics: Dict[str, Any]) -> str:
        """Calculate overall grade (A-F)"""
        avg_score = np.mean([
            key_metrics.get('health_score', 70),
            key_metrics.get('efficiency_score', 70),
            key_metrics.get('growth_potential', 70)
        ])
        
        if avg_score >= 90:
            return 'A'
        elif avg_score >= 80:
            return 'B'
        elif avg_score >= 70:
            return 'C'
        elif avg_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_executive_summary(self, insights_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an executive summary of the insights"""
        
        health_score = insights_data['key_metrics']['health_score']
        top_insight = insights_data['insights'][0] if insights_data['insights'] else None
        top_risk = next((a for a in insights_data['alerts'] if a['severity'] == 'high'), None)
        
        # Determine overall status
        if health_score > 80:
            overall_status = 'excellent'
            status_message = 'Excelente saúde financeira'
        elif health_score > 70:
            overall_status = 'healthy'
            status_message = 'Boa saúde financeira'
        elif health_score > 50:
            overall_status = 'attention_needed'
            status_message = 'Atenção necessária'
        else:
            overall_status = 'critical'
            status_message = 'Situação crítica'
        
        summary = {
            'overall_status': overall_status,
            'status_message': status_message,
            'key_message': top_insight['title'] if top_insight else 'Análise completa disponível',
            'main_opportunity': insights_data['predictions']['opportunities'][0] if insights_data['predictions']['opportunities'] else None,
            'main_risk': top_risk['title'] if top_risk else None,
            'recommended_action': insights_data['recommendations'][0]['title'] if insights_data['recommendations'] else None,
            'executive_takeaway': self._generate_executive_takeaway(insights_data, analysis_data)
        }
        
        return summary
    
    def _generate_executive_takeaway(self, insights_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
        """Generate a concise executive takeaway"""
        basic = analysis_data.get('basic_metrics', {})
        net_flow = float(basic.get('net_flow', 0))
        growth = analysis_data.get('growth_metrics', {})
        
        if net_flow > 0 and growth.get('income_trend') == 'growing':
            return "Empresa lucrativa com crescimento consistente. Foque em escalar operações."
        elif net_flow > 0 and growth.get('expense_trend') == 'growing':
            return "Lucrativa mas com despesas crescentes. Implemente controles de custo."
        elif net_flow < 0 and growth.get('income_trend') == 'growing':
            return "Déficit atual mas receita crescente. Mantenha foco no crescimento."
        elif net_flow < 0:
            return "Situação deficitária requer ação imediata. Reduza custos e aumente vendas."
        else:
            return "Performance estável. Busque oportunidades de crescimento."
    
    def _generate_enhanced_fallback_insights(self, financial_data: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """Generate enhanced fallback insights when AI is not available"""
        
        # Prepare analysis
        analysis_data = self._prepare_comprehensive_analysis(financial_data)
        
        insights = []
        recommendations = []
        alerts = []
        
        # Extract safe values
        income = float(financial_data.get('income', 0))
        expenses = float(financial_data.get('expenses', 0))
        net_flow = float(financial_data.get('net_flow', income - expenses))
        period_days = max(1, financial_data.get('period_days', 30))
        
        # Generate rule-based insights
        
        # Cash flow analysis
        if net_flow > 0:
            profit_margin = self._safe_percentage(net_flow, income)
            insights.append({
                'type': 'success',
                'title': f'Lucratividade de {profit_margin:.1f}%',
                'description': f'Sua empresa manteve uma margem de lucro saudável, gerando R$ {net_flow:,.2f} de resultado positivo no período',
                'value': f'R$ {net_flow:,.2f}',
                'trend': 'up',
                'priority': 'high',
                'actionable': True
            })
            
            if profit_margin > 20:
                recommendations.append({
                    'type': 'revenue_growth',
                    'title': 'Invista em Crescimento',
                    'description': 'Com margem saudável, considere investir em marketing ou expansão',
                    'potential_impact': 'Crescimento de 20-30%',
                    'priority': 'medium',
                    'time_to_implement': 'medio_prazo'
                })
        else:
            deficit = abs(net_flow)
            deficit_percentage = self._safe_percentage(deficit, income)
            insights.append({
                'type': 'danger',
                'title': f'Déficit de R$ {deficit:,.2f}',
                'description': f'As despesas superaram as receitas em {deficit_percentage:.1f}%. Ação imediata necessária.',
                'value': f'-R$ {deficit:,.2f}',
                'trend': 'down',
                'priority': 'high',
                'actionable': True
            })
            
            alerts.append({
                'severity': 'high',
                'title': 'Fluxo de Caixa Negativo',
                'description': 'Resultado operacional negativo compromete sustentabilidade',
                'action_required': 'Implemente plano de redução de custos e aumento de receitas'
            })
        
        # Burn rate analysis
        daily_burn = expenses / period_days
        monthly_burn = daily_burn * 30
        
        if income > 0:
            runway_months = self._safe_division(income, monthly_burn)
            if runway_months < 3:
                alerts.append({
                    'severity': 'high',
                    'title': f'Runway de apenas {runway_months:.1f} meses',
                    'description': 'Recursos atuais cobrem menos de 3 meses de operação',
                    'action_required': 'Busque capital ou reduza drasticamente custos'
                })
        
        # Category analysis
        top_categories = financial_data.get('top_expense_categories', [])
        if top_categories:
            top_cat = top_categories[0]
            cat_percentage = float(top_cat.get('percentage', 0))
            if cat_percentage > 30:
                cat_amount = float(top_cat.get('amount', 0))
                insights.append({
                    'type': 'warning',
                    'title': f'{top_cat["name"]} representa {cat_percentage:.1f}% dos gastos',
                    'description': f'Esta categoria está consumindo R$ {cat_amount:,.2f}. Avalie oportunidades de otimização.',
                    'value': f'{cat_percentage:.1f}%',
                    'trend': 'stable',
                    'priority': 'medium',
                    'actionable': True
                })
                
                potential_savings = cat_amount * 0.1  # 10% reduction
                recommendations.append({
                    'type': 'cost_reduction',
                    'title': f'Otimize gastos com {top_cat["name"]}',
                    'description': f'Uma redução de 10% economizaria R$ {potential_savings:,.2f} por período',
                    'potential_impact': f'R$ {potential_savings:,.2f}',
                    'priority': 'high',
                    'time_to_implement': 'curto_prazo'
                })
        
        # Growth analysis
        growth_metrics = analysis_data['growth_metrics']
        if growth_metrics.get('income_trend') == 'growing':
            avg_growth = growth_metrics.get('avg_income_growth', 0)
            insights.append({
                'type': 'success',
                'title': 'Receita em Crescimento',
                'description': f'Crescimento médio de {avg_growth:.1f}% ao período',
                'value': f'+{avg_growth:.1f}%',
                'trend': 'up',
                'priority': 'medium',
                'actionable': False
            })
        elif growth_metrics.get('income_trend') == 'declining':
            avg_decline = abs(growth_metrics.get('avg_income_growth', 0))
            alerts.append({
                'severity': 'medium',
                'title': 'Receita em Declínio',
                'description': f'Queda média de {avg_decline:.1f}% detectada',
                'action_required': 'Revise estratégia de vendas e retenção de clientes'
            })
        
        # Expense growth warning
        if growth_metrics.get('expense_trend') == 'growing':
            expense_growth = growth_metrics.get('avg_expense_growth', 0)
            if expense_growth > 10:
                insights.append({
                    'type': 'warning',
                    'title': f'Despesas crescendo {expense_growth:.1f}% ao período',
                    'description': 'Crescimento acelerado de despesas pode comprometer lucratividade',
                    'value': f'+{expense_growth:.1f}%',
                    'trend': 'up',
                    'priority': 'high',
                    'actionable': True
                })
        
        # Risk-based recommendations
        risks = analysis_data['risk_indicators']
        if risks.get('concentration_risk') == 'high':
            recommendations.append({
                'type': 'risk_mitigation',
                'title': 'Diversifique Fornecedores',
                'description': 'Alta concentração em categoria única aumenta vulnerabilidade',
                'potential_impact': 'Redução de 30% no risco operacional',
                'priority': 'medium',
                'time_to_implement': 'medio_prazo'
            })
        
        # Efficiency recommendations
        if expenses > income * 0.9:
            recommendations.append({
                'type': 'efficiency',
                'title': 'Implemente Automação',
                'description': 'Automatize processos repetitivos para reduzir custos operacionais',
                'potential_impact': '10-15% de redução em custos administrativos',
                'priority': 'medium',
                'time_to_implement': 'medio_prazo'
            })
        
        # Predictions (simplified but realistic)
        daily_income = self._safe_division(income, period_days)
        daily_expenses = self._safe_division(expenses, period_days)
        
        # Apply growth trends to predictions
        income_growth_factor = 1 + (growth_metrics.get('avg_income_growth', 0) / 100)
        expense_growth_factor = 1 + (growth_metrics.get('avg_expense_growth', 0) / 100)
        
        predictions = {
            'next_month_income': float(daily_income * 30 * income_growth_factor),
            'next_month_expenses': float(daily_expenses * 30 * expense_growth_factor),
            'projected_savings': float((daily_income * income_growth_factor - daily_expenses * expense_growth_factor) * 30),
            'growth_rate': growth_metrics.get('avg_income_growth', 0),
            'risk_score': risks.get('overall_risk_score', 5),
            'opportunities': self._identify_opportunities(analysis_data),
            'threats': self._identify_threats(analysis_data)
        }
        
        # Key metrics
        health_score = self._calculate_health_score(net_flow, income, risks)
        efficiency_score = self._calculate_efficiency_score(expenses, income)
        growth_potential = self._calculate_growth_potential(growth_metrics, risks)
        
        return {
            'insights': insights,
            'predictions': predictions,
            'recommendations': recommendations,
            'alerts': alerts,
            'key_metrics': {
                'health_score': health_score,
                'efficiency_score': efficiency_score,
                'growth_potential': growth_potential,
                'overall_grade': self._calculate_overall_grade({
                    'health_score': health_score,
                    'efficiency_score': efficiency_score,
                    'growth_potential': growth_potential
                })
            },
            'summary': {
                'overall_status': 'critical' if health_score < 40 else 'attention_needed' if health_score < 70 else 'healthy',
                'status_message': 'Análise baseada em regras (IA indisponível)',
                'key_message': insights[0]['title'] if insights else 'Análise disponível',
                'main_opportunity': recommendations[0]['title'] if recommendations else None,
                'main_risk': alerts[0]['title'] if alerts else None,
                'recommended_action': recommendations[0]['title'] if recommendations else None
            },
            'ai_generated': False,
            'fallback_mode': True,
            'generated_at': timezone.now().isoformat(),
            'version': CACHE_VERSION
        }
    
    def _calculate_health_score(self, net_flow: float, income: float, risks: Dict[str, Any]) -> int:
        """Calculate financial health score"""
        base_score = 50
        
        # Profitability impact
        if income > 0:
            profit_margin = self._safe_percentage(net_flow, income)
            if profit_margin > 20:
                base_score += 30
            elif profit_margin > 10:
                base_score += 20
            elif profit_margin > 0:
                base_score += 10
            else:
                base_score -= 20
        else:
            base_score -= 30
        
        # Risk impact
        risk_score = risks.get('overall_risk_score', 5)
        base_score -= (risk_score - 5) * 5
        
        return max(0, min(100, base_score))
    
    def _calculate_efficiency_score(self, expenses: float, income: float) -> int:
        """Calculate operational efficiency score"""
        if income == 0:
            return 20
        
        expense_ratio = self._safe_percentage(expenses, income)
        
        if expense_ratio < 60:
            return 90
        elif expense_ratio < 70:
            return 80
        elif expense_ratio < 80:
            return 70
        elif expense_ratio < 90:
            return 60
        elif expense_ratio < 100:
            return 50
        else:
            return max(20, 100 - int(expense_ratio))
    
    def _calculate_growth_potential(self, growth_metrics: Dict[str, Any], risks: Dict[str, Any]) -> int:
        """Calculate growth potential score"""
        base_score = 50
        
        # Income trend impact
        if growth_metrics.get('income_trend') == 'growing':
            base_score += 20
        elif growth_metrics.get('income_trend') == 'declining':
            base_score -= 20
        
        # Growth rate impact
        avg_growth = growth_metrics.get('avg_income_growth', 0)
        if avg_growth > 20:
            base_score += 20
        elif avg_growth > 10:
            base_score += 10
        elif avg_growth < -10:
            base_score -= 10
        
        # Consistency impact
        consistency = growth_metrics.get('consistency', 'unknown')
        if consistency == 'very_consistent':
            base_score += 10
        elif consistency == 'highly_variable':
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _identify_opportunities(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Identify business opportunities"""
        opportunities = []
        
        growth = analysis_data.get('growth_metrics', {})
        if growth.get('income_trend') == 'growing':
            opportunities.append('Momento favorável para expansão')
        
        patterns = analysis_data.get('patterns', {})
        if patterns.get('category_concentration', {}).get('diversification_score', 0) < 3:
            opportunities.append('Diversificação de fornecedores pode reduzir custos')
        
        basic = analysis_data.get('basic_metrics', {})
        if float(basic.get('income', 0)) > float(basic.get('expenses', 0)) * 1.2:
            opportunities.append('Margem permite investimento em crescimento')
        
        return opportunities[:3]  # Top 3
    
    def _identify_threats(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Identify business threats"""
        threats = []
        
        risks = analysis_data.get('risk_indicators', {})
        if risks.get('cash_flow_risk') in ['high', 'critical']:
            threats.append('Risco de insolvência no curto prazo')
        
        growth = analysis_data.get('growth_metrics', {})
        if growth.get('expense_trend') == 'growing' and growth.get('avg_expense_growth', 0) > 15:
            threats.append('Crescimento descontrolado de despesas')
        
        if risks.get('concentration_risk') == 'high':
            threats.append('Alta dependência de categoria única')
        
        anomalies = analysis_data.get('anomalies', [])
        if any(a.get('severity') == 'high' for a in anomalies):
            threats.append('Transações anômalas detectadas')
        
        return threats[:3]  # Top 3
    
    def analyze_anomaly(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific transaction anomaly"""
        if not self.client:
            return {
                'is_anomaly': True,
                'explanation': 'Análise detalhada indisponível (IA offline)',
                'risk_level': 'medium',
                'action': 'Revisar manualmente esta transação'
            }
        
        try:
            # Sanitize transaction data
            safe_transaction = self._sanitize_for_ai({'transaction': transaction})['transaction']
            safe_context = self._sanitize_for_ai({'context': context})['context']
            
            prompt = f"""
            Analise esta transação suspeita:
            
            Transação: {json.dumps(safe_transaction, ensure_ascii=False)}
            Contexto: {json.dumps(safe_context, ensure_ascii=False)}
            
            Determine:
            1. Se é realmente uma anomalia
            2. Possíveis explicações
            3. Nível de risco (baixo/médio/alto)
            4. Ação recomendada
            
            Retorne em JSON: {{"is_anomaly": bool, "explanation": str, "risk_level": str, "action": str}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate response
            if 'risk_level' in result and result['risk_level'] not in ['baixo', 'médio', 'alto', 'low', 'medium', 'high']:
                result['risk_level'] = 'medium'
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing anomaly: {e}")
            return {
                'is_anomaly': True,
                'explanation': 'Erro na análise automática',
                'risk_level': 'medium',
                'action': 'Revisar manualmente'
            }
    
    def generate_custom_report_insights(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom insights for specific report types"""
        if not self.client:
            return {
                'insights': 'Insights personalizados indisponíveis no momento',
                'fallback': True
            }
        
        try:
            # Sanitize data
            safe_data = self._sanitize_for_ai(data)
            
            prompts = {
                'cash_flow': "Analise o fluxo de caixa e identifique padrões de entrada/saída, sazonalidades e faça previsões para os próximos 30 dias",
                'profit_loss': "Analise a DRE e identifique principais drivers de lucro/prejuízo, tendências e oportunidades de melhoria",
                'category_analysis': "Analise a distribuição de gastos por categoria e sugira otimizações específicas com potencial de economia",
                'tax_report': "Analise os dados fiscais e identifique oportunidades de economia tributária legal e conformidade"
            }
            
            prompt = prompts.get(report_type, "Analise os dados financeiros fornecidos e forneça insights relevantes")
            prompt += f"\n\nDados: {json.dumps(safe_data, ensure_ascii=False)}\n\nRetorne insights específicos em JSON com estrutura: {{\"insights\": [lista], \"metrics\": {{}}}}."
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um analista financeiro especializado em relatórios para PMEs brasileiras."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['report_type'] = report_type
            result['generated_at'] = timezone.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating custom insights: {e}")
            return {
                'insights': f'Erro ao gerar insights para {report_type}',
                'error': str(e),
                'fallback': True
            }


# Singleton instance
enhanced_ai_service = EnhancedAIInsightsService()