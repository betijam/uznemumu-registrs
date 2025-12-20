# 🧪 Local Testing Guide - NACE Implementation

## Prerequisites
- Docker Desktop running
- PostgreSQL client (optional, for verification)
- `NACE.csv` file in project root ✅

---

## Step 1: Stop Existing Services

```powershell
# Stop any running containers
docker-compose down

# Or if using production compose
docker-compose -f docker-compose.prod.yml down

# Clean up (optional - only if you want fresh start)
docker-compose down -v  # This removes database volume!
```

---

## Step 2: Database Setup

### Option A: Fresh Database (Recommended)

```powershell
# Start only the database
docker-compose up -d db

# Wait for database to be ready (15 seconds)
Start-Sleep -Seconds 15

# Database will auto-create schema from init.sql
```

### Option B: Update Existing Database

If you have existing data you want to keep:

```powershell
# Connect to database
docker exec -it uzneumu-registrs_v2-db-1 psql -U postgres -d company_registry

# Run migration SQL
```

```sql
-- Add NACE columns (if not exist)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_code VARCHAR(10);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_text VARCHAR(500);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_section VARCHAR(5);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_section_text VARCHAR(200);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS employee_count INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_data_year INTEGER;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_companies_nace_code ON companies(nace_code);
CREATE INDEX IF NOT EXISTS idx_companies_nace_section ON companies(nace_section);
CREATE INDEX IF NOT EXISTS idx_companies_employee_count ON companies(employee_count);

-- Verify
\d companies

-- Exit
\q
```

---

## Step 3: Install Backend Dependencies

```powershell
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify psycopg2 is installed (needed for NACE)
pip list | Select-String psycopg2
```

---

## Step 4: Set Environment Variables

Create `.env` file in `backend/` directory:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/company_registry
ENABLE_ETL_SCHEDULER=false
```

Or set in PowerShell:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/company_registry"
$env:ENABLE_ETL_SCHEDULER="false"
```

---

## Step 5: Run ETL to Load Data

### Full ETL (All Data + NACE)

```powershell
cd backend

# Activate venv if not active
.\venv\Scripts\Activate.ps1

# Run ETL (this will take 30-40 minutes)
$env:RUN_ETL="true"
$env:ETL_REASON="Initial data load with NACE"
python etl_main.py
```

**Expected Output:**
```
ETL Service Boot
RUN_ETL env: true
🚀 Starting ETL (explicitly enabled)
Starting Full ETL Job...
Initializing database tables...
Tables already exist, skipping initialization.
Downloading data...
Processing Companies...
🏭 Processing NACE Industry Classification...
Loaded 5432 NACE codes and 89 sections
Updated 42,500 companies with NACE classification
✅ ETL finished successfully
```

### Quick Test (Sample Data Only)

If you want to test quickly with limited data, you can modify ETL temporarily or just wait for companies + NACE to load.

---

## Step 6: Verify Data Loaded

```powershell
# Connect to database
docker exec -it uzneumu-registrs_v2-db-1 psql -U postgres -d company_registry
```

```sql
-- Check company count
SELECT COUNT(*) FROM companies;

-- Check NACE data loaded
SELECT COUNT(*) FROM companies WHERE nace_code IS NOT NULL;
SELECT COUNT(*) FROM companies WHERE nace_section IS NOT NULL;

-- View sample companies with NACE
SELECT regcode, name, nace_code, nace_text, nace_section_text, employee_count
FROM companies 
WHERE nace_code IS NOT NULL 
LIMIT 10;

-- Check industry distribution
SELECT nace_section, nace_section_text, COUNT(*) as count
FROM companies
WHERE nace_section IS NOT NULL AND nace_section != '00'
GROUP BY nace_section, nace_section_text
ORDER BY count DESC
LIMIT 10;

-- Exit
\q
```

**Expected Results:**
- Total companies: ~200,000
- Companies with NACE: ~80,000-160,000 (40-80%)
- Top industries: IT (62), Construction (41), Retail (47), etc.

---

## Step 7: Start Backend API

```powershell
# Terminal 1: Backend
cd backend
.\venv\Scripts\Activate.ps1

# Start API server
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Verify backend is running:**
```powershell
# Test health endpoint
curl http://localhost:8001/health

# Test company with NACE data
curl http://localhost:8001/companies/40103680527

# Test benchmarking
curl http://localhost:8001/companies/40103680527/benchmark

# Test competitors
curl http://localhost:8001/companies/40103680527/competitors

# Test industries
curl http://localhost:8001/industries

# Test search with NACE filter
curl "http://localhost:8001/search?nace=62"
```

---

## Step 8: Start Frontend

```powershell
# Terminal 2: Frontend
cd frontend

# Install dependencies (if not done)
npm install

