#!/usr/bin/env python
"""
Simular exatamente o que o frontend faz ao validar o payment
railway run python test_validation_endpoint.py
"""

import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

def test_validation_endpoint():
    print("🧪 SIMULAÇÃO DA VALIDAÇÃO DE PAYMENT")
    print("=" * 60)
    
    # Session ID do log
    session_id = "cs_test_a14pcsW0nHOBw39hfZgXA4uKHeOLVHUhIwr7yY4hmXZh2iArqNqwMjoNs2"
    
    # Simular como se fosse uma chamada do frontend
    
    # Primeiro, verificar se podemos encontrar o user
    try:
        user = User.objects.get(email="arabel.bebel@hotmail.com")
        print(f"✅ User encontrado: {user.email}")
        
        # Verificar company
        def get_user_company(user):
            try:
                return Company.objects.get(owner=user)
            except Company.DoesNotExist:
                return None
            except Company.MultipleObjectsReturned:
                return Company.objects.filter(owner=user).first()
        
        company = get_user_company(user)
        if company:
            print(f"✅ Company encontrada: {company.id} - {company.name}")
        else:
            print("❌ Company não encontrada!")
            return
            
    except User.DoesNotExist:
        print("❌ User não encontrado!")
        return
    
    # Simular a validação diretamente usando Django
    print(f"\n🔍 SIMULANDO VALIDAÇÃO DJANGO:")
    print(f"Session ID: {session_id}")
    
    try:
        from apps.payments.views import ValidatePaymentView
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        # Criar request factory
        factory = APIRequestFactory()
        
        # Dados da requisição
        data = {'session_id': session_id}
        
        # Criar requisição POST
        request = factory.post('/api/payments/checkout/validate/', data, format='json')
        request.user = user  # Simular usuário autenticado
        
        # Criar view e processar
        view = ValidatePaymentView()
        response = view.post(request)
        
        print(f"📊 RESULTADO DA VALIDAÇÃO:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Data: {response.data}")
        
        if response.status_code == 400:
            print(f"❌ ERRO NA VALIDAÇÃO!")
            if 'code' in response.data:
                print(f"   Código: {response.data['code']}")
            if 'message' in response.data:
                print(f"   Mensagem: {response.data['message']}")
            if 'details' in response.data:
                print(f"   Detalhes: {response.data['details']}")
        
        elif response.status_code == 200:
            print(f"✅ VALIDAÇÃO SUCESSO!")
            
    except Exception as e:
        print(f"❌ Erro na simulação Django: {e}")
        import traceback
        traceback.print_exc()
    
    # Também testar com curl simulado (como se fosse o frontend)
    print(f"\n🌐 TESTE DE ENDPOINT HTTP:")
    
    # Primeiro fazer login para obter token (se possível)
    # Isso é mais complicado porque precisaria de senha, etc.
    print("   (Teste HTTP seria feito pelo frontend com token de auth)")
    
    print(f"\n📋 PRÓXIMOS PASSOS:")
    print("1. Execute este script no Railway para ver os logs detalhados")
    print("2. Verifique se o session existe no Stripe")
    print("3. Compare com os logs da ValidatePaymentView")

if __name__ == "__main__":
    test_validation_endpoint()