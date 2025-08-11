# 🚀 Finance Hub - Complete Deployment Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Environment Setup](#environment-setup)
5. [Deployment Process](#deployment-process)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)
11. [Performance Optimization](#performance-optimization)
12. [Disaster Recovery](#disaster-recovery)

---

## Overview

Finance Hub is deployed on Railway with a fully automated CI/CD pipeline. The deployment includes:

- **Backend**: Django REST API with Gunicorn
- **Frontend**: Next.js SSR application  
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Workers**: Celery for async tasks
- **Scheduler**: Celery Beat for periodic tasks

### Key Features

- ✅ **Zero-downtime deployments**
- ✅ **Automated health checks**
- ✅ **Multi-stage Docker builds**
- ✅ **Automatic rollback on failure**
- ✅ **Environment-specific configurations**
- ✅ **Comprehensive monitoring**

---

## Architecture

```mermaid
graph TB
    subgraph "Railway Cloud"
        subgraph "Application Layer"
            BE[Django Backend]
            FE[Next.js Frontend]
            CW[Celery Workers]
            CB[Celery Beat]
        end
        
        subgraph "Data Layer"
            PG[(PostgreSQL)]
            RD[(Redis)]
            S3[S3 Storage]
        end
        
        subgraph "Infrastructure"
            LB[Load Balancer]
            CDN[CDN]
        end
    end
    
    subgraph "External Services"
        STRIPE[Stripe]
        PLUGGY[Pluggy Banking]
        OPENAI[OpenAI]
        RESEND[Resend Email]
    end
    
    subgraph "CI/CD"
        GH[GitHub Actions]
        RAIL[Railway CLI]
    end
    
    Users --> CDN
    CDN --> FE
    FE --> LB
    LB --> BE
    BE --> PG
    BE --> RD
    BE --> S3
    BE --> CW
    CW --> RD
    CB --> RD
    
    BE --> STRIPE
    BE --> PLUGGY
    BE --> OPENAI
    BE --> RESEND
    
    GH --> RAIL
    RAIL --> Railway Cloud
```

---

## Prerequisites

### Local Development

```bash
# Required tools
- Python 3.11+
- Node.js 18+
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose
- Railway CLI

# Install Railway CLI
npm install -g @railway/cli

# Verify installations
python --version
node --version
docker --version
railway --version
```

### Railway Account Setup

1. Create account at [railway.app](https://railway.app)
2. Create new project
3. Add services:
   - PostgreSQL
   - Redis
   - Backend service
   - Frontend service
   - Celery worker service
   - Celery beat service

---

## Environment Setup

### 1. Configure Railway Variables

```bash
# Use the automated setup script
cd deploy
chmod +x setup-railway-env.sh
./setup-railway-env.sh

# Or manually in Railway Dashboard
```

### 2. Required Environment Variables

#### Backend Service

```env
# Core Settings
DJANGO_SECRET_KEY=<generate-new-key>
DJANGO_ENV=production
DEBUG=False
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}

# Database (auto-provided by Railway)
DATABASE_URL=${{DATABASE_URL}}

# Redis (auto-provided by Railway)
REDIS_URL=${{REDIS_URL}}

# Email
RESEND_API_KEY=re_xxxxx

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxx

# Pluggy Banking
PLUGGY_CLIENT_ID=xxxxx
PLUGGY_CLIENT_SECRET=xxxxx

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# URLs
FRONTEND_URL=https://your-frontend.railway.app
BACKEND_URL=https://your-backend.railway.app
```

#### Frontend Service

```env
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api
NEXT_PUBLIC_APP_URL=https://your-frontend.railway.app
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_xxxxx
```

### 3. Secrets Management

Store sensitive values in Railway's environment variables or use a secrets manager:

```bash
# Never commit secrets to git!
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "*.key" >> .gitignore
```

---

## Deployment Process

### Automatic Deployment (Recommended)

```bash
# 1. Push to main branch
git add .
git commit -m "feat: new feature"
git push origin main

# GitHub Actions will automatically:
# - Run tests
# - Build Docker images
# - Deploy to Railway
# - Run health checks
```

### Manual Deployment

```bash
# 1. Login to Railway
railway login

# 2. Link project
railway link

# 3. Deploy backend
railway service backend
railway up

# 4. Deploy frontend
railway service frontend
railway up

# 5. Deploy workers
railway service celery
railway up

railway service celery-beat
railway up
```

### Local Testing with Docker

```bash
# Test production build locally
docker-compose -f docker-compose.railway.yml up

# Access services
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# PgAdmin: http://localhost:5050
```

---

## Deployment Process (Railway Auto-Deploy)

### Automatic Deployment

Railway automatically deploys when you push to GitHub:

```bash
# Push to main branch
git add .
git commit -m "feat: new feature"
git push origin main

# Railway will automatically:
# - Detect the push
# - Build Docker image
# - Run migrations
# - Deploy services
# - Health checks
```

### Railway Dashboard

Monitor deployment status:
- 🟡 **Building** - Docker image being built
- 🟢 **Active** - Deployment successful
- 🔴 **Failed** - Check logs for errors

### No CI/CD Required

Railway handles everything automatically:
- Build optimization
- Caching
- Health checks
- Rollback on failure

---

## Monitoring & Health Checks

### Health Endpoints

```bash
# Backend health check
curl https://your-backend.railway.app/api/health/

# Frontend health check  
curl https://your-frontend.railway.app/api/health

# Detailed health status
curl https://your-backend.railway.app/api/health/detailed/
```

### Response Format

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "storage": "healthy"
  },
  "metrics": {
    "response_time_ms": 45,
    "memory_usage_mb": 256,
    "active_connections": 12
  }
}
```

### Monitoring Setup

```bash
# View logs
railway logs --service backend

# Monitor metrics
railway metrics --service backend

# Set up alerts
railway alerts create \
  --metric cpu \
  --threshold 80 \
  --webhook https://your-webhook.com
```

---

## Rollback Procedures

### Automatic Rollback

Triggered automatically when:
- Health checks fail after deployment
- Error rate exceeds threshold
- Critical services are down

### Manual Rollback

#### Using GitHub Actions

```bash
gh workflow run rollback.yml \
  -f environment=production \
  -f reason="Critical bug found"
```

#### Using Railway CLI

```bash
# Quick rollback to previous
railway rollback

# Rollback to specific deployment
railway rollback --deployment-id abc123
```

#### Using Rollback Script

```bash
cd deploy
chmod +x rollback.sh
./rollback.sh

# Follow interactive prompts
```

---

## Troubleshooting

### Common Issues

#### 1. Migration Failures

```bash
# Check migration status
railway run python manage.py showmigrations

# Fix inconsistent migrations
railway run python manage.py migrate --fake-initial

# Reset specific app
railway run python manage.py migrate app_name zero
railway run python manage.py migrate app_name
```

#### 2. Static Files Not Loading

```bash
# Collect static files manually
railway run python manage.py collectstatic --noinput

# Verify static files location
railway run ls -la /app/staticfiles/
```

#### 3. Celery Workers Not Processing

```bash
# Check worker status
railway run celery -A core inspect active

# Purge queue
railway run celery -A core purge

# Restart workers
railway service celery
railway restart
```

#### 4. Database Connection Issues

```bash
# Test connection
railway run python manage.py dbshell

# Check connection pool
railway run python -c "
from django.db import connection
print(connection.queries_log)
"
```

### Debug Mode

```bash
# Enable debug temporarily (NEVER in production!)
railway variables set DEBUG=True
railway up

# Check logs
railway logs --tail

# Disable debug
railway variables set DEBUG=False
railway up
```

### Performance Issues

```bash
# Profile slow queries
railway run python manage.py debugsqlshell

# Check memory usage
railway metrics --service backend

# Optimize database
railway run python manage.py optimize_db
```

---

## Security Considerations

### Security Checklist

- [ ] Use strong `DJANGO_SECRET_KEY` (50+ characters)
- [ ] Enable HTTPS only (`SECURE_SSL_REDIRECT=True`)
- [ ] Set secure cookies (`SESSION_COOKIE_SECURE=True`)
- [ ] Configure CORS properly
- [ ] Use rate limiting
- [ ] Enable HSTS headers
- [ ] Regular security updates
- [ ] Encrypt sensitive data
- [ ] Audit logs enabled
- [ ] Regular backups

### Security Headers

```python
# Automatically configured in production
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### Secrets Rotation

```bash
# Rotate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Update in Railway
railway variables set DJANGO_SECRET_KEY=<new-key>

# Rotate API keys periodically
```

---

## Performance Optimization

### Docker Optimization

- Multi-stage builds reduce image size by 60%
- Layer caching speeds up builds
- Non-root user for security
- Health checks built-in

### Database Optimization

```bash
# Add indexes
railway run python manage.py optimize_indexes

# Analyze queries
railway run python manage.py analyze_queries

# Vacuum database
railway run python manage.py dbshell -c "VACUUM ANALYZE;"
```

### Caching Strategy

```python
# Redis caching configured
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    }
}
```

### CDN Configuration

```nginx
# Cloudflare or other CDN
# Cache static assets for 1 year
Cache-Control: public, max-age=31536000

# Cache API responses selectively
Cache-Control: private, max-age=300
```

---

## Disaster Recovery

### Backup Strategy

#### Automated Backups

```bash
# Database backups (daily)
railway run python manage.py backup_db

# Media files backup (weekly)
railway run python manage.py backup_media
```

#### Manual Backup

```bash
# Export database
railway run pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Export environment variables
railway variables > env_backup_$(date +%Y%m%d).txt
```

### Recovery Procedures

#### Database Recovery

```bash
# Restore from backup
railway run psql $DATABASE_URL < backup_20240101.sql

# Verify data integrity
railway run python manage.py check_data_integrity
```

#### Full System Recovery

1. **Restore Database**
   ```bash
   railway run psql $DATABASE_URL < latest_backup.sql
   ```

2. **Restore Media Files**
   ```bash
   aws s3 sync s3://backup-bucket/media /app/media
   ```

3. **Restore Environment**
   ```bash
   railway variables import < env_backup.txt
   ```

4. **Deploy Application**
   ```bash
   railway up
   ```

5. **Verify Services**
   ```bash
   ./deploy/post-deploy.sh
   ```

---

## Maintenance

### Scheduled Maintenance

```bash
# Enable maintenance mode
railway variables set MAINTENANCE_MODE=True
railway up

# Perform maintenance tasks
railway run python manage.py maintenance_tasks

# Disable maintenance mode
railway variables set MAINTENANCE_MODE=False
railway up
```

### Updates and Upgrades

```bash
# Update dependencies
pip-compile --upgrade requirements.in
npm update

# Test locally
docker-compose up

# Deploy updates
git commit -am "chore: update dependencies"
git push origin main
```

---

## Support and Resources

### Documentation

- [Railway Docs](https://docs.railway.app)
- [Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

### Monitoring Services

- Application: Railway Metrics Dashboard
- Errors: Sentry (if configured)
- Uptime: UptimeRobot or Pingdom
- Analytics: Google Analytics

### Emergency Contacts

- **DevOps Team**: devops@caixahub.com.br
- **On-Call Engineer**: Use PagerDuty
- **Railway Support**: support@railway.app

### Useful Commands

```bash
# View all services
railway list

# Check service status
railway status

# View recent deployments
railway deployments list

# Connect to database
railway run python manage.py dbshell

# Run Django shell
railway run python manage.py shell

# Execute one-off commands
railway run <command>
```

---

## Appendix

### File Structure

```
finance_hub/
├── .github/
│   └── workflows/
│       ├── deploy-railway.yml    # CI/CD pipeline
│       └── rollback.yml          # Rollback workflow
├── backend/
│   ├── Dockerfile                # Optimized multi-stage build
│   ├── deploy/                   # Deployment scripts
│   │   ├── start-production.sh   # Main startup script
│   │   ├── start-celery.sh       # Celery worker script
│   │   ├── start-celery-beat.sh  # Celery beat script
│   │   ├── pre-deploy.sh         # Pre-deployment validation
│   │   └── post-deploy.sh        # Post-deployment checks
│   └── railway.json              # Railway configuration
├── frontend/
│   ├── Dockerfile                # Next.js production build
│   └── railway.toml              # Railway configuration
├── deploy/
│   ├── setup-railway-env.sh     # Environment setup script
│   └── rollback.sh               # Manual rollback script
├── docker-compose.railway.yml    # Local Railway simulation
├── railway.json                  # Main Railway configuration
└── .env.railway.example          # Environment template
```

### Version History

- **v2.0.0** - Complete deployment automation
- **v1.5.0** - Added rollback procedures
- **v1.0.0** - Initial Railway deployment

---

*Last Updated: January 2025*
*Maintained by: Finance Hub DevOps Team*