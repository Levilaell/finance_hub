# Caixa Digital - Finance Management System

## Project Overview

Caixa Digital is a comprehensive financial management system designed for Brazilian businesses. It provides multi-tenant support, open banking integrations, transaction categorization, and financial reporting capabilities.

## Technology Stack

### Backend
- **Framework**: Django 5.0.1 with Django REST Framework
- **Database**: PostgreSQL with Redis for caching
- **Task Queue**: Celery with Redis broker
- **Real-time**: Django Channels for WebSocket support
- **Authentication**: JWT (djangorestframework-simplejwt) with 2FA support
- **File Storage**: AWS S3 compatible (django-storages)
- **Monitoring**: Sentry integration

### Frontend
- **Framework**: Next.js 14.2.5 with TypeScript
- **Styling**: TailwindCSS with Radix UI components
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React and Heroicons
- **Notifications**: React Hot Toast and Sonner

### Banking Integrations
- **Belvo**: Open Banking API for bank connections
- **Pluggy**: Alternative banking data provider
- **Sandbox**: Mock banking data for development

## Project Structure

```
finance_management/
├── backend/
│   ├── apps/
│   │   ├── authentication/     # User auth, 2FA, JWT
│   │   ├── banking/           # Bank accounts, transactions
│   │   ├── categories/        # Transaction categorization
│   │   ├── companies/         # Multi-tenant support
│   │   ├── notifications/     # Email & WebSocket notifications
│   │   ├── payments/          # Payment processing
│   │   └── reports/           # Financial reports generation
│   ├── core/                  # Django settings and configuration
│   ├── templates/             # Email templates
│   └── manage.py
├── frontend/
│   ├── app/                   # Next.js app directory
│   │   ├── (auth)/           # Authentication pages
│   │   ├── (dashboard)/      # Main application pages
│   │   └── banking/          # Banking integration pages
│   ├── components/           # Reusable React components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API service layer
│   ├── store/               # Zustand stores
│   └── types/               # TypeScript type definitions
└── docs/                    # Documentation (deleted)
```

## Key Features

### Authentication & Security
- Custom User model with email-based authentication
- JWT token authentication with refresh tokens
- Two-factor authentication (2FA) with TOTP
- Backup codes for 2FA recovery
- Email verification system
- Password reset functionality
- Rate limiting on sensitive endpoints

### Banking Integration
- **Belvo Integration**:
  - Create links to financial institutions
  - Fetch accounts and balances
  - Retrieve transaction history
  - Automatic transaction categorization
  
- **Pluggy Integration**:
  - Alternative banking data provider
  - Item-based connection model
  - Transaction synchronization
  
- **Sandbox Mode**:
  - Mock banking data for testing
  - Simulated transactions and accounts

### Transaction Management
- Automatic transaction import from connected banks
- Manual transaction entry
- Transaction categorization with AI-powered suggestions
- Duplicate detection
- Transaction search and filtering
- Bulk operations support

### Financial Features
- **Budgets**: Category-based budget tracking
- **Goals**: Financial goal setting and monitoring
- **Reports**: 
  - Income/expense reports
  - Cash flow analysis
  - Category breakdowns
  - Export to PDF/Excel

### Multi-tenancy
- Company-based isolation
- User invitations and permissions
- Subscription plans:
  - Basic, Pro, Enterprise tiers
  - Feature limitations per plan
  - Payment gateway integration ready

### Real-time Features
- WebSocket notifications
- Live transaction updates
- Real-time balance synchronization
- Activity feeds

## Development Guidelines

### Backend Development

1. **Django Apps Structure**:
   - Each app should be self-contained
   - Use signals sparingly, prefer explicit service calls
   - Keep views thin, move logic to services
   - Use serializers for validation and transformation

2. **API Design**:
   - RESTful endpoints with consistent naming
   - Use ViewSets for CRUD operations
   - Custom actions for non-CRUD operations
   - Proper HTTP status codes
   - Comprehensive error messages

3. **Database**:
   - Always add indexes for foreign keys and commonly queried fields
   - Use select_related and prefetch_related to avoid N+1 queries
   - Implement soft deletes where appropriate
   - Use database transactions for critical operations

4. **Caching Strategy**:
   - Cache expensive queries with appropriate TTL
   - Use cache invalidation on updates
   - Redis for session storage and real-time features

5. **Task Queue**:
   - Use Celery for long-running tasks
   - Implement proper retry logic
   - Monitor task execution with Celery Beat

### Frontend Development

1. **Component Structure**:
   - Functional components with TypeScript
   - Use custom hooks for shared logic
   - Implement proper loading and error states
   - Follow atomic design principles

