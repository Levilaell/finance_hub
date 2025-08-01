"""
Serviço de Cache Inteligente para AI Insights
Otimiza performance através de cache estratégico de dados financeiros
"""
import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from apps.banking.models import Transaction, BankAccount
from .encryption_service import encryption_service

logger = logging.getLogger(__name__)


class CacheService:
    """Serviço de cache inteligente para otimizar consultas financeiras"""
    
    # Configurações de cache (em segundos)
    CACHE_DURATIONS = {
        'financial_context': 300,      # 5 minutos
        'monthly_summary': 1800,       # 30 minutos
        'insights_dashboard': 900,     # 15 minutos
        'transaction_stats': 600,      # 10 minutos
        'anomaly_context': 1200,       # 20 minutos
        'company_metrics': 3600,       # 1 hora
    }
    
    @classmethod
    def get_cache_key(cls, key_type: str, company_id: str, **kwargs) -> str:
        """Gera chave de cache única"""
        # Adiciona parâmetros extras à chave se fornecidos
        extra_params = '_'.join(f"{k}_{v}" for k, v in sorted(kwargs.items()) if v is not None)
        base_key = f"ai_insights:{key_type}:{company_id}"
        
        if extra_params:
            return f"{base_key}:{extra_params}"
        return base_key
    
    @classmethod
    def get_financial_context(cls, company_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtém contexto financeiro da empresa com cache
        
        Args:
            company_id: ID da empresa
            force_refresh: Força atualização do cache
            
        Returns:
            Dict com contexto financeiro completo
        """
        cache_key = cls.get_cache_key('financial_context', company_id)
        
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit para contexto financeiro: {company_id}")
                # Decrypt the cached data
                if isinstance(cached_data, dict):
                    return encryption_service.decrypt_dict(cached_data)
                return cached_data
        
        logger.debug(f"Gerando contexto financeiro: {company_id}")
        
        try:
            # Período atual (últimos 30 dias)
            now = timezone.now()
            start_date = now - timedelta(days=30)
            
            # Buscar contas da empresa
            accounts = BankAccount.objects.filter(
                company_id=company_id,
                is_active=True
            )
            
            # Saldo atual total
            current_balance = accounts.aggregate(
                total=Sum('balance')
            )['total'] or 0
            
            # Transações do período
            transactions = Transaction.objects.filter(
                account__company_id=company_id,
                date__gte=start_date
            )
            
            # Estatísticas básicas
            stats = transactions.aggregate(
                total_income=Sum('amount', filter=Q(amount__gt=0)),
                total_expenses=Sum('amount', filter=Q(amount__lt=0)),
                transaction_count=Count('id'),
                avg_transaction=Avg('amount')
            )
            
            # Top categorias de despesa
            top_expense_categories = transactions.filter(
                amount__lt=0,
                category__isnull=False
            ).values('category__name').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('total')[:5]
            
            # Calcular percentuais
            total_expenses = abs(stats['total_expenses'] or 0)
            for category in top_expense_categories:
                category['total'] = abs(category['total'])
                category['percentage'] = (
                    (category['total'] / total_expenses * 100) 
                    if total_expenses > 0 else 0
                )
            
            # Tendência dos últimos 7 dias vs 7 dias anteriores
            last_week = now - timedelta(days=7)
            previous_week = now - timedelta(days=14)
            
            recent_flow = transactions.filter(
                date__gte=last_week
            ).aggregate(
                income=Sum('amount', filter=Q(amount__gt=0)),
                expenses=Sum('amount', filter=Q(amount__lt=0))
            )
            
            previous_flow = transactions.filter(
                date__gte=previous_week,
                date__lt=last_week
            ).aggregate(
                income=Sum('amount', filter=Q(amount__gt=0)),
                expenses=Sum('amount', filter=Q(amount__lt=0))
            )
            
            # Calcular tendências
            income_trend = 0
            expense_trend = 0
            
            if previous_flow['income'] and recent_flow['income']:
                income_trend = (
                    (recent_flow['income'] - previous_flow['income']) 
                    / previous_flow['income'] * 100
                )
            
            if previous_flow['expenses'] and recent_flow['expenses']:
                expense_trend = (
                    (abs(recent_flow['expenses']) - abs(previous_flow['expenses'])) 
                    / abs(previous_flow['expenses']) * 100
                )
            
            context = {
                'current_balance': float(current_balance),
                'monthly_income': float(stats['total_income'] or 0),
                'monthly_expenses': float(abs(stats['total_expenses'] or 0)),
                'net_cash_flow': float((stats['total_income'] or 0) + (stats['total_expenses'] or 0)),
                'transaction_count': stats['transaction_count'],
                'avg_transaction_value': float(stats['avg_transaction'] or 0),
                'accounts_count': accounts.count(),
                'top_expense_categories': list(top_expense_categories),
                'trends': {
                    'income_trend_7d': round(income_trend, 2),
                    'expense_trend_7d': round(expense_trend, 2),
                    'recent_income': float(recent_flow['income'] or 0),
                    'recent_expenses': float(abs(recent_flow['expenses'] or 0))
                },
                'period': {
                    'start': start_date.isoformat(),
                    'end': now.isoformat()
                },
                'generated_at': now.isoformat()
            }
            
            # Encrypt sensitive data before caching
            encrypted_context = encryption_service.encrypt_financial_context(context)
            
            # Cache o resultado
            cache.set(
                cache_key,
                encrypted_context,
                cls.CACHE_DURATIONS['financial_context']
            )
            
            logger.info(f"Contexto financeiro cacheado para empresa {company_id}")
            return context
            
        except Exception as e:
            logger.error(f"Erro ao gerar contexto financeiro: {str(e)}")
            return {}
    
    @classmethod
    def get_monthly_summary(cls, company_id: str, months: int = 6) -> Dict[str, Any]:
        """
        Obtém resumo mensal com cache
        
        Args:
            company_id: ID da empresa
            months: Número de meses para análise
            
        Returns:
            Dict com dados mensais
        """
        cache_key = cls.get_cache_key('monthly_summary', company_id, months=months)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit para resumo mensal: {company_id}")
            return cached_data
        
        logger.debug(f"Gerando resumo mensal: {company_id}")
        
        try:
            now = timezone.now()
            monthly_data = []
            
            for i in range(months):
                # Início do mês
                month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                
                # Próximo mês
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1)
                
                # Transações do mês
                month_transactions = Transaction.objects.filter(
                    account__company_id=company_id,
                    date__gte=month_start,
                    date__lt=month_end
                )
                
                # Estatísticas do mês
                month_stats = month_transactions.aggregate(
                    income=Sum('amount', filter=Q(amount__gt=0)),
                    expenses=Sum('amount', filter=Q(amount__lt=0)),
                    count=Count('id')
                )
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'month_name': month_start.strftime('%B %Y'),
                    'income': float(month_stats['income'] or 0),
                    'expenses': float(abs(month_stats['expenses'] or 0)),
                    'net_flow': float((month_stats['income'] or 0) + (month_stats['expenses'] or 0)),
                    'transaction_count': month_stats['count']
                })
            
            summary = {
                'months': monthly_data,
                'total_income': sum(m['income'] for m in monthly_data),
                'total_expenses': sum(m['expenses'] for m in monthly_data),
                'avg_monthly_income': sum(m['income'] for m in monthly_data) / len(monthly_data),
                'avg_monthly_expenses': sum(m['expenses'] for m in monthly_data) / len(monthly_data),
                'generated_at': now.isoformat()
            }
            
            # Cache o resultado
            cache.set(
                cache_key,
                summary,
                cls.CACHE_DURATIONS['monthly_summary']
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo mensal: {str(e)}")
            return {'months': [], 'generated_at': now.isoformat()}
    
    @classmethod
    def get_transaction_stats(cls, company_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Obtém estatísticas de transações com cache
        """
        cache_key = cls.get_cache_key('transaction_stats', company_id, days=days)
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            now = timezone.now()
            start_date = now - timedelta(days=days)
            
            transactions = Transaction.objects.filter(
                account__company_id=company_id,
                date__gte=start_date
            )
            
            # Estatísticas por tipo
            type_stats = transactions.values('transaction_type').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-count')
            
            # Estatísticas por categoria
            category_stats = transactions.filter(
                category__isnull=False
            ).values('category__name').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-count')
            
            # Estatísticas temporais (por dia da semana)
            from django.db.models import Case, When, IntegerField
            weekday_stats = transactions.extra(
                select={'weekday': "EXTRACT(dow FROM transaction_date)"}
            ).values('weekday').annotate(
                count=Count('id'),
                avg_amount=Avg('amount')
            ).order_by('weekday')
            
            stats = {
                'total_transactions': transactions.count(),
                'by_type': list(type_stats),
                'by_category': list(category_stats),
                'by_weekday': list(weekday_stats),
                'period_days': days,
                'generated_at': now.isoformat()
            }
            
            cache.set(
                cache_key,
                stats,
                cls.CACHE_DURATIONS['transaction_stats']
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas de transações: {str(e)}")
            return {}
    
    @classmethod
    def invalidate_company_cache(cls, company_id: str):
        """
        Invalida todo o cache relacionado a uma empresa
        
        Args:
            company_id: ID da empresa
        """
        cache_patterns = [
            f"ai_insights:*:{company_id}",
            f"ai_insights:*:{company_id}:*"
        ]
        
        try:
            from django.core.cache.utils import make_key
            from django.core.cache import cache
            
            # Para cada tipo de cache, tenta invalidar
            for cache_type in cls.CACHE_DURATIONS.keys():
                # Cache básico
                basic_key = cls.get_cache_key(cache_type, company_id)
                cache.delete(basic_key)
                
                # Variações com parâmetros comuns
                for months in [3, 6, 12]:
                    key_with_months = cls.get_cache_key(cache_type, company_id, months=months)
                    cache.delete(key_with_months)
                
                for days in [7, 15, 30, 60, 90]:
                    key_with_days = cls.get_cache_key(cache_type, company_id, days=days)
                    cache.delete(key_with_days)
            
            logger.info(f"Cache invalidado para empresa {company_id}")
            
        except Exception as e:
            logger.error(f"Erro ao invalidar cache da empresa {company_id}: {str(e)}")
    
    @classmethod
    def warm_cache(cls, company_id: str):
        """
        Pré-aquece o cache com dados comumente acessados
        
        Args:
            company_id: ID da empresa
        """
        try:
            logger.info(f"Pré-aquecendo cache para empresa {company_id}")
            
            # Gera dados principais
            cls.get_financial_context(company_id, force_refresh=True)
            cls.get_monthly_summary(company_id, months=6)
            cls.get_transaction_stats(company_id, days=30)
            
            logger.info(f"Cache pré-aquecido para empresa {company_id}")
            
        except Exception as e:
            logger.error(f"Erro ao pré-aquecer cache: {str(e)}")
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Dict com estatísticas de uso do cache
        """
        try:
            from django.core.cache import cache
            
            # Retorna informações básicas (Redis stats removed for simplicity)
            return {
                'backend': str(type(cache)),
                'cache_durations': cls.CACHE_DURATIONS,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            return {'error': str(e)}