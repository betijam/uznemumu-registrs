# ⚠️ RAILWAY CONFIGURATION - CRITICAL

## Problem: ETL Service Infinite Loop

Your ETL service is currently stuck in an infinite restart loop because:
1. `python etl_main.py` runs ETL and exits successfully
2. Railway sees the process exit and automatically restarts it
3. ETL runs again, and again, forever...

## Solution: Disable Auto-Restart

### In Railway Dashboard:

1. Go to your **ETL Service**
2. Click **Settings** tab
3. Under **Deploy** → Find **Restart Policy**
4. Set to: **Never restart** or **On failure only**
5. Save changes

### Alternative: Use Railway Cron Jobs (Recommended)

Instead of running ETL as a service, use Railway Cron Jobs:

1. Delete the ETL service (or disable it)
2. Go to Project Settings → **Cron Jobs**
3. Create new cron job:
   - **Service**: Your backend service
   - **Schedule**: `0 3 * * *` (daily at 3 AM)
   - **Command**: `python etl_main.py`

This way ETL only runs when scheduled, not continuously.

---

## Fixes Applied to Code

### 1. Fixed Duplicate Key Error ✅

**File**: `backend/etl/loader.py`

**Problem**: Chunked loading was creating duplicate `(company_regcode, year)` across chunks

**Solution**: Added PostgreSQL `ON CONFLICT DO UPDATE` for `financial_reports` table
- First chunk: TRUNCATE + INSERT
- Subsequent chunks: INSERT ... ON CONFLICT DO UPDATE (upsert)
- Keeps most recent data for each company/year

### 2. Risk Processing Errors

**Current errors**:
```
cannot reindex on an axis with duplicate labels
```

These are in `process_risks.py` for liquidations and suspensions. Need to fix duplicate handling.

---

## Next Steps

1. **Immediate**: Configure Railway restart policy to **Never** or **On failure only**
2. Deploy the updated code (with fixed loader.py)
3. Manually trigger ONE ETL run to test
4. Set up Railway Cron Job for scheduled runs
