# 🏭 NACE-Only Processing Guide

Quick guide to run **ONLY** NACE industry classification without full ETL.

---

## 🚀 Method 1: Railway Shell (Easiest)

### Step 1: Connect to Railway
```bash
railway login
railway link  # Select your project
```

### Step 2: Open Shell Session
```bash
railway shell --service backend
```

### Step 3: Run NACE Script
```bash
cd /app
python run_nace_only.py
```

**Expected Output:**
```
============================================================
NACE CLASSIFICATION - STANDALONE RUN
============================================================
Step 1: Locating NACE.csv...
✅ Found NACE.csv at: /app/NACE.csv
Step 2: Downloading VID tax data...
Downloaded 139382 VID records
Step 3: Saving temporary VID data...
Step 4: Processing NACE classification...
🏭 Processing NACE Industry Classification...
...
✅ NACE CLASSIFICATION COMPLETED SUCCESSFULLY
============================================================
```

**Time:** ~5-10 minutes (vs 30-40 for full ETL)

---

## 🔄 Method 2: Railway One-liner

```bash
railway run --service backend python run_nace_only.py
```

---

## 💻 Method 3: Local Execution (Against Railway DB)

### Step 1: Get Railway Database URL
```bash
railway variables --service backend | grep DATABASE_URL
```

### Step 2: Run Locally
```bash
cd backend
export DATABASE_URL="postgresql://postgres:xxx@xxx.railway.app:xxxx/railway"
python run_nace_only.py
```

---

## 🛠️ Method 4: Create Railway API Endpoint (Future)

Add to `backend/main.py`:

```python
from fastapi import Header, HTTPException

@app.post("/admin/trigger-nace")
async def trigger_nace(authorization: str = Header(None)):
    """Manually trigger NACE processing (admin only)"""
    
    # Simple auth check
    if authorization != f"Bearer {os.getenv('ADMIN_SECRET', 'changeme')}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Run in background
    import subprocess
    subprocess.Popen(["python", "run_nace_only.py"])
    
    return {"status": "NACE processing started in background"}
```

Then trigger via:
```bash
curl -X POST https://your-backend.railway.app/admin/trigger-nace \
  -H "Authorization: Bearer YOUR_SECRET"
```

---

## ✅ Verification

After NACE processing completes, verify:

```bash
# Connect to database
railway connect postgres

# Check NACE coverage
SELECT 
  COUNT(*) FILTER (WHERE nace_code IS NOT NULL) as with_nace,
  COUNT(*) as total,
  ROUND(COUNT(*) FILTER (WHERE nace_code IS NOT NULL)::numeric / COUNT(*) * 100, 1) as coverage_pct
FROM companies;

# Top industries
SELECT nace_section, nace_section_text, COUNT(*) as companies
FROM companies
WHERE nace_section IS NOT NULL
GROUP BY nace_section, nace_section_text
ORDER BY companies DESC
LIMIT 10;
```

**Expected:**
- ~80% coverage (160k+ companies with NACE)
- Sections like "62" (IT), "46" (Wholesale), "41" (Construction)

---

## 🐛 Troubleshooting

### "NACE.csv not found"
**Fix:** Ensure `backend/NACE.csv` exists in latest deploy
```bash
railway run --service backend ls -la NACE.csv
```

### "VID download failed"
**Fix:** VID URL might be down, check `backend/etl/config.py` for latest URL

### "Database connection failed"
**Fix:** Ensure `DATABASE_URL` env var is set in Railway

### Process hangs
**Fix:** Railway shell timeout. Use `railway run` instead:
```bash
railway run --service backend python run_nace_only.py
```

---

## 📊 What Gets Updated

NACE-only processing updates these fields in `companies` table:
- `nace_code` (e.g., "6201")
- `nace_text` (e.g., "Datorprogrammēšana")
- `nace_section` (e.g., "62")
- `nace_section_text` (e.g., "IT pakalpojumi")
- `employee_count` (from latest VID data)
- `tax_data_year` (e.g., 2024)

**Does NOT touch:**
- Financial reports
- Procurements
- Company registry data
- Ratings/risks

---

## 🔐 Security Note

`run_nace_only.py` requires database access. 

**For production:**
- Add authentication to API endpoint method
- Use Railway secrets for admin tokens
- Monitor execution logs

---

## 📞 Quick Reference Commands

```bash
# Railway Shell
railway shell --service backend
python run_nace_only.py

# One-liner
railway run --service backend python run_nace_only.py

# Check status
railway logs --service backend | grep NACE

# Verify results
railway connect postgres
SELECT COUNT(*) FROM companies WHERE nace_code IS NOT NULL;
```
