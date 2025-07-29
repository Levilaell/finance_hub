# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Finance Hub (CaixaHub) is a financial management SaaS platform with a Django REST API backend and Next.js frontend. The platform integrates with Pluggy API for Open Banking connections, allowing users to sync bank accounts, categorize transactions, generate reports, and manage subscriptions.

## Development Commands

### Backend (Django)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Run specific app tests
python manage.py test apps.banking.tests
python manage.py test apps.authentication.tests

# Run Celery worker (for async tasks)
celery -A core worker -l info

# Run Celery beat (for scheduled tasks)
celery -A core beat -l info

# Static files collection (production)
python manage.py collectstatic --noinput
```

### Frontend (Next.js)

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run linter
npm run lint
```

### Docker

```bash
# Start all services
docker-compose up -d

# Start with development profile (includes pgAdmin and Mailhog)
docker-compose --profile dev up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute Django commands in container
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

## Architecture

### Backend Structure

The Django backend follows a modular app structure:

- **apps/authentication**: Custom user model, JWT authentication, email verification
- **apps/banking**: Pluggy API integration for Open Banking, account/transaction sync
- **apps/categories**: Transaction categorization system
- **apps/companies**: Multi-tenant company management, subscription billing
- **apps/reports**: Financial reports and AI-powered insights (OpenAI integration)
- **apps/notifications**: WebSocket notifications via Django Channels
- **apps/payments**: Stripe and MercadoPago payment processing

Key integrations:
- **Pluggy API**: Open Banking connections (OAuth flow, webhook processing)
- **Stripe**: Subscription billing and payment processing
- **OpenAI**: AI-powered financial insights and report generation
- **Celery**: Async task processing (bank sync, report generation)
- **Redis**: Caching and Celery broker
- **PostgreSQL**: Primary database

### Frontend Structure

Next.js 14 app with App Router:

- **app/(auth)**: Authentication pages (login, register, password reset)
- **app/(dashboard)**: Protected dashboard pages
- **components**: Reusable UI components using shadcn/ui
- **hooks**: Custom React hooks for data fetching and state management
- **services**: API client services for backend communication
- **store**: Zustand stores for global state management

Key libraries:
- **React Query (TanStack Query)**: Server state management and caching
- **Zustand**: Client state management
- **shadcn/ui**: Component library built on Radix UI
- **React Hook Form + Zod**: Form handling and validation
- **Pluggy Connect SDK**: Bank connection widget integration

## Critical Patterns

### Authentication Flow
- JWT tokens stored in httpOnly cookies (backend) and localStorage (frontend)
- Access token lifetime: 60 minutes, Refresh token: 7 days
- Automatic token refresh on 401 responses
- Email verification required for new accounts

### Bank Connection Flow
1. Frontend requests Connect Token from backend
2. Backend generates token via Pluggy API
3. Frontend opens Pluggy Connect widget
4. User authenticates with bank (OAuth or credentials)
5. Widget returns itemId to frontend
6. Frontend creates BankConnection via backend API
7. Backend starts async sync task via Celery
8. Webhook notifications trigger real-time updates

### Multi-tenancy
- Company-based isolation using Django's auth system
- Users can belong to multiple companies
- All queries filtered by user's active company
- Subscription limits enforced at company level

### API Patterns
- RESTful endpoints with consistent naming
- Django REST Framework with JWT authentication
- Pagination on list endpoints (default 20 items)
- Throttling configured per endpoint type
- Custom exception handler for consistent error responses

## Environment Variables

Backend (.env):
```
DJANGO_SETTINGS_MODULE=core.settings.development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
PLUGGY_CLIENT_ID=your-pluggy-id
PLUGGY_CLIENT_SECRET=your-pluggy-secret
PLUGGY_WEBHOOK_SECRET=your-webhook-secret
STRIPE_SECRET_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook
OPENAI_API_KEY=your-openai-key
```

Frontend (.env.local):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_PLUGGY_CONNECT_URL=https://connect.pluggy.ai
```

## Testing Approach

### Backend
- Unit tests for models and serializers
- Integration tests for API endpoints
- Mock external APIs (Pluggy, Stripe, OpenAI)
- Use Django's TestCase and APITestCase

### Frontend
- Jest + React Testing Library for component tests
- Mock API responses for service tests
- Test user interactions and state changes
- Coverage targets: 80% for critical paths

## Common Development Tasks

### Adding a New Bank Connection
1. Use management command to test Pluggy auth: `python manage.py test_pluggy_auth`
2. Sync connectors: `python manage.py sync_pluggy_connectors`
3. Test webhook locally using ngrok or similar

### Debugging Subscription Issues
1. Check user's company subscription: `python manage.py check_user_companies <email>`
2. View usage counters: `python manage.py check_usage_api`
3. Fix counter issues: `python manage.py fix_all_counters`

### Performance Monitoring
- Django Debug Toolbar available in development
- Sentry integration for error tracking
- Custom logging configuration in core/settings/logging.py
- Separate log files: django.log, banking.log, pluggy.log, errors.log