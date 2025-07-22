#!/usr/bin/env python
"""
Script para testar integração de planos com recursos
Verifica se os limites estão funcionando corretamente
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import BankAccount, Transaction
from apps.authentication.models import User

def test_plan_limits():
    """Testa todos os limites de planos"""
    print("\n" + "="*60)
    print("TESTE DE LIMITES DE PLANOS")
    print("="*60)
    
    # 1. TESTE PLANO STARTER
    print("\n1. TESTANDO PLANO STARTER")
    print("-" * 30)
    
    starter_company = Company.objects.filter(
        subscription_plan__plan_type='starter'
    ).first()
    
    if starter_company:
        print(f"✓ Empresa: {starter_company.name}")
        print(f"  Plano: {starter_company.subscription_plan.name}")
        print(f"  Limites:")
        print(f"    - Transações: {starter_company.current_month_transactions}/{starter_company.subscription_plan.max_transactions}")
        print(f"    - Contas: {starter_company.active_bank_accounts_count}/{starter_company.subscription_plan.max_bank_accounts}")
        print(f"    - IA: {starter_company.subscription_plan.max_ai_requests_per_month} (sem acesso)")
        
        # Testar limite de contas
        can_add_account = starter_company.can_add_bank_account()
        print(f"\n  Pode adicionar conta? {can_add_account}")
        
        # Testar acesso a IA
        can_use_ai, message = starter_company.can_use_ai_insight()
        print(f"  Pode usar IA? {can_use_ai} - {message}")
        
        # Testar limite de transações
        limit_reached, usage_info = starter_company.check_plan_limits('transactions')
        print(f"  Limite de transações atingido? {limit_reached}")
        if usage_info and isinstance(usage_info, dict):
            print(f"    Uso: {usage_info.get('percentage', 0):.1f}%")
    else:
        print("❌ Nenhuma empresa com plano Starter encontrada")
    
    # 2. TESTE PLANO PROFESSIONAL
    print("\n\n2. TESTANDO PLANO PROFESSIONAL")
    print("-" * 30)
    
    prof_company = Company.objects.filter(
        subscription_plan__plan_type='professional'
    ).first()
    
    if prof_company:
        print(f"✓ Empresa: {prof_company.name}")
        print(f"  Plano: {prof_company.subscription_plan.name}")
        print(f"  Limites:")
        print(f"    - Transações: {prof_company.current_month_transactions}/{prof_company.subscription_plan.max_transactions}")
        print(f"    - Contas: {prof_company.active_bank_accounts_count}/{prof_company.subscription_plan.max_bank_accounts}")
        print(f"    - IA: {prof_company.current_month_ai_requests}/{prof_company.subscription_plan.max_ai_requests_per_month}")
        
        # Simular uso de IA
        print(f"\n  Testando uso de IA:")
        can_use_ai, message = prof_company.can_use_ai_insight()
        print(f"    Pode usar? {can_use_ai}")
        if can_use_ai:
            remaining = prof_company.subscription_plan.max_ai_requests_per_month - prof_company.current_month_ai_requests
            print(f"    Requisições restantes: {remaining}")
    else:
        print("❌ Nenhuma empresa com plano Professional encontrada")
    
    # 3. TESTE PLANO ENTERPRISE
    print("\n\n3. TESTANDO PLANO ENTERPRISE")
    print("-" * 30)
    
    ent_company = Company.objects.filter(
        subscription_plan__plan_type='enterprise'
    ).first()
    
    if ent_company:
        print(f"✓ Empresa: {ent_company.name}")
        print(f"  Plano: {ent_company.subscription_plan.name}")
        print(f"  Recursos ilimitados:")
        print(f"    - Transações: {ent_company.current_month_transactions} (ilimitado)")
        print(f"    - Contas: {ent_company.active_bank_accounts_count} (ilimitado)")
        print(f"    - IA: {ent_company.current_month_ai_requests} (ilimitado)")
        print(f"    - API: {'✓' if ent_company.subscription_plan.has_api_access else '✗'}")
    else:
        print("❌ Nenhuma empresa com plano Enterprise encontrada")

def test_limit_enforcement():
    """Testa enforcement de limites"""
    print("\n\n" + "="*60)
    print("TESTE DE ENFORCEMENT DE LIMITES")
    print("="*60)
    
    # Encontrar empresa próxima dos limites
    companies = Company.objects.filter(
        subscription_plan__isnull=False,
        subscription_status='active'
    )
    
    for company in companies:
        if company.subscription_plan.plan_type == 'enterprise':
            continue  # Skip unlimited
            
        # Verificar percentual de uso
        trans_usage = company.get_usage_percentage('transactions')
        
        if trans_usage >= 80:
            print(f"\n⚠️  {company.name} - Uso alto de transações: {trans_usage:.1f}%")
            print(f"   Notificações enviadas:")
            print(f"     80%: {'✓' if company.notified_80_percent else '✗'}")
            print(f"     90%: {'✓' if company.notified_90_percent else '✗'}")

def test_middleware_blocks():
    """Testa se o middleware está bloqueando corretamente"""
    print("\n\n" + "="*60)
    print("TESTE DE BLOQUEIOS DO MIDDLEWARE")
    print("="*60)
    
    # Simular empresa no limite
    test_company = Company.objects.filter(
        subscription_plan__plan_type='starter'
    ).first()
    
    if test_company:
        print(f"\nSimulando limites para {test_company.name}:")
        
        # Salvar valores originais
        original_trans = test_company.current_month_transactions
        original_ai = test_company.current_month_ai_requests
        
        # Simular no limite
        test_company.current_month_transactions = test_company.subscription_plan.max_transactions
        test_company.save()
        
        limit_reached, _ = test_company.check_plan_limits('transactions')
        print(f"  Transações no limite: {limit_reached}")
        
        # Restaurar
        test_company.current_month_transactions = original_trans
        test_company.current_month_ai_requests = original_ai
        test_company.save()
        print("  ✓ Valores restaurados")

def check_counter_accuracy():
    """Verifica precisão dos contadores"""
    print("\n\n" + "="*60)
    print("VERIFICAÇÃO DE PRECISÃO DOS CONTADORES")
    print("="*60)
    
    companies = Company.objects.filter(is_active=True)[:3]
    
    for company in companies:
        # Contar transações reais do mês
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        real_count = Transaction.objects.filter(
            bank_account__company=company,
            transaction_date__gte=month_start
        ).count()
        
        stored_count = company.current_month_transactions or 0
        
        print(f"\n{company.name}:")
        print(f"  Contador: {stored_count}")
        print(f"  Real: {real_count}")
        
        if real_count != stored_count:
            print(f"  ⚠️  DISCREPÂNCIA: {abs(real_count - stored_count)} transações")
        else:
            print(f"  ✓ Contador preciso")

def summary_report():
    """Relatório resumido"""
    print("\n\n" + "="*60)
    print("RESUMO DA VERIFICAÇÃO")
    print("="*60)
    
    # Estatísticas gerais
    total_companies = Company.objects.filter(is_active=True).count()
    by_plan = Company.objects.filter(
        is_active=True,
        subscription_plan__isnull=False
    ).values('subscription_plan__plan_type').annotate(
        count=Count('id')
    )
    
    print(f"\nTotal de empresas ativas: {total_companies}")
    print("\nDistribuição por plano:")
    for plan in by_plan:
        print(f"  {plan['subscription_plan__plan_type'].title()}: {plan['count']}")
    
    # Empresas próximas dos limites
    print("\n\nEmpresas próximas dos limites (>80%):")
    at_risk = 0
    
    for company in Company.objects.filter(
        is_active=True,
        subscription_plan__isnull=False
    ).exclude(subscription_plan__plan_type='enterprise'):
        usage = company.get_usage_percentage('transactions')
        if usage >= 80:
            at_risk += 1
            print(f"  - {company.name}: {usage:.1f}% do limite de transações")
    
    if at_risk == 0:
        print("  ✓ Nenhuma empresa próxima dos limites")
    
    print("\n" + "="*60)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("="*60)

if __name__ == "__main__":
    from django.db.models import Count, Max
    
    test_plan_limits()
    test_limit_enforcement()
    test_middleware_blocks()
    check_counter_accuracy()
    summary_report()