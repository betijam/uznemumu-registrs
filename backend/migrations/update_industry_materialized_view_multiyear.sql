-- Refactor industry_stats_materialized for multi-year support
-- and populate with Level 1 (Sections) and Level 2 (Divisions) data for 2018-2025
-- FIX: Explicitly map NACE codes to Sections (A-U) because source data lacks Section letters

-- 1. DROP and RECREATE tables with correct Schema
DROP TABLE IF EXISTS industry_stats_materialized CASCADE;
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
    top5_concentration DECIMAL(10,4),  
    total_tax_paid BIGINT,
    tax_burden DECIMAL(10,4),          
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (nace_code, data_year)
);

CREATE INDEX idx_industry_stats_level_year ON industry_stats_materialized(nace_level, data_year);
CREATE INDEX idx_industry_stats_parent ON industry_stats_materialized(parent_code);

DROP TABLE IF EXISTS industry_leaders_cache CASCADE;
CREATE TABLE industry_leaders_cache (
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

CREATE INDEX idx_leaders_nace_year ON industry_leaders_cache(nace_code, data_year);

-- 2. POPULATE LEVEL 1 (SECTIONS A-U) with MAPPING
INSERT INTO industry_stats_materialized (
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
            ELSE NULL -- Unknown
        END as section_code
    FROM companies c
    WHERE c.status = 'active' AND c.nace_code IS NOT NULL
),
section_years AS (
    SELECT 
        cs.section_code as nace_code,
        f.year as data_year,
        NULL::VARCHAR as nace_name, -- Let backend fill from dict
        SUM(f.turnover) as total_turnover,
        SUM(f.profit) as total_profit,
        SUM(COALESCE(f.employees, 0)) as employee_count,
        COUNT(DISTINCT cs.regcode) as active_companies
    FROM company_sections cs
    JOIN financial_reports f ON f.company_regcode = cs.regcode
    WHERE cs.section_code IS NOT NULL
      AND f.turnover IS NOT NULL 
      AND f.turnover < 1e15
    GROUP BY cs.section_code, f.year
),
prev_year_stats AS (
    SELECT nace_code, data_year, total_turnover FROM section_years
),
tax_data AS (
    SELECT 
        cs.section_code as nace_code,
        t.year as data_year,
        SUM(t.total_tax_paid) as total_tax,
        SUM(t.social_tax_vsaoi) as vsaoi,
        SUM(t.avg_employees) as tax_employees
    FROM company_sections cs
    JOIN tax_payments t ON t.company_regcode = cs.regcode
    WHERE cs.section_code IS NOT NULL
    GROUP BY cs.section_code, t.year
)
SELECT
    s.nace_code,
    s.data_year,
    1 as nace_level,
    COALESCE(s.nace_name, s.nace_code),
    NULL as parent_code,
    s.total_turnover::BIGINT,
    s.total_profit::BIGINT,
    s.employee_count::INT,
    s.active_companies::INT,
    -- Growth
    CASE WHEN COALESCE(prev.total_turnover, 0) > 0 
         THEN ROUND(((s.total_turnover - prev.total_turnover) / prev.total_turnover * 100)::NUMERIC, 2)
         ELSE NULL END as turnover_growth,
    -- Tax
    COALESCE(t.total_tax, 0)::BIGINT as total_tax_paid,
    -- Salary
    CASE WHEN COALESCE(t.tax_employees, 0) > 0 
         THEN ROUND((t.vsaoi / 0.3409 / t.tax_employees / 12)::NUMERIC)::INT
         ELSE NULL END as avg_gross_salary,
    -- Tax Burden
    CASE WHEN s.total_turnover > 0 
         THEN ROUND((COALESCE(t.total_tax, 0) / s.total_turnover * 100)::NUMERIC, 4)
         ELSE NULL END as tax_burden
FROM section_years s
LEFT JOIN prev_year_stats prev ON s.nace_code = prev.nace_code AND prev.data_year = s.data_year - 1
LEFT JOIN tax_data t ON t.nace_code = s.nace_code AND t.data_year = s.data_year
ON CONFLICT (nace_code, data_year) DO UPDATE SET
    total_turnover = EXCLUDED.total_turnover,
    total_profit = EXCLUDED.total_profit,
    active_companies = EXCLUDED.active_companies,
    updated_at = NOW();

-- 3. POPULATE LEVEL 2 (DIVISIONS 01-99)
INSERT INTO industry_stats_materialized (
    nace_code, data_year, nace_level, nace_name, parent_code,
    total_turnover, total_profit, employee_count, active_companies,
    turnover_growth, total_tax_paid, avg_gross_salary, tax_burden
)
WITH division_years AS (
    SELECT 
        LEFT(c.nace_code, 2) as nace_code,
        f.year as data_year,
        MAX(c.nace_text) as nace_name, -- Approximate name
        SUM(f.turnover) as total_turnover,
        SUM(f.profit) as total_profit,
        SUM(COALESCE(f.employees, 0)) as employee_count,
        COUNT(DISTINCT c.regcode) as active_companies
    FROM companies c
    JOIN financial_reports f ON f.company_regcode = c.regcode
    WHERE c.nace_code IS NOT NULL AND LENGTH(c.nace_code) >= 2
      AND c.status = 'active'
      AND f.turnover IS NOT NULL 
      AND f.turnover < 1e15
    GROUP BY LEFT(c.nace_code, 2), f.year
),
prev_year_stats AS (
    SELECT nace_code, data_year, total_turnover FROM division_years
),
tax_data AS (
    SELECT 
        LEFT(c.nace_code, 2) as nace_code,
        t.year as data_year,
        SUM(t.total_tax_paid) as total_tax,
        SUM(t.social_tax_vsaoi) as vsaoi,
        SUM(t.avg_employees) as tax_employees
    FROM companies c
    JOIN tax_payments t ON t.company_regcode = c.regcode
    WHERE c.nace_code IS NOT NULL AND LENGTH(c.nace_code) >= 2
    GROUP BY LEFT(c.nace_code, 2), t.year
)
SELECT
    s.nace_code,
    s.data_year,
    2 as nace_level,
    COALESCE(s.nace_name, 'Division ' || s.nace_code) as nace_name, 
    -- Map Parent Code (Section) for hierarchy
    CASE 
        WHEN s.nace_code BETWEEN '01' AND '03' THEN 'A'
        WHEN s.nace_code BETWEEN '05' AND '09' THEN 'B'
        WHEN s.nace_code BETWEEN '10' AND '33' THEN 'C'
        WHEN s.nace_code = '35' THEN 'D'
        WHEN s.nace_code BETWEEN '36' AND '39' THEN 'E'
        WHEN s.nace_code BETWEEN '41' AND '43' THEN 'F'
        WHEN s.nace_code BETWEEN '45' AND '47' THEN 'G'
        WHEN s.nace_code BETWEEN '49' AND '53' THEN 'H'
        WHEN s.nace_code BETWEEN '55' AND '56' THEN 'I'
        WHEN s.nace_code BETWEEN '58' AND '63' THEN 'J'
        WHEN s.nace_code BETWEEN '64' AND '66' THEN 'K'
        WHEN s.nace_code = '68' THEN 'L'
        WHEN s.nace_code BETWEEN '69' AND '75' THEN 'M'
        WHEN s.nace_code BETWEEN '77' AND '82' THEN 'N'
        WHEN s.nace_code = '84' THEN 'O'
        WHEN s.nace_code = '85' THEN 'P'
        WHEN s.nace_code BETWEEN '86' AND '88' THEN 'Q'
        WHEN s.nace_code BETWEEN '90' AND '93' THEN 'R'
        WHEN s.nace_code BETWEEN '94' AND '96' THEN 'S'
        WHEN s.nace_code BETWEEN '97' AND '98' THEN 'T'
        WHEN s.nace_code = '99' THEN 'U'
    END as parent_code,
    s.total_turnover::BIGINT,
    s.total_profit::BIGINT,
    s.employee_count::INT,
    s.active_companies::INT,
    CASE WHEN COALESCE(prev.total_turnover, 0) > 0 
         THEN ROUND(((s.total_turnover - prev.total_turnover) / prev.total_turnover * 100)::NUMERIC, 2)
         ELSE NULL END as turnover_growth,
    COALESCE(t.total_tax, 0)::BIGINT as total_tax_paid,
    CASE WHEN COALESCE(t.tax_employees, 0) > 0 
         THEN ROUND((t.vsaoi / 0.3409 / t.tax_employees / 12)::NUMERIC)::INT
         ELSE NULL END as avg_gross_salary,
    CASE WHEN s.total_turnover > 0 
         THEN ROUND((COALESCE(t.total_tax, 0) / s.total_turnover * 100)::NUMERIC, 4)
         ELSE NULL END as tax_burden
FROM division_years s
LEFT JOIN prev_year_stats prev ON s.nace_code = prev.nace_code AND prev.data_year = s.data_year - 1
LEFT JOIN tax_data t ON t.nace_code = s.nace_code AND t.data_year = s.data_year
ON CONFLICT (nace_code, data_year) DO UPDATE SET
    total_turnover = EXCLUDED.total_turnover,
    total_profit = EXCLUDED.total_profit,
    active_companies = EXCLUDED.active_companies,
    updated_at = NOW();

ANALYZE industry_stats_materialized;