# Set environment variable
$env:NEXT_PUBLIC_API_URL="http://localhost:8001"

# Start dev server
npm run dev
```

**Verify frontend is running:**
- Open: http://localhost:3000
- Should see homepage with stats

---

## Step 9: Test NACE Features

### Frontend Testing Checklist

1. **Homepage**
   - Navigate to http://localhost:3000
   - Check "Dienas statistika" card

2. **Search**
   - Search for a company (e.g., "Mikrotikls")
   - Click on result

3. **Company Profile** 
   - Check header for purple industry badge (🏭 IT pakalpojumi)
   - Scroll down to see 2-column grid:
     - **Left:** "Pozīcija Nozarē" card
       - Should show "Top X%" for turnover/employees
       - Industry averages at bottom
     - **Right:** "Tuvākie Konkurenti" card
       - List of 5 competitors
       - Click to navigate to competitor

4. **Test Different Industries**
   - Try companies in different sectors:
     - IT: Search "software", "IT"
     - Construction: Search "būvniecība"
     - Retail: Search for shops

### API Testing

```powershell
# Find a company with NACE data
curl http://localhost:8001/search?q=mikrotikls

# Get full details (check for nace_code, nace_text, etc.)
curl http://localhost:8001/companies/{regcode-from-search}

# Test benchmarking (should return percentiles)
curl http://localhost:8001/companies/{regcode}/benchmark

# Test competitors (should return 5 companies)
curl http://localhost:8001/companies/{regcode}/competitors?limit=5

# Test industry stats
curl http://localhost:8001/industries
```

---

## Step 10: Test with Docker Compose (Production-like)

```powershell
# Stop dev servers (Ctrl+C in both terminals)

# Build and start all services
docker-compose up --build

# Or production compose
docker-compose -f docker-compose.prod.yml up --build
```

**Services will start:**
- Database: localhost:5432
- Backend: localhost:8001
- Frontend: localhost:3000

---

## 🐛 Troubleshooting

### Issue: No NACE data in companies

**Check:**
```sql
SELECT COUNT(*) FROM companies WHERE nace_code IS NOT NULL;
```

**If 0:**
```powershell
# Re-run ETL
cd backend
$env:RUN_ETL="true"
python etl_main.py
```

### Issue: Backend can't find NACE.csv

**Error:** `NACE.csv not found in project root`

**Fix:**
```powershell
# Verify NACE.csv is in project root
Get-ChildItem NACE.csv

# Should show: NACE.csv in root directory
# If not, copy it there
```

### Issue: Database connection failed

**Error:** `could not connect to server`

**Fix:**
```powershell
# Check database is running
docker ps | Select-String postgres

# If not, start it
docker-compose up -d db
```

### Issue: Frontend shows no industry badge

**Reasons:**
1. Company has no NACE data (check API response)
2. API not returning NACE fields (check backend logs)
3. Frontend not fetching correctly (check browser console)

**Debug:**
```powershell
# Check API response
curl http://localhost:8001/companies/40103680527 | ConvertFrom-Json | Select-Object nace_code, nace_text
```

### Issue: Benchmarking shows "No data"

**Reasons:**
- Company has no NACE section
- No other companies in same industry
- No financial data for percentile calculation

**Verify:**
```sql
-- Check company's NACE
SELECT regcode, nace_section, nace_section_text 
FROM companies 
WHERE regcode = 40103680527;

-- Check industry has multiple companies
SELECT COUNT(*) 
FROM companies 
WHERE nace_section = (SELECT nace_section FROM companies WHERE regcode = 40103680527);
```

---

## 📊 Sample Test Data

Good companies to test with (likely have NACE data):

```
40103680527 - Mikrotīkls SIA (IT)
40003551060 - Latvenergo AS (Energy)
40003023209 - Rīgas Satiksme (Transport)
```

Search and test with these to see full NACE features.

---

## ✅ Success Criteria

Your local setup is working if:

- [ ] Database contains companies with nace_code
- [ ] Backend API returns NACE fields in `/companies/{id}`
- [ ] Benchmarking endpoint returns percentiles
- [ ] Competitors endpoint returns 5 companies
- [ ] Industries endpoint lists all sectors
- [ ] Frontend shows purple industry badge
- [ ] "Pozīcija Nozarē" card displays
- [ ] "Tuvākie Konkurenti" section has data
- [ ] Clicking competitor navigates to their profile

---

## 🚀 Ready for Railway?

Once local testing passes, you can deploy to Railway:

```powershell
git status
git add .
git commit -m "feat: complete NACE implementation - tested locally"
git push origin main
```

Railway will automatically:
1. Build new images
2. Run migrations
3. Restart services
4. ETL will run on next cron trigger (3:00 AM) or manual trigger
