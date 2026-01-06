# Regions Page - Quick Fixes Needed

## Issues Found

1. ✅ **Syntax fixed** - locations.py compiles successfully after null byte removal
2. ⚠️ **Server restart needed** - Backend returns 405 (routes not loaded)
3. ⚠️ **Frontend needs avg_salary display** - Column added but may not show data

## Actions Required

### 1. Restart Backend Container
The locations.py file was corrupted with null bytes and cleaned. Server must restart to load routes.

```bash
# In Docker or wherever backend runs
docker-compose restart backend
# OR
# Stop and start the uvicorn process
```

### 2. Verify API After Restart
```bash
curl http://localhost:8000/api/locations/cities?limit=2
curl http://localhost:8000/api/locations/municipalities?limit=2
```

Should return JSON with `avg_salary` field.

### 3. Check Frontend Issues

**Issue 1: Vid. alga not showing**
- Frontend interface has `avg_salary` field ✅
- API should return it after restart ✅  
- Column is in table ✅

**Issue 2: Cities not clickable**
- Links are in code ✅
- Check if styling makes them visible

**Issue 3: Novadi fails**
- 405 error = server not restarted
- Should work after restart

## Expected Result After Restart

- `/api/locations/cities` returns cities with avg_salary
- `/api/locations/municipalities` returns municipalities with avg_salary
- Frontend table shows all columns including "Vid. alga"
- Location names are clickable blue links
- Both cities and municipalities work
