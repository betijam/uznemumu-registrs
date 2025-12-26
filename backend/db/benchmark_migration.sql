-- ==========================================
-- Benchmark Tool - Database Migration
-- Creates tables for company comparison functionality
-- ==========================================

-- 1. BENCHMARK SESSIONS
-- Stores user comparison sessions for shareability and analytics
CREATE TABLE IF NOT EXISTS benchmark_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NULL,  -- FK to users if auth is implemented, NULL for anonymous
    created_at TIMESTAMP DEFAULT NOW(),
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    company_ids TEXT NOT NULL,  -- Comma-separated registration numbers
    source VARCHAR(50) CHECK (source IN ('company_profile', 'company_list', 'direct_url')),
    
    -- Validation: ensure 2-5 companies
    CONSTRAINT check_company_count CHECK (
        array_length(string_to_array(company_ids, ','), 1) BETWEEN 2 AND 5
    )
);

CREATE INDEX IF NOT EXISTS idx_benchmark_sessions_created_at ON benchmark_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_benchmark_sessions_user_id ON benchmark_sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_benchmark_sessions_year ON benchmark_sessions(year);


-- 2. INDUSTRY YEAR AGGREGATES
-- Pre-computed statistics per industry per year for benchmark comparisons
CREATE TABLE IF NOT EXISTS industry_year_aggregates (
    id SERIAL PRIMARY KEY,
    industry_code VARCHAR(10) NOT NULL,  -- NACE code
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    
    -- Aggregated metrics
    avg_revenue NUMERIC(15,2),
    median_revenue NUMERIC(15,2),
    avg_profit NUMERIC(15,2),
    avg_profit_margin NUMERIC(5,2),  -- Percentage
    avg_employees INTEGER,
    avg_salary NUMERIC(10,2),
    avg_revenue_per_employee NUMERIC(15,2),
    
    -- Company counts
    total_companies INTEGER DEFAULT 0,
    profitable_companies INTEGER DEFAULT 0,
    
    -- Percentile thresholds (for ranking)
    revenue_p25 NUMERIC(15,2),  -- 25th percentile
    revenue_p50 NUMERIC(15,2),  -- Median
    revenue_p75 NUMERIC(15,2),  -- 75th percentile
    revenue_p90 NUMERIC(15,2),  -- 90th percentile
    
    -- Metadata
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(industry_code, year)
);

CREATE INDEX IF NOT EXISTS idx_industry_aggregates_lookup ON industry_year_aggregates(industry_code, year);
CREATE INDEX IF NOT EXISTS idx_industry_aggregates_year ON industry_year_aggregates(year);


-- 3. COMPANY INDUSTRY RANKINGS
-- Pre-computed rankings per company per industry per year
-- This speeds up benchmark queries significantly
CREATE TABLE IF NOT EXISTS company_industry_rankings (
    id SERIAL PRIMARY KEY,
    company_regcode BIGINT NOT NULL,
    industry_code VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    
    -- Rankings
    revenue_rank INTEGER,  -- Position by revenue (1 = highest)
    profit_rank INTEGER,   -- Position by profit
    employee_rank INTEGER, -- Position by employee count
    
    -- Totals for percentile calculation
    total_companies INTEGER,
    
    -- Percentiles
    revenue_percentile NUMERIC(5,2),  -- 0-100
    profit_percentile NUMERIC(5,2),
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(company_regcode, industry_code, year)
);

CREATE INDEX IF NOT EXISTS idx_company_rankings_lookup ON company_industry_rankings(company_regcode, industry_code, year);
CREATE INDEX IF NOT EXISTS idx_company_rankings_company ON company_industry_rankings(company_regcode);
CREATE INDEX IF NOT EXISTS idx_company_rankings_year ON company_industry_rankings(year);


-- ==========================================
-- VIEWS FOR EASIER QUERYING
-- ==========================================

-- View: Latest industry aggregates
CREATE OR REPLACE VIEW v_industry_latest_stats AS
SELECT DISTINCT ON (industry_code)
    industry_code,
    year,
    avg_revenue,
    avg_profit_margin,
    avg_employees,
    avg_salary,
    avg_revenue_per_employee,
    total_companies
FROM industry_year_aggregates
ORDER BY industry_code, year DESC;


-- View: Company benchmark data (combines financial + rankings)
CREATE OR REPLACE VIEW v_company_benchmark_data AS
SELECT 
    c.regcode,
    c.name,
    c.nace_code AS industry_code,
    c.nace_text AS industry_name,
    fr.year,
    fr.turnover AS revenue,
    fr.profit,
    fr.employees,
    fr.ebitda,
    fr.equity,
    fr.total_assets,
    fr.net_profit_margin,
    fr.roe,
    fr.roa,
    tp.avg_employees,
    CASE 
        WHEN fr.employees > 0 AND tp.avg_employees > 0 
        THEN (tp.total_tax_paid / tp.avg_employees) 
        ELSE NULL 
    END AS avg_salary,
    CASE 
        WHEN fr.employees > 0 
        THEN fr.turnover / fr.employees 
        ELSE NULL 
    END AS revenue_per_employee,
    CASE 
        WHEN fr.turnover > 0 
        THEN (fr.profit / fr.turnover) * 100 
        ELSE NULL 
    END AS profit_margin_pct,
    cr.rating_grade,
    cir.revenue_rank,
    cir.revenue_percentile,
    cir.total_companies AS industry_total_companies
FROM companies c
LEFT JOIN financial_reports fr ON c.regcode = fr.company_regcode
LEFT JOIN tax_payments tp ON c.regcode = tp.company_regcode AND fr.year = tp.year
LEFT JOIN company_ratings cr ON c.regcode = cr.company_regcode
LEFT JOIN company_industry_rankings cir ON c.regcode = cir.company_regcode 
    AND c.nace_code = cir.industry_code 
    AND fr.year = cir.year
WHERE c.status = 'active';


-- ==========================================
-- GRANT PERMISSIONS (if needed)
-- ==========================================
-- GRANT SELECT, INSERT ON benchmark_sessions TO app_user;
-- GRANT SELECT ON industry_year_aggregates TO app_user;
-- GRANT SELECT ON company_industry_rankings TO app_user;
