# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Finance Hub (CaixaHub) is a financial management SaaS platform with Django backend and Next.js frontend. The platform integrates with financial institutions through Pluggy API for Open Banking connectivity.

## Key Architecture

### Backend (Django)
- **Framework**: Django 5.0 with Django REST Framework
- **Database**: PostgreSQL (production), SQLite (testing)
- **Task Queue**: Celery with Redis
- **Real-time**: Django Channels with Redis
- **Authentication**: JWT via djangorestframework-simplejwt
- **Payment Processing**: Stripe and MercadoPago
- **Banking Integration**: Pluggy API for Open Banking

### Frontend (Next.js)
- **Framework**: Next.js 14 with TypeScript
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **UI Components**: Radix UI with Tailwind CSS
- **Banking Connect**: Pluggy Connect SDK
- **Form Handling**: React Hook Form with Zod validation

## Common Development Commands

### Backend
```bash
# Run development server
cd backend
python manage.py runserver

# Run with specific settings
python manage.py runserver --settings=core.settings.development

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Run tests
python manage.py test

# Run Celery worker
celery -A core worker -l info

# Run Celery beat (scheduler)
celery -A core beat -l info

# Create superuser
python manage.py createsuperuser

# Sync Pluggy connectors
python manage.py sync_pluggy_connectors

# Seed subscription plans
python manage.py seed_plans
```

### Frontend
```bash
# Run development server
cd frontend
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint
```

### Docker
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Start with development profile (includes pgAdmin, Mailhog)
docker-compose --profile dev up

# Rebuild containers
docker-compose build

# Run migrations in container
docker-compose exec backend python manage.py migrate
```

## Project Structure

### Key Backend Apps
- **authentication**: Custom user model, JWT auth, email verification
- **companies**: Multi-tenant companies, subscription plans, usage tracking
- **banking**: Pluggy integration, bank accounts, transactions
- **categories**: Transaction categorization with AI assistance
- **reports**: Financial reports, AI insights
- **notifications**: WebSocket notifications, email service
- **payments**: Stripe/MercadoPago webhooks, subscription management

### Frontend Structure
- **app/(auth)**: Authentication pages (login, register, forgot password)
- **app/(dashboard)**: Main application pages
- **components/banking**: Banking-specific components (Pluggy Connect)
- **services**: API client services for each backend app
- **store**: Zustand stores for auth and banking state
- **hooks**: Custom hooks including Pluggy Connect integration

## Pluggy Integration Points

The banking integration uses Pluggy API v2:
- **PluggyConnector**: Cached bank connector information
- **PluggyItem**: User's bank connection
- **BankAccount**: Individual bank accounts
- **Transaction**: Financial transactions with categorization

Key Pluggy workflows:
1. User connects bank via Pluggy Connect SDK
2. Backend creates PluggyItem and syncs accounts
3. Celery tasks periodically sync transactions
4. Webhooks handle real-time updates

## Environment Variables

Backend requires:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `SECRET_KEY`: Django secret
- `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`: Pluggy API credentials
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`: Stripe API
- `OPENAI_API_KEY`: For AI features

Frontend requires:
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_PLUGGY_CLIENT_ID`: Pluggy client ID for Connect SDK

## Testing Approach

Backend uses Django's test framework:
- Unit tests in each app's `tests/` directory
- Test settings in `core/settings/test.py`
- In-memory SQLite for fast tests

Frontend uses Jest with React Testing Library:
- Test files in `__tests__/` directory
- Component tests with mocked dependencies
- Coverage reports via `npm run test:coverage`

## Important Patterns

1. **Multi-tenancy**: All models filtered by company
2. **Subscription Limits**: Check limits before operations via `companies.middleware`
3. **Async Tasks**: Heavy operations use Celery tasks
4. **Error Handling**: Custom exception handler in `core.error_handlers`
5. **API Throttling**: Rate limits configured per endpoint type
6. **Banking Sync**: Periodic Celery tasks update account balances and transactions