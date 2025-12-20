# Railway Build Fix - Root Directory Configuration

## Problem
Railway build is failing with:
```
"/requirements.txt": not found
```

## Root Cause
Railway is building from the repository root, but the backend code is in `/backend` subdirectory.

## Solution

### For API Service

1. Go to Railway dashboard → Your API service
2. Click **Settings** tab
3. Scroll to **Deploy** section
4. Find **Root Directory** setting
5. Set it to: `backend`
6. Click **Save**
7. Redeploy the service

### For ETL Service (when you create it)

Same steps:
1. Settings → Deploy → Root Directory → `backend`
2. Save and deploy

## Alternative: Use Dockerfile Path

If Root Directory doesn't work:
1. Settings → Deploy
2. **Dockerfile Path**: `backend/Dockerfile`
3. **Build Context**: Leave as `.` or set to `backend`

## Verify Configuration

After setting Root Directory to `backend`, Railway should:
- ✅ Find `backend/Dockerfile`
- ✅ Find `backend/requirements.txt`
- ✅ Build successfully
- ✅ Find `main.py` for the start command

## Environment Variables to Set

While you're in Settings, make sure these are set:

```
DATABASE_URL=<from PostgreSQL plugin>
ENABLE_ETL_SCHEDULER=false
```

## Start Command

Settings → Deploy → Start Command:
```
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```
