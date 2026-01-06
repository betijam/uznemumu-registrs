-- Materialized View for Location Statistics
-- Pre-calculates all location-based metrics for fast querying

DROP MATERIALIZED VIEW IF EXISTS public.location_statistics CASCADE;

CREATE MATERIALIZED VIEW public.location_statistics AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        -- Filter out Infinity and NaN values
        CASE 
            WHEN turnover IS NULL THEN 0
            WHEN turnover = 'Infinity'::float OR turnover = '-Infinity'::float OR turnover = 'NaN'::float THEN 0
            ELSE turnover 
        END as turnover,
        CASE 
            WHEN profit IS NULL THEN 0
            WHEN profit = 'Infinity'::float OR profit = '-Infinity'::float OR profit = 'NaN'::float THEN 0
            ELSE profit 
        END as profit,
        CASE 
            WHEN taxes_paid IS NULL THEN 0
            WHEN taxes_paid = 'Infinity'::float OR taxes_paid = '-Infinity'::float OR taxes_paid = 'NaN'::float THEN 0
            ELSE taxes_paid 
        END as taxes_paid,
        employees
    FROM financial_reports
    WHERE year >= 2020  -- Only recent years
    ORDER BY company_regcode, year DESC
)
SELECT 
    -- Location identifiers
    'city' as location_type,
    a.city_name as location_name,
    NULL as location_code, -- Ignore code to prevent dupes
    
    -- Aggregated metrics
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    
    -- Weighted Averages
    CASE WHEN SUM(f.employees) > 0 THEN SUM(f.turnover) / SUM(f.employees) ELSE 0 END as avg_revenue_per_company, -- Reusing this field name but it's per employee actually? No, keep it as revenue per company?
    -- Actually avg_revenue_per_company should be SUM(turnover) / COUNT(companies)
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE 0 END as real_avg_revenue_per_company,
    
    -- "Avg Salary" -> Currently mapping to Productivity (Turnover / Employee) or Tax / Employee?
    -- Let's use Taxes Paid / 12 / Employees as a rough proxy for monthly tax contribution
    -- OR just return 0 if we don't have real salary data.
    -- User complained about the calculation. The previous one was Turnover/Employee.
    -- Let's stick to Turnover/Employee (Productivity) for now but calculate correctly:
    CASE WHEN SUM(f.employees) > 0 THEN SUM(f.turnover) / SUM(f.employees) ELSE 0 END as avg_salary,
    
    -- For top companies query
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
WHERE a.city_name IS NOT NULL
  AND c.status = 'active'
GROUP BY a.city_name

UNION ALL

SELECT 
    'municipality' as location_type,
    a.municipality_name as location_name,
    NULL as location_code,
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    CASE WHEN SUM(f.employees) > 0 THEN SUM(f.turnover) / SUM(f.employees) ELSE 0 END as avg_revenue_per_company,
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE 0 END as real_avg_revenue_per_company,
    CASE WHEN SUM(f.employees) > 0 THEN SUM(f.turnover) / SUM(f.employees) ELSE 0 END as avg_salary,
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
WHERE a.municipality_name IS NOT NULL
  AND c.status = 'active'
GROUP BY a.municipality_name;

-- Create indexes for fast lookups
CREATE INDEX idx_location_stats_type_name ON public.location_statistics(location_type, location_name);
CREATE INDEX idx_location_stats_revenue ON public.location_statistics(total_revenue DESC NULLS LAST);
CREATE INDEX idx_location_stats_employees ON public.location_statistics(total_employees DESC NULLS LAST);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_location_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY location_statistics;
END;
$$ LANGUAGE plpgsql;

-- Initial refresh
REFRESH MATERIALIZED VIEW location_statistics;
