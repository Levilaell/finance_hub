# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0009_pluggy_integration_complete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='marketing_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='marketing name'),
        ),
    ]