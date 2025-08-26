#!/usr/bin/env python
"""
Debug script para investigar o problema atual de company ID mismatch
Executar com: python manage.py shell < debug_current_payment_issue.py
"""

import os
import sys
import django
from django.db import transaction
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

User = get_user_model()

def investigate_current_issue():
    """Investiga o problema atual de company ID mismatch"""
    
    print("=" * 80)
    print("🔍 INVESTIGAÇÃO: Company ID Mismatch - Payment Validation Issue")
    print("=" * 80)
    
    # 1. Verificar o usuário específico dos logs
    print("\n1️⃣ VERIFICANDO USUÁRIO DOS LOGS:")
    print("-" * 50)
    
    try:
        user = User.objects.get(email="arabel.bebel@hotmail.com")
        print(f"✅ Usuário encontrado:")
        print(f"   ID: {user.id}")
        print(f"   Nome: {user.first_name} {user.last_name}")
        print(f"   Email: {user.email}")
        print(f"   Ativo: {user.is_active}")
        
        # Verificar company associada
        if hasattr(user, 'company'):
            company = user.company
            print(f"   Company ID: {company.id}")
            print(f"   Company Nome: {company.name}")
            print(f"   Company Status: {company.subscription_status}")
        else:
            print("   ❌ Usuário não tem company associada!")
            
    except User.DoesNotExist:
        print("❌ Usuário não encontrado!")
        return
    
    # 2. Verificar todas as companies
    print("\n2️⃣ VERIFICANDO TODAS AS COMPANIES:")
    print("-" * 50)
    
    from apps.companies.models import Company
    companies = Company.objects.all().order_by('id')
    
    print(f"Total de companies: {companies.count()}")
    for company in companies:
        print(f"   Company {company.id}: {company.name} (status: {company.subscription_status})")
    
    # 3. Verificar especificamente a Company 4
    print("\n3️⃣ VERIFICANDO COMPANY 4 ESPECIFICAMENTE:")
    print("-" * 50)
    
    try:
        company_4 = Company.objects.get(id=4)
        print(f"✅ Company 4 existe:")
        print(f"   Nome: {company_4.name}")
        print(f"   Status: {company_4.subscription_status}")
        print(f"   Usuários associados:")
        
        # Verificar usuários da company 4
        users_company_4 = User.objects.filter(company=company_4)
        for u in users_company_4:
            print(f"     - {u.first_name} {u.last_name} ({u.email})")
            
    except Company.DoesNotExist:
        print("❌ Company 4 NÃO EXISTE!")
    
    # 4. Verificar últimas sessions do Stripe
    print("\n4️⃣ VERIFICANDO STRIPE CHECKOUT SESSIONS:")
    print("-" * 50)
    
    try:
        import stripe
        from django.conf import settings
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Buscar últimas sessions
        sessions = stripe.checkout.Session.list(limit=5)
        
        print("Últimas 5 checkout sessions:")
        for session in sessions.data:
            metadata = session.get('metadata', {})
            company_id = metadata.get('company_id', 'N/A')
            print(f"   Session {session.id}: company_id={company_id}, status={session.payment_status}")
            
    except Exception as e:
        print(f"❌ Erro ao buscar sessions do Stripe: {e}")
    
    # 5. Verificar subscriptions ativas
    print("\n5️⃣ VERIFICANDO SUBSCRIPTIONS ATIVAS:")
    print("-" * 50)
    
    from apps.payments.models import Subscription
    subscriptions = Subscription.objects.all().order_by('-created_at')[:5]
    
    print("Últimas 5 subscriptions:")
    for sub in subscriptions:
        print(f"   Sub {sub.id}: Company {sub.company.id} ({sub.company.name}) - Status: {sub.status}")
    
    # 6. Verificar audit logs recentes
    print("\n6️⃣ VERIFICANDO AUDIT LOGS RECENTES:")
    print("-" * 50)
    
    try:
        from apps.payments.models import PaymentAuditLog
        recent_audits = PaymentAuditLog.objects.order_by('-created_at')[:10]
        
        print("Últimos 10 audit logs:")
        for audit in recent_audits:
            print(f"   {audit.created_at.strftime('%Y-%m-%d %H:%M:%S')}: {audit.action}")
            print(f"     User: {audit.user.email if audit.user else 'N/A'}")
            print(f"     Company: {audit.company.id if audit.company else 'N/A'}")
            if audit.metadata:
                print(f"     Metadata: {audit.metadata}")
            print()
            
    except Exception as e:
        print(f"⚠️  Não foi possível verificar audit logs: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 PRÓXIMOS PASSOS RECOMENDADOS:")
    print("=" * 80)
    print("1. Verificar se o usuário está autenticado com a company correta")
    print("2. Verificar middleware de company assignment")
    print("3. Analisar código de criação do checkout session")
    print("4. Verificar se há cache ou session incorreta")
    print("=" * 80)

if __name__ == "__main__":
    investigate_current_issue()