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
            WHEN turnover IS NULL THEN NULL
            WHEN turnover = 'Infinity'::float OR turnover = '-Infinity'::float OR turnover = 'NaN'::float THEN NULL
            ELSE turnover 
        END as turnover,
        CASE 
            WHEN profit IS NULL THEN NULL
            WHEN profit = 'Infinity'::float OR profit = '-Infinity'::float OR profit = 'NaN'::float THEN NULL
            ELSE profit 
        END as profit,
        employees,
        CASE 
            WHEN employees > 0 AND turnover > 0 
                AND turnover != 'Infinity'::float AND turnover != 'NaN'::float
            THEN turnover / employees 
            ELSE NULL 
        END as avg_salary
    FROM financial_reports
    WHERE year >= 2020  -- Only recent years
    ORDER BY company_regcode, year DESC
)
SELECT 
    -- Location identifiers
    'city' as location_type,
    a.city_name as location_name,
    a.city_code as location_code,
    
    -- Aggregated metrics
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    AVG(f.avg_salary) as avg_salary,
    AVG(f.turnover) as avg_revenue_per_company,
    
    -- For top companies query
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
WHERE a.city_name IS NOT NULL
  AND c.status = 'active'
GROUP BY a.city_name, a.city_code

UNION ALL

SELECT 
    'municipality' as location_type,
    a.municipality_name as location_name,
    a.municipality_code as location_code,
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    AVG(f.avg_salary) as avg_salary,
    AVG(f.turnover) as avg_revenue_per_company,
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
WHERE a.municipality_name IS NOT NULL
  AND c.status = 'active'
GROUP BY a.municipality_name, a.municipality_code;

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
