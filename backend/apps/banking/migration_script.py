"""
Migration script to transition from old models to new Pluggy structure
Run this after applying the new model migrations
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def migrate_bank_providers_to_connectors():
    """Migrate BankProvider to PluggyConnector"""
    from apps.banking.models import BankProvider
    from apps.banking.models_new import PluggyConnector
    
    logger.info("Migrating bank providers to connectors...")
    
    for provider in BankProvider.objects.all():
        # Try to find matching connector ID
        # This is a placeholder - you'll need to map actual Pluggy IDs
        pluggy_id = int(provider.code) if provider.code.isdigit() else hash(provider.code) % 10000
        
        connector, created = PluggyConnector.objects.update_or_create(
            pluggy_id=pluggy_id,
            defaults={
                'name': provider.name,
                'image_url': provider.logo_url,
                'primary_color': provider.primary_color or provider.color,
                'type': 'PERSONAL_BANK',  # Default, will need to be updated
                'country': 'BR',
                'is_open_finance': provider.is_open_finance,
                'products': ['ACCOUNTS', 'TRANSACTIONS'],  # Default
            }
        )
        
        if created:
            logger.info(f"Created connector for {provider.name}")
        else:
            logger.info(f"Updated connector for {provider.name}")


def migrate_bank_accounts():
    """Migrate BankAccount to new structure with PluggyItem"""
    from apps.banking.models import BankAccount as OldBankAccount
    from apps.banking.models_new import PluggyItem, BankAccount, PluggyConnector
    
    logger.info("Migrating bank accounts...")
    
    for old_account in OldBankAccount.objects.all():
        try:
            # Find or create connector
            if old_account.bank_provider.code.isdigit():
                pluggy_connector_id = int(old_account.bank_provider.code)
            else:
                pluggy_connector_id = hash(old_account.bank_provider.code) % 10000
            
            connector = PluggyConnector.objects.get(pluggy_id=pluggy_connector_id)
            
            # Create PluggyItem if account has pluggy_item_id
            item = None
            if old_account.pluggy_item_id:
                item, _ = PluggyItem.objects.update_or_create(
                    pluggy_id=old_account.pluggy_item_id,
                    defaults={
                        'company': old_account.company,
                        'connector': connector,
                        'status': 'UPDATED' if old_account.status == 'active' else 'ERROR',
                        'created_at': old_account.created_at,
                        'updated_at': old_account.updated_at,
                        'last_successful_update': old_account.last_sync_at,
                    }
                )
            
            # Create new BankAccount
            if item and old_account.external_id:
                account_type_map = {
                    'checking': 'BANK',
                    'savings': 'BANK',
                    'credit_card': 'CREDIT',
                    'investment': 'INVESTMENT',
                    'business': 'BANK',
                    'digital': 'BANK',
                }
                
                subtype_map = {
                    'checking': 'CHECKING_ACCOUNT',
                    'savings': 'SAVINGS_ACCOUNT',
                    'credit_card': 'CREDIT_CARD',
                }
                
                BankAccount.objects.update_or_create(
                    pluggy_id=old_account.external_id,
                    defaults={
                        'item': item,
                        'company': old_account.company,
                        'type': account_type_map.get(old_account.account_type, 'OTHER'),
                        'subtype': subtype_map.get(old_account.account_type, 'OTHER'),
                        'number': old_account.account_number,
                        'name': old_account.name or old_account.nickname or '',
                        'owner': old_account.metadata.get('owner', '') if old_account.metadata else '',
                        'balance': old_account.current_balance,
                        'balance_date': old_account.last_sync_at or timezone.now(),
                        'currency_code': old_account.currency,
                        'is_active': old_account.is_active,
                        'created_at': old_account.created_at,
                        'updated_at': old_account.updated_at,
                    }
                )
                logger.info(f"Migrated account {old_account.display_name}")
            
        except Exception as e:
            logger.error(f"Error migrating account {old_account.id}: {e}")


def migrate_categories():
    """Migrate TransactionCategory to new structure"""
    from apps.banking.models import TransactionCategory as OldCategory
    from apps.banking.models_new import TransactionCategory
    
    logger.info("Migrating transaction categories...")
    
    # First migrate parent categories
    for old_cat in OldCategory.objects.filter(parent__isnull=True):
        category, created = TransactionCategory.objects.update_or_create(
            slug=old_cat.slug,
            defaults={
                'name': old_cat.name,
                'type': old_cat.category_type if old_cat.category_type != 'transfer' else 'both',
                'icon': old_cat.icon,
                'color': old_cat.color,
                'is_system': old_cat.is_system,
                'is_active': old_cat.is_active,
                'order': old_cat.order,
            }
        )
        
        if created:
            logger.info(f"Created category {old_cat.name}")
    
    # Then migrate child categories
    for old_cat in OldCategory.objects.filter(parent__isnull=False):
        try:
            parent = TransactionCategory.objects.get(slug=old_cat.parent.slug)
            
            category, created = TransactionCategory.objects.update_or_create(
                slug=old_cat.slug,
                parent=parent,
                defaults={
                    'name': old_cat.name,
                    'type': old_cat.category_type if old_cat.category_type != 'transfer' else 'both',
                    'icon': old_cat.icon,
                    'color': old_cat.color,
                    'is_system': old_cat.is_system,
                    'is_active': old_cat.is_active,
                    'order': old_cat.order,
                    'parent': parent,
                }
            )
            
            if created:
                logger.info(f"Created subcategory {old_cat.name}")
                
        except Exception as e:
            logger.error(f"Error migrating category {old_cat.id}: {e}")


def migrate_transactions():
    """Migrate Transaction to new structure"""
    from apps.banking.models import Transaction as OldTransaction
    from apps.banking.models_new import Transaction, BankAccount, TransactionCategory
    
    logger.info("Migrating transactions...")
    
    # Process in batches
    batch_size = 1000
    total = OldTransaction.objects.count()
    
    for offset in range(0, total, batch_size):
        batch = OldTransaction.objects.all()[offset:offset + batch_size]
        
        for old_trans in batch:
            try:
                # Find new account
                if not old_trans.external_id or not old_trans.bank_account.external_id:
                    continue
                
                try:
                    new_account = BankAccount.objects.get(
                        pluggy_id=old_trans.bank_account.external_id
                    )
                except BankAccount.DoesNotExist:
                    logger.warning(f"Account not found for transaction {old_trans.id}")
                    continue
                
                # Map transaction type
                type_map = {
                    'credit': 'CREDIT',
                    'debit': 'DEBIT',
                    'transfer_in': 'CREDIT',
                    'transfer_out': 'DEBIT',
                    'pix_in': 'CREDIT',
                    'pix_out': 'DEBIT',
                    'fee': 'DEBIT',
                    'interest': 'CREDIT',
                    'adjustment': 'CREDIT' if old_trans.amount > 0 else 'DEBIT',
                }
                
                trans_type = type_map.get(old_trans.transaction_type, 'DEBIT')
                
                # Find category
                new_category = None
                if old_trans.category:
                    try:
                        new_category = TransactionCategory.objects.get(
                            slug=old_trans.category.slug
                        )
                    except TransactionCategory.DoesNotExist:
                        pass
                
                # Extract merchant from metadata
                merchant = {}
                if old_trans.counterpart_name:
                    merchant['name'] = old_trans.counterpart_name
                if old_trans.counterpart_document:
                    merchant['cnpj'] = old_trans.counterpart_document
                
                # Create transaction
                Transaction.objects.update_or_create(
                    pluggy_id=old_trans.external_id,
                    defaults={
                        'account': new_account,
                        'type': trans_type,
                        'status': 'POSTED' if old_trans.status == 'completed' else 'PENDING',
                        'description': old_trans.description[:500],
                        'amount': abs(old_trans.amount),
                        'currency_code': 'BRL',
                        'date': old_trans.transaction_date,
                        'merchant': merchant,
                        'category': new_category,
                        'notes': old_trans.notes,
                        'tags': old_trans.tags,
                        'metadata': old_trans.metadata,
                        'created_at': old_trans.created_at,
                        'updated_at': old_trans.updated_at,
                    }
                )
                
            except Exception as e:
                logger.error(f"Error migrating transaction {old_trans.id}: {e}")
        
        logger.info(f"Processed {min(offset + batch_size, total)}/{total} transactions")


def run_migration():
    """Run all migrations"""
    with transaction.atomic():
        migrate_bank_providers_to_connectors()
        migrate_categories()
        migrate_bank_accounts()
        migrate_transactions()
        
    logger.info("Migration completed!")


if __name__ == '__main__':
    run_migration()