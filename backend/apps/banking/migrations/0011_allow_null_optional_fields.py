# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0010_allow_null_marketing_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='tax_number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='tax number'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='owner',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='balance_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='balance date'),
        ),
    ]