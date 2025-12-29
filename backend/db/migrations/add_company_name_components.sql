-- Migration: Add company name component columns
-- Date: 2025-12-29
-- Description: Extract and store name_in_quotes, type, type_text, and addressid from register.csv

-- Add new columns to companies table
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS name_in_quotes TEXT,
ADD COLUMN IF NOT EXISTS type TEXT,
ADD COLUMN IF NOT EXISTS type_text TEXT,
ADD COLUMN IF NOT EXISTS addressid TEXT;

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_companies_type ON companies(type);

-- Verify migration
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'name_in_quotes'
    ) THEN
        RAISE EXCEPTION 'Migration failed: name_in_quotes column not found';
    END IF;
    
    RAISE NOTICE 'Migration completed successfully: Company name components added';
END $$;
