-- Migration for Business Intelligence Dashboard
-- 1. Create table for caching static dashboard data (Tops, Pulse aggregates)
-- This table will store pre-computed JSON blobs to be served instantly by the API.

CREATE TABLE IF NOT EXISTS dashboard_cache (
    key TEXT PRIMARY KEY,          -- e.g., 'main_dashboard'
    data JSONB NOT NULL,           -- The full JSON payload for the frontend
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Create optimized index for "Live" pulse queries (New Today/This Week)
-- We need to count companies registered in the last few days quickly.
CREATE INDEX IF NOT EXISTS idx_companies_reg_date_desc ON companies(registration_date DESC);

-- 3. Create optimized index for "Active" count
-- Used for "Total Active Companies" pulse metric.
CREATE INDEX IF NOT EXISTS idx_companies_status_active ON companies(status) WHERE status = 'A';

-- 4. Create indexes for Top List queries (Turnover, Profit) if they don't exist
-- These help the worker script calculate tops faster.
CREATE INDEX IF NOT EXISTS idx_financial_reports_turnover_year ON financial_reports(year, turnover DESC);
CREATE INDEX IF NOT EXISTS idx_financial_reports_profit_year ON financial_reports(year, profit DESC);
