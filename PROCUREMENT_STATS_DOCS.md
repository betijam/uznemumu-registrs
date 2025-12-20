# 📊 Procurement & Homepage Statistics - Technical Documentation

## 1. Valsts Iepirkumi (Procurement) Section

### Data Display Logic - Company Profile

**Location:** Company detail page → "Valsts iepirkumi" tab
**API Endpoint:** `GET /companies/{regcode}`
**Code:** `backend/app/routers/companies.py` lines 288-304

### SQL Query
```sql
SELECT authority_name, subject, amount, contract_date
FROM procurements
WHERE winner_regcode = :regcode
ORDER BY contract_date DESC 
LIMIT 10
```

### Filtering Rules

#### ✅ **What IS Displayed:**
- **Only WON contracts** (uzvarēti iepirkumi)
- **Company must be winner** (`winner_regcode` matches company)
- **Top 10 most recent** by contract date
- **All years included** (2018-2025, no year filter)
- **No amount filter** (includes all contract sizes)

#### ❌ **What is NOT Displayed:**
- Procurement bids (participation without winning)
- Contracts where company is not the winner
- Contracts older than the 10 most recent
- Draft/unsigned contracts (only finalized with `contract_date`)

### Data Source & Years

**Data comes from:** EIS (Elektroniskā Iepirkumu Sistēma)

**Years Loaded (ETL):**
```python
EIS_RESULTS_URLS = {
    2025: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2025.csv",
    2024: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2024.csv",
    2023: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2023.csv",
    2022: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2022.csv",
    2021: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2021.csv",
    2020: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2020.csv",
    2019: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2019.csv",
    2018: "https://data.gov.lv/.../eis_e_iepirkumi_rezultati_2018.csv"
}
```

**Total historical range:** **8 years** (2018-2025)

### ETL Processing Logic

**File:** `backend/etl/process_procurements.py`

**Key Steps:**

1. **Validation Against Companies Table**
   ```python
   # Only load procurements for companies that exist in our database
   df = df[df['winner_regcode'].isin(valid_regcodes)]
   ```

2. **Data Cleaning**
   - Removes spaces from amounts: `"100 000,50"` → `100000.50`
   - Converts European decimal format: `","` → `"."`
   - Parses dates to standard format
   - Filters invalid registration codes

3. **Field Mapping**
   ```python
   'Uzvaretaja_registracijas_numurs' → 'winner_regcode'
   'Liguma_dok_noslegsanas_datums'  → 'contract_date'
   'Pasutitaja_nosaukums'            → 'authority_name'
   'Iepirkuma_nosaukums'             → 'subject'
   'Aktuala_liguma_summa'            → 'amount'
   'Hipersaite_EIS...'               → 'source_link'
   ```

4. **Storage**
   - All years appended to same table
   - No truncation between years
   - Full history maintained

### Display Format (Frontend)

**Fields Shown:**
- **Pasūtītājs** (Authority) - Who ordered
- **Priekšmets** (Subject) - What was ordered
- **Summa** (Amount) - Contract value in EUR
- **Datums** (Date) - Contract signing date

**Sorting:** Newest first (`ORDER BY contract_date DESC`)

**Example:**
```
Latvijas Banka | Par Latvijas Bankas naudas apstrādes... | € 19 480 | 2024-01-15
```

---

## 2. Homepage KPI Statistics

### Location
Homepage → Three stat cards at top

**API Endpoint:** `GET /stats`
**Code:** `backend/app/routers/search.py` lines 9-59

### KPI #1: Dienas statistika (Daily Stats)

![Dienas statistika card](uploaded_image_1_1766256422692.png)

**SQL Query:**
```sql
SELECT COUNT(*) as cnt 
FROM companies 
WHERE registration_date >= CURRENT_DATE
```

**What It Shows:**
- **Number:** Companies registered **TODAY** (šodien)
- **Change:** `today_count - 10` (mock calculation - **not real trend**)

