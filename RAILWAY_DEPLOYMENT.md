# Railway Deployment Guide

## Required Environment Variables

Before deploying to Railway, you **MUST** set these environment variables in the Railway dashboard:

### Critical Variables (Required)
```bash
# Django Secret Key - MUST be set!
DJANGO_SECRET_KEY=your-secret-key-here

# Database URL - Railway provides this automatically as DATABASE_URL
DATABASE_URL=postgresql://user:password@host:port/dbname

# Django Environment
DJANGO_SETTINGS_MODULE=core.settings.production

# CORS Origins - Your frontend URL
CORS_ALLOWED_ORIGINS=https://your-frontend.railway.app
```

### Generate a Secret Key
```bash
# Run this command to generate a secure secret key:
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Optional but Recommended Variables
```bash
# Frontend URL
FRONTEND_URL=https://your-frontend.railway.app

# Redis URL (for caching and Celery)
REDIS_URL=redis://default:password@host:port

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Stripe (if using payments)
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Pluggy API (if using banking integration)
PLUGGY_CLIENT_ID=your-client-id
PLUGGY_CLIENT_SECRET=your-client-secret
PLUGGY_WEBHOOK_SECRET=your-webhook-secret
PLUGGY_WEBHOOK_URL=https://your-backend.railway.app/api/banking/webhooks/pluggy/

# OpenAI (if using AI features)
OPENAI_API_KEY=sk-xxx

# Sentry (for error tracking)
SENTRY_DSN=https://xxx@sentry.io/xxx
```

## Deployment Steps

1. **Fork/Clone the repository**

2. **Create a new project in Railway**

3. **Add PostgreSQL database**
   - Railway will automatically provide the `DATABASE_URL`

4. **Set Environment Variables**
   - Go to your service settings
   - Add all required variables listed above
   - At minimum, set `DJANGO_SECRET_KEY`

5. **Deploy**
   - Railway will automatically build and deploy using the Dockerfile

6. **Check Health Status**
   - Visit: `https://your-app.railway.app/health/`
   - Should return JSON with status "healthy"

## Troubleshooting

### 500 Error on Health Check
- **Cause**: Missing `DJANGO_SECRET_KEY` environment variable
- **Solution**: Set the variable in Railway dashboard

### Database Connection Failed
- **Cause**: `DATABASE_URL` not set or incorrect
- **Solution**: Railway should provide this automatically. Check your database service.

### CORS Issues
- **Cause**: Frontend URL not in `CORS_ALLOWED_ORIGINS`
- **Solution**: Add your frontend URL to the environment variable

### Static Files Not Loading
- **Cause**: WhiteNoise configuration issue
- **Solution**: Check that `collectstatic` ran successfully during build

## Monitoring

The health check endpoint provides detailed information:
```json
GET /health/

{
  "status": "healthy",
  "checks": {
    "environment": "core.settings.production",
    "configuration": "complete",
    "database": "healthy",
    "database_tables": "complete",
    "cache": "healthy",
    "migrations": "all applied"
  },
  "version": "1.1.0"
}
```

If there are issues, warnings will be included:
```json
{
  "status": "healthy",
  "checks": {...},
  "warnings": [
    "DJANGO_SECRET_KEY environment variable must be set in Railway",
    "DATABASE_URL environment variable must be set in Railway"
  ]
}
```