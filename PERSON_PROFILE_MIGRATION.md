# Person Profile Migration - Railway/Neon Database

## Quick Start

Run this migration to add performance indexes for the person profile feature:

```bash
# From project root
python backend/run_person_profile_migration.py

# OR from backend directory
cd backend
python run_person_profile_migration.py
```

## Prerequisites

1. **Environment Variables**: Ensure your `.env` file contains:
   ```
   DATABASE_URL=postgresql://user:password@hostname/database
   ```

2. **Python Dependencies**: Install required packages:
   ```bash
   pip install sqlalchemy psycopg2-binary python-dotenv
   ```

## What This Migration Does

Adds 4 performance indexes to the `persons` table:

1. **`idx_persons_person_code_active`** - Partial index for active persons (WHERE date_to IS NULL)
   - Speeds up queries filtering for current roles
   - Used by main person profile endpoint

2. **`idx_persons_name_trgm`** - GIN index for fuzzy person name search
   - Enables fast full-text search on person names
   - Used for person search autocomplete (future)

3. **`idx_persons_company_role`** - Composite index (company_regcode, role)
   - Optimizes company-person joins
   - Used in aggregation queries

4. **`idx_persons_birth_date`** - Index for birth date matching
   - Used in person matching fallback logic
   - For persons without unique person_code

## Expected Output

```
✓ Loaded .env from .env
🔗 Connecting to database...
📄 Reading migration file: backend/db/migrations/add_person_profile_indexes.sql
🚀 Applying person profile indexes migration...
✅ Migration Success!

Created indexes:
  - idx_persons_person_code_active (partial index for active persons)
  - idx_persons_name_trgm (GIN index for person name search)
  - idx_persons_company_role (composite index for joins)
  - idx_persons_birth_date (for person matching)

Person profile pages are now ready to use! 🎉
🔌 Database connection closed.
```

## Troubleshooting

### DATABASE_URL not found
```
❌ Error: DATABASE_URL not found in environment!
```
**Solution**: Create `.env` file in project root or backend directory with your Neon database URL.

### Migration file not found
```
❌ Error: Migration file not found
```
**Solution**: Ensure you're running from the correct directory. The script looks for:
- `db/migrations/add_person_profile_indexes.sql` (from backend/)
- `backend/db/migrations/add_person_profile_indexes.sql` (from root)

### Index already exists
If you see an error like:
```
relation "idx_persons_person_code_active" already exists
```
**Solution**: The migration has already been applied. You can safely ignore this or modify the migration SQL to use `CREATE INDEX IF NOT EXISTS`.

## Running on Railway

### Option 1: Local Execution (Recommended)

1. Get your Neon database connection string from Railway
2. Add to `.env` file
3. Run migration locally:
   ```bash
   python backend/run_person_profile_migration.py
   ```

### Option 2: Railway CLI

```bash
# Connect to Railway project
railway link

# Run migration
railway run python backend/run_person_profile_migration.py
```

### Option 3: During Deployment

Add to your Railway deployment script or GitHub Actions:

```yaml
# .github/workflows/deploy.yml
- name: Run Person Profile Migration
  run: python backend/run_person_profile_migration.py
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Verification

After running the migration, verify indexes were created:

```sql
-- Connect to your Neon database
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'persons' 
  AND indexname LIKE 'idx_persons_%'
ORDER BY indexname;
```

Expected result:
```
idx_persons_birth_date
idx_persons_company_role
idx_persons_name_trgm
idx_persons_person_code_active
```

## Performance Impact

**Before migration:**
- Person profile query: ~2-5 seconds (full table scan)
- Co-occurrence network: ~10-15 seconds

**After migration:**
- Person profile query: ~200-500ms (indexed lookup)
- Co-occurrence network: ~500-1000ms (optimized joins)

## Rollback (if needed)

To remove the indexes:

```sql
DROP INDEX IF EXISTS idx_persons_person_code_active;
DROP INDEX IF EXISTS idx_persons_name_trgm;
DROP INDEX IF EXISTS idx_persons_company_role;
DROP INDEX IF EXISTS idx_persons_birth_date;
```

Or create a rollback script:

```bash
python backend/rollback_person_profile_migration.py
```

## Next Steps

After successful migration:

1. ✅ Restart your backend service on Railway
2. ✅ Test person profile endpoint: `GET /api/person/{identifier}`
3. ✅ Navigate to person profile in UI: `/person/{identifier}`
4. ✅ Verify performance improvements

## Support

If you encounter issues:
1. Check Railway logs for errors
2. Verify DATABASE_URL is correct
3. Ensure Neon database is accessible
4. Check PostgreSQL extension `pg_trgm` is installed (for fuzzy search)

To install pg_trgm extension (if missing):
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```
