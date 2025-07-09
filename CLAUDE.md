# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Caixa Digital is a comprehensive finance management SaaS platform designed for Brazilian small and medium enterprises (SMEs). The system integrates with Brazilian banks through Open Banking APIs (Belvo and Pluggy) to provide automated financial tracking, reporting, and management capabilities.

## Technology Stack

### Backend
- **Framework**: Django 5.0.1 with Django REST Framework 3.14.0
- **Database**: PostgreSQL with Redis for caching
- **Async Processing**: Celery with Redis broker
- **Real-time**: Django Channels for WebSocket support
- **Authentication**: JWT tokens (djangorestframework-simplejwt)
- **Payment Processing**: Stripe and MercadoPago
- **Banking Integration**: Belvo and Pluggy APIs
- **AI Integration**: OpenAI for transaction categorization

### Frontend
- **Framework**: Next.js 14.2.5 with TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Data Fetching**: React Query
- **Forms**: React Hook Form
- **UI Components**: Shadcn/ui

## Project Structure

```
finance_management/
├── backend/
│   ├── apps/
│   │   ├── authentication/    # User authentication and 2FA
│   │   ├── banking/          # Bank account integration
│   │   ├── categories/       # Transaction categorization
│   │   ├── companies/        # Multi-tenant company management
│   │   ├── notifications/    # WebSocket notifications
│   │   ├── payments/         # Subscription billing
│   │   └── reports/          # Financial report generation
│   ├── core/                 # Django settings and configuration
│   ├── media/                # User uploads
│   └── staticfiles/          # Collected static files
└── frontend/
    ├── app/                  # Next.js App Router
    ├── components/           # React components
    ├── hooks/                # Custom React hooks
    ├── lib/                  # Utilities
    ├── services/             # API services
    └── types/                # TypeScript definitions
```

## Key Features

1. **Multi-tenant Architecture**: Each company has isolated data with role-based access control
2. **Open Banking Integration**: Automated bank transaction synchronization via Belvo and Pluggy
3. **AI-Powered Categorization**: Automatic transaction categorization using OpenAI
4. **Real-time Updates**: WebSocket support for live notifications
5. **Subscription Management**: Tiered pricing (Starter, Pro, Enterprise) with Stripe/MercadoPago
6. **Brazilian Market Focus**: CNPJ validation, Brazilian banking standards support

## Development Commands

### Backend Setup and Commands

```bash
# Environment setup
cd backend
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser
python manage.py create_default_categories
python manage.py create_bank_providers
python manage.py create_subscription_plans

# Development server
python manage.py runserver

# Run tests
python manage.py test
python manage.py test apps.banking  # Test specific app

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Static files
python manage.py collectstatic --noinput

# Celery workers (ensure Redis is running)
celery -A core worker -l info
celery -A core beat -l info

# Django shell
python manage.py shell
python manage.py dbshell
```

### Frontend Setup and Commands

Note: The frontend is currently in skeleton state. Standard Next.js commands would be:

```bash
cd frontend
npm install
npm run dev      # Development server
npm run build    # Production build
npm run start    # Production server
npm run lint     # Run ESLint
npm run test     # Run tests
```

## Environment Variables

### Backend (.env)
```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=finance_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-openai-key
BELVO_SECRET_ID=your-belvo-id
BELVO_SECRET_PASSWORD=your-belvo-password
STRIPE_SECRET_KEY=your-stripe-key
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-email-password
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login (returns JWT tokens)
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/verify-email/` - Email verification
- `POST /api/auth/reset-password/` - Password reset

### Companies
- `GET /api/companies/` - List user's companies
- `POST /api/companies/` - Create new company
- `GET /api/companies/{id}/` - Company details
- `PUT /api/companies/{id}/` - Update company
- `POST /api/companies/{id}/invite/` - Invite user to company

### Banking
- `GET /api/banking/accounts/` - List bank accounts
- `POST /api/banking/connect/` - Connect new bank account
- `GET /api/banking/transactions/` - List transactions
- `POST /api/banking/sync/` - Sync bank transactions
- `GET /api/banking/providers/` - List available bank providers

### Categories
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category
- `PUT /api/transactions/{id}/categorize/` - Categorize transaction

### Reports
- `GET /api/reports/` - List reports
- `POST /api/reports/generate/` - Generate new report
- `GET /api/reports/{id}/export/` - Export report (PDF/Excel)

## Architecture Guidelines

### Backend Development
1. **Apps Structure**: Each Django app should be self-contained with its own models, views, serializers, and URLs
2. **API Design**: Follow RESTful conventions with proper HTTP methods and status codes
3. **Authentication**: All endpoints except auth require JWT token in header: `Authorization: Bearer <token>`
4. **Permissions**: Use Django's permission classes for role-based access control
5. **Database Queries**: Optimize with `select_related()` and `prefetch_related()` for foreign keys
6. **Async Tasks**: Use Celery for long-running operations (report generation, bank sync)

### Frontend Development
1. **Component Structure**: Use functional components with TypeScript
2. **State Management**: Zustand for global state, React Query for server state
3. **API Calls**: Centralize in services directory with proper error handling
4. **Authentication**: Store JWT tokens securely, implement refresh token rotation
5. **Forms**: Use React Hook Form with validation schemas
6. **Styling**: Follow TailwindCSS utility-first approach

## Security Considerations

1. **Authentication**: JWT tokens with short expiration and refresh token rotation
2. **API Security**: Rate limiting, CORS configuration, request ID tracking
3. **Data Encryption**: Sensitive bank tokens encrypted in database
4. **Multi-tenancy**: Strict data isolation between companies
5. **Input Validation**: Server-side validation for all inputs
6. **Environment Variables**: Never commit secrets, use .env files

## Testing

### Backend Testing
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Run specific app tests
python manage.py test apps.banking.tests
```

### Frontend Testing
```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Type checking
npm run type-check
```

## Common Development Tasks

### Adding a New Django App
```bash
python manage.py startapp app_name
# Add to INSTALLED_APPS in settings
# Create models, views, serializers
# Add URLs to main urlpatterns
```

### Creating Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Connecting to a New Bank Provider
1. Add provider credentials to environment variables
2. Create provider model instance via admin or command
3. Implement provider-specific API integration in banking app
4. Test connection and transaction sync

### Adding a New API Endpoint
1. Create viewset in `apps/<app>/views.py`
2. Create serializer in `apps/<app>/serializers.py`
3. Add URL pattern in `apps/<app>/urls.py`
4. Add tests in `apps/<app>/tests/`
5. Document endpoint in API documentation

## Troubleshooting

### Common Issues
1. **Redis Connection Error**: Ensure Redis server is running (`redis-server`)
2. **Database Connection**: Check PostgreSQL is running and credentials are correct
3. **CORS Errors**: Verify frontend URL is in CORS_ALLOWED_ORIGINS
4. **WebSocket Connection**: Check Redis is running and CHANNEL_LAYERS configuration
5. **Bank Sync Failures**: Verify API credentials and check provider status

### Debug Mode
- Set `DEBUG=True` in .env for detailed error messages
- Use Django Debug Toolbar for query optimization
- Check logs in development for detailed tracebacks

## Deployment Checklist

1. Set `DEBUG=False` in production
2. Configure proper `ALLOWED_HOSTS`
3. Set up SSL certificates
4. Configure production database (PostgreSQL)
5. Set up Redis for caching and Celery
6. Configure email service for notifications
7. Set up file storage (S3 for media files)
8. Configure Sentry for error monitoring
9. Set up proper backup strategy
10. Configure monitoring and logging