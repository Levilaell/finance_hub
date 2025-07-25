"""
Consent Renewal Service
Gerencia renovação automática de consentimentos expirados
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from celery import shared_task
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db import models

from .models import BankAccount
from .pluggy_client import PluggyClient, PluggyError
from .pluggy_error_handlers import error_handler

logger = logging.getLogger(__name__)


class ConsentRenewalService:
    """
    Serviço para renovação automática de consentimentos
    """
    
    def __init__(self):
        self.client = PluggyClient()
    
    async def check_and_renew_consents(self, company_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Verifica e renova consentimentos próximos de expirar ou expirados
        
        Args:
            company_id: ID da empresa (opcional, para filtrar)
            
        Returns:
            Relatório das renovações
        """
        try:
            # Buscar contas que precisam de renovação
            accounts = await self._get_accounts_needing_renewal(company_id)
            
            logger.info(f"Verificando {len(accounts)} contas para renovação de consentimento")
            
            results = {
                'total': len(accounts),
                'renewed': 0,
                'failed': 0,
                'details': []
            }
            
            for account in accounts:
                try:
                    renewal_result = await self.renew_consent(account)
                    if renewal_result['success']:
                        results['renewed'] += 1
                    else:
                        results['failed'] += 1
                    results['details'].append(renewal_result)
                    
                except Exception as e:
                    logger.error(f"Erro ao renovar consentimento da conta {account.id}: {e}")
                    results['failed'] += 1
                    results['details'].append({
                        'account_id': account.id,
                        'success': False,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao verificar consentimentos: {e}")
            raise
    
    async def renew_consent(self, account: BankAccount) -> Dict[str, Any]:
        """
        Renova o consentimento de uma conta específica
        
        Args:
            account: Conta bancária
            
        Returns:
            Resultado da renovação
        """
        try:
            if not account.pluggy_item_id:
                return {
                    'account_id': account.id,
                    'success': False,
                    'error': 'Conta sem item_id do Pluggy'
                }
            
            logger.info(f"Iniciando renovação de consentimento para conta {account.id}")
            
            # Verificar status atual do item
            item = self.client.get_item(account.pluggy_item_id)
            current_status = item.get('status')
            
            # Verificar se precisa renovação
            consent_info = self._extract_consent_info(item)
            
            if not consent_info['needs_renewal']:
                logger.info(f"Conta {account.id} não precisa de renovação")
                return {
                    'account_id': account.id,
                    'success': True,
                    'message': 'Consentimento ainda válido',
                    'expires_at': consent_info.get('expires_at')
                }
            
            # Tentar renovar usando update_item
            logger.info(f"Tentando renovar consentimento do item {account.pluggy_item_id}")
            
            try:
                update_result = self.client.update_item(account.pluggy_item_id)
                new_status = update_result.get('status')
                
                # Verificar se renovação foi bem sucedida
                if new_status in ['ACTIVE', 'UPDATED', 'UPDATING']:
                    # Atualizar informações da conta
                    account.last_sync = timezone.now()
                    account.sync_status = 'active'
                    account.sync_error_message = ''
                    await account.asave()
                    
                    logger.info(f"✅ Consentimento renovado para conta {account.id}")
                    
                    return {
                        'account_id': account.id,
                        'success': True,
                        'message': 'Consentimento renovado com sucesso',
                        'new_status': new_status
                    }
                    
                elif new_status == 'WAITING_USER_ACTION':
                    # Precisa de ação do usuário
                    await self._handle_user_action_required(account, update_result)
                    
                    return {
                        'account_id': account.id,
                        'success': False,
                        'requires_user_action': True,
                        'message': 'Renovação requer ação do usuário'
                    }
                    
                else:
                    # Outro status não esperado
                    return {
                        'account_id': account.id,
                        'success': False,
                        'message': f'Status inesperado: {new_status}',
                        'status': new_status
                    }
                    
            except PluggyError as e:
                # Usar o error handler para decidir ação
                error_action = error_handler.handle_error(
                    e.error_code,
                    e.error_data,
                    {
                        'item_id': account.pluggy_item_id,
                        'account_id': account.id,
                        'user_id': account.company.user_id,
                        'is_open_finance': account.bank_provider.is_open_finance
                    }
                )
                
                # Se é erro de consentimento expirado e podemos renovar
                if error_action.get('action') == 'renew_consent':
                    # Já tentamos renovar, marcar como precisando de ação do usuário
                    await self._handle_user_action_required(account, {'error': str(e)})
                    
                return {
                    'account_id': account.id,
                    'success': False,
                    'error': str(e),
                    'error_action': error_action
                }
                
        except Exception as e:
            logger.error(f"Erro ao renovar consentimento: {e}")
            return {
                'account_id': account.id,
                'success': False,
                'error': str(e)
            }
    
    def _extract_consent_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai informações de consentimento do item
        """
        consent_info = {
            'needs_renewal': False,
            'expires_at': None,
            'is_expired': False
        }
        
        # Verificar status do item
        status = item.get('status')
        if status in ['LOGIN_ERROR', 'OUTDATED', 'WAITING_USER_ACTION']:
            consent_info['needs_renewal'] = True
            return consent_info
        
        # Verificar data de expiração do consentimento
        consent = item.get('consent', {})
        expires_at = consent.get('expiresAt')
        
        if expires_at:
            try:
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                consent_info['expires_at'] = expiry_date
                
                # Verificar se está próximo de expirar (7 dias)
                days_until_expiry = (expiry_date - timezone.now()).days
                
                if days_until_expiry <= 0:
                    consent_info['is_expired'] = True
                    consent_info['needs_renewal'] = True
                elif days_until_expiry <= 7:
                    consent_info['needs_renewal'] = True
                    
            except Exception as e:
                logger.error(f"Erro ao analisar data de expiração: {e}")
        
        # Verificar se há warnings sobre consentimento
        status_detail = item.get('statusDetail', {})
        for product, details in status_detail.items():
            if isinstance(details, dict):
                warnings = details.get('warnings', [])
                for warning in warnings:
                    if 'consent' in str(warning).lower() or 'authorization' in str(warning).lower():
                        consent_info['needs_renewal'] = True
                        break
        
        return consent_info
    
    async def _get_accounts_needing_renewal(self, company_id: Optional[int] = None) -> List[BankAccount]:
        """
        Busca contas que precisam de renovação de consentimento
        """
        from asgiref.sync import sync_to_async
        
        query = BankAccount.objects.filter(
            is_active=True,
            pluggy_item_id__isnull=False
        ).select_related('bank_provider', 'company')
        
        if company_id:
            query = query.filter(company_id=company_id)
        
        # Filtrar por status que indicam necessidade de renovação
        query = query.filter(
            models.Q(sync_status__in=['login_error', 'waiting_user_action', 'expired']) |
            models.Q(last_sync__lt=timezone.now() - timedelta(days=30))  # Não sincroniza há 30 dias
        )
        
        accounts = await sync_to_async(list)(query)
        return accounts
    
    async def _handle_user_action_required(self, account: BankAccount, details: Dict):
        """
        Trata casos onde é necessária ação do usuário
        """
        from asgiref.sync import sync_to_async
        
        # Atualizar status da conta
        account.sync_status = 'waiting_user_action'
        account.sync_error_message = 'Reconexão necessária - por favor, faça login novamente'
        await sync_to_async(account.save)()
        
        # TODO: Enviar notificação ao usuário
        logger.info(f"Notificação pendente: Conta {account.id} precisa de reconexão manual")


# Tarefas Celery para execução agendada
@shared_task
def check_and_renew_consents_task():
    """
    Tarefa agendada para verificar e renovar consentimentos
    Deve ser executada diariamente
    """
    import asyncio
    
    async def run_renewal():
        service = ConsentRenewalService()
        return await service.check_and_renew_consents()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_renewal())
        logger.info(f"Renovação de consentimentos concluída: {result}")
        return result
    finally:
        loop.close()


@shared_task
def renew_single_consent_task(account_id: int):
    """
    Tarefa para renovar consentimento de uma conta específica
    """
    import asyncio
    from asgiref.sync import sync_to_async
    
    async def run_renewal():
        try:
            account = await sync_to_async(BankAccount.objects.get)(id=account_id)
            service = ConsentRenewalService()
            return await service.renew_consent(account)
        except BankAccount.DoesNotExist:
            logger.error(f"Conta {account_id} não encontrada")
            return {'success': False, 'error': 'Conta não encontrada'}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_renewal())
        logger.info(f"Renovação de consentimento para conta {account_id}: {result}")
        return result
    finally:
        loop.close()