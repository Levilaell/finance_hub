# Generated migration for adding encrypted fields to AI Insights models

from django.db import migrations
from apps.ai_insights.models_encrypted import EncryptedJSONField


class Migration(migrations.Migration):

    dependencies = [
        ('ai_insights', '0002_auto_20240101_0000'),
    ]

    operations = [
        # Update AIConversation.financial_context to use EncryptedJSONField
        migrations.AlterField(
            model_name='aiconversation',
            name='financial_context',
            field=EncryptedJSONField(
                default=dict,
                help_text='Encrypted snapshot of financial data',
                verbose_name='contexto financeiro',
                auto_detect=True
            ),
        ),
        
        # Update AIMessage.structured_data to use EncryptedJSONField
        migrations.AlterField(
            model_name='aimessage',
            name='structured_data',
            field=EncryptedJSONField(
                null=True,
                blank=True,
                help_text='Encrypted structured data for charts, tables, etc',
                verbose_name='dados estruturados',
                auto_detect=True
            ),
        ),
        
        # Update AIInsight.data_context to use EncryptedJSONField if it exists
        migrations.AlterField(
            model_name='aiinsight',
            name='data_context',
            field=EncryptedJSONField(
                null=True,
                blank=True,
                help_text='Encrypted context data',
                verbose_name='contexto de dados',
                auto_detect=True
            ),
        ),
    ]