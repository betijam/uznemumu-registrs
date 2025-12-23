-- ==========================================
-- Industry Analytics Module - Database Migration
-- Creates tables for pre-computed industry statistics
-- ==========================================

-- 1. INDUSTRY STATS MATERIALIZED
-- Stores aggregated metrics for each NACE code
CREATE TABLE IF NOT EXISTS industry_stats_materialized (
    nace_code VARCHAR(10) PRIMARY KEY,
    nace_level INT,                    -- 1 (Section A-U) or 2-4 (sub-levels)
    nace_name VARCHAR(500),
    parent_code VARCHAR(10),
    total_turnover BIGINT,
    turnover_growth DECIMAL(10,2),     -- % change vs previous year
    total_profit BIGINT,
    avg_gross_salary INT,              -- Monthly average in EUR
    employee_count INT,
    active_companies INT,
    top5_concentration DECIMAL(10,4),  -- TOP 5 market share %
    total_tax_paid BIGINT,
    tax_burden DECIMAL(10,4),          -- Tax as % of turnover
    data_year INT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_industry_stats_level ON industry_stats_materialized(nace_level);
CREATE INDEX IF NOT EXISTS idx_industry_stats_parent ON industry_stats_materialized(parent_code);


-- 2. INDUSTRY LEADERS CACHE
-- TOP 5 companies per industry for fast loading
CREATE TABLE IF NOT EXISTS industry_leaders_cache (
    id SERIAL PRIMARY KEY,
    nace_code VARCHAR(10),
    company_regcode BIGINT,
    company_name TEXT,
    turnover DECIMAL(15,2),
    profit DECIMAL(15,2),
    employees INT,
    rank INT,
    data_year INT,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(nace_code, company_regcode, data_year)
);

CREATE INDEX IF NOT EXISTS idx_leaders_nace ON industry_leaders_cache(nace_code);
CREATE INDEX IF NOT EXISTS idx_leaders_year ON industry_leaders_cache(data_year);


-- ==========================================
-- DATA POPULATION QUERIES
-- Run these to populate the tables
-- ==========================================

-- Clear existing data before repopulating
TRUNCATE TABLE industry_stats_materialized;
TRUNCATE TABLE industry_leaders_cache;

-- 3. POPULATE NACE SECTIONS (Level 1: A-U)
-- Get section-level stats from companies table
INSERT INTO industry_stats_materialized (
    nace_code, nace_level, nace_name, parent_code,
    total_turnover, turnover_growth, total_profit,
    avg_gross_salary, employee_count, active_companies,
    top5_concentration, total_tax_paid, tax_burden, data_year
)
WITH section_stats AS (
    SELECT 
        c.nace_section as nace_code,
        MAX(c.nace_section_text) as nace_name,
        SUM(CASE WHEN f.turnover IS NOT NULL AND f.turnover != 'NaN'::float AND f.turnover < 1e15 THEN f.turnover ELSE 0 END) as total_turnover,
        SUM(CASE WHEN f.profit IS NOT NULL AND f.profit != 'NaN'::float AND ABS(f.profit) < 1e15 THEN f.profit ELSE 0 END) as total_profit,
        SUM(COALESCE(f.employees, 0)) as employee_count,
        COUNT(DISTINCT c.regcode) as active_companies,
        MAX(f.year) as data_year
    FROM companies c
    LEFT JOIN LATERAL (
        SELECT turnover, profit, employees, year
        FROM financial_reports
        WHERE company_regcode = c.regcode
          AND (turnover IS NULL OR (turnover != 'NaN'::float AND turnover < 1e15))
        ORDER BY year DESC
        LIMIT 1
    ) f ON true
    WHERE c.nace_section IS NOT NULL
      AND c.status = 'active'
    GROUP BY c.nace_section
),
section_tax AS (
    SELECT 
        c.nace_section,
        SUM(COALESCE(t.total_tax_paid, 0)) as total_tax,
        SUM(COALESCE(t.social_tax_vsaoi, 0)) as total_vsaoi,
        SUM(COALESCE(t.avg_employees, 0)) as tax_employees
    FROM companies c
    LEFT JOIN LATERAL (
        SELECT total_tax_paid, social_tax_vsaoi, avg_employees
        FROM tax_payments
        WHERE company_regcode = c.regcode
        ORDER BY year DESC
        LIMIT 1
    ) t ON true
    WHERE c.nace_section IS NOT NULL
    GROUP BY c.nace_section
),
section_prev_year AS (
    SELECT 
        c.nace_section as nace_code,
        SUM(CASE WHEN f.turnover IS NOT NULL AND f.turnover != 'NaN'::float AND f.turnover < 1e15 THEN f.turnover ELSE 0 END) as prev_turnover
    FROM companies c
    INNER JOIN financial_reports f ON f.company_regcode = c.regcode
    WHERE c.nace_section IS NOT NULL
      AND f.year = (SELECT MAX(year) - 1 FROM financial_reports)
    GROUP BY c.nace_section
),
section_top5 AS (
    SELECT 
        nace_section,
        SUM(top5_turnover) as top5_sum
    FROM (
        SELECT 
            c.nace_section,
            f.turnover as top5_turnover,
            ROW_NUMBER() OVER (PARTITION BY c.nace_section ORDER BY f.turnover DESC) as rn
        FROM companies c
        LEFT JOIN LATERAL (
            SELECT turnover FROM financial_reports
            WHERE company_regcode = c.regcode
              AND turnover IS NOT NULL 
              AND turnover != 'NaN'::float
              AND turnover > 0
              AND turnover < 1e15
            ORDER BY year DESC LIMIT 1
        ) f ON true
        WHERE c.nace_section IS NOT NULL AND f.turnover IS NOT NULL
    ) ranked
    WHERE rn <= 5
    GROUP BY nace_section
)
SELECT 
    s.nace_code,
    1 as nace_level,
    s.nace_name,
    NULL as parent_code,
    NULLIF(s.total_turnover, 0)::BIGINT,
    CASE WHEN COALESCE(p.prev_turnover, 0) > 0 AND COALESCE(s.total_turnover, 0) > 0
        THEN ROUND(((s.total_turnover - p.prev_turnover) / p.prev_turnover * 100)::NUMERIC, 2)
        ELSE NULL 
    END as turnover_growth,
    NULLIF(s.total_profit, 0)::BIGINT,
    CASE WHEN COALESCE(t.tax_employees, 0) > 0 
        THEN ROUND((t.total_vsaoi / 0.3409 / t.tax_employees / 12)::NUMERIC)::INT
        ELSE NULL 
    END as avg_gross_salary,
    COALESCE(s.employee_count, 0)::INT,
    s.active_companies::INT,
    CASE WHEN COALESCE(s.total_turnover, 0) > 0 AND COALESCE(t5.top5_sum, 0) > 0
        THEN ROUND((t5.top5_sum / s.total_turnover * 100)::NUMERIC, 4)
        ELSE NULL 
    END as top5_concentration,
    NULLIF(t.total_tax, 0)::BIGINT,
    CASE WHEN COALESCE(s.total_turnover, 0) > 0 AND COALESCE(t.total_tax, 0) > 0
        THEN ROUND((t.total_tax / s.total_turnover * 100)::NUMERIC, 4)
        ELSE NULL 
    END as tax_burden,
    s.data_year
FROM section_stats s
LEFT JOIN section_tax t ON t.nace_section = s.nace_code
LEFT JOIN section_prev_year p ON p.nace_code = s.nace_code
LEFT JOIN section_top5 t5 ON t5.nace_section = s.nace_code
WHERE s.nace_code IS NOT NULL;


-- 4. POPULATE INDUSTRY LEADERS (TOP 5 per section)
INSERT INTO industry_leaders_cache (
    nace_code, company_regcode, company_name,
    turnover, profit, employees, rank, data_year
)
SELECT 
    nace_section,
    regcode,
    name,
    turnover,
    profit,
    employees,
    rn as rank,
    year as data_year
FROM (
    SELECT 
        c.nace_section,
        c.regcode,
        c.name,
        f.turnover,
        f.profit,
        f.employees,
        f.year,
        ROW_NUMBER() OVER (PARTITION BY c.nace_section ORDER BY f.turnover DESC NULLS LAST) as rn
    FROM companies c
    LEFT JOIN LATERAL (
        SELECT turnover, profit, employees, year
        FROM financial_reports
        WHERE company_regcode = c.regcode
          AND turnover IS NOT NULL
          AND turnover > 0
          AND turnover < 1e15
        ORDER BY year DESC
        LIMIT 1
    ) f ON true
    WHERE c.nace_section IS NOT NULL
      AND c.status = 'active'
      AND f.turnover IS NOT NULL
) ranked
WHERE rn <= 5;


-- 5. VERIFY DATA
SELECT 'industry_stats_materialized' as table_name, COUNT(*) as row_count FROM industry_stats_materialized
UNION ALL
SELECT 'industry_leaders_cache' as table_name, COUNT(*) as row_count FROM industry_leaders_cache;
