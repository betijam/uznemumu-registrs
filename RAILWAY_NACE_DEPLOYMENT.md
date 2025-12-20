# 🚀 Railway Deployment Guide - NACE Implementation

## ✅ Pre-Deployment Checklist

### Files to Commit
```bash
# Backend changes
backend/db/init.sql                    # NACE columns added
backend/etl/process_nace.py           # NEW - NACE processor
backend/etl/__init__.py               # NACE integration
backend/etl/process_taxes.py          # NACE call added
backend/app/routers/companies.py      # NACE fields in response
backend/app/routers/benchmarking.py   # NEW - benchmarking endpoints
backend/app/routers/search.py         # Stats fixed, NACE filter added
backend/main.py                        # Benchmarking router added

# Frontend changes
frontend/src/app/company/[id]/page.tsx    # Industry badge, benchmarking, competitors
frontend/src/app/page.tsx                 # Homepage stats fixed
frontend/src/components/CompanyTabs.tsx   # Procurement period label

# Data file
NACE.csv                              # MUST be in project root!
```

### Git Commands
```bash
git add .
git status  # Verify all files above are staged
git commit -m "feat: NACE industry classification with benchmarking and competitor analysis"
git push origin main
```

---

## 🗄️ Railway Database Migration

### Step 1: Connect to Railway Database

**Via Railway CLI:**
```bash
railway login
railway link  # Select your project
railway connect postgres
```

**Or via psql directly:**
```bash
# Get DATABASE_URL from Railway dashboard
psql "postgresql://postgres:[password]@[host]:[port]/railway"
```

### Step 2: Run Migration SQL

```sql
-- Add NACE columns to companies table
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_code VARCHAR(10);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_text VARCHAR(500);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_section VARCHAR(5);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_section_text VARCHAR(200);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS employee_count INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_data_year INTEGER;

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_companies_nace_code ON companies(nace_code);
CREATE INDEX IF NOT EXISTS idx_companies_nace_section ON companies(nace_section);
CREATE INDEX IF NOT EXISTS idx_companies_employee_count ON companies(employee_count);

-- Verify columns were added
\d companies

-- Check if any data exists (should be 0 initially)
SELECT COUNT(*) FROM companies WHERE nace_code IS NOT NULL;

-- Exit
\q
```

**Expected Output:**
```
ALTER TABLE
ALTER TABLE
...
CREATE INDEX
CREATE INDEX
CREATE INDEX

 count 
-------
     0
(1 row)
```

---

## 📁 NACE.csv File Upload to Railway

### Problem
Railway doesn't include `NACE.csv` in the build (it's not in git-tracked files).

### Solution Options

#### Option A: Add NACE.csv to Git (Recommended)
```bash
# Verify file exists in project root
ls -la NACE.csv

# Add to git
git add NACE.csv
git commit -m "chore: add NACE dictionary for industry classification"
git push origin main
```

**Railway will automatically include it in the build!**

#### Option B: Upload via Railway CLI
```bash
railway login
railway link

# Copy file to railway service
railway run --service backend bash
# Inside railway shell:
curl -o /app/NACE.csv https://your-server.com/NACE.csv
# Or manually paste content
```

#### Option C: Hardcode in ETL
Modify `process_nace.py` to download NACE.csv from a public URL if not found locally.

**Recommend: Option A** - simplest and most reliable.

---

## 🔄 Manual ETL Trigger on Railway

### Current Setup
- **API Service**: `RUN_ETL=false` (Auto-run disabled ✅)
- **ETL Service**: Separate service, runs only on manual trigger

### Method 1: Railway Dashboard (Easiest)

1. Go to Railway Dashboard → Your Project
2. Find **ETL service** (or backend if combined)
3. Click **"Deploy"** → **"Redeploy"**
4. Watch logs for ETL progress

### Method 2: Railway CLI

```bash
railway login
railway link

# Trigger one-time deployment
railway up --service etl

# Or if using single service, set env and redeploy:
railway variables set RUN_ETL=true --service backend
railway up --service backend
# After ETL completes, unset:
railway variables set RUN_ETL=false --service backend
```

### Method 3: Via API Endpoint (If Implemented)

If you create a protected `/etl/trigger` endpoint:

```bash
curl -X POST https://your-backend.railway.app/etl/trigger \
  -H "Authorization: Bearer YOUR_SECRET_TOKEN"
```

**For now, use Method 1 or 2.**

---

## 📊 NACE Data Loading Process

### What Happens When ETL Runs

1. **Downloads VID Tax Data** (~200k companies)
2. **Loads NACE Dictionary** from `NACE.csv` (5432 codes)
3. **Matches & Updates**:
   - Extracts NACE code from VID data
   - Normalizes code (removes dots)
   - Looks up industry description
   - Extracts section code (e.g., "62" from "6201")
   - Updates `companies` table with:
     - `nace_code`
     - `nace_text`
     - `nace_section`
     - `nace_section_text`
     - `employee_count`
     - `tax_data_year`

### Expected Results