**Logic:**
```python
today_count = conn.execute(text("""
    SELECT COUNT(*) as cnt 
    FROM companies 
    WHERE registration_date >= CURRENT_DATE
""")).scalar() or 0

stats["daily_stats"]["new_today"] = today_count
stats["daily_stats"]["change"] = max(0, today_count - 10)  # Simple mock
```

**⚠️ Important:** 
- **Change** is **MOCK DATA** (fake trend calculation)
- Only counts companies with `registration_date = TODAY`
- Does **NOT** include historical trends
- Icon shows ↑ or ↓ based on mock change

### KPI #2: TOP Pelnošie (Top Earner)

**SQL Query:**
```sql
SELECT c.name, f.turnover
FROM financial_reports f
JOIN companies c ON c.regcode = f.company_regcode
WHERE f.turnover IS NOT NULL
ORDER BY f.turnover DESC
LIMIT 1
```

**What It Shows:**
- Company with **highest turnover** (apgrozījums)
- **ANY year** (no year filter)
- Detail: `"Apgrozījums: {amount} €"`

**Logic:**
```python
top_earner = conn.execute(text("""
    SELECT c.name, f.turnover
    FROM financial_reports f
    JOIN companies c ON c.regcode = f.company_regcode
    WHERE f.turnover IS NOT NULL
    ORDER BY f.turnover DESC
    LIMIT 1
""")).fetchone()

if top_earner:
    stats["top_earner"]["name"] = top_earner.name
    stats["top_earner"]["detail"] = f"Apgrozījums: {top_earner.turnover:,.0f} €"
```

**Filters Applied:**
- ✅ Turnover must NOT be NULL
- ✅ Must have financial report
- ❌ **NO year filter** (could be from 2015 or 2024)
- ❌ **NO status filter** (could be inactive company)

### KPI #3: TOP Iepirkumi (Top Procurement Revenue)

**SQL Query:**
```sql
SELECT SUM(amount) as total, COUNT(*) as cnt
FROM procurements
WHERE contract_date >= CURRENT_DATE - INTERVAL '7 days'
```

**What It Shows:**
- **Total procurement value** from **last 7 days**
- Formatted in **millions** (`M€`)
- Detail: `"{count} iepirkumi pēdējā nedēļā"`

**Logic:**
```python
top_procurement = conn.execute(text("""
    SELECT SUM(amount) as total, COUNT(*) as cnt
    FROM procurements
    WHERE contract_date >= CURRENT_DATE - INTERVAL '7 days'
""")).fetchone()

if top_procurement and top_procurement.total:
    total_m = top_procurement.total / 1_000_000
    stats["top_revenue"]["amount"] = f"{total_m:.1f} M€"
    stats["top_revenue"]["detail"] = f"{top_procurement.cnt} iepirkumi pēdējā nedēļā"
```

**Filters Applied:**
- ✅ Only contracts from **last 7 days**
- ✅ Sums **ALL procurements** (all companies, all authorities)
- ✅ Converts to millions for display
- ❌ **NO company filter** (total across entire system)
- ❌ **NO minimum amount** (includes all contract sizes)

**Example Output:**
```json
{
  "amount": "322.3 M€",
  "detail": "10 iepirkumi pēdējā nedēļā"
}
```

---

## 🔍 Key Differences Summary

### Procurement Section (Company Profile)
| Aspect | Value |
|--------|-------|
| **Scope** | Single company only |
| **Years** | All years (2018-2025) |
| **Limit** | Top 10 most recent |
| **Filter** | Only WON contracts |
| **Sort** | Newest first |

### Homepage KPI - TOP Iepirkumi
| Aspect | Value |
|--------|-------|
| **Scope** | **ALL companies** (system-wide) |
| **Years** | Last **7 days only** |
| **Limit** | No limit (SUM all) |
| **Filter** | All contracts in timeframe |
| **Display** | Total value in millions |

