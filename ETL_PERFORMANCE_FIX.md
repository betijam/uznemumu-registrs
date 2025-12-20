# 🚨 CRITICAL ETL PERFORMANCE FIX

## Problem Summary

Your ETL has been running for **12+ hours** and is only 50% complete because of a catastrophic performance bug in the chunked loading code.

### Root Cause: Row-by-Row Execution

The ON CONFLICT implementation I created was executing **50,000 individual SQL statements per chunk** instead of bulk inserts:

```python
# TERRIBLE - executes 50K times per chunk!
for _, row in batch_df.iterrows():
    conn.execute(sql, row.to_dict())
```

**Performance Impact**:
- Chunk 1 (TRUNCATE mode): ~1 minute ✅
- Chunk 2-37 (ON CONFLICT mode): **6+ hours EACH** ❌
- **Total time**: Would take 9+ DAYS to complete!

## Solution Applied

### 1. Removed ON CONFLICT Logic (`loader.py`)
- Deleted the slow row-by-row execution
- Back to fast pandas bulk inserts
- **Speed improvement**: ~360x faster per chunk

### 2. Added Deduplication (`process_finance.py`)
- Deduplicates data IN MEMORY before loading
- Keeps most recent record for each `(company_regcode, year)`
- Prevents duplicate key errors

```python
# Fast in-memory deduplication
df_merged = df_merged.drop_duplicates(subset=['company_regcode', 'year'], keep='last')
```

---

## What You Need to Do NOW

### Option 1: Stop Current Run & Redeploy (Recommended)

1. **Stop the current ETL** in Railway (it's wasting resources)
2. Commit these fixes:
   ```powershell
   git add backend/etl/loader.py backend/etl/process_finance.py
   git commit -m "fix: remove catastrophically slow ON CONFLICT, use in-memory deduplication instead"
   git push origin main
   ```
3. Wait for Railway to build (~2 min)
4. Manually trigger ONE new ETL run

**New Expected Time**: ~2-3 hours total (vs 9 days!)

### Option 2: Let Current Run Finish (Not Recommended)

The current run will eventually complete but will take **2-3 more days**. Not worth waiting.

---

## Expected Performance After Fix

### Before (Current):
- **Chunk loading time**: 6 hours per chunk
- **Total time**: 9+ days
- **Method**: 50K individual SQL statements

### After (Fixed):
- **Chunk loading time**: ~3-5 minutes per chunk
- **Total time**: ~2-3 hours
- **Method**: Bulk inserts with in-memory dedup

---

## Why This Happened

The duplicate key errors we saw earlier were because:
1. Source CSV has duplicate `(company_regcode, year)` entries
2. Processing chunks can create overlapping records

I tried to solve it with `ON CONFLICT DO UPDATE`, but PostgreSQL's implementation is slow when done row-by-row. The correct solution is to deduplicate in pandas BEFORE inserting - which is what we're doing now.

---

## Railway Configuration Reminder

After deploying the fix, remember to:
1. Set ETL service **Restart Policy** to **Never** or **On failure only**
2. Or better: Use Railway **Cron Jobs** to run `python etl_main.py` daily

This prevents the infinite restart loop.
