"""
MercadoPago payment service stub
"""
from typing import Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class MercadoPagoService:
    """Stub for MercadoPago payment processing"""
    
    @classmethod
    def process_credit_purchase(
        cls,
        company: 'Company',
        payment_method: 'PaymentMethod',
        amount: Decimal,
        description: str
    ) -> Dict[str, Any]:
        """
        Process credit purchase via MercadoPago
        
        TODO: Implement actual MercadoPago integration
        """
        logger.info(
            f"Processing MercadoPago payment of R$ {amount} for {company.name}"
        )
        
        # For now, return success
        return {
            'success': True,
            'payment_id': f'mp_test_{company.id}_{amount}',
            'gateway': 'mercadopago',
            'status': 'approved',
            'error': None
        }