---

## 📊 Data Quality Notes

### Procurement Coverage
- **Data Source:** Official EIS system (government procurement platform)
- **Update Frequency:** ETL runs fetch latest data
- **Historical Depth:** 8 years (2018-2025)
- **Completeness:** Only companies that exist in our `companies` table

### Statistical Accuracy

**✅ Accurate:**
- Daily new company count
- Top earner by turnover (factual)
- Procurement totals (factual sums)

**⚠️ Mock/Simplified:**
- Daily stats "change" (line 28: `today_count - 10`)
- No real trend analysis
- Top earner doesn't specify year

---

## 🛠️ Potential Improvements

### Homepage Stats
1. **Real Trend Calculation**
   ```sql
   -- Compare today vs yesterday
   SELECT 
     (SELECT COUNT(*) FROM companies WHERE registration_date = CURRENT_DATE) -
     (SELECT COUNT(*) FROM companies WHERE registration_date = CURRENT_DATE - 1)
   ```

2. **Add Year to Top Earner**
   ```python
   "detail": f"Apgrozījums: {turnover:,.0f} € ({year})"
   ```

3. **Configurable Procurement Timeframe**
   ```python
   # Make "7 days" a parameter
   WHERE contract_date >= CURRENT_DATE - INTERVAL :days days
   ```

### Procurement Display
1. **Add Year Filter UI**
   - Allow filtering by year: 2024, 2023, etc.
   - Show year distribution chart

2. **Pagination**
   - Currently shows only 10
   - Add "Show more" button

3. **Total Stats**
   ```sql
   -- Show totals for this company
   SELECT 
     COUNT(*) as total_contracts,
     SUM(amount) as total_value,
     MIN(contract_date) as first_contract,
     MAX(contract_date) as latest_contract
   FROM procurements
   WHERE winner_regcode = :regcode
   ```

---

## 🧪 Testing Queries

### Check Procurement Data
```sql
-- How many procurements total?
SELECT COUNT(*) FROM procurements;

-- Procurements by year
SELECT year, COUNT(*), SUM(amount)/1000000 as total_millions
FROM procurements
GROUP BY year
ORDER BY year DESC;

-- Top 10 companies by procurement wins
SELECT c.name, COUNT(*) as wins, SUM(p.amount)/1000000 as total_m
FROM procurements p
JOIN companies c ON c.regcode = p.winner_regcode
GROUP BY c.name
ORDER BY wins DESC
LIMIT 10;

-- Recent 7-day activity (homepage stat)
SELECT COUNT(*), SUM(amount)/1000000 as total_m
FROM procurements
WHERE contract_date >= CURRENT_DATE - INTERVAL '7 days';
```

### Check Homepage Stats Data
```sql
-- Today's new companies
SELECT COUNT(*) FROM companies WHERE registration_date >= CURRENT_DATE;

-- Top earner
SELECT c.name, MAX(f.turnover) as max_turnover
FROM financial_reports f
JOIN companies c ON c.regcode = f.company_regcode
GROUP BY c.name
ORDER BY max_turnover DESC
LIMIT 1;
```

---

## 📝 Code References

### Backend Files
- **Procurement ETL:** `backend/etl/process_procurements.py`
- **Homepage Stats:** `backend/app/routers/search.py` (lines 9-59)
- **Company Procurements:** `backend/app/routers/companies.py` (lines 288-304)
- **Config (URLs):** `backend/etl/config.py` (EIS_RESULTS_URLS)

### Database Tables
- `procurements` - Won contracts (results)
- `procurement_bids` - Participation (openings) - **NOT displayed in UI**
- `companies` - For validation and joining
- `financial_reports` - For TOP Pelnošie stat

### Frontend Display
- Homepage: `frontend/src/app/page.tsx`
- Company Profile: `frontend/src/components/CompanyTabs.tsx`
