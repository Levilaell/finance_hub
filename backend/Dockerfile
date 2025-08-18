# Stage 1: Builder
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /build

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Static files builder
FROM python:3.11-slim AS static-builder

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy Django project
COPY backend/ /app/

# Collect static files
RUN DJANGO_SECRET_KEY="build-key" \
    DJANGO_SETTINGS_MODULE=core.settings.production \
    DATABASE_URL="sqlite:///tmp/db.sqlite3" \
    DJANGO_COLLECT_STATIC=1 \
    python manage.py collectstatic --noinput

# Stage 3: Final production image
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    curl \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    DJANGO_SETTINGS_MODULE=core.settings.production

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser backend/ /app/

# Copy static files from static-builder
COPY --from=static-builder --chown=appuser:appuser /app/staticfiles /app/staticfiles

# Create necessary directories
RUN mkdir -p /app/media /app/logs /keys && \
    chown -R appuser:appuser /app /keys

# Make start.sh executable
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health/ || exit 1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start command
CMD ["/bin/bash", "/app/start.sh"]