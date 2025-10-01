# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def copy_category_data(apps, schema_editor):
    """Copy data from category/category_id to pluggy_category/pluggy_category_id."""
    Transaction = apps.get_model('banking', 'Transaction')
    for transaction in Transaction.objects.all():
        transaction.pluggy_category = transaction.category
        transaction.pluggy_category_id = transaction.category_id
        transaction.save(update_fields=['pluggy_category', 'pluggy_category_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0005_category'),
    ]

    operations = [
        # Step 1: Add new fields
        migrations.AddField(
            model_name='transaction',
            name='pluggy_category',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='transaction',
            name='pluggy_category_id',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user_category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transactions',
                to='banking.category'
            ),
        ),

        # Step 2: Copy data from old fields to new fields
        migrations.RunPython(copy_category_data, reverse_code=migrations.RunPython.noop),

        # Step 3: Remove old index
        migrations.RemoveIndex(
            model_name='transaction',
            name='banking_tra_categor_f47655_idx',
        ),

        # Step 4: Remove old fields
        migrations.RemoveField(
            model_name='transaction',
            name='category',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='category_id',
        ),

        # Step 5: Add new indexes
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['pluggy_category', 'date'], name='banking_tra_pluggy__c44c0e_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user_category', 'date'], name='banking_tra_user_ca_a7b9c3_idx'),
        ),
    ]
