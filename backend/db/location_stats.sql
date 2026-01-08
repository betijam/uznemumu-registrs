-- Materialized View for Location Statistics
-- Pre-calculates all location-based metrics for fast querying
-- Updated: Municipalities now include data from cities within them

DROP MATERIALIZED VIEW IF EXISTS public.location_statistics CASCADE;

CREATE MATERIALIZED VIEW public.location_statistics AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        CASE 
            WHEN turnover = 'Infinity'::float OR turnover = '-Infinity'::float OR turnover = 'NaN'::float THEN NULL
            ELSE turnover 
        END as turnover,
        CASE 
            WHEN profit = 'Infinity'::float OR profit = '-Infinity'::float OR profit = 'NaN'::float THEN NULL
            ELSE profit 
        END as profit,
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
        avg_employees
    FROM tax_payments
    WHERE year >= 2020
      AND social_tax_vsaoi > 0
      AND avg_employees > 0
    ORDER BY company_regcode, year DESC
)
-- Cities (excluding Rīga, as it's both city and municipality)
SELECT 
    'city' as location_type,
    a.city_name as location_name,
    NULL as location_code,
    
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    
    -- Weighted average salary
    CASE 
        WHEN SUM(t.avg_employees) > 0 THEN
            SUM((t.social_tax_vsaoi / 0.3409) / 12) / SUM(t.avg_employees)
        ELSE NULL
    END as avg_salary,
    
    -- Avg Revenue per company
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE NULL END as avg_revenue_per_company,
    
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
LEFT JOIN latest_taxes t ON c.regcode = t.company_regcode
WHERE a.city_name IS NOT NULL
  AND a.city_name != 'Rīga'  -- Rīga ir gan pilsēta, gan novads
  AND c.status = 'active'
GROUP BY a.city_name

UNION ALL

-- Municipalities (includes companies from both municipality and its cities)
SELECT 
    'municipality' as location_type,
    a.municipality_name as location_name,
    NULL as location_code,
    
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    
    CASE 
        WHEN SUM(t.avg_employees) > 0 THEN
            SUM((t.social_tax_vsaoi / 0.3409) / 12) / SUM(t.avg_employees)
        ELSE NULL
    END as avg_salary,
    
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE NULL END as avg_revenue_per_company,
    
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
LEFT JOIN latest_taxes t ON c.regcode = t.company_regcode
WHERE a.municipality_name IS NOT NULL
  -- No additional filter - includes all companies where municipality_name exists,
  -- regardless of whether city_name is also set
  AND c.status = 'active'
GROUP BY a.municipality_name

UNION ALL

-- Rīga as special case (both city and municipality)
SELECT 
    'city' as location_type,
    'Rīga' as location_name,
    NULL as location_code,
    
    COUNT(DISTINCT c.regcode) as company_count,
    SUM(f.employees) as total_employees,
    SUM(f.turnover) as total_revenue,
    SUM(f.profit) as total_profit,
    
    CASE 
        WHEN SUM(t.avg_employees) > 0 THEN
            SUM((t.social_tax_vsaoi / 0.3409) / 12) / SUM(t.avg_employees)
        ELSE NULL
    END as avg_salary,
    
    CASE WHEN COUNT(DISTINCT c.regcode) > 0 THEN SUM(f.turnover) / COUNT(DISTINCT c.regcode) ELSE NULL END as avg_revenue_per_company,
    
    ARRAY_AGG(c.regcode ORDER BY f.turnover DESC NULLS LAST) FILTER (WHERE f.turnover IS NOT NULL) as top_company_codes
    
FROM companies c
JOIN address_dimension a ON c.addressid = a.address_id
LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
LEFT JOIN latest_taxes t ON c.regcode = t.company_regcode
WHERE (a.city_name = 'Rīga' OR a.municipality_name = 'Rīga')
  AND c.status = 'active';

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
