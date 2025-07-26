import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check if the column name is correct
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'pluggy_connectors' 
        AND column_name IN ('pluggy_id', 'True', '1')
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("Found columns:", columns)
    
    # If there's a column named 'True' or '1', rename it to 'pluggy_id'
    for col in columns:
        col_name = col[0]
        if col_name in ['True', '1']:
            print(f"Renaming column '{col_name}' to 'pluggy_id'")
            cursor.execute(f'ALTER TABLE pluggy_connectors RENAME COLUMN "{col_name}" TO pluggy_id')