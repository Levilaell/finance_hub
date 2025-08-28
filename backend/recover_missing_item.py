#!/usr/bin/env python
"""
Script para recuperar item Pluggy perdido: f1f40504-32c4-44c2-9181-5d38cc2cfc8d

Este script executa manualmente a lógica que deveria ter sido executada pelo webhook
item/created mas que não funcionou devido ao bug na função _handle_item_created.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/levilaell/Desktop/finance_hub/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.banking.models import PluggyItem, BankAccount, PluggyConnector
from apps.banking.integrations.pluggy.client import PluggyClient
from apps.companies.models import Company
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recover_missing_item():
    """Recover the missing Pluggy item from the logs"""
    
    # Item ID from the logs
    item_id = 'f1f40504-32c4-44c2-9181-5d38cc2cfc8d'
    
    logger.info(f"Starting recovery for item: {item_id}")
    
    # Check if item already exists
    existing_item = PluggyItem.objects.filter(pluggy_item_id=item_id).first()
    if existing_item:
        logger.info(f"Item {item_id} already exists in database")
        logger.info(f"Company: {existing_item.company.name}")
        logger.info(f"Status: {existing_item.status}")
        
        # Check accounts
        accounts = BankAccount.objects.filter(item=existing_item)
        logger.info(f"Found {accounts.count()} accounts for this item")
        for account in accounts:
            logger.info(f"  - Account: {account.name} ({account.type})")
        
        return existing_item
    
    logger.info(f"Item {item_id} not found in database, attempting to recover...")
    
    try:
        with PluggyClient() as client:
            # Get item details from Pluggy API
            item_data = client.get_item(item_id)
            logger.info(f"Retrieved item data from Pluggy API")
            logger.info(f"Connector: {item_data.get('connector', {}).get('name')}")
            logger.info(f"Status: {item_data.get('status')}")
            logger.info(f"Client User ID: {item_data.get('clientUserId')}")
            
            # Try to determine company from client_user_id
            client_user_id = item_data.get('clientUserId')
            company = None
            
            if client_user_id:
                try:
                    user = User.objects.get(id=int(client_user_id))
                    if hasattr(user, 'company') and user.company:
                        company = user.company
                        logger.info(f"Found company {company.name} for user {user.email}")
                except (User.DoesNotExist, ValueError, AttributeError) as e:
                    logger.warning(f"Could not find user/company for clientUserId {client_user_id}: {e}")
            
            if not company:
                # List companies and let user choose
                companies = Company.objects.filter(
                    is_active=True
                ).order_by('-created_at')
                
                logger.info("Available companies:")
                for i, comp in enumerate(companies, 1):
                    items_count = PluggyItem.objects.filter(company=comp).count()
                    logger.info(f"  {i}. {comp.name} ({comp.owner.email if comp.owner else 'No owner'}) - {items_count} items")
                
                if companies.exists():
                    # Use the most recent company by default
                    company = companies.first()
                    logger.info(f"Using most recent company: {company.name}")
                else:
                    logger.error("No companies found with Pluggy configuration")
                    return None
            
            # Get or create connector
            connector_id = item_data['connector']['id']
            connector, connector_created = PluggyConnector.objects.get_or_create(
                pluggy_id=connector_id,
                defaults={
                    'name': item_data['connector'].get('name', f'Connector {connector_id}'),
                    'country': 'BR',
                    'type': 'UNKNOWN'
                }
            )
            
            if connector_created:
                logger.info(f"Created new connector: {connector.name}")
            else:
                logger.info(f"Using existing connector: {connector.name}")
            
            # Create the PluggyItem
            item = PluggyItem.objects.create(
                pluggy_item_id=item_id,
                company=company,
                connector=connector,
                client_user_id=client_user_id or str(company.owner.id if company.owner else ''),
                status=item_data['status'],
                execution_status=item_data.get('executionStatus', ''),
                pluggy_created_at=item_data['createdAt'],
                pluggy_updated_at=item_data['updatedAt'],
                status_detail=item_data.get('statusDetail', {}),
                error_code=item_data.get('error', {}).get('code', '') if item_data.get('error') else '',
                error_message=item_data.get('error', {}).get('message', '') if item_data.get('error') else ''
            )
            
            logger.info(f"✅ Created PluggyItem {item.id} for company {company.name}")
            
            # Try to create accounts if item status allows
            if item.status in ['UPDATED', 'OUTDATED']:
                try:
                    accounts_data = client.get_accounts(item_id)
                    created_accounts = []
                    
                    logger.info(f"Found {len(accounts_data)} accounts in Pluggy API")
                    
                    for account_data in accounts_data:
                        account, account_created = BankAccount.objects.update_or_create(
                            pluggy_account_id=account_data['id'],
                            defaults={
                                'item': item,
                                'company': company,
                                'type': account_data['type'],
                                'subtype': account_data.get('subtype', ''),
                                'number': account_data.get('number', ''),
                                'name': account_data.get('name', ''),
                                'marketing_name': account_data.get('marketingName', ''),
                                'owner': account_data.get('owner', ''),
                                'tax_number': account_data.get('taxNumber', ''),
                                'balance': Decimal(str(account_data.get('balance', 0))),
                                'currency_code': account_data.get('currencyCode', 'BRL'),
                                'bank_data': account_data.get('bankData', {}),
                                'credit_data': account_data.get('creditData', {}),
                                'pluggy_created_at': account_data.get('createdAt'),
                                'pluggy_updated_at': account_data.get('updatedAt')
                            }
                        )
                        
                        if account_created:
                            created_accounts.append(account)
                            logger.info(f"✅ Created account: {account.name} ({account.type}) - Balance: {account.balance}")
                        else:
                            logger.info(f"✅ Updated account: {account.name} ({account.type}) - Balance: {account.balance}")
                    
                    logger.info(f"✅ Processed {len(accounts_data)} accounts ({len(created_accounts)} new)")
                    
                    # Try to sync
                    from apps.banking.tasks import sync_bank_account
                    try:
                        task = sync_bank_account.delay(str(item.id))
                        logger.info(f"✅ Queued sync task: {task.id}")
                    except Exception as celery_error:
                        logger.warning(f"⚠️ Could not queue sync task (Celery may not be running): {celery_error}")
                        logger.info("You can manually sync later via the UI")
                    
                except Exception as e:
                    logger.error(f"Failed to create accounts for item {item_id}: {e}")
            
            else:
                logger.warning(f"Item status is {item.status}, cannot create accounts yet")
                logger.info("You may need to update the connection via Pluggy Connect")
            
            return item
            
    except Exception as e:
        logger.error(f"Failed to recover item {item_id}: {e}", exc_info=True)
        return None

def check_current_state():
    """Check current state of Pluggy items and accounts"""
    
    logger.info("=== CURRENT STATE CHECK ===")
    
    # Check PluggyItems
    items = PluggyItem.objects.all().order_by('-created_at')
    logger.info(f"Total PluggyItems in database: {items.count()}")
    
    for item in items:
        accounts_count = BankAccount.objects.filter(item=item).count()
        logger.info(f"  - {item.pluggy_item_id} ({item.connector.name}) - {accounts_count} accounts - {item.status}")
    
    # Check BankAccounts
    accounts = BankAccount.objects.all().order_by('-created_at')
    logger.info(f"Total BankAccounts in database: {accounts.count()}")
    
    for account in accounts[:5]:  # Show only first 5
        logger.info(f"  - {account.name} ({account.type}) - {account.balance} {account.currency_code}")
    
    if accounts.count() > 5:
        logger.info(f"  ... and {accounts.count() - 5} more accounts")

if __name__ == '__main__':
    logger.info("🔍 Pluggy Item Recovery Script")
    logger.info("=" * 50)
    
    # Check current state first
    check_current_state()
    
    logger.info("\n" + "=" * 50)
    logger.info("🚀 Starting recovery process...")
    
    # Attempt recovery
    recovered_item = recover_missing_item()
    
    if recovered_item:
        logger.info("\n" + "=" * 50)
        logger.info("✅ Recovery completed successfully!")
        logger.info(f"Item ID: {recovered_item.pluggy_item_id}")
        logger.info(f"Company: {recovered_item.company.name}")
        logger.info(f"Status: {recovered_item.status}")
        
        # Check accounts created
        accounts = BankAccount.objects.filter(item=recovered_item)
        logger.info(f"Accounts created: {accounts.count()}")
        
        logger.info("\n🎯 Next steps:")
        logger.info("1. Check /accounts in the frontend - accounts should now appear")
        logger.info("2. Try manual sync if needed")
        logger.info("3. Check transactions after sync completes")
        
    else:
        logger.error("\n❌ Recovery failed!")
        logger.info("Check the logs above for error details")
    
    logger.info("\n" + "=" * 50)
    logger.info("Script completed")