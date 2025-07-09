#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
    sleep 0.1
done
echo "PostgreSQL started"

echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    sleep 0.1
done
echo "Redis started"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create default categories if they don't exist
echo "Creating default categories..."
python manage.py create_default_categories || true

# Create superuser if it doesn't exist (only in development)
if [ "$DJANGO_SETTINGS_MODULE" = "core.settings.development" ] && [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        username='$SUPERUSER_EMAIL',
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD',
        first_name='Admin',
        last_name='Caixa Digital'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

# Execute the main command
exec "$@"