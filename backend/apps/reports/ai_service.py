"""
AI Service for CaixaHub - Real AI insights using OpenAI
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from django.conf import settings
from openai import OpenAI
from django.utils import timezone
from .ai_service import ai_insights_service  


logger = logging.getLogger(__name__)


class AIInsightsService:
    """Service to generate real AI-powered financial insights using OpenAI"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            logger.warning("OpenAI API key not found. AI insights will be disabled.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    def generate_insights(
        self, 
        financial_data: Dict[str, Any],
        company_name: str = "Empresa"
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights from financial data
        
        Args:
            financial_data: Dictionary containing financial metrics
            company_name: Name of the company
            
        Returns:
            Dictionary with AI-generated insights, predictions, and recommendations
        """
        if not self.client:
            logger.warning("OpenAI client not available. Returning basic insights.")
            return self._generate_basic_insights(financial_data)
        
        try:
            # Prepare the prompt with financial data
            prompt = self._create_analysis_prompt(financial_data, company_name)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": """Você é um consultor financeiro especializado em análise de dados 
                        para pequenas e médias empresas brasileiras. Analise os dados fornecidos e gere 
                        insights práticos, previsões realistas e recomendações acionáveis. 
                        Responda sempre em português brasileiro de forma clara e profissional.
                        Retorne a resposta em formato JSON válido."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            
            try:
                # Try to parse as JSON
                insights_data = json.loads(ai_response)
                return self._format_ai_insights(insights_data)
            except json.JSONDecodeError:
                # If not valid JSON, parse the text response
                return self._parse_text_insights(ai_response, financial_data)
                
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return self._generate_basic_insights(financial_data)
    
    def _create_analysis_prompt(self, data: Dict[str, Any], company_name: str) -> str:
        """Create a detailed prompt for financial analysis"""
        
        # Extract key metrics
        income = data.get('income', 0)
        expenses = data.get('expenses', 0)
        net_flow = data.get('net_flow', 0)
        transaction_count = data.get('transaction_count', 0)
        period_days = data.get('period_days', 30)
        top_categories = data.get('top_expense_categories', [])
        
        # Calculate additional metrics
        daily_avg_income = income / period_days if period_days > 0 else 0
        daily_avg_expense = expenses / period_days if period_days > 0 else 0
        profit_margin = (net_flow / income * 100) if income > 0 else 0
        
        prompt = f"""
        Analise os seguintes dados financeiros da empresa {company_name} para um período de {period_days} dias:
        
        RESUMO FINANCEIRO:
        - Receita Total: R$ {income:,.2f}
        - Despesas Totais: R$ {expenses:,.2f}
        - Resultado Líquido: R$ {net_flow:,.2f}
        - Margem de Lucro: {profit_margin:.1f}%
        - Número de Transações: {transaction_count}
        - Média Diária de Receita: R$ {daily_avg_income:,.2f}
        - Média Diária de Despesas: R$ {daily_avg_expense:,.2f}
        
        PRINCIPAIS CATEGORIAS DE GASTOS:
        """
        
        for i, cat in enumerate(top_categories[:5], 1):
            prompt += f"\n{i}. {cat['name']}: R$ {cat['amount']:,.2f} ({cat['percentage']:.1f}%)"
        
        prompt += """
        
        Com base nesses dados, forneça uma análise detalhada em formato JSON com a seguinte estrutura:
        {
            "insights": [
                {
                    "type": "success/warning/danger/info",
                    "title": "Título do Insight",
                    "description": "Descrição detalhada",
                    "value": "Valor relevante",
                    "trend": "up/down/stable"
                }
            ],
            "predictions": {
                "next_month_income": valor_numerico,
                "next_month_expenses": valor_numerico,
                "projected_savings": valor_numerico,
                "risk_analysis": "descrição dos riscos"
            },
            "recommendations": [
                {
                    "type": "warning/info/success",
                    "title": "Título da Recomendação",
                    "description": "Descrição detalhada e acionável",
                    "priority": "high/medium/low"
                }
            ]
        }
        
        Gere pelo menos 4 insights únicos e perspicazes, previsões baseadas em tendências, 
        e 3-5 recomendações práticas e específicas para melhorar a saúde financeira da empresa.
        """
        
        return prompt
    
    def _format_ai_insights(self, ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format AI insights to match expected structure"""
        
        # Ensure all required fields exist with defaults
        insights = ai_data.get('insights', [])
        predictions = ai_data.get('predictions', {})
        recommendations = ai_data.get('recommendations', [])
        
        # Validate and clean insights
        cleaned_insights = []
        for insight in insights[:6]:  # Limit to 6 insights
            if isinstance(insight, dict) and 'title' in insight:
                cleaned_insights.append({
                    'type': insight.get('type', 'info'),
                    'title': insight.get('title', 'Insight'),
                    'description': insight.get('description', ''),
                    'value': insight.get('value', ''),
                    'trend': insight.get('trend', None)
                })
        
        # Validate predictions
        cleaned_predictions = {
            'next_month_income': float(predictions.get('next_month_income', 0)),
            'next_month_expenses': float(predictions.get('next_month_expenses', 0)),
            'projected_savings': float(predictions.get('projected_savings', 0)),
            'risk_analysis': predictions.get('risk_analysis', '')
        }
        
        # Validate recommendations
        cleaned_recommendations = []
        for rec in recommendations[:5]:  # Limit to 5 recommendations
            if isinstance(rec, dict) and 'title' in rec:
                cleaned_recommendations.append({
                    'type': rec.get('type', 'info'),
                    'title': rec.get('title', 'Recomendação'),
                    'description': rec.get('description', ''),
                    'priority': rec.get('priority', 'medium')
                })
        
        return {
            'insights': cleaned_insights,
            'predictions': cleaned_predictions,
            'recommendations': cleaned_recommendations,
            'ai_generated': True
        }
    
    def _parse_text_insights(self, text: str, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        logger.warning("Failed to parse AI response as JSON, using text parsing")
        
        # Extract basic insights from the text
        insights = []
        
        # Try to find insights in the text
        if "positiv" in text.lower():
            insights.append({
                'type': 'success',
                'title': 'Análise Positiva',
                'description': 'A IA identificou aspectos positivos em suas finanças',
                'value': f"R$ {financial_data.get('net_flow', 0):,.2f}",
                'trend': 'up'
            })
        
        if "negativ" in text.lower() or "atenção" in text.lower():
            insights.append({
                'type': 'warning',
                'title': 'Pontos de Atenção',
                'description': 'A IA identificou áreas que precisam de atenção',
                'value': 'Análise',
                'trend': 'down'
            })
        
        # If no insights were extracted, add a generic one
        if not insights:
            insights.append({
                'type': 'info',
                'title': 'Análise Processada',
                'description': 'A IA processou seus dados financeiros',
                'value': 'Completo',
            })
        
        # Basic predictions based on financial data
        income = financial_data.get('income', 0)
        expenses = financial_data.get('expenses', 0)
        
        return {
            'insights': insights,
            'predictions': {
                'next_month_income': float(income),
                'next_month_expenses': float(expenses),
                'projected_savings': float(income - expenses),
                'risk_analysis': 'Análise de risco baseada em IA'
            },
            'recommendations': [
                {
                    'type': 'info',
                    'title': 'Análise Completa Disponível',
                    'description': 'A IA gerou insights detalhados sobre suas finanças',
                    'priority': 'medium'
                }
            ],
            'ai_generated': True,
            'parse_method': 'text'
        }
    
    def _generate_basic_insights(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic insights when AI is not available"""
        
        income = financial_data.get('income', 0)
        expenses = financial_data.get('expenses', 0)
        net_flow = financial_data.get('net_flow', 0)
        
        insights = []
        
        # Cash flow insight
        if net_flow > 0:
            insights.append({
                'type': 'success',
                'title': 'Fluxo de Caixa Positivo',
                'description': f'Resultado positivo de R$ {net_flow:,.2f}',
                'value': f'R$ {net_flow:,.2f}',
                'trend': 'up'
            })
        else:
            insights.append({
                'type': 'warning',
                'title': 'Fluxo de Caixa Negativo',
                'description': f'Déficit de R$ {abs(net_flow):,.2f}',
                'value': f'R$ {abs(net_flow):,.2f}',
                'trend': 'down'
            })
        
        # Add note about AI
        insights.append({
            'type': 'info',
            'title': 'IA Indisponível',
            'description': 'Configure a chave da API OpenAI para insights avançados',
            'value': 'Config'
        })
        
        return {
            'insights': insights,
            'predictions': {
                'next_month_income': float(income),
                'next_month_expenses': float(expenses),
                'projected_savings': float(net_flow),
                'risk_analysis': 'IA não disponível'
            },
            'recommendations': [
                {
                    'type': 'info',
                    'title': 'Ative a IA',
                    'description': 'Configure OPENAI_API_KEY no arquivo .env para insights avançados',
                    'priority': 'high'
                }
            ],
            'ai_generated': False
        }


# Singleton instance
ai_insights_service = AIInsightsService()