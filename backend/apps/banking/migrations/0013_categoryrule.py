# Generated migration for CategoryRule model

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('banking', '0012_add_ocr_fields_to_bill'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pattern', models.CharField(max_length=200)),
                ('match_type', models.CharField(
                    choices=[('prefix', 'Prefixo'), ('contains', 'Contém'), ('fuzzy', 'Similaridade')],
                    default='prefix',
                    max_length=20
                )),
                ('is_active', models.BooleanField(default=True)),
                ('applied_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rules',
                    to='banking.category'
                )),
                ('created_from_transaction', models.ForeignKey(
                    blank=True,
                    help_text='Transação que originou a criação desta regra',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_rules',
                    to='banking.transaction'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='category_rules',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Category Rule',
                'verbose_name_plural': 'Category Rules',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'pattern', 'match_type')},
            },
        ),
        migrations.AddIndex(
            model_name='categoryrule',
            index=models.Index(fields=['user', 'is_active'], name='banking_cat_user_id_6a5b2e_idx'),
        ),
    ]
