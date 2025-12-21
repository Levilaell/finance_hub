# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcquisitionTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acquisition_angle', models.CharField(
                    choices=[
                        ('time', 'Tempo - Economia de horas'),
                        ('price', 'Preço - Custo-benefício'),
                        ('delay', 'Atraso - Evitar multas'),
                        ('visibility', 'Visibilidade - Controle financeiro'),
                        ('organic', 'Orgânico - Sem campanha'),
                        ('unknown', 'Desconhecido'),
                    ],
                    db_index=True,
                    default='unknown',
                    max_length=50,
                    verbose_name='ângulo de aquisição'
                )),
                ('signup_price_id', models.CharField(
                    blank=True,
                    max_length=100,
                    null=True,
                    verbose_name='price ID do signup'
                )),
                ('subscription_status', models.CharField(
                    choices=[
                        ('trialing', 'Trial'),
                        ('active', 'Ativa'),
                        ('past_due', 'Atrasada'),
                        ('canceled', 'Cancelada'),
                        ('unpaid', 'Não paga'),
                        ('incomplete', 'Incompleta'),
                    ],
                    db_index=True,
                    default='trialing',
                    max_length=20,
                    verbose_name='status da assinatura'
                )),
                ('stripe_subscription_id', models.CharField(
                    blank=True,
                    max_length=100,
                    null=True,
                    verbose_name='Stripe subscription ID'
                )),
                ('trial_started_at', models.DateTimeField(blank=True, null=True, verbose_name='início do trial')),
                ('trial_ended_at', models.DateTimeField(blank=True, null=True, verbose_name='fim do trial')),
                ('converted_at', models.DateTimeField(
                    blank=True,
                    help_text='Quando passou de trial para ativa',
                    null=True,
                    verbose_name='data da conversão'
                )),
                ('canceled_at', models.DateTimeField(blank=True, null=True, verbose_name='data do cancelamento')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='acquisition_tracking',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Rastreamento de Aquisição',
                'verbose_name_plural': 'Rastreamentos de Aquisição',
                'db_table': 'acquisition_tracking',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='acquisitiontracking',
            index=models.Index(fields=['acquisition_angle', 'subscription_status'], name='acquisition_acquisi_c3baf2_idx'),
        ),
        migrations.AddIndex(
            model_name='acquisitiontracking',
            index=models.Index(fields=['subscription_status', '-created_at'], name='acquisition_subscri_e4b5f3_idx'),
        ),
    ]