2. **State Management**:
   - Zustand for global application state
   - React Query for server state
   - Local state for component-specific data
   - Avoid prop drilling

3. **API Integration**:
   - Centralized API client with interceptors
   - Proper error handling and retry logic
   - Type-safe API calls with TypeScript
   - Optimistic updates where appropriate

4. **Performance**:
   - Lazy load components and routes
   - Image optimization with Next.js Image
   - Minimize bundle size
   - Use React.memo judiciously

5. **Styling**:
   - TailwindCSS utility classes
   - Component variants with CVA
   - Consistent spacing and color schemes
   - Mobile-first responsive design

## Environment Setup

### Backend Environment Variables
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `BELVO_SECRET_ID`: Belvo API credentials
- `BELVO_SECRET_PASSWORD`: Belvo API password
- `PLUGGY_CLIENT_ID`: Pluggy API credentials
- `PLUGGY_CLIENT_SECRET`: Pluggy API secret
- `AWS_ACCESS_KEY_ID`: S3 storage credentials
- `AWS_SECRET_ACCESS_KEY`: S3 storage secret
- `SENTRY_DSN`: Error tracking

### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_BELVO_PUBLIC_KEY`: Belvo widget key
- `NEXT_PUBLIC_PLUGGY_CONNECT_TOKEN`: Pluggy widget token

## Common Tasks

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Default Data
```bash
python manage.py create_default_categories
python manage.py create_bank_providers
python manage.py create_subscription_plans
```

### Run Development Servers
```bash
# Backend
python manage.py runserver

# Frontend
npm run dev

# Celery Worker
celery -A core worker -l info

# Celery Beat
celery -A core beat -l info
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login with email/password
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - Logout and blacklist token
- `GET /api/auth/profile/` - Get user profile
- `POST /api/auth/verify-email/` - Verify email address
- `POST /api/auth/reset-password/` - Request password reset

### Banking
- `GET /api/banking/accounts/` - List bank accounts
- `POST /api/banking/accounts/` - Create bank account
- `GET /api/banking/transactions/` - List transactions
- `POST /api/banking/transactions/bulk-categorize/` - Categorize multiple transactions
- `POST /api/banking/connect/belvo/` - Connect Belvo account
- `POST /api/banking/connect/pluggy/` - Connect Pluggy account
- `POST /api/banking/sync/` - Sync transactions

### Categories
- `GET /api/categories/` - List transaction categories
- `POST /api/categories/` - Create custom category
- `GET /api/categories/suggestions/` - Get AI-powered suggestions

### Reports
- `GET /api/reports/dashboard/` - Dashboard summary
- `GET /api/reports/cashflow/` - Cash flow report
- `GET /api/reports/categories/` - Category breakdown
- `POST /api/reports/export/` - Export report to PDF/Excel

## Security Considerations

1. **Authentication**:
   - JWT tokens with short expiration
   - Refresh tokens stored securely
   - Token blacklisting on logout
   - Rate limiting on auth endpoints

2. **Data Privacy**:
   - Encryption at rest for sensitive data
   - HTTPS only in production
   - PII data masking in logs
   - GDPR compliance ready

3. **API Security**:
   - CORS properly configured
   - Input validation and sanitization
   - SQL injection prevention with ORM
   - XSS protection with proper escaping

4. **Banking Security**:
   - Encrypted credential storage
   - Token-based bank connections
   - No plain-text password storage
   - Audit logging for sensitive operations

## Testing

### Backend Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.banking

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Testing
```bash
# Run tests
npm test

# With coverage
npm run test:coverage
```

## Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Redis and PostgreSQL running
- [ ] Celery workers started
- [ ] SSL certificates configured
- [ ] Monitoring and logging setup
- [ ] Backup strategy implemented

### Docker Support
The project includes Docker configuration for easy deployment:
- `docker-compose.yml` for development
- `docker-compose.production.yml` for production
- Separate Dockerfiles for frontend and backend

## Troubleshooting

### Common Issues

1. **Banking Connection Failures**:
   - Check API credentials
   - Verify webhook URLs
   - Check rate limits
   - Review error logs

2. **Transaction Sync Issues**:
   - Check Celery worker status
   - Verify Redis connection
   - Review sync task logs
   - Check for duplicate transactions

3. **Performance Issues**:
   - Enable Django Debug Toolbar
   - Check database query optimization
   - Review caching strategy
   - Monitor Celery task performance

## Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Use conventional commits
5. Create feature branches
6. Submit pull requests with clear descriptions

## License

This project is proprietary software. All rights reserved.