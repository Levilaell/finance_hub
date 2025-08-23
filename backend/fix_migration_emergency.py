#!/usr/bin/env python3
"""
CORREÇÃO EMERGENCIAL - InconsistentMigrationHistory
Execute via: railway shell && python fix_migration_emergency.py
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def fix_migration_history():
    """Corrige o histórico inconsistente de migrações"""
    print('🚨 CORREÇÃO EMERGENCIAL - InconsistentMigrationHistory')
    print('=' * 60)
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar estado atual
            print('1. 🔍 Verificando estado atual...')
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app = 'companies' 
                AND name IN ('0008_alter_resourceusage_options_and_more', '0009_add_early_access')
                ORDER BY name;
            """)
            
            current_state = cursor.fetchall()
            print('Estado atual:')
            for app, name, applied in current_state:
                print(f'  {app}.{name} - {applied}')
            
            # 2. Verificar se 0008 existe
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'companies' 
                AND name = '0008_alter_resourceusage_options_and_more';
            """)
            
            has_0008 = cursor.fetchone()[0] > 0
            
            if not has_0008:
                print('\n2. 🔧 Marcando 0008 como aplicada (fake apply)...')
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('companies', '0008_alter_resourceusage_options_and_more', NOW());
                """)
                print('✅ Migration 0008 marcada como aplicada')
            else:
                print('\n2. ✅ Migration 0008 já está aplicada')
            
            # 3. Verificar correção
            print('\n3. 🔍 Verificando correção...')
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app = 'companies' 
                AND name IN ('0008_alter_resourceusage_options_and_more', '0009_add_early_access')
                ORDER BY name;
            """)
            
            final_state = cursor.fetchall()
            print('Estado final:')
            for app, name, applied in final_state:
                print(f'  ✅ {app}.{name} - {applied}')
            
            print('\n🎯 CORREÇÃO CONCLUÍDA')
            print('Agora execute: python manage.py migrate')
            return True
            
    except Exception as e:
        print(f'❌ Erro na correção: {e}')
        return False

if __name__ == '__main__':
    success = fix_migration_history()
    if success:
        print('\n✅ Execute agora: python manage.py migrate')
    else:
        print('\n❌ Correção falhou - contate suporte')
    sys.exit(0 if success else 1)