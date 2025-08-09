# Generated manually to fix merchant field nullable issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0002_add_consent_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='merchant',
            field=models.JSONField(
                default=dict,
                blank=True,
                null=True,  # Allow NULL values
                verbose_name='merchant'
            ),
        ),
    ]