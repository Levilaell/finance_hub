#!/usr/bin/env python3
"""
VALIDAÇÃO PREVENTIVA DE TODAS AS MIGRAÇÕES
Identifica potenciais problemas de InconsistentMigrationHistory antes do deploy
"""

import os
import sys
import django
from django.db import connection
from datetime import datetime

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

def get_migration_dependencies():
    """Identifica dependências entre migrações baseado no padrão numérico"""
    dependencies = {}
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app IN ('companies', 'banking', 'authentication', 'reports', 'payments', 'ai_insights', 'notifications', 'audit')
            ORDER BY app, name
        """)
        
        all_migrations = cursor.fetchall()
        
        for app, name, applied in all_migrations:
            if app not in dependencies:
                dependencies[app] = []
            dependencies[app].append((name, applied))
    
    return dependencies

def check_sequential_order(app, migrations):
    """Verifica se migrações numericamente sequenciais estão em ordem cronológica"""
    problems = []
    
    # Ordenar por nome (que deve ser sequencial)
    migrations_by_name = sorted(migrations, key=lambda x: x[0])
    
    # Verificar se timestamps estão em ordem
    for i in range(len(migrations_by_name) - 1):
        current_name, current_time = migrations_by_name[i]
        next_name, next_time = migrations_by_name[i + 1]
        
        if current_time > next_time:
            problems.append({
                'app': app,
                'current': (current_name, current_time),
                'next': (next_name, next_time),
                'issue': f"Migration {current_name} is applied AFTER {next_name} (timestamp order incorrect)"
            })
    
    return problems

def validate_all_migrations():
    """Valida ordem de todas as migrações"""
    
    print("🔍 VALIDAÇÃO PREVENTIVA DE MIGRAÇÕES")
    print("=" * 60)
    
    dependencies = get_migration_dependencies()
    all_problems = []
    
    for app, migrations in dependencies.items():
        print(f"\n📱 Validando app: {app}")
        print(f"   Migrações encontradas: {len(migrations)}")
        
        problems = check_sequential_order(app, migrations)
        
        if problems:
            print(f"   ⚠️  Problemas encontrados: {len(problems)}")
            for problem in problems:
                print(f"      ❌ {problem['issue']}")
                all_problems.append(problem)
        else:
            print(f"   ✅ Todas as migrações estão em ordem correta")
    
    print(f"\n📊 RESUMO DA VALIDAÇÃO")
    print("=" * 40)
    print(f"Apps validados: {len(dependencies)}")
    print(f"Problemas encontrados: {len(all_problems)}")
    
    if all_problems:
        print(f"\n💥 PROBLEMAS IDENTIFICADOS:")
        for i, problem in enumerate(all_problems, 1):
            print(f"{i}. App '{problem['app']}':")
            print(f"   {problem['current'][0]} ({problem['current'][1]})")
            print(f"   {problem['next'][0]} ({problem['next'][1]})")
            print(f"   Issue: {problem['issue']}\n")
        
        print("🔧 SUGESTÕES DE CORREÇÃO:")
        for problem in all_problems:
            app = problem['app']
            current_name = problem['current'][0]
            next_name = problem['next'][0]
            
            print(f"\n-- Corrigir app {app}")
            print(f"UPDATE django_migrations SET applied = '2025-08-12 XX:00:00+00' WHERE app = '{app}' AND name = '{current_name}';")
            print(f"UPDATE django_migrations SET applied = '2025-08-12 XX:30:00+00' WHERE app = '{app}' AND name = '{next_name}';")
        
        return False
    else:
        print("🎉 Todas as migrações estão em ordem correta!")
        return True

def show_migration_summary():
    """Mostra resumo de todas as migrações por app"""
    print("\n📋 RESUMO COMPLETO DAS MIGRAÇÕES")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, COUNT(*) as total
            FROM django_migrations 
            WHERE app IN ('companies', 'banking', 'authentication', 'reports', 'payments', 'ai_insights', 'notifications', 'audit')
            GROUP BY app
            ORDER BY app
        """)
        
        summary = cursor.fetchall()
        
        for app, total in summary:
            print(f"📱 {app}: {total} migrações")

if __name__ == "__main__":
    try:
        is_valid = validate_all_migrations()
        show_migration_summary()
        
        if is_valid:
            print(f"\n✅ VALIDAÇÃO PASSOU - Todas as migrações estão corretas")
            print("🚀 Deploy pode prosseguir com segurança")
        else:
            print(f"\n❌ VALIDAÇÃO FALHOU - Problemas encontrados")
            print("🔧 Execute as correções sugeridas antes do deploy")
            
    except Exception as e:
        print(f"\n💥 ERRO NA VALIDAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)