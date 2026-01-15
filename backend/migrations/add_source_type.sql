
-- Add source_type column to financial_reports to distinguish consolidated data (UKGP)
-- UKGP = Consolidated (should be ignored for stats/charts)
-- UGP = Standard
-- NULL = Standard (Legacy)

ALTER TABLE financial_reports 
ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT NULL;

-- Create index for faster filtering
-- We will frequently filter by (source_type IS NULL OR source_type = 'UGP')
-- A partial index works great here
CREATE INDEX IF NOT EXISTS idx_financial_reports_source_type 
ON financial_reports(company_regcode, year) 
WHERE source_type IS NULL OR source_type = 'UGP';
