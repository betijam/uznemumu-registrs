-- Add company size history tracking table
-- Run this migration to enable year-by-year size tracking

CREATE TABLE IF NOT EXISTS company_size_history (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT REFERENCES companies(regcode),
    year INTEGER NOT NULL,
    size_category VARCHAR(20), -- 'Mikro', 'Mazs', 'Vidējs', 'Liels'
    employees INTEGER,
    turnover DECIMAL(15,2),
    total_assets DECIMAL(15,2),
    calculated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(company_regcode, year)
);

CREATE INDEX idx_size_history_regcode ON company_size_history(company_regcode);
CREATE INDEX idx_size_history_year ON company_size_history(year);
CREATE INDEX idx_size_history_category ON company_size_history(size_category);

-- Add helper column to companies table for quick access to latest size
-- (This is redundant with history but optimizes common queries)
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS latest_size_year INTEGER,
ADD COLUMN IF NOT EXISTS size_changed_recently BOOLEAN DEFAULT FALSE;

COMMENT ON TABLE company_size_history IS 'Year-by-year EU SME size classification history';
COMMENT ON COLUMN company_size_history.size_category IS 'EU classification: Mikro, Mazs, Vidējs, Liels';
COMMENT ON COLUMN companies.size_changed_recently IS 'TRUE if size category changed in last year';
