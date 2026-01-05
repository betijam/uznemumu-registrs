-- Materialized View for Analytics
-- This pre-calculates expensive joins and math for the Explore page

DROP MATERIALIZED VIEW IF EXISTS company_stats_materialized;

CREATE MATERIALIZED VIEW company_stats_materialized AS
WITH latest_fin AS (
    -- Get latest financial year for each company
    -- For simplicity, we stick to a global latest year like dashboard, or we take the latest available per company?
    -- Explore page defaults to "2024" (or calculated latest).
    -- To allow sorting by "latest" data, we might need a specific year column.
    -- Let's stick to the logic: Data for the "Global Working Year" (usually last closed year).
    -- Or, ideally, we include stats for multiple years? No, Explore is usually "Latest".
    -- Let's pin it to the dashboard logic: Determine "Latest Year" dynamically or fixed.
    -- Better: Create keys (regcode, year) if we want multi-year support.
    -- But for fast sorting, we usually want "Current Status".
    -- Let's build it for specific years. OR simply assume "Latest Available" for each company?
    -- Explore page uses `?year=X`. We should probably materialize for the specific "Active Reporting Year".
    -- Let's allow it to contain data for the last 2 years.
    SELECT 
        f.company_regcode,
        f.year,
        f.turnover,
        f.profit,
        f.employees
    FROM financial_reports f
),
growth_calc AS (
    SELECT 
        cur.company_regcode,
        cur.year,
        cur.turnover,
        cur.profit,
        cur.employees,
        prev.turnover as prev_turnover,
        ROUND(((CAST(cur.turnover AS NUMERIC) - CAST(prev.turnover AS NUMERIC)) / NULLIF(ABS(CAST(prev.turnover AS NUMERIC)), 0)) * 100, 1) as turnover_growth,
        (cur.profit / NULLIF(cur.turnover, 0)) * 100 as profit_margin
    FROM latest_fin cur
    LEFT JOIN latest_fin prev ON cur.company_regcode = prev.company_regcode AND prev.year = cur.year - 1
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
    -- We can also include search fields here to avoid joining companies? 
    -- companies table is small-ish (200k rows), joining on regcode (PK) is fast.
    -- Main issue was the math and multi-joins.
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
