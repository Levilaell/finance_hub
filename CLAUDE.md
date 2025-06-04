# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Caixa Digital is a top-tier financial SaaS for Brazilian SMEs. It's a full-stack application with Django REST backend and Next.js frontend, focusing on bank account integration, financial management, and reporting.

## Architecture

**Backend (Django REST API):**
- Custom user model in `apps.authentication.User`
- Core apps: authentication, companies, banking, categories, reports, notifications, payments
- Banking integrations: Belvo (primary), Pluggy (deprecated)
- Async processing: Celery with Redis
- Real-time features: Django Channels with WebSockets
- Multi-environment settings: base, development, production, test

**Frontend (Next.js 14):**
- App Router with TypeScript
- State management: Zustand
- Data fetching: TanStack Query
- UI: Tailwind CSS + Radix UI components
- Form handling: React Hook Form + Zod validation

**Key Integrations:**
- Banking: Belvo API for bank connections (replacing Pluggy)
- Payments: Stripe and MercadoPago
- Notifications: Email + WebSocket real-time updates
- Report generation: ReportLab + XlsxWriter

## Development Commands

**Backend (from /backend directory):**
```bash
# Install dependencies
pip install -r requirements.txt

# Database operations
python manage.py migrate
python manage.py makemigrations
python manage.py collectstatic

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser

# Management commands
python manage.py create_default_categories
python manage.py create_bank_providers
python manage.py create_subscription_plans

# Celery worker (separate terminal)
celery -A core worker -l info

# Celery beat scheduler (separate terminal)
celery -A core beat -l info
```

**Frontend (from /frontend directory):**
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Environment Setup

**Required Backend Environment Variables:**
- `SECRET_KEY`: Django secret key
- `DEBUG`: True/False
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL settings
- `REDIS_URL`: Redis connection string
- `BELVO_SECRET_ID`, `BELVO_SECRET_PASSWORD`: Belvo API credentials
- `FIELD_ENCRYPTION_KEY`: Field-level encryption key for sensitive data
- `OPENAI_API_KEY`: For AI-powered features

**Frontend Environment:**
- API endpoints configured to connect to Django backend on localhost:8000

## Key Security Features

- Field-level encryption for sensitive banking data
- JWT authentication with short-lived tokens (15min access, 1 day refresh)
- Rate limiting and IP whitelisting
- Comprehensive audit logging
- CORS protection
- Custom security middleware stack

## Banking Integration Flow

1. User initiates bank connection via Belvo Connect widget
2. Frontend receives connection token and sends to backend
3. Backend validates and stores bank connection
4. Async sync service fetches accounts and transactions
5. Data is cached and made available through REST API
6. Real-time updates via WebSocket notifications

## Testing Strategy

Backend tests located in `apps/{app_name}/tests/`
Frontend components and hooks should include unit tests
Use Django's built-in test framework for backend testing