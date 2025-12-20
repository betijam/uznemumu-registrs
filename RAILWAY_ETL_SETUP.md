# 🚨 Railway ETL Configuration - CRITICAL

## Problem Solved
ETL was auto-starting on every deploy because `python etl_main.py` would immediately run the ETL process.

## Solution: Kill Switch Implemented

`etl_main.py` now has a **safety mechanism** - ETL will **NEVER** run unless explicitly enabled.

---

## Railway Configuration

### 1. ETL Service Settings

**Start Command:**
```bash
python etl_main.py
```

**Environment Variables:**
- Do NOT set `RUN_ETL` at all (or set `RUN_ETL=false`)
- ETL service will start, log "ETL is DISABLED", and exit immediately
- **Zero resource usage** ✅

### 2. Running ETL Manually

When you want to trigger ETL:

**Option A: Temporary ENV variable**
1. Go to ETL Service → Variables
2. Add: `RUN_ETL=true`
3. Trigger redeploy
4. **IMPORTANT:** Remove `RUN_ETL=true` after completion!

**Option B: Command override (better)**
1. ETL Service → Deployments → Latest
2. Click "..." → Shell
3. Run: `python etl_main.py --run`

### 3. Automated ETL (Recommended: Railway Cron)

**Setup Railway Cron Job:**
1. Project Settings → **Cron Jobs** → Create
2. **Name:** Daily ETL
3. **Command:** 
   ```bash
   RUN_ETL=true python etl_main.py
   ```
4. **Schedule:** `0 3 * * *` (daily at 3:00 AM)
5. **Service:** Select your backend/etl service

**Alternatively in cron:**
```bash
python etl_main.py --run
```

---

## How It Works

### Default Behavior (Deploy/Restart)
```
ETL Service Boot
RUN_ETL env: None
CLI --run flag: False
🛑 ETL is DISABLED. Exiting without running anything.
   To run ETL, set RUN_ETL=true or pass --run flag.
```
Container exits with code 0. No ETL runs. ✅

### When Enabled (Cron or Manual)
```
ETL Service Boot
RUN_ETL env: true
CLI --run flag: False
🚀 Starting ETL (explicitly enabled)
[... ETL process ...]
✅ ETL finished successfully
```

---

## Safety Features

### Kill Switch
- **ENV check:** `RUN_ETL=true`
- **CLI check:** `--run` flag
- Both must be absent → ETL won't run

### Logging
- Clear logging shows why ETL did/didn't run
- `ETL_REASON` env can document why ETL was triggered

### Future: DB Lock (Optional)
To prevent parallel ETL runs, add PostgreSQL advisory lock:
```python
# In etl/__init__.py
from sqlalchemy import text

def run_all_etl():
    with engine.connect() as conn:
        # Try to acquire lock (ETL_LOCK_ID = 123456)
        result = conn.execute(text("SELECT pg_try_advisory_lock(123456)"))
        if not result.scalar():
            logger.error("Another ETL process is running. Aborting.")
            return
        
        try:
            # ... existing ETL code ...
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(123456)"))
```

---

## Quick Reference

| Scenario | Configuration | Result |
|----------|--------------|--------|
| Deploy/Restart | No `RUN_ETL`, no `--run` | ETL disabled, exits immediately |
| Manual trigger | `python etl_main.py --run` | ETL runs once |
| Cron job | `RUN_ETL=true python etl_main.py` | ETL runs on schedule |
| Emergency stop | Remove `RUN_ETL` var | Next run will be disabled |

---

## Commit This Fix

```bash
git add backend/etl_main.py
git commit -m "feat: add ETL kill switch - prevent auto-run on deploy"
git push origin main
```

After deploy, ETL will stop auto-starting! 🎉
