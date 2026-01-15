
-- 1. Add column to companies table
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS latest_turnover BIGINT DEFAULT 0;

-- 2. Populate it with data from financial_reports (Optimize this Update)
-- We use a CTE to get the latest turnover for each company once
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode) 
        company_regcode, 
        turnover 
    FROM financial_reports 
    WHERE turnover IS NOT NULL 
    AND turnover != 'NaN'
    ORDER BY company_regcode, year DESC
)
UPDATE companies c
SET latest_turnover = lf.turnover
FROM latest_financials lf
WHERE c.regcode = lf.company_regcode;

-- 3. Create Index for fast sorting by turnover
CREATE INDEX IF NOT EXISTS idx_companies_turnover ON companies (latest_turnover DESC NULLS LAST);

-- 4. Create Index for similarity search combined with turnover (Experimental, might help if PG uses it)
-- Usually separate indexes are fine, but let's ensure base indexes exist
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON companies USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_name_quotes_trgm ON companies USING GIN (name_in_quotes gin_trgm_ops);
