
-- 1. Delete explicitly consolidated reports (UKGP)
-- This is safe because we prefer UGP (or legacy NULL)
DELETE FROM financial_reports WHERE source_type = 'UKGP';

-- 2. Deduplicate remaining rows (if any duplicates exist for same regcode+year)
-- Keep the one with the highest ID (latest inserted)
DELETE FROM financial_reports a USING financial_reports b
WHERE a.id < b.id 
  AND a.company_regcode = b.company_regcode 
  AND a.year = b.year;

-- 3. Add UNIQUE constraint to prevent future duplicates
-- This enables fast UPSERT (ON CONFLICT DO UPDATE) in loader.py
ALTER TABLE financial_reports 
ADD CONSTRAINT unique_company_year UNIQUE (company_regcode, year);

-- 4. Analyze to update stats
ANALYZE financial_reports;
