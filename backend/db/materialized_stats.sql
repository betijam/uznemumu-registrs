-- Materialized View for Analytics
-- This pre-calculates expensive joins and math for the Explore page
-- OPTIMIZED: Stores ONLY the latest available financial year for each company.

DROP MATERIALIZED VIEW IF EXISTS company_stats_materialized CASCADE;

CREATE MATERIALIZED VIEW company_stats_materialized AS
WITH latest_fin AS (
    -- Get ONLY the latest financial year for each company using DISTINCT ON
    SELECT DISTINCT ON (f.company_regcode)
        f.company_regcode,
        f.year,
        f.turnover,
        f.profit,
        f.employees
    FROM financial_reports f
    ORDER BY f.company_regcode, f.year DESC
),
growth_calc AS (
    SELECT 
        cur.company_regcode,
        cur.year,
        cur.turnover,
        cur.profit,
        cur.employees,
        -- Calculate growth vs previous year (if exists)
        p.turnover as prev_turnover,
        CASE 
            WHEN p.turnover IS NOT NULL AND p.turnover <> 0 THEN
                ROUND(((cur.turnover - p.turnover) / ABS(p.turnover)) * 100, 1)
            ELSE NULL 
        END as turnover_growth,
        CASE
            WHEN cur.turnover IS NOT NULL AND cur.turnover <> 0 THEN
                ROUND((cur.profit / cur.turnover) * 100, 2)
            ELSE NULL
        END as profit_margin
    FROM latest_fin cur
    -- Join with previous year for growth calc (this query is fast as it joins on distinct set)
    LEFT JOIN financial_reports p ON cur.company_regcode = p.company_regcode AND p.year = cur.year - 1
),
salary_calc AS (
    -- Latest salary info
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        total_tax_paid,
        CASE 
            WHEN avg_employees > 0 THEN
                ROUND((social_tax_vsaoi / avg_employees / 12 / 0.3409), 2)
            ELSE NULL
        END as avg_salary
    FROM tax_payments
    WHERE avg_employees >= 1 -- Relaxed filter to include more data
    ORDER BY company_regcode, year DESC
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
LEFT JOIN salary_calc s ON s.company_regcode = c.regcode
WITH DATA;

-- Indexes for fast sorting and filtering
CREATE UNIQUE INDEX idx_stats_pk ON company_stats_materialized(regcode);
CREATE INDEX idx_stats_turnover ON company_stats_materialized(turnover DESC NULLS LAST);
CREATE INDEX idx_stats_profit ON company_stats_materialized(profit DESC NULLS LAST);
CREATE INDEX idx_stats_growth ON company_stats_materialized(turnover_growth DESC NULLS LAST);
CREATE INDEX idx_stats_salary ON company_stats_materialized(avg_salary DESC NULLS LAST);
CREATE INDEX idx_stats_year ON company_stats_materialized(year);
