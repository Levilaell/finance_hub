#!/usr/bin/env python
"""
Teste rápido do endpoint de status
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.banking.models import BankAccount

# Criar cliente de teste
from rest_framework.test import APIClient
client = APIClient()

# Fazer login (ajuste conforme seu sistema)
User = get_user_model()
try:
    # Pegar primeiro usuário com company
    user = User.objects.filter(company__isnull=False).first()
    if user:
        # Forçar autenticação para API
        client.force_authenticate(user=user)
        print(f"✅ Logado como: {user.email}")
        
        # Pegar primeira conta Pluggy do usuário
        account = BankAccount.objects.filter(
            company=user.company,
            pluggy_item_id__isnull=False
        ).first()
        
        # Se não encontrar, pegar qualquer conta Pluggy
        if not account:
            account = BankAccount.objects.filter(
                pluggy_item_id__isnull=False
            ).first()
        
        if account:
            print(f"\n📊 Testando conta: {account.nickname} (ID: {account.id})")
            
            # Testar endpoint de status
            response = client.get(f'/api/banking/pluggy/accounts/{account.id}/status/')
            
            print(f"\n📡 Status Code: {response.status_code}")
            print(f"📝 Response: {response.json()}")
            
            # Se precisar reconexão, testar endpoint de reconexão
            data = response.json()
            if data.get('data', {}).get('needs_reconnection'):
                print(f"\n🔄 Conta precisa reconexão! Testando endpoint de reconexão...")
                
                response = client.post(f'/api/banking/pluggy/accounts/{account.id}/reconnect/')
                print(f"\n📡 Status Code: {response.status_code}")
                print(f"📝 Response: {response.json()}")
        else:
            print("❌ Nenhuma conta Pluggy encontrada")
    else:
        print("❌ Nenhum usuário com company encontrado")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()