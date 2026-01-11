"""
ETL State Tracking: Add timestamps and state management
"""

-- Create ETL state tracking table
CREATE TABLE IF NOT EXISTS etl_state (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) UNIQUE NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'IDLE',
    error_message TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial state for extended financial fields job
INSERT INTO etl_state (job_name, status) 
VALUES ('extended_financial_fields', 'IDLE')
ON CONFLICT (job_name) DO NOTHING;

-- Add created/updated timestamps to financial_reports
ALTER TABLE financial_reports 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_financial_reports_created_at 
ON financial_reports(created_at);

-- Backfill existing records with current timestamp
UPDATE financial_reports 
SET created_at = NOW(), updated_at = NOW() 
WHERE created_at IS NULL;

-- Verify
SELECT COUNT(*) as total_records, 
       COUNT(created_at) as with_created_at 
FROM financial_reports;

SELECT * FROM etl_state WHERE job_name = 'extended_financial_fields';
