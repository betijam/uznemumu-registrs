
-- 1. Companies: Functional indexes for fast unaccented search
CREATE INDEX IF NOT EXISTS idx_companies_name_lower_unaccent ON companies USING gin (immutable_unaccent(lower(name)) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_name_quotes_lower_unaccent ON companies USING gin (immutable_unaccent(lower(name_in_quotes)) gin_trgm_ops);

-- 2. Persons: The biggest bottleneck
-- We need a similar index on persons to prevent full table scans
CREATE INDEX IF NOT EXISTS idx_persons_name_lower_unaccent ON persons USING gin (immutable_unaccent(lower(person_name)) gin_trgm_ops);

-- 3. Ensure turnover column exists and is indexed (from previous step, just as backup)
CREATE INDEX IF NOT EXISTS idx_companies_turnover_desc ON companies (latest_turnover DESC NULLS LAST);
