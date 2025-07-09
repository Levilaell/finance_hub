# Build stage
FROM python:3.11-slim as builder

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies with wheel cache
COPY requirements.txt .
RUN pip install --no-cache-dir --find-links https://wheel-index.org/simple/ -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create user for running the application
RUN useradd -m -u 1000 appuser

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health/')"

# Default command (can be overridden)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120", "core.wsgi:application"]