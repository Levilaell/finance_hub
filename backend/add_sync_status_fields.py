#!/usr/bin/env python
"""
Adicionar campos sync_status manualmente
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        # Verificar se os campos existem
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bank_accounts' 
            AND column_name IN ('sync_status', 'sync_error_message')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Colunas existentes: {existing_columns}")
        
        # Adicionar sync_status se não existir
        if 'sync_status' not in existing_columns:
            print("Adicionando coluna sync_status...")
            cursor.execute("""
                ALTER TABLE bank_accounts 
                ADD COLUMN sync_status VARCHAR(30) DEFAULT 'active'
            """)
            print("✅ Coluna sync_status adicionada")
        else:
            print("ℹ️ Coluna sync_status já existe")
        
        # Adicionar sync_error_message se não existir
        if 'sync_error_message' not in existing_columns:
            print("Adicionando coluna sync_error_message...")
            cursor.execute("""
                ALTER TABLE bank_accounts 
                ADD COLUMN sync_error_message TEXT DEFAULT ''
            """)
            print("✅ Coluna sync_error_message adicionada")
        else:
            print("ℹ️ Coluna sync_error_message já existe")
        
        connection.commit()
        print("\n✅ Campos adicionados com sucesso!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()