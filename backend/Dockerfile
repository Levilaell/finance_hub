FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY backend/ /app/

# Make scripts executable
RUN chmod +x /app/startup.sh /app/fix_database.py 2>/dev/null || true

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs /keys

# Create keys directory with proper permissions for appuser
RUN chown -R 1000:1000 /keys && chmod 755 /keys

# Run collectstatic with dummy environment variables
RUN DJANGO_COLLECT_STATIC=1 \
    DJANGO_SECRET_KEY="dummy-key-for-collectstatic" \
    DJANGO_SETTINGS_MODULE=core.settings.production \
    DATABASE_URL="postgres://dummy:dummy@dummy:5432/dummy" \
    python manage.py collectstatic --noinput || true

# Copy entrypoint script to root directory
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Railway sets PORT dynamically
EXPOSE 8000

# Use entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]