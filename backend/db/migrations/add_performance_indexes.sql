-- Performance indexes for homepage stats and company page
-- Run on Railway PostgreSQL

-- ============= HOMEPAGE STATS =============

-- Index for registration date queries (dienas statistika)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_registration_date 
ON companies(registration_date);

-- Index for financial reports - optimizes top earner query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_reports_year_turnover 
ON financial_reports(year DESC, turnover DESC NULLS LAST);

-- Index for procurements date queries (weekly procurements)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_procurements_contract_date 
ON procurements(contract_date);

-- ============= COMPANY PAGE =============

-- Financial reports by company (used in get_company_details)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_reports_regcode 
ON financial_reports(company_regcode);

-- Tax payments by company
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tax_payments_regcode 
ON tax_payments(company_regcode);

-- Persons by company (UBOs, members, officers)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_persons_regcode 
ON persons(company_regcode);

-- Procurements by winner (company page procurement history)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_procurements_winner 
ON procurements(winner_regcode);

-- Active risks only (filtered query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risks_regcode_active 
ON risks(company_regcode) WHERE active = TRUE;

-- Company ratings by regcode
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_company_ratings_regcode 
ON company_ratings(company_regcode);

-- ============= VERIFY =============
SELECT indexname, tablename FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%'
ORDER BY tablename;
