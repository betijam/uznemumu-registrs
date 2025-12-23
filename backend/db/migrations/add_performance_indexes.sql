-- Performance indexes for /stats endpoint
-- Run on Railway PostgreSQL

-- Index for registration date queries (dienas statistika)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_registration_date 
ON companies(registration_date);

-- Index for financial reports - optimizes top earner query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_reports_year_turnover 
ON financial_reports(year DESC, turnover DESC NULLS LAST);

-- Index for procurements date queries (weekly procurements)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_procurements_contract_date 
ON procurements(contract_date);

-- Verify indexes created
SELECT indexname, indexdef FROM pg_indexes 
WHERE tablename IN ('companies', 'financial_reports', 'procurements');