```sql
-- Check NACE coverage
SELECT 
  COUNT(*) as total_companies,
  COUNT(nace_code) as with_nace,
  ROUND(COUNT(nace_code)::numeric / COUNT(*) * 100, 1) as coverage_pct
FROM companies;

-- Expected:
--  total_companies | with_nace | coverage_pct 
-- -----------------+-----------+--------------
--           200000 |    160000 |         80.0

-- Top industries
SELECT 
  nace_section,
  nace_section_text,
  COUNT(*) as companies,
  SUM(employee_count) as employees
FROM companies
WHERE nace_section IS NOT NULL AND nace_section != '00'
GROUP BY nace_section, nace_section_text
ORDER BY companies DESC
LIMIT 10;
```

---

## 🧪 Post-Deployment Verification

### 1. Check Database Migration

```bash
railway connect postgres
```

```sql
-- Verify NACE columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'companies' 
  AND column_name LIKE 'nace%'
ORDER BY column_name;

-- Should return:
-- nace_code, nace_section, nace_section_text, nace_text
```

### 2. Test API Endpoints

```bash
# Get company with NACE data
curl https://your-backend.railway.app/companies/40103680527

# Should include:
# {
#   "nace_code": "6201",
#   "nace_text": "Datorprogrammēšana",
#   "nace_section": "62",
#   "nace_section_text": "IT pakalpojumi",
#   ...
# }

# Test benchmarking
curl https://your-backend.railway.app/companies/40103680527/benchmark

# Test competitors
curl https://your-backend.railway.app/companies/40103680527/competitors

# Test industries
curl https://your-backend.railway.app/industries

# Test homepage stats (fixed)
curl https://your-backend.railway.app/stats
```

### 3. Check Frontend

1. Visit your Railway frontend URL
2. **Homepage**: Check stats cards (no mock data, current year)
3. **Search**: Test industry filter
4. **Company Profile**: 
   - Purple industry badge in header
   - "Pozīcija Nozarē" card
   - "Tuvākie Konkurenti" section
   - Procurement section shows "2018-2025" period

---

## 🐛 Troubleshooting

### Issue: NACE columns missing after deploy

**Cause:** Migration not run

**Fix:**
```bash
railway connect postgres
# Run ALTER TABLE commands from Step 2
```

### Issue: "NACE.csv not found"

**Cause:** File not in Railway build

**Fix:**
```bash
# Add to git
git add NACE.csv
git commit -m "chore: add NACE dictionary"
git push origin main
```

### Issue: All companies have nace_code = NULL

**Cause:** ETL not run yet OR migration not complete

**Fix:**
1. Verify migration: `\d companies` in psql
2. Trigger ETL manually (see Method 1 above)
3. Wait 30-40 minutes for completion
4. Check logs for errors

### Issue: Benchmarking returns "No data"

**Cause:** Company has no NACE section OR no other companies in industry

**Fix:**
```sql
-- Check company NACE
SELECT regcode, nace_section, nace_section_text 
FROM companies 
WHERE regcode = 40103680527;

-- Check industry size
SELECT nace_section, COUNT(*) 
FROM companies 
WHERE nace_section = (SELECT nace_section FROM companies WHERE regcode = 40103680527)
GROUP BY nace_section;

-- Need at least 10 companies for benchmarking to work
```

### Issue: Homepage stats show 0

**Cause:** Database empty OR API not connected

**Fix:**
```bash
# Check database has data
railway connect postgres
```

```sql
SELECT COUNT(*) FROM companies;
-- Should be > 100,000

SELECT COUNT(*) FROM procurements;
-- Should be > 10,000

SELECT COUNT(*) FROM financial_reports;
-- Should be > 500,000
```

---

## 📝 Summary - Deployment Steps

1. ✅ **Commit all changes** (including NACE.csv)
2. ✅ **Push to GitHub** (`git push origin main`)
3. ✅ **Railway auto-deploys** (wait ~3-5 minutes)
4. ✅ **Run database migration** (psql → ALTER TABLE)
5. ✅ **Trigger ETL manually** (Railway dashboard redeploy)
6. ✅ **Wait for ETL** (~30-40 minutes)
7. ✅ **Verify API** (test endpoints)
8. ✅ **Check frontend** (homepage, company profiles)

---

## ⏱️ Time Estimates

- **Deployment**: 3-5 minutes (automatic)
- **Migration**: 1 minute (manual SQL)
- **ETL Run**: 30-40 minutes (manual trigger)
- **Total**: ~45 minutes from push to fully functional

---

## 🔐 Security Notes

- Never commit Railway `DATABASE_URL` to git
- Keep `RUN_ETL=false` on API service to prevent auto-runs
- Use separate ETL service or manual triggers only
- Consider adding auth to ETL trigger endpoints (future)

---

## 📞 Support

If issues persist:
1. Check Railway logs: `railway logs --service backend`
2. Check database state: `railway connect postgres`
3. Verify NACE.csv exists: `railway run --service backend ls -la NACE.csv`
4. Review ETL logs for specific errors
