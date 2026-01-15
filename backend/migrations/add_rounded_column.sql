
ALTER TABLE financial_reports 
ADD COLUMN IF NOT EXISTS rounded_to_nearest TEXT DEFAULT 'ONES';
