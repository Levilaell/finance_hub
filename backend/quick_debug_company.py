#!/usr/bin/env python
"""
Quick debug para investigar Company ID 4 issue
Executar: railway run python quick_debug_company.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

# Função exata do views.py
def get_user_company(user):
    try:
        return Company.objects.get(owner=user)
    except Company.DoesNotExist:
        return None
    except Company.MultipleObjectsReturned:
        return Company.objects.filter(owner=user).first()

print("🔍 Quick Debug - Company ID 4 Issue")
print("=" * 50)

try:
    # Buscar usuário
    user = User.objects.get(email="arabel.bebel@hotmail.com")
    print(f"✅ User: {user.id} - {user.email}")
    
    # Testar função get_user_company
    company = get_user_company(user)
    if company:
        print(f"✅ Company: {company.id} - {company.name}")
        print(f"   Status: {company.subscription_status}")
        print(f"   Owner ID: {company.owner.id}")
        
        if company.id == 4:
            print("🎯 CONFIRMADO: Retorna Company 4")
        
    else:
        print("❌ get_user_company() retornou None")
        
    # Verificar se Company 4 existe
    try:
        comp4 = Company.objects.get(id=4)
        print(f"✅ Company 4 existe: {comp4.name} (Owner: {comp4.owner.email})")
    except Company.DoesNotExist:
        print("❌ Company 4 NÃO existe")
        
    # Listar todas as companies
    print(f"\nTodas as companies:")
    for c in Company.objects.all().order_by('id'):
        print(f"   {c.id}: {c.name} (Owner: {c.owner.email})")

except User.DoesNotExist:
    print("❌ User não encontrado!")
except Exception as e:
    print(f"❌ Erro: {e}")