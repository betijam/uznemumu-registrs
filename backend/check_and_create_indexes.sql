-- Check existing indexes on key tables
-- Run this in Neon database console

-- 1. Check indexes on companies table
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'companies'
ORDER BY indexname;

-- 2. Check indexes on financial_reports table
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'financial_reports'
ORDER BY indexname;

-- 3. Check indexes on persons table (officers, members)
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('officers', 'members', 'ubos')
ORDER BY tablename, indexname;

-- 4. Create missing indexes if needed
-- Uncomment and run these if indexes don't exist:

-- CREATE INDEX IF NOT EXISTS idx_companies_regcode ON companies(regcode);
-- CREATE INDEX IF NOT EXISTS idx_financial_reports_regcode ON financial_reports(company_regcode);
-- CREATE INDEX IF NOT EXISTS idx_financial_reports_year ON financial_reports(year);
-- CREATE INDEX IF NOT EXISTS idx_officers_regcode ON officers(company_regcode);
-- CREATE INDEX IF NOT EXISTS idx_members_regcode ON members(company_regcode);
-- CREATE INDEX IF NOT EXISTS idx_ubos_regcode ON ubos(company_regcode);
-- CREATE INDEX IF NOT EXISTS idx_procurements_regcode ON procurements(company_regcode);
-- CREATE INDEX IF NOT EXISTS idx_risks_regcode ON risks(company_regcode);
