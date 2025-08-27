#!/usr/bin/env python
"""
Script para debuggar sessions do Stripe em produção
Executar: railway run python debug_stripe_sessions.py

Vai investigar:
1. Se as Stripe keys estão corretas
2. Quais sessions existem no Stripe
3. Se há problema de test vs live mode
4. Comparar com sessions no banco de dados
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.conf import settings
import stripe
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.payments.models import Payment

User = get_user_model()

def debug_stripe_sessions():
    print("🔍 STRIPE SESSIONS DEBUG")
    print("=" * 60)
    
    # 1. Verificar configuração Stripe
    print("\n1️⃣ CONFIGURAÇÃO STRIPE:")
    print("-" * 30)
    
    stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if stripe_secret:
        # Mostrar apenas últimos 4 caracteres por segurança
        key_preview = stripe_secret[-4:] if len(stripe_secret) >= 4 else "***"
        is_test = stripe_secret.startswith('sk_test_')
        mode = "TEST" if is_test else "LIVE"
        print(f"✅ Stripe Key: ...{key_preview} ({mode} mode)")
        
        stripe.api_key = stripe_secret
    else:
        print("❌ STRIPE_SECRET_KEY não configurada!")
        return
    
    # 2. Verificar usuário e company
    print("\n2️⃣ USUÁRIO E COMPANY:")
    print("-" * 30)
    
    try:
        user = User.objects.get(email="arabel.bebel@hotmail.com")
        print(f"✅ User: {user.id} - {user.email}")
        
        # Usar a mesma função do código
        def get_user_company(user):
            try:
                return Company.objects.get(owner=user)
            except Company.DoesNotExist:
                return None
            except Company.MultipleObjectsReturned:
                return Company.objects.filter(owner=user).first()
        
        company = get_user_company(user)
        if company:
            print(f"✅ Company: {company.id} - {company.name}")
        else:
            print("❌ Nenhuma company encontrada!")
            return
            
    except User.DoesNotExist:
        print("❌ Usuário não encontrado!")
        return
    
    # 3. Buscar sessions recentes do Stripe
    print("\n3️⃣ SESSIONS RECENTES NO STRIPE:")
    print("-" * 30)
    
    try:
        # Buscar últimas 10 sessions
        sessions = stripe.checkout.Session.list(limit=10)
        
        print(f"Total sessions encontradas: {len(sessions.data)}")
        
        company_sessions = []
        for session in sessions.data:
            metadata = session.get('metadata', {})
            session_company_id = metadata.get('company_id')
            
            print(f"\nSession: {session.id}")
            print(f"  Status: {session.payment_status}")
            print(f"  Company ID: {session_company_id}")
            print(f"  Created: {session.created}")
            print(f"  Amount: {session.amount_total}")
            
            if str(session_company_id) == str(company.id):
                company_sessions.append(session)
                print(f"  🎯 MATCH com company atual!")
        
        print(f"\n📊 Sessions da Company {company.id}: {len(company_sessions)}")
        
        # 4. Testar validação da última session da company
        if company_sessions:
            latest_session = company_sessions[0]
            print(f"\n4️⃣ TESTANDO VALIDAÇÃO DA ÚLTIMA SESSION:")
            print("-" * 30)
            
            session_id = latest_session.id
            print(f"Session ID: {session_id}")
            
            try:
                # Tentar retrieve exatamente como no código
                test_session = stripe.checkout.Session.retrieve(session_id)
                print(f"✅ Session retrieve funcionou!")
                print(f"  Payment Status: {test_session.payment_status}")
                print(f"  Metadata: {test_session.get('metadata', {})}")
                
            except stripe.error.InvalidRequestError as e:
                print(f"❌ InvalidRequestError: {e}")
                print(f"   Código: {e.code if hasattr(e, 'code') else 'N/A'}")
                print(f"   Param: {e.param if hasattr(e, 'param') else 'N/A'}")
                
            except Exception as e:
                print(f"❌ Outro erro: {e}")
        else:
            print("\n4️⃣ Nenhuma session da company encontrada para teste")
    
    except stripe.error.AuthenticationError:
        print("❌ Erro de autenticação - Stripe key inválida")
    except stripe.error.StripeError as e:
        print(f"❌ Erro Stripe: {e}")
    except Exception as e:
        print(f"❌ Erro geral: {e}")
    
    # 5. Verificar payments no banco local
    print("\n5️⃣ PAYMENTS NO BANCO LOCAL:")
    print("-" * 30)
    
    try:
        payments = Payment.objects.filter(company=company).order_by('-created_at')[:5]
        
        print(f"Últimos 5 payments da company {company.id}:")
        for payment in payments:
            print(f"  Payment {payment.id}: {payment.status} - R$ {payment.amount}")
            if payment.stripe_payment_intent_id:
                print(f"    Stripe Intent: {payment.stripe_payment_intent_id}")
            print(f"    Criado: {payment.created_at}")
    
    except Exception as e:
        print(f"❌ Erro ao buscar payments: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Verificar se test/live keys estão corretas")
    print("2. Verificar se session_id sendo usado é válido")
    print("3. Verificar logs do Stripe Dashboard")
    print("4. Testar criar nova session")
    print("=" * 60)

if __name__ == "__main__":
    debug_stripe_sessions()