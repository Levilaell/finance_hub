# Deploy Instructions for Sync Fix

## Steps to Deploy

1. **Push to GitHub**
```bash
git push origin main
```

2. **Wait for Railway Deploy**
The push will trigger automatic deployment on Railway.

3. **Apply Migration on Railway**
After deployment is complete, run in Railway console:
```bash
python manage.py migrate banking
```

This will create the new fields:
- `sync_status` 
- `sync_error_message`

## What Changed

1. **Removed sync_item call** that was causing WAITING_USER_ACTION
2. **Added status check** before syncing
3. **Added sync status fields** to track sync state
4. **Improved webhook handling** for authentication states

## Expected Behavior After Fix

- Sync will check item status first
- If item needs authentication, it will return appropriate error
- No more forced sync attempts on items requiring user action
- Webhooks will update account status accordingly