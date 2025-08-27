#!/usr/bin/env python3
"""
Debug Company ID 4 Issue - Production Problem
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.append('/Users/levilaell/Desktop/finance_hub/backend')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company
# Importar get_user_company do local correto
def get_user_company(user):
    """Get company for user"""
    try:
        from apps.companies.models import Company
        return Company.objects.get(owner=user)
    except Company.DoesNotExist:
        return None
    except Company.MultipleObjectsReturned:
        from apps.companies.models import Company
        return Company.objects.filter(owner=user).first()

User = get_user_model()

def main():
    print("🔍 INVESTIGANDO PROBLEMA COMPANY ID 4")
    print("=" * 60)
    
    # 1. Investigar usuário específico dos logs
    user_email = "arabel.bebel@hotmail.com" 
    print(f"\n1️⃣ Investigando usuário: {user_email}")
    print("-" * 40)
    
    try:
        user = User.objects.get(email=user_email)
        print(f"✅ Usuário encontrado:")
        print(f"   ID: {user.id}")
        print(f"   Nome: {user.get_full_name()}")
        print(f"   Email: {user.email}")
        
        # Testar get_user_company
        company = get_user_company(user)
        if company:
            print(f"\n✅ get_user_company() retorna:")
            print(f"   Company ID: {company.id}")
            print(f"   Nome: {company.name}")
            print(f"   Status: {company.subscription_status}")
            
            if company.id == 4:
                print("   🎯 PROBLEMA IDENTIFICADO: Retorna Company ID 4!")
            else:
                print(f"   ℹ️  Company ID {company.id} é diferente de 4")
        else:
            print("❌ get_user_company() retorna None")
            
    except User.DoesNotExist:
        print("❌ Usuário não encontrado no banco local!")
        
    # 2. Verificar se Company 4 existe
    print(f"\n2️⃣ Verificando Company ID 4:")
    print("-" * 40)
    
    try:
        company_4 = Company.objects.get(id=4)
        print(f"✅ Company 4 EXISTE:")
        print(f"   Nome: {company_4.name}")
        print(f"   Owner: {company_4.owner.email}")
        print(f"   Status: {company_4.subscription_status}")
    except Company.DoesNotExist:
        print("❌ Company ID 4 NÃO EXISTE!")
        print("   🚨 PROBLEMA: Backend tenta usar company inexistente")
    
    # 3. Listar todas companies
    print(f"\n3️⃣ Todas as companies no sistema:")
    print("-" * 40)
    
    companies = Company.objects.all().order_by('id')
    for comp in companies:
        mark = "🎯" if comp.owner.email == user_email else "  "
        print(f"{mark} ID: {comp.id}, Nome: {comp.name}, Owner: {comp.owner.email}")
    
    print(f"\n" + "=" * 60)
    print("📋 DIAGNÓSTICO:")
    print("1. Verificar se usuário existe e qual company pertence")
    print("2. Verificar se get_user_company() está funcionando")
    print("3. Identificar por que produção usa Company 4")

if __name__ == "__main__":
    main()