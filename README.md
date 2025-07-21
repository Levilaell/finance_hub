# CaixaHub

A comprehensive personal finance management system with AI-powered insights, budgeting tools, and financial reporting.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finance_management
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Run deployment script**
   ```bash
   ./scripts/deploy.sh
   ```

The script will:
- Build all Docker images
- Start all services (database, backend, frontend, redis, etc.)
- Run database migrations
- Create default categories
- Seed subscription plans
- Collect static files
- Optionally create a superuser

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin

Development environment also includes:
- **pgAdmin**: http://localhost:5050 (admin@financeapp.com / admin)
- **Mailhog**: http://localhost:8025

## 🛠️ Manual Deployment

If you prefer manual deployment:

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create default categories
docker-compose exec backend python manage.py create_default_categories

# Seed plans
docker-compose exec backend python manage.py seed_plans

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

## 📦 Services

- **Backend**: Django REST API with Celery workers
- **Frontend**: Next.js with TypeScript
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Web Server**: Nginx (production)
- **Email**: Mailhog (development)

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f [service_name]

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build [service_name]

# Access Django shell
docker-compose exec backend python manage.py shell

# Run tests
docker-compose exec backend python manage.py test
docker-compose exec frontend npm test
```

## 🌍 Production Deployment

For production deployment:

1. Update `.env` with production values:
   - Set `DEBUG=False`
   - Configure real database credentials
   - Set up email service
   - Configure payment gateways (Stripe, MercadoPago)
   - Set up AWS S3 for media files

2. Use production docker-compose profile:
   ```bash
   docker-compose up -d
   ```

3. Set up SSL/TLS with Let's Encrypt or your certificate provider

4. Configure a proper domain name in Nginx

## 📝 Environment Variables

Key environment variables (see `backend/.env.example`):

- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `STRIPE_*`: Stripe payment configuration
- `AWS_*`: AWS S3 configuration for media files
- `EMAIL_*`: Email service configuration

## 🔒 Security Notes

- Always use strong passwords in production
- Keep SECRET_KEY secure and unique
- Enable HTTPS in production
- Regularly update dependencies
- Set up proper firewall rules
- Use environment-specific `.env` files