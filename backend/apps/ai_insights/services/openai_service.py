"""
OpenAI Service for GPT-4o mini integration
"""
import json
import logging
from typing import Dict, Any, Optional
from decouple import config
import requests

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI API (GPT-4o mini).
    """

    def __init__(self):
        self.api_key = config('OPENAI_API_KEY', default='')
        self.model = 'gpt-4o-mini'
        self.api_url = 'https://api.openai.com/v1/chat/completions'

        if not self.api_key:
            logger.warning('⚠️ OPENAI_API_KEY not configured in environment variables')

    def generate_insight(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate financial insights using GPT-4o mini.

        Args:
            analysis_data: Structured financial data for analysis

        Returns:
            Dict with insights in structured format

        Raises:
            Exception if API call fails or response is invalid
        """
        if not self.api_key:
            raise ValueError('OpenAI API key not configured. Please add OPENAI_API_KEY to .env file.')

        try:
            # Build the prompt
            prompt = self._build_prompt(analysis_data)

            # Validate prompt
            if not self._validate_prompt(prompt):
                raise ValueError('Invalid prompt structure')

            # Call OpenAI API
            response = self._call_api(prompt)

            # Parse and validate response
            insights = self._parse_response(response)

            if not self._validate_response(insights):
                raise ValueError('Invalid response structure from AI')

            return insights

        except Exception as e:
            logger.error(f'Error generating insights with OpenAI: {str(e)}')
            raise

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """Build structured prompt for GPT-4o mini."""

        context = data.get('context', {})
        financial_data = data.get('data', {})

        prompt = f"""Você é um analista financeiro especializado em PMEs brasileiras.

**CONTEXTO DA EMPRESA:**
- Tipo: {context.get('company_type', 'N/A')}
- Setor: {context.get('business_sector', 'N/A')}
- Período analisado: {context.get('period', 'N/A')}
- Última análise: {context.get('previous_analysis_date', 'Primeira análise')}

**DADOS FINANCEIROS:**
{json.dumps(financial_data, indent=2, ensure_ascii=False)}

**TAREFA:**
Analise a saúde financeira desta PME e forneça insights acionáveis em português brasileiro.

**IMPORTANTE:**
- Base suas análises APENAS nos dados fornecidos
- NÃO invente números ou informações
- Se dados forem insuficientes, indique isso
- Seja específico e objetivo

**FORMATO DE RESPOSTA (JSON válido):**
{{
  "health_score": 7.5,
  "health_status": "Bom",
  "summary": "Resumo executivo da análise (2-3 frases)",
  "insights": [
    {{
      "type": "alert",
      "severity": "high|medium|low",
      "title": "Título do insight",
      "description": "Descrição detalhada baseada nos dados",
      "recommendation": "Recomendação acionável"
    }}
  ],
  "predictions": {{
    "next_month_cash_flow": 16500.00,
    "confidence": "high|medium|low",
    "reasoning": "Justificativa baseada nos dados históricos"
  }},
  "top_recommendations": [
    "Recomendação 1",
    "Recomendação 2",
    "Recomendação 3"
  ]
}}

Retorne APENAS o JSON, sem texto adicional antes ou depois."""

        return prompt

    def _validate_prompt(self, prompt: str) -> bool:
        """Validate prompt structure before sending to API."""
        if not prompt or len(prompt) < 100:
            logger.error('Prompt too short or empty')
            return False

        required_keywords = ['CONTEXTO', 'DADOS FINANCEIROS', 'TAREFA', 'FORMATO DE RESPOSTA']
        for keyword in required_keywords:
            if keyword not in prompt:
                logger.error(f'Missing required keyword in prompt: {keyword}')
                return False

        return True

    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API with the prompt."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'Você é um analista financeiro especializado em PMEs brasileiras. Responda sempre em JSON válido.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,  # Lower temperature for more consistent outputs
            'response_format': {'type': 'json_object'}
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise Exception('OpenAI API request timed out')
        except requests.exceptions.RequestException as e:
            raise Exception(f'OpenAI API request failed: {str(e)}')

    def _parse_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAI API response and extract insights."""
        try:
            # Extract content from API response
            content = api_response['choices'][0]['message']['content']

            # Parse JSON
            insights = json.loads(content)

            # Add metadata
            insights['tokens_used'] = api_response.get('usage', {}).get('total_tokens', 0)
            insights['model_version'] = api_response.get('model', self.model)

            return insights

        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.error(f'Error parsing OpenAI response: {str(e)}')
            logger.error(f'Response: {api_response}')
            raise Exception('Failed to parse AI response')

    def _validate_response(self, insights: Dict[str, Any]) -> bool:
        """Validate the structure of AI response."""
        required_fields = ['health_score', 'health_status', 'summary', 'insights', 'top_recommendations']

        for field in required_fields:
            if field not in insights:
                logger.error(f'Missing required field in AI response: {field}')
                return False

        # Validate health_score range
        score = insights.get('health_score')
        if not isinstance(score, (int, float)) or not (0 <= score <= 10):
            logger.error(f'Invalid health_score: {score}')
            return False

        # Validate health_status
        valid_statuses = ['Excelente', 'Bom', 'Regular', 'Ruim']
        if insights.get('health_status') not in valid_statuses:
            logger.error(f"Invalid health_status: {insights.get('health_status')}")
            return False

        # Validate insights structure
        if not isinstance(insights.get('insights'), list):
            logger.error('insights field must be a list')
            return False

        for insight in insights['insights']:
            required_insight_fields = ['type', 'severity', 'title', 'description', 'recommendation']
            if not all(field in insight for field in required_insight_fields):
                logger.error(f'Invalid insight structure: {insight}')
                return False

        # Validate recommendations
        if not isinstance(insights.get('top_recommendations'), list):
            logger.error('top_recommendations must be a list')
            return False

        return True

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the configured model."""
        return {
            'model': self.model,
            'api_configured': bool(self.api_key),
            'api_url': self.api_url
        }
