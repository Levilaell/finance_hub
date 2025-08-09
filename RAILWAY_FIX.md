# Railway Deployment Fix

## Problem
The `DATABASE_URL` environment variable is not being resolved properly in Railway. It's currently set as:
```
DATABASE_URL="${{finance-db.DATABASE_URL}}"
```

## Solution

### Option 1: Fix the Reference Variable (Recommended)
1. Go to Railway Dashboard → Your Project → Backend Service → Variables
2. Find the `DATABASE_URL` variable
3. Delete the current value
4. Click the reference button (looks like a chain link or `${}`)
5. Select your database service (likely called `finance-db` or `Postgres`)
6. Select `DATABASE_URL` from the dropdown
7. Save the changes

### Option 2: Use Direct Database URL
1. Go to Railway Dashboard → Your Database Service
2. Click on the Variables tab
3. Copy the `DATABASE_URL` value (should look like: `postgresql://user:pass@host:port/dbname`)
4. Go to your Backend Service → Variables
5. Replace `DATABASE_URL` with the actual URL you copied
6. Save the changes

### Option 3: Check Service Names
If the reference variable should work, ensure:
1. Your database service is actually named `finance-db`
2. If it has a different name (like `postgres` or `database`), update the reference:
   - Change from: `${{finance-db.DATABASE_URL}}`
   - To: `${{postgres.DATABASE_URL}}` (or whatever your DB service is named)

## Similarly, fix Redis URL
The `REDIS_URL` variable also appears to use template syntax:
```
REDIS_URL="${{finance-redis.REDIS_URL}}"
CELERY_BROKER_URL="${{finance-redis.REDIS_URL}}"
CELERY_RESULT_BACKEND="${{finance-redis.REDIS_URL}}"
```

Apply the same fix for these variables.

## After Fixing
1. Railway will automatically redeploy your service
2. The health check should pass within 1-2 minutes
3. Your app should be accessible at the Railway URL

## Verification
You can verify the fix worked by:
1. Checking the deployment logs - you should see "Migrations completed" 
2. The health check should return 200 OK
3. Visit `/health/` endpoint - it should show database as "healthy"