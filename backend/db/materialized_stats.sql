-- Materialized View for Analytics
-- This pre-calculates expensive joins and math for the Explore page

DROP MATERIALIZED VIEW IF EXISTS company_stats_materialized;

CREATE MATERIALIZED VIEW company_stats_materialized AS
WITH latest_fin AS (
    -- Get latest financial year for each company
    -- Explicitly CAST to correct types, handling 'NaN' strings as NULL
    SELECT 
        f.company_regcode,
        f.year,
        CAST(NULLIF(f.turnover, 'NaN') AS NUMERIC) as turnover,
        CAST(NULLIF(f.profit, 'NaN') AS NUMERIC) as profit,
        CAST(NULLIF(f.employees, 'NaN') AS INTEGER) as employees
    FROM financial_reports f
),
growth_calc AS (
    SELECT 
        cur.company_regcode,
        cur.year,
        cur.turnover,
        cur.profit,
        cur.employees,
        p.turnover as prev_turnover,
        ROUND(((cur.turnover - p.turnover) / NULLIF(ABS(p.turnover), 0)) * 100, 1) as turnover_growth,
        (cur.profit / NULLIF(cur.turnover, 0)) * 100 as profit_margin
    FROM latest_fin cur
    LEFT JOIN latest_fin p ON cur.company_regcode = p.company_regcode AND p.year = cur.year - 1
),
salary_calc AS (
    SELECT 
        company_regcode,
        year,
        total_tax_paid,
        (social_tax_vsaoi / NULLIF(avg_employees, 0) / 12 / 0.3409) as avg_salary
    FROM tax_payments
    WHERE avg_employees >= 5
)
SELECT 
    c.regcode,
    g.year,
    g.turnover,
    g.profit,
    g.employees,
    g.turnover_growth,
    g.profit_margin,
    s.avg_salary,
    s.total_tax_paid as tax_paid
FROM companies c
JOIN growth_calc g ON g.company_regcode = c.regcode
LEFT JOIN salary_calc s ON s.company_regcode = c.regcode AND s.year = g.year
WITH DATA;

-- Indexes for fast sorting
CREATE INDEX idx_stats_turnover ON company_stats_materialized(turnover DESC NULLS LAST);
CREATE INDEX idx_stats_profit ON company_stats_materialized(profit DESC NULLS LAST);
CREATE INDEX idx_stats_growth ON company_stats_materialized(turnover_growth DESC NULLS LAST);
CREATE INDEX idx_stats_salary ON company_stats_materialized(avg_salary DESC NULLS LAST);
CREATE INDEX idx_stats_year ON company_stats_materialized(year);
CREATE UNIQUE INDEX idx_stats_pk ON company_stats_materialized(regcode, year);
