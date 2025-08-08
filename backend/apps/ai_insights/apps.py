from django.apps import AppConfig


class AiInsightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_insights'
    verbose_name = 'AI Insights'
    
    def ready(self):
        """Import signals and connect handlers when app is ready"""
        pass
