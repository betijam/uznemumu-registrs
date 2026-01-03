-- Add contract end date and termination date columns
ALTER TABLE procurements ADD COLUMN IF NOT EXISTS contract_end_date DATE;
ALTER TABLE procurements ADD COLUMN IF NOT EXISTS termination_date DATE;

-- Create index for performance on date filtering (for expiring contracts)
CREATE INDEX IF NOT EXISTS idx_procurements_end_date ON procurements(contract_end_date);
