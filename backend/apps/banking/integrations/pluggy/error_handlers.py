"""
Pluggy API error handlers
"""
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class PluggyErrorHandler:
    """
    Centralized error handling for Pluggy API errors
    """
    
    ERROR_HANDLERS = {
        'INVALID_CREDENTIALS': 'handle_invalid_credentials',
        'USER_AUTHORIZATION_REVOKED': 'handle_authorization_revoked',
        'CONSENT_EXPIRED': 'handle_consent_expired',
        'RATE_LIMIT_EXCEEDED': 'handle_rate_limit',
        'ITEM_LOCKED': 'handle_item_locked',
        'ITEM_NOT_FOUND': 'handle_item_not_found',
        'ACCOUNT_NOT_FOUND': 'handle_account_not_found',
        'CONNECTOR_UNAVAILABLE': 'handle_connector_unavailable',
        'MFA_REQUIRED': 'handle_mfa_required',
        'SESSION_EXPIRED': 'handle_session_expired',
        'INVALID_PARAMETER': 'handle_invalid_parameter',
        'INTERNAL_ERROR': 'handle_internal_error',
    }
    
    def handle_error(self, error_code: str, error_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Pluggy API error based on error code
        
        Args:
            error_code: The error code from Pluggy
            error_data: Additional error data
            context: Context about the operation (account, operation type, etc.)
            
        Returns:
            Action to take: retry, renew_consent, notify_user, etc.
        """
        handler_name = self.ERROR_HANDLERS.get(error_code, 'handle_generic_error')
        handler = getattr(self, handler_name, self.handle_generic_error)
        
        logger.warning(f"Handling Pluggy error: {error_code} with handler: {handler_name}")
        return handler(error_data, context)
    
    def handle_invalid_credentials(self, error_data: Dict, context: Dict) -> Dict:
        """Handle invalid credentials error"""
        account = context.get('account')
        if account:
            account.status = 'error'
            account.sync_error_message = 'Credenciais inválidas. Reconecte sua conta.'
            account.save()
            
        return {
            'action': 'notify_user',
            'message': 'As credenciais da conta são inválidas. Por favor, reconecte sua conta.',
            'reconnection_required': True
        }
    
    def handle_authorization_revoked(self, error_data: Dict, context: Dict) -> Dict:
        """Handle authorization revoked error"""
        account = context.get('account')
        if account:
            account.status = 'disconnected'
            account.sync_error_message = 'Autorização revogada pelo usuário'
            account.save()
            
        return {
            'action': 'notify_user',
            'message': 'A autorização foi revogada. Por favor, reconecte sua conta.',
            'reconnection_required': True
        }
    
    def handle_consent_expired(self, error_data: Dict, context: Dict) -> Dict:
        """Handle expired consent (Open Finance)"""
        account = context.get('account')
        if account:
            account.status = 'consent_expired'
            account.sync_error_message = 'Consentimento Open Finance expirado'
            account.save()
            
        return {
            'action': 'renew_consent',
            'message': 'O consentimento Open Finance expirou e precisa ser renovado.',
            'reconnection_required': True
        }
    
    def handle_rate_limit(self, error_data: Dict, context: Dict) -> Dict:
        """Handle rate limit exceeded"""
        retry_after = error_data.get('retry_after', 3600)  # Default 1 hour
        
        account = context.get('account')
        if account:
            account.sync_status = 'rate_limited'
            account.sync_error_message = f'Limite de requisições atingido. Tente após {retry_after}s'
            account.metadata['rate_limit_retry_after'] = timezone.now() + timedelta(seconds=retry_after)
            account.save()
            
        return {
            'action': 'retry_later',
            'retry_after': retry_after,
            'message': 'Limite de requisições atingido. Tentaremos novamente mais tarde.'
        }
    
    def handle_item_locked(self, error_data: Dict, context: Dict) -> Dict:
        """Handle item locked (being updated)"""
        return {
            'action': 'retry',
            'retry_delay': 30,  # 30 seconds
            'message': 'Item está sendo atualizado. Tentando novamente em breve.'
        }
    
    def handle_item_not_found(self, error_data: Dict, context: Dict) -> Dict:
        """Handle item not found"""
        account = context.get('account')
        if account:
            account.status = 'error'
            account.sync_error_message = 'Item não encontrado na Pluggy'
            account.save()
            
        return {
            'action': 'notify_user',
            'message': 'A conexão não foi encontrada. Por favor, reconecte sua conta.',
            'reconnection_required': True
        }
    
    def handle_account_not_found(self, error_data: Dict, context: Dict) -> Dict:
        """Handle account not found"""
        return {
            'action': 'skip',
            'message': 'Conta bancária não encontrada na instituição.'
        }
    
    def handle_connector_unavailable(self, error_data: Dict, context: Dict) -> Dict:
        """Handle connector temporarily unavailable"""
        return {
            'action': 'retry_later',
            'retry_after': 1800,  # 30 minutes
            'message': 'Instituição temporariamente indisponível.'
        }
    
    def handle_mfa_required(self, error_data: Dict, context: Dict) -> Dict:
        """Handle MFA required"""
        account = context.get('account')
        if account:
            account.status = 'mfa_required'
            account.sync_error_message = 'Autenticação adicional necessária'
            account.save()
            
        return {
            'action': 'notify_user',
            'message': 'Autenticação adicional necessária. Por favor, reconecte sua conta.',
            'reconnection_required': True
        }
    
    def handle_session_expired(self, error_data: Dict, context: Dict) -> Dict:
        """Handle session expired"""
        return {
            'action': 'renew_session',
            'message': 'Sessão expirada. Renovando automaticamente.'
        }
    
    def handle_invalid_parameter(self, error_data: Dict, context: Dict) -> Dict:
        """Handle invalid parameter error"""
        logger.error(f"Invalid parameter error: {error_data}")
        return {
            'action': 'log_error',
            'message': 'Erro de parâmetro inválido. Contate o suporte.'
        }
    
    def handle_internal_error(self, error_data: Dict, context: Dict) -> Dict:
        """Handle internal Pluggy error"""
        return {
            'action': 'retry_later',
            'retry_after': 300,  # 5 minutes
            'message': 'Erro interno na Pluggy. Tentaremos novamente em breve.'
        }
    
    def handle_generic_error(self, error_data: Dict, context: Dict) -> Dict:
        """Handle unknown errors"""
        logger.error(f"Unknown Pluggy error: {error_data}")
        return {
            'action': 'log_error',
            'message': 'Erro desconhecido. Por favor, tente novamente mais tarde.'
        }


# Global instance
error_handler = PluggyErrorHandler()