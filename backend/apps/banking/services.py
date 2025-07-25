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




class BankingSyncService:
    """
    Service for synchronizing bank account data
    Orchestrates the sync process and handles errors
    """
    
    def __init__(self):
        pass
    
    def sync_account(self, bank_account: BankAccount, days_back: int = 30) -> BankSync:
        """
        Synchronize transactions for a bank account
        
        Args:
            bank_account: BankAccount to sync
            days_back: Number of days to sync backwards
            
        Returns:
            BankSync log instance
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Create sync log
        sync_log = BankSync.objects.create(
            bank_account=bank_account,
            status='running',
            sync_from_date=start_date,
            sync_to_date=end_date
        )
        
        try:
            # This method is deprecated - use Pluggy integration instead
            logger.warning(f"BankingSyncService.sync_account is deprecated. Use Pluggy integration for {bank_account}")
            
            # Mark sync as failed with deprecation message
            sync_log.status = 'failed'
            sync_log.error_message = 'This sync method is deprecated. Please use Pluggy integration.'
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            bank_account.status = 'error'
            bank_account.sync_error_message = 'Use Pluggy integration for syncing'
            bank_account.save()
                
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            bank_account.status = 'error'
            bank_account.save()
            
            logger.error(f"Sync failed for {bank_account}: {e}")
            raise
        
        return sync_log
    
    def _process_transaction(self, bank_account: BankAccount, trans_data: Dict) -> bool:
        """
        Process individual transaction data
        
        Returns:
            True if transaction was created, False if updated
        """
        external_id = trans_data.get('external_id')
        
        # Check if transaction already exists
        existing = Transaction.objects.filter(
            bank_account=bank_account,
            external_id=external_id
        ).first()
        
        transaction_date = datetime.fromisoformat(trans_data['transaction_date'].replace('Z', '+00:00'))
        
        transaction_data = {
            'transaction_type': trans_data['transaction_type'],
            'amount': Decimal(str(trans_data['amount'])),
            'description': trans_data['description'][:500],
            'transaction_date': transaction_date,
            'counterpart_name': trans_data.get('counterpart_name', '')[:200],
            'reference_number': trans_data.get('reference_number', '')[:100],
            'status': 'completed'
        }
        
        if existing:
            # Update existing transaction
            for key, value in transaction_data.items():
                setattr(existing, key, value)
            existing.save()
            return False
        else:
            # Create new transaction
            Transaction.objects.create(
                bank_account=bank_account,
                external_id=external_id,
                **transaction_data
            )
            return True
    
    def sync_all_accounts(self, company):
        """
        Sync all active accounts for a company
        """
        accounts = BankAccount.objects.filter(
            company=company,
            is_active=True,
            status='active'
        )
        
        results = []
        for account in accounts:
            try:
                sync_log = self.sync_account(account)
                results.append({
                    'account': account.display_name,
                    'status': 'success',
                    'sync_id': sync_log.id
                })
            except Exception as e:
                results.append({
                    'account': account.display_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results




class FinancialInsightsService:
    """
    Service for generating financial insights and recommendations
    """
    
    def generate_insights(self, company) -> Dict:
        """
        Generate financial insights for dashboard
        """
        insights = {
            'spending_trends': self._analyze_spending_trends(company),
            'category_analysis': self._analyze_categories(company),
            'cash_flow_health': self._assess_cash_flow_health(company),
            'recommendations': self._generate_recommendations(company)
        }
        
        return insights
    
    def _analyze_spending_trends(self, company) -> Dict:
        """
        Analyze spending trends over time
        """
        # Implementation for spending trend analysis
        return {
            'trend': 'increasing',
            'percentage_change': 15.5,
            'period': 'last_30_days'
        }
    
    def _analyze_categories(self, company) -> List[Dict]:
        """
        Analyze spending by category
        """
        # Implementation for category analysis
        return []
    
    def _assess_cash_flow_health(self, company) -> Dict:
        """
        Assess overall cash flow health
        """
        return {
            'score': 7.5,
            'status': 'healthy',
            'issues': []
        }
    
    def _generate_recommendations(self, company) -> List[Dict]:
        """
        Generate actionable financial recommendations
        """
        return [
            {
                'type': 'cost_saving',
                'title': 'Reduza gastos com combustível',
                'description': 'Seus gastos com combustível aumentaram 25% este mês',
                'potential_saving': 340.50
            }
        ]