"""
Enhanced AI Service for CaixaHub - Advanced financial analysis using OpenAI
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


class EnhancedAIInsightsService:
    """Enhanced service for generating advanced AI-powered financial insights"""
    
    def __init__(self):
        """Initialize OpenAI client with fallback options"""
        self.client = None
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
                self.client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
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
        Generate comprehensive AI-powered insights with caching
        
        Args:
            financial_data: Dictionary containing all financial metrics
            company_name: Name of the company
            force_refresh: Force regeneration ignoring cache
            
        Returns:
            Dictionary with insights, predictions, recommendations, and alerts
        """
        # Generate cache key
        cache_key = self._generate_cache_key(financial_data, company_name)
        
        # Check cache unless force refresh
        if not force_refresh:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached insights for {company_name}")
                cached_result['from_cache'] = True
                return cached_result
        
        # Generate new insights
        if not self.client:
            logger.warning("OpenAI client not available. Using enhanced fallback insights.")
            return self._generate_enhanced_fallback_insights(financial_data, company_name)
        
        try:
            # Prepare comprehensive analysis
            analysis_data = self._prepare_comprehensive_analysis(financial_data)
            
            # Create detailed prompt
            prompt = self._create_advanced_analysis_prompt(analysis_data, company_name)
            
            # Call OpenAI API with optimized parameters
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using the faster, more cost-effective model
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Parse and validate response
            ai_response = response.choices[0].message.content
            insights_data = json.loads(ai_response)
            
            # Format and enhance insights
            result = self._format_and_enhance_insights(insights_data, analysis_data)
            
            # Cache the result for 24 hours
            cache.set(cache_key, result, 86400)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return self._generate_enhanced_fallback_insights(financial_data, company_name)
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return self._generate_enhanced_fallback_insights(financial_data, company_name)
    
    def _generate_cache_key(self, financial_data: Dict[str, Any], company_name: str) -> str:
        """Generate a cache key based on financial data"""
        # Create a simplified version of the data for hashing
        key_data = {
            'company': company_name,
            'period_days': financial_data.get('period_days'),
            'income': float(financial_data.get('income', 0)),
            'expenses': float(financial_data.get('expenses', 0)),
            'transaction_count': financial_data.get('transaction_count', 0)
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
        """
    
    def _prepare_comprehensive_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive analysis data for AI processing"""
        
        # Extract base metrics
        income = financial_data.get('income', 0)
        expenses = financial_data.get('expenses', 0)
        net_flow = financial_data.get('net_flow', 0)
        period_days = financial_data.get('period_days', 30)
        
        # Calculate advanced metrics
        analysis = {
            'basic_metrics': financial_data,
            'calculated_metrics': {
                'profit_margin': (net_flow / income * 100) if income > 0 else 0,
                'expense_ratio': (expenses / income * 100) if income > 0 else 0,
                'daily_burn_rate': expenses / period_days if period_days > 0 else 0,
                'daily_revenue': income / period_days if period_days > 0 else 0,
                'months_of_runway': income / (expenses / period_days * 30) if expenses > 0 and period_days > 0 else 0
            },
            'patterns': self._analyze_patterns(financial_data),
            'anomalies': self._detect_anomalies(financial_data),
            'growth_metrics': self._calculate_growth_metrics(financial_data),
            'risk_indicators': self._assess_risk_indicators(financial_data)
        }
        
        return analysis
    
    def _analyze_patterns(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze spending and income patterns"""
        patterns = {
            'weekly_variation': [],
            'category_concentration': {},
            'payment_frequency': {},
            'seasonal_indicators': []
        }
        
        # Analyze weekly patterns
        weekly_data = financial_data.get('weekly_patterns', [])
        if weekly_data:
            incomes = [w['income'] for w in weekly_data]
            expenses = [w['expenses'] for w in weekly_data]
            
            if incomes:
                patterns['weekly_variation'] = {
                    'income_volatility': self._calculate_volatility(incomes),
                    'expense_volatility': self._calculate_volatility(expenses),
                    'best_week': max(weekly_data, key=lambda x: x['net']),
                    'worst_week': min(weekly_data, key=lambda x: x['net'])
                }
        
        # Analyze category concentration
        categories = financial_data.get('top_expense_categories', [])
        if categories:
            total_categorized = sum(cat['amount'] for cat in categories)
            patterns['category_concentration'] = {
                'top_3_percentage': sum(cat['percentage'] for cat in categories[:3]),
                'diversification_score': len([c for c in categories if c['percentage'] > 5]),
                'dominant_category': categories[0] if categories else None
            }
        
        return patterns
    
    def _detect_anomalies(self, financial_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect financial anomalies"""
        anomalies = []
        
        # Check for unusual transactions
        largest_expense = financial_data.get('largest_expense', {})
        if largest_expense.get('amount', 0) > financial_data.get('expenses', 0) * 0.2:
            anomalies.append({
                'type': 'large_expense',
                'description': f"Despesa de R$ {largest_expense['amount']:,.2f} representa mais de 20% do total",
                'transaction': largest_expense['description']
            })
        
        # Check for spending spikes
        weekly_data = financial_data.get('weekly_patterns', [])
        if len(weekly_data) > 1:
            avg_weekly_expense = sum(w['expenses'] for w in weekly_data) / len(weekly_data)
            for week in weekly_data:
                if week['expenses'] > avg_weekly_expense * 1.5:
                    anomalies.append({
                        'type': 'spending_spike',
                        'week': week['week_start'],
                        'amount': week['expenses'],
                        'deviation': (week['expenses'] / avg_weekly_expense - 1) * 100
                    })
        
        return anomalies
    
    def _calculate_growth_metrics(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate growth and trend metrics"""
        weekly_data = financial_data.get('weekly_patterns', [])
        
        if len(weekly_data) < 2:
            return {'trend': 'insufficient_data'}
        
        # Calculate week-over-week growth
        income_growth = []
        expense_growth = []
        
        for i in range(1, len(weekly_data)):
            if weekly_data[i-1]['income'] > 0:
                income_growth.append(
                    (weekly_data[i]['income'] - weekly_data[i-1]['income']) / weekly_data[i-1]['income'] * 100
                )
            if weekly_data[i-1]['expenses'] > 0:
                expense_growth.append(
                    (weekly_data[i]['expenses'] - weekly_data[i-1]['expenses']) / weekly_data[i-1]['expenses'] * 100
                )
        
        return {
            'income_trend': 'growing' if sum(income_growth) > 0 else 'declining',
            'expense_trend': 'growing' if sum(expense_growth) > 0 else 'declining',
            'avg_income_growth': sum(income_growth) / len(income_growth) if income_growth else 0,
            'avg_expense_growth': sum(expense_growth) / len(expense_growth) if expense_growth else 0,
            'momentum': 'positive' if sum(income_growth) > sum(expense_growth) else 'negative'
        }
    
    def _assess_risk_indicators(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess financial risk indicators"""
        income = financial_data.get('income', 0)
        expenses = financial_data.get('expenses', 0)
        
        risks = {
            'cash_flow_risk': 'high' if expenses > income else 'medium' if expenses > income * 0.8 else 'low',
            'concentration_risk': 'high' if len(financial_data.get('top_expense_categories', [])) < 3 else 'low',
            'volatility_risk': self._assess_volatility_risk(financial_data),
            'dependency_risk': self._assess_dependency_risk(financial_data)
        }
        
        return risks
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation)"""
        if not values or len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        if mean == 0:
            return 0
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        return (std_dev / mean) * 100
    
    def _assess_volatility_risk(self, financial_data: Dict[str, Any]) -> str:
        """Assess volatility risk level"""
        weekly_data = financial_data.get('weekly_patterns', [])
        if not weekly_data:
            return 'unknown'
        
        income_values = [w['income'] for w in weekly_data]
        volatility = self._calculate_volatility(income_values)
        
        if volatility > 50:
            return 'high'
        elif volatility > 25:
            return 'medium'
        return 'low'
    
    def _assess_dependency_risk(self, financial_data: Dict[str, Any]) -> str:
        """Assess customer dependency risk"""
        # This would need actual customer data, using a simplified version
        top_categories = financial_data.get('top_expense_categories', [])
        if top_categories and top_categories[0]['percentage'] > 40:
            return 'high'
        return 'low'
    
    def _create_advanced_analysis_prompt(self, analysis_data: Dict[str, Any], company_name: str) -> str:
        """Create an advanced analysis prompt with all insights"""
        
        basic = analysis_data['basic_metrics']
        calculated = analysis_data['calculated_metrics']
        patterns = analysis_data['patterns']
        anomalies = analysis_data['anomalies']
        growth = analysis_data['growth_metrics']
        risks = analysis_data['risk_indicators']
        
        prompt = f"""
        Analise os dados financeiros detalhados da empresa {company_name}:
        
        MÉTRICAS BÁSICAS ({basic['period_days']} dias):
        - Receita Total: R$ {basic['income']:,.2f}
        - Despesas Totais: R$ {basic['expenses']:,.2f}
        - Resultado Líquido: R$ {basic['net_flow']:,.2f}
        - Transações: {basic['transaction_count']}
        
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
            prompt += f"\n{i}. {cat['name']}: R$ {cat['amount']:,.2f} ({cat['percentage']:.1f}%) - {cat['count']} transações"
        
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
        """
        
        return prompt
    
    def _format_and_enhance_insights(self, ai_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and enhance AI insights with additional context"""
        
        # Ensure all required fields exist
        formatted = {
            'insights': [],
            'predictions': {},
            'recommendations': [],
            'alerts': [],
            'key_metrics': {},
            'summary': {},
            'ai_generated': True,
            'generated_at': timezone.now().isoformat()
        }
        
        # Process insights with priority sorting
        insights = ai_data.get('insights', [])
        for insight in insights:
            if isinstance(insight, dict) and 'title' in insight:
                formatted_insight = {
                    'type': insight.get('type', 'info'),
                    'title': insight.get('title', 'Insight'),
                    'description': insight.get('description', ''),
                    'value': insight.get('value', ''),
                    'trend': insight.get('trend'),
                    'priority': insight.get('priority', 'medium'),
                    'actionable': insight.get('actionable', True)
                }
                formatted['insights'].append(formatted_insight)
        
        # Sort insights by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        formatted['insights'].sort(key=lambda x: priority_order.get(x['priority'], 1))
        
        # Process predictions with validation
        predictions = ai_data.get('predictions', {})
        formatted['predictions'] = {
            'next_month_income': float(predictions.get('next_month_income', 0)),
            'next_month_expenses': float(predictions.get('next_month_expenses', 0)),
            'projected_savings': float(predictions.get('projected_savings', 0)),
            'growth_rate': float(predictions.get('growth_rate', 0)),
            'risk_score': int(predictions.get('risk_score', 5)),
            'opportunities': predictions.get('opportunities', []),
            'threats': predictions.get('threats', [])
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
                    'time_to_implement': rec.get('time_to_implement', 'curto_prazo')
                }
                formatted['recommendations'].append(formatted_rec)
        
        # Process alerts
        alerts = ai_data.get('alerts', [])
        for alert in alerts:
            if isinstance(alert, dict) and 'title' in alert:
                formatted['alerts'].append({
                    'severity': alert.get('severity', 'medium'),
                    'title': alert.get('title', 'Alerta'),
                    'description': alert.get('description', ''),
                    'action_required': alert.get('action_required', '')
                })
        
        # Add key metrics
        formatted['key_metrics'] = {
            'health_score': ai_data.get('key_metrics', {}).get('health_score', 70),
            'efficiency_score': ai_data.get('key_metrics', {}).get('efficiency_score', 70),
            'growth_potential': ai_data.get('key_metrics', {}).get('growth_potential', 70)
        }
        
        # Generate executive summary
        formatted['summary'] = self._generate_executive_summary(formatted, analysis_data)
        
        return formatted
    
    def _generate_executive_summary(self, insights_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an executive summary of the insights"""
        
        health_score = insights_data['key_metrics']['health_score']
        top_insight = insights_data['insights'][0] if insights_data['insights'] else None
        top_risk = next((a for a in insights_data['alerts'] if a['severity'] == 'high'), None)
        
        summary = {
            'overall_status': 'healthy' if health_score > 70 else 'attention_needed' if health_score > 40 else 'critical',
            'key_message': top_insight['title'] if top_insight else 'Análise completa disponível',
            'main_opportunity': insights_data['predictions']['opportunities'][0] if insights_data['predictions']['opportunities'] else None,
            'main_risk': top_risk['title'] if top_risk else None,
            'recommended_action': insights_data['recommendations'][0]['title'] if insights_data['recommendations'] else None
        }
        
        return summary
    
    def _generate_enhanced_fallback_insights(self, financial_data: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """Generate enhanced fallback insights when AI is not available"""
        
        # Prepare analysis
        analysis_data = self._prepare_comprehensive_analysis(financial_data)
        
        insights = []
        recommendations = []
        alerts = []
        
        # Generate rule-based insights
        income = financial_data.get('income', 0)
        expenses = financial_data.get('expenses', 0)
        net_flow = financial_data.get('net_flow', 0)
        
        # Cash flow analysis
        if net_flow > 0:
            profit_margin = (net_flow / income * 100) if income > 0 else 0
            insights.append({
                'type': 'success',
                'title': f'Lucratividade de {profit_margin:.1f}%',
                'description': f'Sua empresa manteve uma margem de lucro saudável, gerando R$ {net_flow:,.2f} de resultado positivo',
                'value': f'R$ {net_flow:,.2f}',
                'trend': 'up',
                'priority': 'high',
                'actionable': True
            })
        else:
            deficit = abs(net_flow)
            insights.append({
                'type': 'danger',
                'title': f'Déficit de R$ {deficit:,.2f}',
                'description': f'As despesas superaram as receitas em {(deficit/income*100) if income > 0 else 100:.1f}%',
                'value': f'-R$ {deficit:,.2f}',
                'trend': 'down',
                'priority': 'high',
                'actionable': True
            })
            
            alerts.append({
                'severity': 'high',
                'title': 'Fluxo de Caixa Negativo',
                'description': 'Ação imediata necessária para reverter o déficit',
                'action_required': 'Reduza despesas ou aumente receitas urgentemente'
            })
        
        # Category analysis
        top_categories = financial_data.get('top_expense_categories', [])
        if top_categories:
            top_cat = top_categories[0]
            if top_cat['percentage'] > 30:
                insights.append({
                    'type': 'warning',
                    'title': f'{top_cat["name"]} representa {top_cat["percentage"]:.1f}% dos gastos',
                    'description': f'Esta categoria está consumindo R$ {top_cat["amount"]:,.2f}, considere otimizar',
                    'value': f'{top_cat["percentage"]:.1f}%',
                    'trend': 'stable',
                    'priority': 'medium',
                    'actionable': True
                })
                
                recommendations.append({
                    'type': 'cost_reduction',
                    'title': f'Otimize gastos com {top_cat["name"]}',
                    'description': f'Uma redução de 10% economizaria R$ {top_cat["amount"]*0.1:,.2f} por período',
                    'potential_impact': f'R$ {top_cat["amount"]*0.1:,.2f}',
                    'priority': 'high',
                    'time_to_implement': 'curto_prazo'
                })
        
        # Growth analysis
        growth_metrics = analysis_data['growth_metrics']
        if growth_metrics.get('income_trend') == 'growing':
            insights.append({
                'type': 'success',
                'title': 'Receita em Crescimento',
                'description': f'Crescimento médio de {growth_metrics["avg_income_growth"]:.1f}% ao período',
                'value': f'+{growth_metrics["avg_income_growth"]:.1f}%',
                'trend': 'up',
                'priority': 'medium',
                'actionable': False
            })
        
        # Risk alerts
        if analysis_data['risk_indicators']['cash_flow_risk'] == 'high':
            alerts.append({
                'severity': 'high',
                'title': 'Alto Risco de Fluxo de Caixa',
                'description': 'Despesas muito próximas ou acima das receitas',
                'action_required': 'Implemente controle de gastos imediato'
            })
        
        # Predictions (simplified)
        period_days = financial_data.get('period_days', 30)
        daily_income = income / period_days if period_days > 0 else 0
        daily_expenses = expenses / period_days if period_days > 0 else 0
        
        predictions = {
            'next_month_income': float(daily_income * 30),
            'next_month_expenses': float(daily_expenses * 30),
            'projected_savings': float((daily_income - daily_expenses) * 30),
            'growth_rate': growth_metrics.get('avg_income_growth', 0),
            'risk_score': 7 if net_flow < 0 else 5 if net_flow < income * 0.2 else 3,
            'opportunities': ['Otimização de custos', 'Diversificação de receitas'],
            'threats': ['Concentração de despesas', 'Volatilidade de receitas'] if growth_metrics.get('income_trend') == 'declining' else []
        }
        
        # Key metrics
        health_score = 30 if net_flow < 0 else 70 if net_flow > income * 0.2 else 50
        efficiency_score = 80 if expenses < income * 0.7 else 50 if expenses < income else 20
        
        return {
            'insights': insights,
            'predictions': predictions,
            'recommendations': recommendations,
            'alerts': alerts,
            'key_metrics': {
                'health_score': health_score,
                'efficiency_score': efficiency_score,
                'growth_potential': 50  # Default fallback
            },
            'summary': {
                'overall_status': 'critical' if health_score < 40 else 'attention_needed' if health_score < 70 else 'healthy',
                'key_message': insights[0]['title'] if insights else 'Análise disponível',
                'main_opportunity': recommendations[0]['title'] if recommendations else None,
                'main_risk': alerts[0]['title'] if alerts else None,
                'recommended_action': recommendations[0]['title'] if recommendations else None
            },
            'ai_generated': False,
            'fallback_mode': True,
            'generated_at': timezone.now().isoformat()
        }
    
    def analyze_anomaly(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific transaction anomaly"""
        if not self.client:
            return {'analysis': 'Análise de IA não disponível', 'severity': 'medium'}
        
        try:
            prompt = f"""
            Analise esta transação suspeita:
            
            Transação: {json.dumps(transaction, ensure_ascii=False)}
            Contexto: {json.dumps(context, ensure_ascii=False)}
            
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
                max_tokens=200
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error analyzing anomaly: {e}")
            return {'analysis': 'Erro na análise', 'severity': 'medium'}
    
    def generate_custom_report_insights(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom insights for specific report types"""
        if not self.client:
            return {'insights': 'Insights personalizados não disponíveis'}
        
        try:
            prompts = {
                'cash_flow': "Analise o fluxo de caixa e identifique padrões de entrada/saída, sazonalidades e previsões",
                'profit_loss': "Analise a DRE e identifique principais drivers de lucro/prejuízo e oportunidades",
                'category_analysis': "Analise a distribuição de gastos por categoria e sugira otimizações",
                'tax_report': "Analise os dados fiscais e identifique oportunidades de economia tributária legal"
            }
            
            prompt = prompts.get(report_type, "Analise os dados financeiros fornecidos")
            prompt += f"\n\nDados: {json.dumps(data, ensure_ascii=False)}\n\nRetorne insights específicos em JSON."
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating custom insights: {e}")
            return {'insights': 'Erro ao gerar insights personalizados'}


# Singleton instance
enhanced_ai_service = EnhancedAIInsightsService()