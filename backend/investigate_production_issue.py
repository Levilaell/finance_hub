#!/usr/bin/env python
"""
Script para investigar o problema de Company ID 4 em produção
Executar no Railway com: railway run python investigate_production_issue.py

Baseado nos logs:
- User: Levi Lael Coelho Silva (arabel.bebel@hotmail.com)
- Created checkout session for company 4
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')  # For production
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company, SubscriptionPlan
from apps.payments.models import Subscription, Payment

User = get_user_model()

def investigate_production_issue():
    """Investiga o problema específico em produção"""
    
    print("=" * 80)
    print("🔍 INVESTIGAÇÃO PRODUÇÃO: Company ID 4 Issue")
    print("Baseado no log: 'Created checkout session ... for company 4'")
    print("=" * 80)
    
    # 1. Verificar o usuário específico
    print("\n1️⃣ VERIFICANDO USUÁRIO ESPECÍFICO:")
    print("-" * 50)
    
    try:
        user = User.objects.get(email="arabel.bebel@hotmail.com")
        print(f"✅ Usuário encontrado:")
        print(f"   ID: {user.id}")
        print(f"   Nome: {user.first_name} {user.last_name}")
        print(f"   Email: {user.email}")
        print(f"   Ativo: {user.is_active}")
        print(f"   Data criação: {user.created_at}")
        
        # Verificar company via related_name
        if hasattr(user, 'company') and user.company:
            company = user.company
            print(f"\n   🏢 Company via user.company:")
            print(f"     ID: {company.id}")
            print(f"     Nome: {company.name}")
            print(f"     Status: {company.subscription_status}")
            print(f"     Owner ID: {company.owner.id}")
            print(f"     Data criação: {company.created_at}")
        else:
            print(f"\n   ❌ user.company não existe ou é None!")
            
            # Verificar usando Company.objects.get(owner=user)
            try:
                company_by_owner = Company.objects.get(owner=user)
                print(f"\n   🔍 Company via Company.objects.get(owner=user):")
                print(f"     ID: {company_by_owner.id}")
                print(f"     Nome: {company_by_owner.name}")
                print(f"     Status: {company_by_owner.subscription_status}")
                print(f"     ⚠️  PROBLEMA: user.company não funciona mas existe company com owner={user.id}")
            except Company.DoesNotExist:
                print(f"   ❌ Nenhuma company com owner={user.id}")
        
    except User.DoesNotExist:
        print("❌ Usuário 'arabel.bebel@hotmail.com' não encontrado!")
        return
    
    # 2. Verificar todas as companies
    print("\n\n2️⃣ VERIFICANDO TODAS AS COMPANIES:")
    print("-" * 50)
    
    companies = Company.objects.all().order_by('id')
    print(f"Total de companies: {companies.count()}")
    
    for company in companies:
        print(f"   Company {company.id}: {company.name}")
        print(f"     Owner: {company.owner.email} (ID: {company.owner.id})")
        print(f"     Status: {company.subscription_status}")
        print(f"     Criada: {company.created_at}")
    
    # 3. Verificar especificamente Company 4
    print("\n\n3️⃣ VERIFICANDO COMPANY 4:")
    print("-" * 50)
    
    try:
        company_4 = Company.objects.get(id=4)
        print(f"✅ Company 4 EXISTE:")
        print(f"   Nome: {company_4.name}")
        print(f"   Owner: {company_4.owner.email} (ID: {company_4.owner.id})")
        print(f"   Status: {company_4.subscription_status}")
        print(f"   Criada: {company_4.created_at}")
        
        # Verificar se o owner da company 4 é o usuário do log
        if company_4.owner.email == "arabel.bebel@hotmail.com":
            print("   ✅ CONFIRMADO: Company 4 pertence ao usuário dos logs")
        else:
            print(f"   ❌ PROBLEMA: Company 4 pertence a {company_4.owner.email}, não ao usuário dos logs")
            
    except Company.DoesNotExist:
        print("❌ Company 4 NÃO EXISTE!")
        print("   🚨 PROBLEMA CRÍTICO: Sistema está tentando usar company inexistente")
    
    # 4. Testar a função get_user_company exatamente como está no código
    print("\n\n4️⃣ TESTANDO FUNÇÃO get_user_company():")
    print("-" * 50)
    
    def get_user_company(user):
        """Cópia exata da função do views.py"""
        try:
            from apps.companies.models import Company
            return Company.objects.get(owner=user)
        except Company.DoesNotExist:
            return None
        except Company.MultipleObjectsReturned:
            # If user owns multiple companies, get the first one
            from apps.companies.models import Company
            return Company.objects.filter(owner=user).first()
    
    try:
        user = User.objects.get(email="arabel.bebel@hotmail.com")
        test_company = get_user_company(user)
        
        if test_company:
            print(f"✅ get_user_company() retornou:")
            print(f"   Company ID: {test_company.id}")
            print(f"   Nome: {test_company.name}")
            
            # Aqui está o problema!
            if test_company.id == 4:
                print("   🎯 CONFIRMADO: get_user_company() está retornando Company 4!")
            else:
                print(f"   ⚠️  get_user_company() retorna ID {test_company.id}, não 4")
        else:
            print("❌ get_user_company() retornou None")
            
    except Exception as e:
        print(f"❌ Erro ao testar get_user_company(): {e}")
    
    # 5. Verificar payments e subscriptions relacionadas
    print("\n\n5️⃣ VERIFICANDO PAYMENTS E SUBSCRIPTIONS:")
    print("-" * 50)
    
    try:
        user = User.objects.get(email="arabel.bebel@hotmail.com")
        user_company = get_user_company(user)
        
        if user_company:
            # Verificar subscriptions
            subscriptions = Subscription.objects.filter(company=user_company).order_by('-created_at')
            print(f"Subscriptions da company {user_company.id}:")
            for sub in subscriptions[:3]:  # Últimas 3
                print(f"   Sub {sub.id}: Status {sub.status}, Criada: {sub.created_at}")
            
            # Verificar payments
            payments = Payment.objects.filter(company=user_company).order_by('-created_at')
            print(f"\nPayments da company {user_company.id}:")
            for pay in payments[:3]:  # Últimos 3
                print(f"   Payment {pay.id}: Status {pay.status}, Amount {pay.amount}, Criado: {pay.created_at}")
                if hasattr(pay, 'stripe_payment_intent_id') and pay.stripe_payment_intent_id:
                    print(f"     Stripe Intent: {pay.stripe_payment_intent_id}")
    
    except Exception as e:
        print(f"❌ Erro ao verificar payments/subscriptions: {e}")
    
    # 6. Verificar últimas checkout sessions do Stripe
    print("\n\n6️⃣ VERIFICANDO STRIPE CHECKOUT SESSIONS:")
    print("-" * 50)
    
    try:
        import stripe
        from django.conf import settings
        
        if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Buscar últimas sessions
            sessions = stripe.checkout.Session.list(limit=10)
            
            print("Últimas 10 checkout sessions:")
            for session in sessions.data:
                metadata = session.get('metadata', {})
                company_id = metadata.get('company_id', 'N/A')
                created = session.get('created', 0)
                status = session.get('payment_status', 'unknown')
                
                print(f"   Session {session.id}:")
                print(f"     Company ID: {company_id}")
                print(f"     Status: {status}")
                print(f"     Criado: {created}")
                
                # Focar na session com company_id = 4
                if str(company_id) == '4':
                    print(f"     🎯 ENCONTRADA SESSION COM COMPANY 4!")
                    print(f"     Metadata completo: {metadata}")
            
    except Exception as e:
        print(f"⚠️  Erro ao buscar Stripe sessions: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 ANÁLISE FINAL:")
    print("=" * 80)
    print("Se Company 4 existe e pertence ao usuário correto:")
    print("  → O código está funcionando corretamente")
    print("  → O problema pode estar na validação do payment")
    print()
    print("Se Company 4 não existe:")
    print("  → Há um problema grave de dados órfãos")
    print("  → Precisa corrigir ou recriar a company")
    print()
    print("Se Company 4 existe mas não pertence ao usuário:")
    print("  → Problema de autenticação/sessão")
    print("  → Usuário pode estar logado com conta errada")
    print("=" * 80)

if __name__ == "__main__":
    investigate_production_issue()