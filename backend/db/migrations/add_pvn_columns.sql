-- Add PVN (VAT) taxpayer columns to companies table
-- Replaces sepa_identifier with official PVN registry data

ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS pvn_number VARCHAR(20),  -- Full PVN number with "LV" prefix
ADD COLUMN IF NOT EXISTS is_pvn_payer BOOLEAN DEFAULT FALSE;

-- Index for quick PVN lookups
CREATE INDEX IF NOT EXISTS idx_companies_pvn ON companies(pvn_number);
CREATE INDEX IF NOT EXISTS idx_companies_is_pvn_payer ON companies(is_pvn_payer);

-- Comments
COMMENT ON COLUMN companies.pvn_number IS 'PVN registration number (format: LV40103680527)';
COMMENT ON COLUMN companies.is_pvn_payer IS 'TRUE if company is active PVN (VAT) taxpayer';

-- Note: sepa_identifier column can be deprecated after PVN migration
