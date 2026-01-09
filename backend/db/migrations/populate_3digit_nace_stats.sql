-- ==========================================
-- Populate 3-Digit NACE Industry Statistics
-- Adds division-level (3-digit) industry averages
-- ==========================================

-- Populate 3-digit NACE industry statistics
INSERT INTO industry_stats_materialized (
    nace_code, nace_level, nace_name, parent_code,
    total_turnover, total_profit, avg_gross_salary, 
    employee_count, active_companies, data_year
)
SELECT 
    SUBSTRING(c.nace_code FROM 1 FOR 3) as nace_code,
    3 as nace_level,
    MAX(c.nace_text) as nace_name,
    MAX(SUBSTRING(c.nace_code FROM 1 FOR 1)) as parent_code,
    SUM(CASE WHEN f.turnover IS NOT NULL AND f.turnover != 'NaN'::float AND f.turnover < 1e15 
        THEN f.turnover ELSE 0 END)::BIGINT as total_turnover,
    SUM(CASE WHEN f.profit IS NOT NULL AND f.profit != 'NaN'::float AND ABS(f.profit) < 1e15 
        THEN f.profit ELSE 0 END)::BIGINT as total_profit,
    -- Calculate avg gross salary from tax data
    CASE WHEN SUM(COALESCE(th.avg_employees, 0)) > 0
        THEN ROUND((SUM(COALESCE(th.social_tax_vsaoi, 0)) / 0.3409 / SUM(COALESCE(th.avg_employees, 0)) / 12)::NUMERIC)::INT
        ELSE NULL 
    END as avg_gross_salary,
    SUM(COALESCE(f.employees, 0))::INT as employee_count,
    COUNT(DISTINCT c.regcode)::INT as active_companies,
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
LEFT JOIN LATERAL (
    SELECT social_tax_vsaoi, avg_employees
    FROM tax_payments
    WHERE company_regcode = c.regcode
    ORDER BY year DESC
    LIMIT 1
) th ON true
WHERE c.nace_code IS NOT NULL
  AND LENGTH(c.nace_code) >= 3
  AND c.status = 'active'
GROUP BY SUBSTRING(c.nace_code FROM 1 FOR 3)
HAVING COUNT(DISTINCT c.regcode) >= 5  -- At least 5 companies for statistical significance
ON CONFLICT (nace_code) DO UPDATE SET
    nace_name = EXCLUDED.nace_name,
    total_turnover = EXCLUDED.total_turnover,
    total_profit = EXCLUDED.total_profit,
    avg_gross_salary = EXCLUDED.avg_gross_salary,
    employee_count = EXCLUDED.employee_count,
    active_companies = EXCLUDED.active_companies,
    data_year = EXCLUDED.data_year,
    updated_at = NOW();

-- Verify results
SELECT 
    nace_level,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE avg_gross_salary IS NOT NULL) as with_salary
FROM industry_stats_materialized
GROUP BY nace_level
ORDER BY nace_level;

-- Show sample 3-digit NACEs
SELECT nace_code, nace_name, avg_gross_salary, active_companies
FROM industry_stats_materialized 
WHERE nace_level = 3
ORDER BY active_companies DESC
LIMIT 10;
