# Manual migration to add missing ai_credits_balance field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0009_merge_20250803_2225'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='ai_credits_balance',
            field=models.IntegerField(default=0, help_text='Current AI credits balance'),
        ),
    ]