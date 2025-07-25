"""
Banking app services
Business logic for financial operations and integrations
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.utils import timezone

from .models import (BankAccount, BankProvider, BankSync,
                     Transaction, TransactionCategory)

logger = logging.getLogger(__name__)




# REMOVED DEPRECATED SERVICES:
# - BankingSyncService: Replaced by Pluggy integration (apps.banking.integrations.pluggy.sync_service)
# - FinancialInsightsService: Not used anywhere in the codebase
#
# All banking synchronization is now handled through Pluggy integration.
# For sync operations, use:
# - PluggyTransactionSyncService for transaction syncing
# - sync_pluggy_account task for async operations
# - POST /api/banking/pluggy/accounts/{id}/sync/ endpoint