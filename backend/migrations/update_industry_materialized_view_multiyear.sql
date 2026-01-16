-- Refactor for DUAL-TABLE strategy: 
-- 1. industry_stats_materialized -> Snapshot of LATEST year only (for lists/dashboard)
-- 2. industry_stats_history    -> Full history 2018-2025 (for detailed charts)

-- DROP EXISTING
DROP TABLE IF EXISTS industry_stats_materialized CASCADE;
DROP TABLE IF EXISTS industry_stats_history CASCADE;

-- CREATE HISTORY TABLE (ALL YEARS)
CREATE TABLE industry_stats_history (
    nace_code VARCHAR(10),
    data_year INT,
    nace_level INT,                    
    nace_name VARCHAR(500),
    parent_code VARCHAR(10),
    total_turnover BIGINT,
    turnover_growth DECIMAL(10,2),    
    total_profit BIGINT,
    avg_gross_salary INT,              
    employee_count INT,
    active_companies INT,
    total_tax_paid BIGINT,
    tax_burden DECIMAL(10,4),          
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (nace_code, data_year)
);

-- CREATE SNAPSHOT TABLE (LATEST YEAR ONLY)
CREATE TABLE industry_stats_materialized (
    nace_code VARCHAR(10),
    data_year INT,
    nace_level INT,                    
    nace_name VARCHAR(500),
    parent_code VARCHAR(10),
    total_turnover BIGINT,
    turnover_growth DECIMAL(10,2),    
    total_profit BIGINT,
    avg_gross_salary INT,              
    employee_count INT,
    active_companies INT,
    total_tax_paid BIGINT,
    tax_burden DECIMAL(10,4),          
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (nace_code) -- Only one entry per code here
);

CREATE INDEX idx_industry_history_level ON industry_stats_history(nace_level, data_year);
CREATE INDEX idx_industry_snapshot_level ON industry_stats_materialized(nace_level);

