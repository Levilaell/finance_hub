# Generated manually - Add subcategory support to CategoryRule

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0016_add_custom_name_to_bankaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoryrule',
            name='subcategory',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subcategory_rules',
                to='banking.category',
                help_text='Subcategoria a aplicar (opcional, deve pertencer à categoria)'
            ),
        ),
        migrations.AddIndex(
            model_name='categoryrule',
            index=models.Index(
                fields=['user', 'is_active', 'category', 'subcategory'],
                name='banking_cat_user_active_cat_sub_idx'
            ),
        ),
    ]
