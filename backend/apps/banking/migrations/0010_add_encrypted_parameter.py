# Generated migration for adding encrypted MFA parameter field

from django.db import migrations, models


def migrate_parameters_to_encrypted(apps, schema_editor):
    """
    Migrate existing unencrypted parameters to encrypted format
    """
    PluggyItem = apps.get_model('banking', 'PluggyItem')
    
    # Import encryption service within the migration to avoid import issues
    from apps.banking.utils.encryption import banking_encryption
    
    for item in PluggyItem.objects.filter(parameter__isnull=False).exclude(parameter={}):
        try:
            # Encrypt the existing parameter
            if item.parameter:
                encrypted = banking_encryption.encrypt_mfa_parameter(item.parameter)
                item.encrypted_parameter = encrypted
                item.save(update_fields=['encrypted_parameter'])
                print(f"Migrated parameter for item {item.pluggy_item_id}")
        except Exception as e:
            print(f"Failed to migrate parameter for item {item.pluggy_item_id}: {e}")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - decrypt parameters back to unencrypted format
    """
    PluggyItem = apps.get_model('banking', 'PluggyItem')
    
    from apps.banking.utils.encryption import banking_encryption
    
    for item in PluggyItem.objects.filter(encrypted_parameter__isnull=False).exclude(encrypted_parameter=''):
        try:
            # Decrypt the parameter
            if item.encrypted_parameter:
                decrypted = banking_encryption.decrypt_mfa_parameter(item.encrypted_parameter)
                item.parameter = decrypted
                item.save(update_fields=['parameter'])
                print(f"Reversed migration for item {item.pluggy_item_id}")
        except Exception as e:
            print(f"Failed to reverse migration for item {item.pluggy_item_id}: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0009_add_transaction_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='pluggyitem',
            name='encrypted_parameter',
            field=models.TextField(blank=True, default='', verbose_name='encrypted parameter'),
        ),
        migrations.RunPython(
            migrate_parameters_to_encrypted,
            reverse_migration
        ),
    ]