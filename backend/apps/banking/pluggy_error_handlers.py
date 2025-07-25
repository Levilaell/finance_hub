"""
Pluggy Error Handlers
Tratamento específico para cada tipo de erro da API Pluggy
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class PluggyErrorHandler:
    """
    Centraliza o tratamento de erros específicos da API Pluggy
    """
    
    # Mapeamento de códigos de erro para handlers
    ERROR_HANDLERS = {
        # Erros de autenticação
        'INVALID_CREDENTIALS': 'handle_invalid_credentials',
        'USER_INPUT_TIMEOUT': 'handle_user_input_timeout',
        'LOGIN_ERROR': 'handle_login_error',
        
        # Erros de autorização Open Finance
        'USER_AUTHORIZATION_NOT_GRANTED': 'handle_authorization_not_granted',
        'USER_AUTHORIZATION_REVOKED': 'handle_authorization_revoked',
        'CONSENT_EXPIRED': 'handle_consent_expired',
        
        # Erros de limite de taxa
        'RATE_LIMIT_EXCEEDED': 'handle_rate_limit',
        'TOO_MANY_REQUESTS': 'handle_rate_limit',
        '423': 'handle_rate_limit',  # HTTP 423 Locked
        
        # Erros de conectividade
        'CONNECTION_ERROR': 'handle_connection_error',
        'TIMEOUT': 'handle_timeout',
        'SERVICE_UNAVAILABLE': 'handle_service_unavailable',
        
        # Erros de dados
        'INVALID_PARAMETERS': 'handle_invalid_parameters',
        'PRODUCT_NOT_AVAILABLE': 'handle_product_not_available',
        'PARTIAL_SUCCESS': 'handle_partial_success',
        
        # Erros gerais
        'INTERNAL_ERROR': 'handle_internal_error',
        'UNKNOWN_ERROR': 'handle_unknown_error',
    }
    
    # Ações de recuperação por tipo de erro
    RECOVERY_ACTIONS = {
        'retry_immediately': ['CONNECTION_ERROR', 'TIMEOUT'],
        'retry_with_backoff': ['RATE_LIMIT_EXCEEDED', 'TOO_MANY_REQUESTS', '423'],
        'require_user_action': ['INVALID_CREDENTIALS', 'USER_AUTHORIZATION_NOT_GRANTED', 
                                'USER_AUTHORIZATION_REVOKED', 'CONSENT_EXPIRED'],
        'log_and_continue': ['PARTIAL_SUCCESS', 'PRODUCT_NOT_AVAILABLE'],
        'alert_support': ['INTERNAL_ERROR', 'UNKNOWN_ERROR']
    }
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def handle_error(self, error_code: str, error_data: Dict[str, Any], 
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa um erro e retorna ação recomendada
        
        Args:
            error_code: Código do erro
            error_data: Dados completos do erro
            context: Contexto adicional (item_id, account_id, etc)
            
        Returns:
            Dict com ação recomendada e dados adicionais
        """
        handler_name = self.ERROR_HANDLERS.get(
            error_code, 
            self.ERROR_HANDLERS.get(str(error_data.get('status_code')), 'handle_unknown_error')
        )
        
        handler = getattr(self, handler_name)
        result = handler(error_code, error_data, context or {})
        
        # Log do erro e ação tomada
        logger.info(f"Error handled - Code: {error_code}, Action: {result.get('action')}")
        
        return result
    
    def handle_invalid_credentials(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Credenciais inválidas - requer ação do usuário"""
        item_id = context.get('item_id')
        user_id = context.get('user_id')
        
        # Notificar usuário
        if user_id:
            self.notification_service.notify_credentials_invalid(user_id, item_id)
        
        return {
            'action': 'require_user_reauthentication',
            'retry': False,
            'message': 'Credenciais inválidas. Por favor, reconecte sua conta.',
            'user_action_required': True,
            'update_status': 'credential_error'
        }
    
    def handle_user_input_timeout(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Timeout esperando input do usuário"""
        return {
            'action': 'notify_user',
            'retry': False,
            'message': 'Tempo esgotado esperando confirmação. Tente novamente.',
            'user_action_required': True,
            'update_status': 'timeout'
        }
    
    def handle_login_error(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Erro genérico de login"""
        return {
            'action': 'require_user_reauthentication',
            'retry': False,
            'message': 'Erro ao fazer login no banco. Verifique suas credenciais.',
            'user_action_required': True,
            'update_status': 'login_error'
        }
    
    def handle_authorization_not_granted(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Usuário não concedeu autorização Open Finance"""
        return {
            'action': 'request_authorization',
            'retry': False,
            'message': 'Você precisa autorizar o acesso aos seus dados bancários.',
            'user_action_required': True,
            'update_status': 'authorization_pending'
        }
    
    def handle_authorization_revoked(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Autorização foi revogada pelo usuário"""
        item_id = context.get('item_id')
        user_id = context.get('user_id')
        
        if user_id:
            self.notification_service.notify_authorization_revoked(user_id, item_id)
        
        return {
            'action': 'request_reauthorization',
            'retry': False,
            'message': 'Sua autorização foi revogada. Reconecte para continuar.',
            'user_action_required': True,
            'update_status': 'authorization_revoked'
        }
    
    def handle_consent_expired(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Consentimento expirou - iniciar renovação automática"""
        item_id = context.get('item_id')
        
        return {
            'action': 'renew_consent',
            'retry': True,
            'retry_method': 'update_item',  # Usar update_item para renovar
            'message': 'Consentimento expirado. Iniciando renovação automática.',
            'user_action_required': False,
            'update_status': 'renewing_consent'
        }
    
    def handle_rate_limit(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Rate limit atingido - implementar backoff"""
        retry_after = error_data.get('retry_after', 3600)  # Default 1 hora
        
        # Para Open Finance, o limite é mensal
        if context.get('is_open_finance'):
            next_month = timezone.now().replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            retry_after = (next_month - timezone.now()).total_seconds()
        
        return {
            'action': 'retry_with_backoff',
            'retry': True,
            'retry_after': retry_after,
            'message': f'Limite de requisições atingido. Tentar novamente em {retry_after/3600:.1f} horas.',
            'user_action_required': False,
            'update_status': 'rate_limited'
        }
    
    def handle_connection_error(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Erro de conexão - tentar novamente"""
        return {
            'action': 'retry_immediately',
            'retry': True,
            'retry_count': context.get('retry_count', 0) + 1,
            'max_retries': 3,
            'message': 'Erro de conexão temporário. Tentando novamente.',
            'user_action_required': False
        }
    
    def handle_timeout(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Timeout na requisição"""
        return {
            'action': 'retry_with_delay',
            'retry': True,
            'retry_delay': 30,  # 30 segundos
            'message': 'Requisição demorou muito. Tentando novamente.',
            'user_action_required': False
        }
    
    def handle_service_unavailable(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Serviço indisponível"""
        return {
            'action': 'retry_with_backoff',
            'retry': True,
            'retry_after': 300,  # 5 minutos
            'message': 'Serviço temporariamente indisponível.',
            'user_action_required': False,
            'update_status': 'service_unavailable'
        }
    
    def handle_invalid_parameters(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Parâmetros inválidos - erro de programação"""
        logger.error(f"Invalid parameters error: {error_data}")
        
        return {
            'action': 'log_error',
            'retry': False,
            'message': 'Erro de configuração. Entre em contato com o suporte.',
            'user_action_required': False,
            'alert_support': True
        }
    
    def handle_product_not_available(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Produto não disponível para esta conta"""
        product = error_data.get('product', 'unknown')
        
        return {
            'action': 'log_and_continue',
            'retry': False,
            'message': f'Produto {product} não disponível para esta conta.',
            'user_action_required': False,
            'continue_with_available': True
        }
    
    def handle_partial_success(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Sucesso parcial - alguns dados foram obtidos"""
        return {
            'action': 'process_available_data',
            'retry': False,
            'message': 'Alguns dados não puderam ser obtidos.',
            'user_action_required': False,
            'process_partial': True,
            'update_status': 'partial_success'
        }
    
    def handle_internal_error(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Erro interno do Pluggy"""
        logger.error(f"Pluggy internal error: {error_data}")
        
        return {
            'action': 'retry_later',
            'retry': True,
            'retry_after': 1800,  # 30 minutos
            'message': 'Erro interno no serviço. Tentaremos novamente mais tarde.',
            'user_action_required': False,
            'alert_support': True
        }
    
    def handle_unknown_error(self, error_code: str, error_data: Dict, context: Dict) -> Dict:
        """Erro desconhecido"""
        logger.warning(f"Unknown error: {error_code} - {error_data}")
        
        return {
            'action': 'log_and_monitor',
            'retry': True,
            'retry_after': 600,  # 10 minutos
            'message': 'Erro inesperado. Tentaremos novamente.',
            'user_action_required': False
        }


class NotificationService:
    """Serviço para notificar usuários sobre problemas com suas conexões"""
    
    def notify_credentials_invalid(self, user_id: int, item_id: str):
        """Notifica usuário sobre credenciais inválidas"""
        # TODO: Implementar notificação via email/push
        logger.info(f"Notifying user {user_id} about invalid credentials for item {item_id}")
    
    def notify_authorization_revoked(self, user_id: int, item_id: str):
        """Notifica usuário sobre autorização revogada"""
        # TODO: Implementar notificação via email/push
        logger.info(f"Notifying user {user_id} about revoked authorization for item {item_id}")
    
    def notify_consent_renewal_needed(self, user_id: int, item_id: str):
        """Notifica usuário sobre necessidade de renovar consentimento"""
        # TODO: Implementar notificação via email/push
        logger.info(f"Notifying user {user_id} about consent renewal for item {item_id}")


# Instância global do handler
error_handler = PluggyErrorHandler()