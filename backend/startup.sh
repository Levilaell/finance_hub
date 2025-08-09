#!/bin/sh
set -e

# Use PORT environment variable, default to 8000 if not set
export PORT=${PORT:-8000}

# Ensure we're using production settings
export DJANGO_ENV=${DJANGO_ENV:-production}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings.production}

echo "🚀 Starting Django server on port $PORT"
echo "📊 Using settings: $DJANGO_SETTINGS_MODULE"

# Try to fix migration issues directly with Python
python - << 'EOF'
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

import django
django.setup()

from django.db import connection
print("🔧 Attempting to fix migration issues...")

try:
    with connection.cursor() as cursor:
        # Check if the problematic migration exists
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'reports' 
            AND name = '0003_aianalysistemplate_aianalysis'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("Found problematic migration, fixing...")
            
            # Add the missing dependency
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('reports', '0002_alter_aianalysis_options_and_more', NOW())
                ON CONFLICT DO NOTHING
            """)
            print("✅ Migration dependency fixed")
            
except Exception as e:
    print(f"⚠️ Could not fix migrations: {e}")

# Now ensure critical tables exist
print("📊 Ensuring critical tables...")

try:
    with connection.cursor() as cursor:
        # Create users table if missing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                password VARCHAR(128) NOT NULL,
                last_login TIMESTAMP WITH TIME ZONE,
                is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                username VARCHAR(150) UNIQUE NOT NULL,
                email VARCHAR(254) NOT NULL,
                first_name VARCHAR(150),
                last_name VARCHAR(150),
                is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                cpf VARCHAR(14),
                phone VARCHAR(20),
                date_of_birth DATE,
                two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                two_factor_secret VARCHAR(32),
                backup_codes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Users table ensured")
        
        # Create companies table if missing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                slug VARCHAR(50) UNIQUE NOT NULL,
                cnpj VARCHAR(18),
                email VARCHAR(254),
                phone VARCHAR(20),
                website VARCHAR(200),
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                owner_id INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Companies table ensured")
        
except Exception as e:
    print(f"⚠️ Could not create tables: {e}")

print("✅ Startup fixes completed")
EOF

# Now try migrations again
echo "🔄 Attempting migrations..."
python manage.py migrate --noinput || echo "⚠️ Some migrations failed but continuing..."

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start gunicorn
echo "✅ Starting Gunicorn server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-level info