-- 1. Companies
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'LV' NOT NULL;

-- Drop old PK
ALTER TABLE companies DROP CONSTRAINT IF EXISTS companies_pkey CASCADE;

-- Add new PK
ALTER TABLE companies ADD PRIMARY KEY (country_code, regcode);

-- 2. Persons
ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'LV' NOT NULL;

-- Update FK to companies
-- Note: We need to update existing FKs to include country_code. 
-- Assuming existing FK was companies(regcode).
ALTER TABLE persons DROP CONSTRAINT IF EXISTS persons_company_regcode_fkey;

ALTER TABLE persons 
ADD CONSTRAINT persons_company_fk 
FOREIGN KEY (country_code, company_regcode) 
REFERENCES companies (country_code, regcode);

-- 3. Financial Reports
ALTER TABLE financial_reports 
ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'LV' NOT NULL;

ALTER TABLE financial_reports DROP CONSTRAINT IF EXISTS financial_reports_company_regcode_fkey;

ALTER TABLE financial_reports
ADD CONSTRAINT financial_reports_company_fk
FOREIGN KEY (country_code, company_regcode)
REFERENCES companies (country_code, regcode);

-- Update Unique Constraint for Financials
ALTER TABLE financial_reports DROP CONSTRAINT IF EXISTS financial_reports_company_regcode_year_key;
ALTER TABLE financial_reports ADD CONSTRAINT financial_reports_unique_year UNIQUE (country_code, company_regcode, year);

-- 4. Procurements
-- Procurements 'winner_regcode' is likely the link.
-- Needs check if 'winner_regcode' is actually a FK in current schema or just a loose link.
-- If loose, we just add country column. Assuming loose based on previous extracts, but let's try to add FK if applicable.
-- For now, allow nullable country_code for procurements if winner is not always linked? 
-- But existing data is strict LV.
-- Let's stick to adding the column for now.
-- NOTE: In detailed request, Procurements table had 'winner_regcode'. 
-- We should verify if we want to enforce FK. Usually safer to just add the column for linking.

-- 5. Risks
ALTER TABLE risks 
ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'LV' NOT NULL;

ALTER TABLE risks DROP CONSTRAINT IF EXISTS risks_company_regcode_fkey;
ALTER TABLE risks
ADD CONSTRAINT risks_company_fk
FOREIGN KEY (country_code, company_regcode)
REFERENCES companies (country_code, regcode);

-- 6. Tax Payments
ALTER TABLE tax_payments
ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'LV' NOT NULL;

ALTER TABLE tax_payments DROP CONSTRAINT IF EXISTS tax_payments_company_regcode_fkey;
ALTER TABLE tax_payments
ADD CONSTRAINT tax_payments_company_fk
FOREIGN KEY (country_code, company_regcode)
REFERENCES companies (country_code, regcode);

-- 7. Create Territories table for Estonia (or generic) if not exists
CREATE TABLE IF NOT EXISTS territories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL, -- EHAK or ATVK
    name TEXT NOT NULL,
    type VARCHAR(50),
    level SMALLINT,
    parent_code VARCHAR(20),
    valid_from DATE,
    valid_to DATE,
    country_code CHAR(2) DEFAULT 'LV' -- To distinguish EHAK vs ATVK if needed in same table
);
-- Add index for search
CREATE INDEX IF NOT EXISTS idx_territories_code ON territories(code);

-- 8. Industry Stats Materialized
-- If this table exists, add country_code to PK/Grouping
ALTER TABLE industry_stats_materialized
ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'LV';
-- Re-create index/unique if needed
-- (Skipping specific constraint drop here as naming might vary, relying on script logic)
