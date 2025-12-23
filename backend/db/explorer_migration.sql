-- Migration for Explorer Module (Faster filtering)

-- 1. Composite index for financial filtering (Year + Sorts)
-- Used when filtering by year and sorting by turnover/profit (Top Lists)
CREATE INDEX IF NOT EXISTS idx_financial_filter ON financial_reports(year, turnover DESC, profit DESC);

-- 2. Index for NACE filtering
-- Used for the Industry Filter
CREATE INDEX IF NOT EXISTS idx_companies_nace_idx ON companies(nace_code);

-- 3. Region/Address text search index (if not exists)
-- Simple GIN index on address for "Region" filtering (LIKE %Riga%)
CREATE INDEX IF NOT EXISTS idx_companies_address_gin ON companies USING GIN(to_tsvector('simple', address));

-- 4. Status index for fast filtering active/liquidated
CREATE INDEX IF NOT EXISTS idx_companies_status_lower ON companies(lower(status));
