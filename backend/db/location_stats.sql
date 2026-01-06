-- Materialized View for Location Statistics
-- Pre-calculates all location-based metrics for fast querying

DROP MATERIALIZED VIEW IF EXISTS public.location_statistics CASCADE;

CREATE MATERIALIZED VIEW public.location_statistics AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        turnover,
        profit,
        employees
    FROM financial_reports
    WHERE year >= 2020
    ORDER BY company_regcode, year DESC
),
latest_taxes AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        social_tax_vsaoi,
        avg_employees,
        -- Calculate monthly gross salary per company
        -- Formula: (Social Tax / 0.3409) / Avg Employees / 12
        CASE 
            WHEN social_tax_vsaoi > 0 AND avg_employees > 0 THEN 
                (social_tax_vsaoi / 0.3409) / avg_employees / 12
            ELSE NULL 
        END as calc_avg_gross_salary
    FROM tax_payments
    WHERE year >= 2020
    ORDER BY company_regcode, year DESC
)
SELECT 
    'city' as location_type,
    a.city_name as location_name,
    NULL as location_code,
    
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    
    -- Real Average Salary (Average of company averages, consistent with Dashboard)
    AVG(t.calc_avg_gross_salary) FILTER (WHERE t.calc_avg_gross_salary > 0 AND t.avg_employees >= 1) as avg_salary,
    
    -- Avg Revenue per company
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE 0 END as avg_revenue_per_company,
    
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
LEFT JOIN latest_taxes t ON c.regcode = t.company_regcode
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
    
    AVG(t.calc_avg_gross_salary) FILTER (WHERE t.calc_avg_gross_salary > 0 AND t.avg_employees >= 1) as avg_salary,
    
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE 0 END as avg_revenue_per_company,
    
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
LEFT JOIN latest_taxes t ON c.regcode = t.company_regcode
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
