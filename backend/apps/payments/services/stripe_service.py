"""
Stripe payment service stub
"""
from typing import Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class StripeService:
    """Stub for Stripe payment processing"""
    
    @classmethod
    def process_credit_purchase(
        cls,
        company: 'Company',
        payment_method: 'PaymentMethod',
        amount: Decimal,
        description: str
    ) -> Dict[str, Any]:
        """
        Process credit purchase via Stripe
        
        TODO: Implement actual Stripe integration
        """
        logger.info(
            f"Processing Stripe payment of R$ {amount} for {company.name}"
        )
        
        # For now, return success
        return {
            'success': True,
            'payment_id': f'stripe_test_{company.id}_{amount}',
            'gateway': 'stripe',
            'status': 'succeeded',
            'error': None
        }