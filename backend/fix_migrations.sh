#!/bin/bash
set -e

echo "🔧 Fixing Database Migrations"
echo "================================"

# This script handles the migration order issue

echo "Step 1: Checking current migration state..."
python manage.py showmigrations banking || true

echo ""
echo "Step 2: Faking banking.0001_initial (table already exists in schema)..."
python manage.py migrate banking 0001 --fake || true

echo ""
echo "Step 3: Running remaining migrations..."
python manage.py migrate --noinput

echo ""
echo "✅ Migrations fixed successfully!"
