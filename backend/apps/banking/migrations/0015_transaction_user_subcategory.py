# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0014_billpayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='user_subcategory',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transactions_as_subcategory',
                to='banking.category',
            ),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user_subcategory', 'date'], name='banking_tra_user_su_idx'),
        ),
    ]
