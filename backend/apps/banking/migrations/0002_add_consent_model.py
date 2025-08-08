# Generated migration for Consent model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pluggy_consent_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('status', models.CharField(choices=[('ACTIVE', 'Ativo'), ('EXPIRED', 'Expirado'), ('REVOKED', 'Revogado')], default='ACTIVE', max_length=20)),
                ('authorized_products', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('open_finance_data', models.JSONField(blank=True, default=dict)),
                ('connection', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='consent', to='banking.pluggyitem')),
            ],
            options={
                'verbose_name': 'Consentimento',
                'verbose_name_plural': 'Consentimentos',
                'db_table': 'banking_consents',
                'ordering': ['-created_at'],
            },
        ),
    ]