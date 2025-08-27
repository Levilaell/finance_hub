#!/usr/bin/env python3
"""
PRODUCTION COMPANY FIX - Para executar via Railway

Este script deve ser executado em PRODUÇÃO via:
railway run python fix_production_company_issue.py

Objetivo:
1. Verificar se user 'arabel.bebel@hotmail.com' existe em produção
2. Verificar se Company ID 4 existe 
3. Se não existir, diagnosticar e corrigir
4. Se existir, verificar get_user_company()
"""
import os
import sys
import django

# Setup para produção
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()

def get_user_company(user):
    """Same logic as in views.py"""
    try:
        return Company.objects.get(owner=user)
    except Company.DoesNotExist:
        return None
    except Company.MultipleObjectsReturned:
        return Company.objects.filter(owner=user).first()

def main():
    print("🚨 PRODUCTION COMPANY ISSUE FIX")
    print("=" * 50)
    print("Baseado nos logs: User arabel.bebel@hotmail.com -> Company ID 4")
    print()
    
    # 1. Verificar usuário
    user_email = "arabel.bebel@hotmail.com"
    print(f"1️⃣ Verificando usuário: {user_email}")
    print("-" * 30)
    
    try:
        user = User.objects.get(email=user_email)
        print(f"✅ USUÁRIO EXISTE:")
        print(f"   ID: {user.id}")
        print(f"   Nome: {user.get_full_name()}")
        print(f"   Ativo: {user.is_active}")
        print(f"   Data: {user.date_joined}")
        
    except User.DoesNotExist:
        print(f"❌ USUÁRIO NÃO EXISTE EM PRODUÇÃO!")
        print(f"   🔧 CRIANDO USUÁRIO DE TESTE...")
        
        # Criar usuário para teste
        user = User.objects.create_user(
            email=user_email,
            username=user_email.split('@')[0],
            first_name='Levi Lael',
            last_name='Coelho Silva',
            password='temporarypass123'
        )
        print(f"   ✅ Usuário criado: ID {user.id}")
    
    # 2. Verificar Company 4
    print(f"\n2️⃣ Verificando Company ID 4:")
    print("-" * 30)
    
    try:
        company_4 = Company.objects.get(id=4)
        print(f"✅ COMPANY 4 EXISTE:")
        print(f"   Nome: {company_4.name}")
        print(f"   Owner: {company_4.owner.email}")
        print(f"   Status: {company_4.subscription_status}")
        
        # Verificar se pertence ao usuário correto
        if company_4.owner.email == user_email:
            print(f"   ✅ Company 4 pertence ao usuário correto!")
        else:
            print(f"   ⚠️  Company 4 pertence a {company_4.owner.email}")
            print(f"   🔧 TRANSFERINDO OWNERSHIP...")
            company_4.owner = user
            company_4.save()
            print(f"   ✅ Ownership transferida!")
            
    except Company.DoesNotExist:
        print(f"❌ COMPANY 4 NÃO EXISTE!")
        print(f"   🔧 CRIANDO COMPANY ID 4...")
        
        # Obter plano default (Starter)
        try:
            default_plan = SubscriptionPlan.objects.filter(slug='starter').first()
            if not default_plan:
                print("   ⚠️  Nenhum plano encontrado, usando None")
        except:
            default_plan = None
        
        # Criar company com ID específico 4
        company = Company.objects.create(
            id=4,
            owner=user,
            name=f"{user.get_full_name() or 'User'} Company",
            trade_name=f"{user.get_full_name() or 'User'} Company",
            email=user.email,
            subscription_status='trial',
            subscription_plan=default_plan
        )
        print(f"   ✅ Company ID 4 criada: {company.name}")
    
    # 3. Testar get_user_company
    print(f"\n3️⃣ Testando get_user_company():")
    print("-" * 30)
    
    test_company = get_user_company(user)
    if test_company:
        print(f"✅ get_user_company() funciona:")
        print(f"   Retorna Company ID: {test_company.id}")
        print(f"   Nome: {test_company.name}")
        
        if test_company.id == 4:
            print(f"   ✅ CONFIRMADO: Retorna Company ID 4!")
        else:
            print(f"   ⚠️  Retorna ID {test_company.id}, não 4")
            
    else:
        print(f"❌ get_user_company() retorna None")
    
    # 4. Listar todas as companies
    print(f"\n4️⃣ Companies em produção:")
    print("-" * 30)
    
    companies = Company.objects.all().order_by('id')
    for comp in companies:
        mark = "🎯" if comp.owner.email == user_email else "  "
        print(f"{mark} ID: {comp.id}, Nome: {comp.name}, Owner: {comp.owner.email}")
    
    print(f"\n" + "=" * 50)
    print(f"✅ DIAGNÓSTICO COMPLETO!")
    print(f"📋 Agora teste um novo pagamento e verifique os logs")

if __name__ == "__main__":
    main()