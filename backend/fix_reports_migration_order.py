#!/usr/bin/env python3
"""
CORREÇÃO DE ORDEM DAS MIGRAÇÕES - APP REPORTS
Corrige InconsistentMigrationHistory: reports.0003 antes de reports.0002
"""

import os
import sys
import django
from django.db import connection, transaction
from datetime import datetime

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

def fix_reports_migration_order():
    """Corrige a ordem das migrações do app reports"""
    
    print("🔍 Verificando estado atual das migrações do app reports...")
    
    with connection.cursor() as cursor:
        # 1. Verificar estado atual
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'reports' AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis')
            ORDER BY applied
        """)
        
        current_state = cursor.fetchall()
        print("\n📊 Estado atual:")
        for app, name, applied in current_state:
            print(f"  {app} | {name} | {applied}")
        
        if not current_state:
            print("❌ Migrações não encontradas no banco!")
            return False
        
        # 2. Verificar se realmente precisa da correção
        migration_data = {row[1]: row[2] for row in current_state}
        
        if '0002_alter_aianalysis_options_and_more' not in migration_data:
            print("❌ Migração 0002 não encontrada!")
            return False
            
        if '0003_aianalysistemplate_aianalysis' not in migration_data:
            print("❌ Migração 0003 não encontrada!")
            return False
        
        timestamp_0002 = migration_data['0002_alter_aianalysis_options_and_more']
        timestamp_0003 = migration_data['0003_aianalysistemplate_aianalysis']
        
        if timestamp_0002 < timestamp_0003:
            print("✅ Migrações já estão na ordem correta!")
            return True
        
        print(f"⚠️  PROBLEMA DETECTADO:")
        print(f"   0002: {timestamp_0002}")
        print(f"   0003: {timestamp_0003}")
        print(f"   0003 está ANTES de 0002 (incorreto)")
        
        # 3. Aplicar correção
        print("\n🔧 Aplicando correção...")
        
        with transaction.atomic():
            # Corrigir 0002 para ser anterior
            cursor.execute("""
                UPDATE django_migrations 
                SET applied = %s
                WHERE app = 'reports' AND name = '0002_alter_aianalysis_options_and_more'
            """, ['2025-08-12 02:00:00+00'])
            
            # Corrigir 0003 para ser posterior
            cursor.execute("""
                UPDATE django_migrations 
                SET applied = %s
                WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis'
            """, ['2025-08-12 02:30:00+00'])
            
            print("✅ Timestamps atualizados com sucesso!")
        
        # 4. Verificar correção
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'reports' AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis')
            ORDER BY applied
        """)
        
        corrected_state = cursor.fetchall()
        print("\n📊 Estado após correção:")
        for app, name, applied in corrected_state:
            print(f"  ✅ {app} | {name} | {applied}")
        
        # 5. Validar todas as migrações do reports
        print("\n🔍 Validando todas as migrações do app reports...")
        cursor.execute("""
            SELECT name, applied 
            FROM django_migrations 
            WHERE app = 'reports'
            ORDER BY applied
        """)
        
        all_reports = cursor.fetchall()
        print("📋 Ordem completa das migrações reports:")
        for name, applied in all_reports:
            print(f"  📄 {name} | {applied}")
        
        return True

if __name__ == "__main__":
    try:
        print("🚀 INICIANDO CORREÇÃO DE MIGRAÇÕES - APP REPORTS")
        print("=" * 60)
        
        success = fix_reports_migration_order()
        
        if success:
            print("\n🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
            print("✅ As migrações do app reports estão agora na ordem correta")
            print("\n📝 Próximos passos:")
            print("1. Fazer deploy novamente")
            print("2. Verificar se não há mais erros de InconsistentMigrationHistory")
        else:
            print("\n❌ CORREÇÃO FALHOU!")
            print("Verifique os logs acima para detalhes")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 ERRO DURANTE A CORREÇÃO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)