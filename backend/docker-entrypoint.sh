#!/bin/bash

# Wait for database
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Database started"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@caixadigital.com.br', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

# Load initial data
echo "Loading initial data..."
python manage.py create_default_categories || echo "Categories already exist"
python manage.py create_bank_providers || echo "Bank providers already exist"
python manage.py create_subscription_plans || echo "Subscription plans already exist"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django server..."
exec "$@"