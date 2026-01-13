# Entity Type Migration - Fast Parallel Version

## Overview
This migration adds `entity_type` column to `persons` table and populates it using parallel processing for maximum speed.

## Performance
- **Batch size**: 10,000 records per batch
- **Workers**: 8 parallel threads
- **Expected speed**: ~50,000-100,000 records/second
- **Total time**: ~30-60 seconds for 1M records

## How to Run

### Option 1: Direct execution
```bash
cd backend
python scripts/migrate_entity_type.py
```

### Option 2: Via wrapper
```bash
cd backend
python scripts/run_migration.py
```

### Option 3: Railway deployment
```bash
# SSH into Railway container
railway run python scripts/migrate_entity_type.py
```

## What it does

1. **Adds column** `entity_type VARCHAR(50)` to `persons` table
2. **Creates index** on `entity_type` for fast filtering
3. **Loads all company regcodes** into memory (~1-2 seconds)
4. **Classifies legal entities** in parallel batches:
   - `FOREIGN_ENTITY` - if regcode NOT in companies table
   - `LEGAL_ENTITY` - if regcode EXISTS in companies table
5. **Marks physical persons** as `PHYSICAL_PERSON`
6. **Verifies results** and shows statistics

## Output Example
```
==============================================================
ENTITY TYPE MIGRATION - FAST PARALLEL VERSION
==============================================================
🔧 Step 1: Adding entity_type column...
✅ Column and index created successfully

Records to process:
  Legal entities: 245,832
  Physical persons: 1,234,567

📋 Loading all company regcodes into memory...
✅ Loaded 156,789 company regcodes

🚀 Step 2a: Classifying legal entities (FOREIGN vs LEGAL)...
Processing 25 batches with 8 workers...
Processed 50,000 records (25,000 records/sec)
Processed 100,000 records (28,571 records/sec)
...
✅ Classified 245,832 legal entities in 8.6s (28,585 records/sec)

👤 Step 2b: Marking physical persons...
✅ Marked 1,234,567 physical persons in 2.3s

📊 Step 3: Verifying results...
==============================================================
ENTITY TYPE DISTRIBUTION:
==============================================================
FOREIGN_ENTITY       | member     | 12,456
LEGAL_ENTITY         | member     | 233,376
PHYSICAL_PERSON      | member     | 456,789
PHYSICAL_PERSON      | officer    | 678,901
PHYSICAL_PERSON      | ubo        | 98,877
==============================================================
✅ All records have entity_type populated!

🎉 Migration completed in 11.2s
```

## Rollback (if needed)
```sql
-- Remove column
ALTER TABLE persons DROP COLUMN IF EXISTS entity_type;

-- Remove index
DROP INDEX IF EXISTS idx_persons_entity_type;
```

## After Migration
1. Deploy updated backend code
2. Test foreign entity tooltips
3. Verify no more 404 errors for foreign companies
4. Monitor performance improvement (~50-100ms faster page loads)
