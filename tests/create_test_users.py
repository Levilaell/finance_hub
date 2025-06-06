#!/usr/bin/env python
"""
Script para criar usuários de teste
Execute: python create_test_users.py
"""

import os
import django
import sys

# Adicionar o diretório backend ao path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.authentication.models import User
from apps.companies.models import Company, SubscriptionPlan

def create_test_users():
    """Criar usuários de teste"""
    
    # Usuários de teste
    test_users = [
        {
            'email': 'admin@test.com',
            'username': 'admin',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_superuser': True,
            'is_staff': True,
        },
        {
            'email': 'test@test.com',
            'username': 'testuser',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'User',
            'is_superuser': False,
            'is_staff': False,
        },
        {
            'email': 'demo@test.com',
            'username': 'demouser',
            'password': 'demo123',
            'first_name': 'Demo',
            'last_name': 'User',
            'is_superuser': False,
            'is_staff': False,
        }
    ]
    
    print("🔧 Criando usuários de teste...\n")
    
    for user_data in test_users:
        email = user_data['email']
        password = user_data.pop('password')
        
        # Criar ou atualizar usuário
        user, created = User.objects.get_or_create(
            email=email,
            defaults=user_data
        )
        
        # Sempre atualizar campos importantes
        for key, value in user_data.items():
            setattr(user, key, value)
        
        user.set_password(password)
        user.is_active = True
        user.is_email_verified = True
        user.save()
        
        print(f"✅ {'Criado' if created else 'Atualizado'}: {email}")
        print(f"   Senha: {password}")
        
        # Verificar senha
        if user.check_password(password):
            print(f"   ✅ Senha verificada")
        else:
            print(f"   ❌ Erro na senha")
        
        # Criar empresa se não for admin e não tiver empresa
        if not user.is_superuser and (not hasattr(user, 'company') or not user.company):
            try:
                plan = SubscriptionPlan.objects.filter(name='Starter').first()
                if plan:
                    company = Company.objects.create(
                        name=f'Empresa {user.first_name}',
                        owner=user,
                        subscription_plan=plan
                    )
                    print(f"   🏢 Empresa criada: {company.name}")
            except Exception as e:
                print(f"   ⚠️  Erro ao criar empresa: {e}")
        
        print()
    
    print("🎉 Usuários de teste criados com sucesso!")
    print("\n📝 Para testar:")
    print("- Frontend: http://localhost:3000/login")
    print("- Admin: http://localhost:8000/admin/")

if __name__ == "__main__":
    create_test_users()