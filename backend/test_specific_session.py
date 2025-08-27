#!/usr/bin/env python
"""
Testar o session específico que foi criado
railway run python test_specific_session.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.conf import settings
import stripe

def test_specific_session():
    print("🧪 TESTE DO SESSION ESPECÍFICO")
    print("=" * 60)
    
    # Session ID do log
    session_id = "cs_test_a14pcsW0nHOBw39hfZgXA4uKHeOLVHUhIwr7yY4hmXZh2iArqNqwMjoNs2"
    
    print(f"📋 Session ID: {session_id}")
    
    # Configurar Stripe
    stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if stripe_secret:
        key_preview = stripe_secret[-4:] if len(stripe_secret) >= 4 else "***"
        is_test = stripe_secret.startswith('sk_test_')
        mode = "TEST" if is_test else "LIVE"
        print(f"🔑 Stripe Key: ...{key_preview} ({mode} mode)")
        
        stripe.api_key = stripe_secret
    else:
        print("❌ STRIPE_SECRET_KEY não configurada!")
        return
    
    # Testar retrieve do session
    try:
        print(f"\n🌐 Tentando recuperar session...")
        session = stripe.checkout.Session.retrieve(session_id)
        
        print(f"✅ SESSION RECUPERADO COM SUCESSO!")
        print(f"   ID: {session.id}")
        print(f"   Payment Status: {session.payment_status}")
        print(f"   Customer: {session.customer}")
        print(f"   Amount: {session.amount_total}")
        print(f"   Currency: {session.currency}")
        print(f"   Created: {session.created}")
        print(f"   Expires At: {session.expires_at}")
        print(f"   Mode: {session.mode}")
        print(f"   URL: {session.url}")
        
        # Verificar metadata
        metadata = session.get('metadata', {})
        print(f"   Metadata: {metadata}")
        
        if not metadata.get('company_id'):
            subscription_metadata = session.get('subscription_data', {}).get('metadata', {})
            print(f"   Subscription Metadata: {subscription_metadata}")
        
        # Status detalhado
        print(f"\n📊 STATUS DETALHADO:")
        print(f"   Status: {session.status}")
        print(f"   Payment Status: {session.payment_status}")
        
        if hasattr(session, 'subscription'):
            print(f"   Subscription: {session.subscription}")
        
        if hasattr(session, 'payment_intent'):
            print(f"   Payment Intent: {session.payment_intent}")
        
        # Verificar se ainda é válido
        import time
        current_timestamp = int(time.time())
        expires_at = session.expires_at
        
        if expires_at and current_timestamp > expires_at:
            print(f"⚠️  SESSION EXPIRADO!")
            print(f"   Expirou em: {expires_at}")
            print(f"   Timestamp atual: {current_timestamp}")
        else:
            print(f"✅ Session ainda válido")
            if expires_at:
                remaining = expires_at - current_timestamp
                print(f"   Expira em: {remaining} segundos")
        
    except stripe.error.InvalidRequestError as e:
        print(f"❌ ERRO InvalidRequestError:")
        print(f"   Message: {str(e)}")
        print(f"   Code: {getattr(e, 'code', 'N/A')}")
        print(f"   Param: {getattr(e, 'param', 'N/A')}")
        print(f"   Type: {getattr(e, 'type', 'N/A')}")
        
        # Verificar se é problema de environment
        if "does not exist" in str(e).lower():
            print(f"\n🔍 POSSÍVEIS CAUSAS:")
            print(f"   1. Session foi criado em ambiente diferente (test vs live)")
            print(f"   2. Session ainda não foi processado pelo Stripe")
            print(f"   3. Session ID está incorreto")
        
    except stripe.error.AuthenticationError as e:
        print(f"❌ ERRO DE AUTENTICAÇÃO:")
        print(f"   {str(e)}")
        print(f"   Verifique as chaves do Stripe")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
    
    # Testar também listagem de sessions
    print(f"\n📋 ÚLTIMAS SESSIONS CRIADAS:")
    try:
        sessions = stripe.checkout.Session.list(limit=5)
        for i, sess in enumerate(sessions.data, 1):
            metadata = sess.get('metadata', {})
            company_id = metadata.get('company_id', 'N/A')
            print(f"   {i}. {sess.id} - Company: {company_id} - Status: {sess.payment_status}")
            
            if sess.id == session_id:
                print(f"      🎯 ESTA É A SESSION QUE ESTAMOS TESTANDO!")
    
    except Exception as e:
        print(f"❌ Erro ao listar sessions: {e}")

if __name__ == "__main__":
    test_specific_session()