# Generated migration for adding performance indexes to Transaction model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0008_delete_consent'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account', 'date'], name='banking_tra_acc_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['type', 'date'], name='banking_tra_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['category', 'date'], name='banking_tra_cat_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account', 'type', '-date'], name='banking_tra_complex_idx'),
        ),
    ]