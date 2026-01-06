"""
Insight Generator - Orchestrates the AI insight generation process
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from apps.ai_insights.models import AIInsight, AIInsightConfig
from apps.ai_insights.services.openai_service import OpenAIService
from apps.ai_insights.services.data_aggregator import DataAggregator

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Orchestrates the process of generating AI insights for a user.
    """

    def __init__(self, user):
        self.user = user
        self.openai_service = OpenAIService()
        self.data_aggregator = DataAggregator(user)

    def generate(self, force: bool = False) -> AIInsight:
        """
        Generate AI insights for the user.

        Args:
            force: If True, generate even if a recent insight exists

        Returns:
            AIInsight instance

        Raises:
            ValueError: If user doesn't have required company information
            Exception: If generation fails
        """
        try:
            # Validate prerequisites
            self._validate_prerequisites()

            # Check if should generate (unless forced)
            if not force and not self._should_generate():
                last_insight = AIInsight.objects.filter(
                    user=self.user,
                    has_error=False
                ).first()
                logger.info(f'Skipping generation for user {self.user.id} - recent insight exists')
                return last_insight

            # Aggregate financial data
            logger.info(f'Aggregating data for user {self.user.id}')
            analysis_data = self.data_aggregator.aggregate_data()

            # Generate insights with AI
            logger.info(f'Calling OpenAI API for user {self.user.id}')
            ai_response = self.openai_service.generate_insight(analysis_data)

            # Save insights to database
            insight = self._save_insight(ai_response, analysis_data)

            # Update config
            self._update_config()

            logger.info(f'✅ Successfully generated insight {insight.id} for user {self.user.id}')
            return insight

        except Exception as e:
            logger.error(f'❌ Error generating insight for user {self.user.id}: {str(e)}')
            # Save error insight and return it instead of re-raising
            # This prevents Celery from retrying and creating duplicate error insights
            error_insight = self._save_error_insight(str(e))
            return error_insight

    def _validate_prerequisites(self):
        """Validate that user has required information for insights."""
        # Check if user has company
        if not hasattr(self.user, 'company') or self.user.company is None:
            raise ValueError('Usuário não possui empresa cadastrada')

        company = self.user.company

        # Check company_type and business_sector
        if not company.company_type or not company.business_sector:
            raise ValueError('Empresa precisa ter tipo e setor cadastrados')

        # Check if user has AI insights enabled
        config, _ = AIInsightConfig.objects.get_or_create(user=self.user)
        if not config.is_enabled:
            raise ValueError('Insights com IA não estão habilitados para este usuário')

    def _should_generate(self) -> bool:
        """
        Check if a new insight should be generated.
        Returns False if a recent insight (< 7 days) exists.
        """
        seven_days_ago = timezone.now() - timedelta(days=7)

        recent_insight = AIInsight.objects.filter(
            user=self.user,
            generated_at__gte=seven_days_ago,
            has_error=False
        ).exists()

        return not recent_insight

    def _save_insight(self, ai_response: dict, analysis_data: dict) -> AIInsight:
        """Save the AI-generated insight to database."""
        # Calculate period
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)

        # Map health_status to model choices
        status_mapping = {
            'Excelente': 'excellent',
            'Bom': 'good',
            'Regular': 'regular',
            'Ruim': 'poor',
            'Crítico': 'poor'  # Map Crítico to poor
        }

        # Separate insights by type
        alerts = [
            insight for insight in ai_response.get('insights', [])
            if insight.get('type') == 'alert'
        ]

        opportunities = [
            insight for insight in ai_response.get('insights', [])
            if insight.get('type') == 'opportunity'
        ]

        with transaction.atomic():
            insight = AIInsight.objects.create(
                user=self.user,
                health_score=Decimal(str(ai_response.get('health_score', 0))),
                health_status=status_mapping.get(
                    ai_response.get('health_status', 'Regular'),
                    'regular'
                ),
                summary=ai_response.get('summary', ''),
                period_start=start_date,
                period_end=end_date,
                alerts=alerts,
                opportunities=opportunities,
                predictions=ai_response.get('predictions', {}),
                recommendations=ai_response.get('top_recommendations', []),
                tokens_used=ai_response.get('tokens_used', 0),
                model_version=ai_response.get('model_version', 'gpt-4o-mini'),
                analysis_data=analysis_data,
                has_error=False
            )

        return insight

    def _save_error_insight(self, error_message: str) -> AIInsight:
        """Save an error insight when generation fails."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)

        with transaction.atomic():
            insight = AIInsight.objects.create(
                user=self.user,
                health_score=Decimal('0'),
                health_status='regular',
                summary='Erro ao gerar análise',
                period_start=start_date,
                period_end=end_date,
                alerts=[],
                opportunities=[],
                predictions={},
                recommendations=[],
                analysis_data={},
                has_error=True,
                error_message=error_message
            )

        return insight

    def _update_config(self):
        """Update AI insight config after successful generation."""
        config, _ = AIInsightConfig.objects.get_or_create(user=self.user)
        config.last_generated_at = timezone.now()
        config.next_scheduled_at = timezone.now() + timedelta(days=7)
        config.save()

    @staticmethod
    def can_generate_for_user(user) -> tuple[bool, str]:
        """
        Check if insights can be generated for a user.

        Returns:
            Tuple of (can_generate: bool, reason: str)
        """
        # Check company
        if not hasattr(user, 'company') or user.company is None:
            return False, 'Usuário não possui empresa cadastrada'

        company = user.company

        # Check company_type and business_sector
        if not company.company_type or not company.business_sector:
            return False, 'Empresa precisa ter tipo e setor cadastrados. Configure em Configurações.'

        # Check if enabled
        try:
            config = AIInsightConfig.objects.get(user=user)
            if not config.is_enabled:
                return False, 'Insights com IA não estão habilitados'
        except AIInsightConfig.DoesNotExist:
            return False, 'Insights com IA não estão configurados'

        return True, 'OK'
