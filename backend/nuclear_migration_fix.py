#!/usr/bin/env python3
"""
NUCLEAR MIGRATION FIX - SOLUÇÃO DEFINITIVA IMEDIATA
Corrige TODOS os problemas de migração de TODOS os apps de uma só vez
Uso: python nuclear_migration_fix.py
"""

import os
import sys
import django
from pathlib import Path
from django.db import connection, transaction

# Setup Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

def setup_django():
    """Configura Django"""
    try:
        django.setup()
        print("✅ Django configurado")
        return True
    except Exception as e:
        print(f"❌ Erro Django: {e}")
        return False

def nuclear_fix():
    """Aplica a correção nuclear - resolve TODOS os problemas"""
    print("🚀 INICIANDO NUCLEAR MIGRATION FIX")
    print("="*50)
    
    fixes = [
        {
            'name': 'Remove companies.0009 duplicada',
            'sql': "DELETE FROM django_migrations WHERE app = 'companies' AND name = '0009_add_early_access';",
            'description': 'Remove migração 0009 que duplica campos da 0008'
        },
        {
            'name': 'Corrige banking.0008 timestamp', 
            'sql': "UPDATE django_migrations SET applied = '2025-07-31 02:00:00+00:00' WHERE app = 'banking' AND name = '0008_delete_consent';",
            'description': 'Ajusta timestamp para depois da 0007'
        },
        {
            'name': 'Remove reports migrations inconsistentes',
            'sql': """DELETE FROM django_migrations WHERE app = 'reports' AND name IN (
                '0002_alter_aianalysis_options_and_more',
                '0003_aianalysistemplate_aianalysis', 
                '0005_fix_inconsistent_history'
            );""",
            'description': 'Remove migrações com timestamp incorreto'
        },
        {
            'name': 'Reaplica reports na ordem correta',
            'sql': """INSERT INTO django_migrations (app, name, applied) VALUES
                ('reports', '0002_alter_aianalysis_options_and_more', '2025-08-12 01:00:00+00:00'),
                ('reports', '0003_aianalysistemplate_aianalysis', '2025-08-12 02:00:00+00:00'),
                ('reports', '0005_fix_inconsistent_history', '2025-08-12 03:00:00+00:00');""",
            'description': 'Reinsere migrações na ordem cronológica correta'
        }
    ]
    
    try:
        with transaction.atomic():
            for i, fix in enumerate(fixes):
                print(f"\n{i+1}. {fix['name']}")
                print(f"   {fix['description']}")
                
                with connection.cursor() as cursor:
                    cursor.execute(fix['sql'])
                    affected = cursor.rowcount if hasattr(cursor, 'rowcount') else 'N/A'
                    print(f"   ✅ Executado (afetou {affected} registros)")
        
        print("\n🎯 NUCLEAR FIX APLICADO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO durante aplicação: {e}")
        return False

def validate_fix():
    """Valida se o fix foi aplicado corretamente"""
    print("\n🔍 VALIDAÇÃO PÓS-FIX")
    print("="*30)
    
    validation_queries = [
        {
            'name': 'Problemas de ordem cronológica',
            'sql': """
                WITH migration_order AS (
                    SELECT 
                        app, name, applied,
                        ROW_NUMBER() OVER (PARTITION BY app ORDER BY name) as file_order,
                        ROW_NUMBER() OVER (PARTITION BY app ORDER BY applied) as time_order
                    FROM django_migrations 
                    WHERE app IN ('companies', 'banking', 'reports')
                )
                SELECT COUNT(*) as problems
                FROM migration_order 
                WHERE file_order != time_order
            """,
            'expected': 0,
            'success_msg': 'Nenhum problema de ordem encontrado',
            'error_msg': 'Ainda existem problemas de ordem'
        },
        {
            'name': 'Migração companies.0009 removida',
            'sql': "SELECT COUNT(*) FROM django_migrations WHERE app = 'companies' AND name = '0009_add_early_access'",
            'expected': 0,
            'success_msg': 'Migração 0009 removida com sucesso',
            'error_msg': 'Migração 0009 ainda existe'
        },
        {
            'name': 'Reports migrations na ordem correta',
            'sql': """
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'reports' 
                AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis', '0005_fix_inconsistent_history')
            """,
            'expected': 3,
            'success_msg': 'Reports migrations reaplicadas',
            'error_msg': 'Reports migrations não reaplicadas corretamente'
        }
    ]
    
    all_ok = True
    
    try:
        with connection.cursor() as cursor:
            for validation in validation_queries:
                cursor.execute(validation['sql'])
                result = cursor.fetchone()[0]
                
                if result == validation['expected']:
                    print(f"✅ {validation['name']}: {validation['success_msg']}")
                else:
                    print(f"❌ {validation['name']}: {validation['error_msg']} (resultado: {result})")
                    all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False

def show_final_status():
    """Mostra o status final das migrações"""
    print("\n📋 STATUS FINAL DAS MIGRAÇÕES")
    print("="*40)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, COUNT(*) as total_migrations
                FROM django_migrations 
                WHERE app IN ('companies', 'banking', 'reports', 'authentication', 'ai_insights', 'audit', 'notifications', 'payments')
                GROUP BY app
                ORDER BY app
            """)
            
            results = cursor.fetchall()
            total_migrations = 0
            
            for app, count in results:
                print(f"   📦 {app}: {count} migrações")
                total_migrations += count
            
            print(f"\n   📊 TOTAL: {total_migrations} migrações")
            
            # Verifica se todas as migrações necessárias existem
            cursor.execute("""
                SELECT 
                    CASE WHEN COUNT(*) = 3 THEN '✅ OK' ELSE '❌ PROBLEMA' END as companies_early_access,
                    (SELECT CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ PROBLEMA' END 
                     FROM information_schema.tables WHERE table_name = 'early_access_invites') as invites_table
                FROM information_schema.columns 
                WHERE table_name = 'companies' 
                AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
            """)
            
            schema_check = cursor.fetchone()
            print(f"\n   🏗️  Schema early_access: {schema_check[0]}")
            print(f"   🏗️  Tabela invites: {schema_check[1]}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")

def main():
    """Função principal"""
    print("💥 NUCLEAR MIGRATION FIX - SOLUÇÃO DEFINITIVA")
    print("="*60)
    print("⚠️  ATENÇÃO: Esta operação modifica diretamente o banco de produção!")
    print("⚠️  Certifique-se de ter backup antes de executar.")
    print()
    
    # Confirma execução
    if 'FORCE' not in os.environ:
        confirm = input("Digite 'NUCLEAR' para confirmar a execução: ")
        if confirm.upper() != 'NUCLEAR':
            print("❌ Execução cancelada")
            return False
    
    # Setup
    if not setup_django():
        return False
    
    # Aplica correções
    if not nuclear_fix():
        return False
    
    # Valida correções
    if not validate_fix():
        print("⚠️  Alguns problemas ainda existem, mas o fix principal foi aplicado")
    
    # Status final
    show_final_status()
    
    print("\n" + "="*60)
    print("🎯 NUCLEAR FIX CONCLUÍDO!")
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("   1. Execute: python manage.py migrate")
    print("   2. Teste o sistema: python manage.py check")
    print("   3. Faça deploy: git push railway main")
    print()
    print("💡 O sistema agora deve fazer deploy sem erros de migração")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)