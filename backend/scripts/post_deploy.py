#!/usr/bin/env python3
"""
Post-Deploy Validation Script
Executa automaticamente após migrações no Railway
"""

import os
import sys
import django
from django.db import connection, transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def refresh_collation():
    """Atualiza collation version para evitar warnings"""
    try:
        with connection.cursor() as cursor:
            cursor.execute('ALTER DATABASE railway REFRESH COLLATION VERSION;')
            print('✅ Collation version refreshed')
            return True
    except Exception as e:
        print(f'⚠️ Could not refresh collation: {e}')
        return False

def validate_critical_tables():
    """Verifica se tabelas críticas existem e têm campos esperados"""
    critical_tables = {
        'companies': ['is_early_access', 'early_access_expires_at'],
        'notifications': ['event', 'event_key'],
        'early_access_invites': ['invite_code', 'expires_at'],
        'transactions': ['account_id', 'company_id']
    }
    
    try:
        with connection.cursor() as cursor:
            for table, fields in critical_tables.items():
                # Check table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, [table])
                
                if not cursor.fetchone()[0]:
                    print(f'❌ Table {table} missing')
                    continue
                
                # Check critical fields
                missing_fields = []
                for field in fields:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = %s AND column_name = %s
                        );
                    """, [table, field])
                    
                    if not cursor.fetchone()[0]:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f'⚠️ Table {table} missing fields: {missing_fields}')
                else:
                    print(f'✅ Table {table} OK')
                    
        return True
    except Exception as e:
        print(f'❌ Validation error: {e}')
        return False

def main():
    """Executa todas as validações pós-deploy"""
    print('🚀 POST-DEPLOY VALIDATION')
    print('=' * 30)
    
    checks = [
        ('Refresh Collation', refresh_collation),
        ('Validate Tables', validate_critical_tables),
    ]
    
    success_count = 0
    for name, check_func in checks:
        try:
            if check_func():
                success_count += 1
        except Exception as e:
            print(f'❌ {name} failed: {e}')
    
    print(f'\n📊 Result: {success_count}/{len(checks)} checks passed')
    
    if success_count == len(checks):
        print('✅ DEPLOY VALIDATION SUCCESSFUL')
        return True
    else:
        print('⚠️ SOME ISSUES DETECTED')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)