-- ------------------------------------------------------------
-- 1. POPULATE HISTORY (Multi-year)
-- ------------------------------------------------------------
INSERT INTO industry_stats_history (
    nace_code, data_year, nace_level, nace_name, parent_code,
    total_turnover, total_profit, employee_count, active_companies,
    turnover_growth, total_tax_paid, avg_gross_salary, tax_burden
)
WITH company_sections AS (
    SELECT 
        c.regcode,
        CASE 
            WHEN LEFT(c.nace_code, 2) BETWEEN '01' AND '03' THEN 'A'
            WHEN LEFT(c.nace_code, 2) BETWEEN '05' AND '09' THEN 'B'
            WHEN LEFT(c.nace_code, 2) BETWEEN '10' AND '33' THEN 'C'
            WHEN LEFT(c.nace_code, 2) = '35' THEN 'D'
            WHEN LEFT(c.nace_code, 2) BETWEEN '36' AND '39' THEN 'E'
            WHEN LEFT(c.nace_code, 2) BETWEEN '41' AND '43' THEN 'F'
            WHEN LEFT(c.nace_code, 2) BETWEEN '45' AND '47' THEN 'G'
            WHEN LEFT(c.nace_code, 2) BETWEEN '49' AND '53' THEN 'H'
            WHEN LEFT(c.nace_code, 2) BETWEEN '55' AND '56' THEN 'I'
            WHEN LEFT(c.nace_code, 2) BETWEEN '58' AND '63' THEN 'J'
            WHEN LEFT(c.nace_code, 2) BETWEEN '64' AND '66' THEN 'K'
            WHEN LEFT(c.nace_code, 2) = '68' THEN 'L'
            WHEN LEFT(c.nace_code, 2) BETWEEN '69' AND '75' THEN 'M'
            WHEN LEFT(c.nace_code, 2) BETWEEN '77' AND '82' THEN 'N'
            WHEN LEFT(c.nace_code, 2) = '84' THEN 'O'
            WHEN LEFT(c.nace_code, 2) = '85' THEN 'P'
            WHEN LEFT(c.nace_code, 2) BETWEEN '86' AND '88' THEN 'Q'
            WHEN LEFT(c.nace_code, 2) BETWEEN '90' AND '93' THEN 'R'
            WHEN LEFT(c.nace_code, 2) BETWEEN '94' AND '96' THEN 'S'
            WHEN LEFT(c.nace_code, 2) BETWEEN '97' AND '98' THEN 'T'
            WHEN LEFT(c.nace_code, 2) = '99' THEN 'U'
            ELSE NULL 
        END as section_code,
        LEFT(c.nace_code, 2) as division_code,
        c.nace_text
    FROM companies c
    WHERE c.status = 'active' AND c.nace_code IS NOT NULL
),
-- Aggregates
stats_raw AS (
    -- Sections (Level 0)
    SELECT 
        cs.section_code as nace_code,
        f.year as data_year,
        0 as nace_level,
        NULL::VARCHAR as nace_name,
        NULL::VARCHAR as parent_code,
        SUM(CASE WHEN f.turnover = 'NaN'::float OR f.turnover > 1e12 THEN 0 ELSE f.turnover END) as turnover,
        SUM(CASE WHEN f.profit = 'NaN'::float OR ABS(f.profit) > 1e12 THEN 0 ELSE f.profit END) as profit,
        SUM(CASE WHEN f.employees = 'NaN'::float THEN 0 ELSE COALESCE(f.employees, 0) END) as employees,
        COUNT(DISTINCT cs.regcode) as companies
    FROM company_sections cs
    JOIN financial_reports f ON f.company_regcode = cs.regcode
    WHERE cs.section_code IS NOT NULL AND (f.source_type IS NULL OR f.source_type = 'UGP')
    GROUP BY cs.section_code, f.year
    UNION ALL
    -- Divisions (Level 1)
    SELECT 
        cs.division_code as nace_code,
        f.year as data_year,
        1 as nace_level,
        MAX(cs.nace_text) as nace_name,
        MAX(cs.section_code) as parent_code,
        SUM(CASE WHEN f.turnover = 'NaN'::float OR f.turnover > 1e12 THEN 0 ELSE f.turnover END) as turnover,
        SUM(CASE WHEN f.profit = 'NaN'::float OR ABS(f.profit) > 1e12 THEN 0 ELSE f.profit END) as profit,
        SUM(CASE WHEN f.employees = 'NaN'::float THEN 0 ELSE COALESCE(f.employees, 0) END) as employees,
        COUNT(DISTINCT cs.regcode) as companies
    FROM company_sections cs
    JOIN financial_reports f ON f.company_regcode = cs.regcode
    WHERE LENGTH(cs.division_code) = 2 AND (f.source_type IS NULL OR f.source_type = 'UGP')
    GROUP BY cs.division_code, f.year
),
tax_data AS (
    -- Combined Tax
    SELECT 
        cs.section_code as nace_code,
        t.year as data_year,
        0 as nace_level,
        SUM(CASE WHEN t.total_tax_paid = 'NaN'::float THEN 0 ELSE t.total_tax_paid END) as total_tax,
        SUM(CASE WHEN t.social_tax_vsaoi = 'NaN'::float THEN 0 ELSE t.social_tax_vsaoi END) as vsaoi,
        SUM(CASE WHEN t.avg_employees = 'NaN'::float THEN 0 ELSE t.avg_employees END) as tax_employees
    FROM company_sections cs
    JOIN tax_payments t ON t.company_regcode = cs.regcode
    WHERE cs.section_code IS NOT NULL
    GROUP BY cs.section_code, t.year
    UNION ALL
    SELECT 
        cs.division_code as nace_code,
        t.year as data_year,
        1 as nace_level,
        SUM(CASE WHEN t.total_tax_paid = 'NaN'::float THEN 0 ELSE t.total_tax_paid END) as total_tax,
        SUM(CASE WHEN t.social_tax_vsaoi = 'NaN'::float THEN 0 ELSE t.social_tax_vsaoi END) as vsaoi,
        SUM(CASE WHEN t.avg_employees = 'NaN'::float THEN 0 ELSE t.avg_employees END) as tax_employees
    FROM company_sections cs
    JOIN tax_payments t ON t.company_regcode = cs.regcode
    WHERE LENGTH(cs.division_code) = 2
    GROUP BY cs.division_code, t.year
)
SELECT
    s.nace_code, s.data_year, s.nace_level, s.nace_name, s.parent_code,
    s.turnover::BIGINT, s.profit::BIGINT, s.employees::INT, s.companies::INT,
    -- Growth (vs previous year in history)
    CASE WHEN COALESCE(p.turnover, 0) > 0 THEN ROUND(((s.turnover - p.turnover) / p.turnover * 100)::NUMERIC, 2) ELSE NULL END as growth,
    COALESCE(t.total_tax, 0)::BIGINT as tax,
    CASE WHEN COALESCE(t.tax_employees, 0) > 0 THEN ROUND((t.vsaoi / 0.3409 / t.tax_employees / 12)::NUMERIC)::INT ELSE NULL END as salary,
    CASE WHEN s.turnover > 0 THEN ROUND((COALESCE(t.total_tax, 0) / s.turnover * 100)::NUMERIC, 4) ELSE NULL END as burden
FROM stats_raw s
LEFT JOIN stats_raw p ON s.nace_code = p.nace_code AND s.nace_level = p.nace_level AND p.data_year = s.data_year - 1
LEFT JOIN tax_data t ON t.nace_code = s.nace_code AND t.nace_level = s.nace_level AND t.data_year = s.data_year;

-- ------------------------------------------------------------
-- 2. POPULATE SNAPSHOT (LATEST YEAR)
-- ------------------------------------------------------------
INSERT INTO industry_stats_materialized
SELECT DISTINCT ON (nace_code) *
FROM industry_stats_history
WHERE data_year = 2024
ORDER BY nace_code, data_year DESC;

ANALYZE industry_stats_materialized;
ANALYZE industry_stats_history;
