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
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Run collectstatic with dummy environment variables
RUN DJANGO_SECRET_KEY="dummy-key-for-collectstatic" \
    DJANGO_SETTINGS_MODULE=core.settings.production \
    DATABASE_URL="postgres://dummy:dummy@dummy:5432/dummy" \
    python manage.py collectstatic --noinput || true

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Railway sets PORT dynamically
EXPOSE 8000

# Use entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]