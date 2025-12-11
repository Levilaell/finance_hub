# Generated migration for adding OCR fields to Bill model

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0011_change_linked_transaction_to_onetoone'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='source_file',
            field=models.FileField(
                blank=True,
                help_text='Original boleto file (PDF or image)',
                null=True,
                upload_to='bills/uploads/%Y/%m/',
                validators=[django.core.validators.FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])],
            ),
        ),
        migrations.AddField(
            model_name='bill',
            name='barcode',
            field=models.CharField(
                blank=True,
                help_text='Linha digitável do boleto (47-48 dígitos)',
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name='bill',
            name='ocr_confidence',
            field=models.FloatField(
                blank=True,
                help_text='OCR confidence score (0-100)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='bill',
            name='ocr_raw_data',
            field=models.JSONField(
                blank=True,
                help_text='Raw OCR extraction data',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='bill',
            name='created_from_ocr',
            field=models.BooleanField(
                default=False,
                help_text='Whether this bill was created from OCR upload',
            ),
        ),
    ]
