-- Migration: Update Person Analytics V4 (Direct Address Names)
-- Uses COALESCE(municipality_name, city_name) as the region name.

DROP MATERIALIZED VIEW IF EXISTS person_analytics_cache CASCADE;

CREATE MATERIALIZED VIEW person_analytics_cache AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        CASE WHEN equity = 'NaN' THEN 0 ELSE COALESCE(equity, 0) END as equity,
        CASE WHEN turnover = 'NaN' THEN 0 ELSE COALESCE(turnover, 0) END as turnover,
        CASE WHEN profit = 'NaN' THEN 0 ELSE COALESCE(profit, 0) END as profit
    FROM financial_reports
    WHERE year >= 2020
    ORDER BY company_regcode, year DESC
),
company_share_totals AS (
    SELECT 
        company_regcode,
        SUM(COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0)) as total_nominal
    FROM persons
    WHERE role = 'member'
    GROUP BY company_regcode
),
person_companies AS (
    SELECT 
        p.person_hash,
        p.person_name,
        p.role,
        
        -- Ownership Fraction
        CASE 
            WHEN p.share_percent > 0 THEN p.share_percent / 100.0
            WHEN cst.total_nominal > 0 THEN 
                (COALESCE(p.number_of_shares, 0) * COALESCE(p.share_nominal_value, 0)) / cst.total_nominal
            ELSE 0
        END as ownership_fraction,

        c.regcode,
        c.name as company_name,
        c.status,
        c.nace_code,
        
        -- Region Name from Address Dimension (Direct Name)
        COALESCE(ad.municipality_name, ad.city_name) as region_name,
        
        f.equity,
        f.turnover,
        f.profit
    FROM persons p
    JOIN companies c ON p.company_regcode = c.regcode
    LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
    LEFT JOIN address_dimension ad ON c.addressid = ad.address_id
    LEFT JOIN company_share_totals cst ON c.regcode = cst.company_regcode
    WHERE p.person_hash IS NOT NULL
      AND p.person_hash NOT IN (SELECT person_hash FROM hidden_persons)
)
SELECT 
    person_hash,
    MAX(person_name) as full_name,
    
    ROUND(SUM(CASE 
        WHEN role = 'member' AND status = 'active'
        THEN ownership_fraction * equity
        ELSE 0 
    END)::numeric, 2) as net_worth,
    
    ROUND(SUM(CASE 
        WHEN role = 'officer' AND status = 'active'
        THEN turnover
        ELSE 0 
    END)::numeric, 2) as managed_turnover,
    
    ROUND(SUM(CASE 
        WHEN role = 'officer' AND status = 'active'
        THEN profit
        ELSE 0 
    END)::numeric, 2) as managed_profit,
    
    COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) as active_companies_count,
    COUNT(DISTINCT regcode) as total_companies_count,
    
    MODE() WITHIN GROUP (ORDER BY LEFT(nace_code, 2)) as primary_nace,
    (ARRAY_AGG(company_name ORDER BY turnover DESC NULLS LAST))[1] as main_company_name,

    -- Main Region (Most frequent city/municipality)
    MODE() WITHIN GROUP (ORDER BY region_name) as main_region,

    ARRAY_AGG(DISTINCT role) as roles

FROM person_companies
GROUP BY person_hash
HAVING COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) > 0;

-- Indexes
CREATE INDEX idx_pac_net_worth ON person_analytics_cache(net_worth DESC NULLS LAST);
CREATE INDEX idx_pac_managed_turnover ON person_analytics_cache(managed_turnover DESC NULLS LAST);
CREATE INDEX idx_pac_active_count ON person_analytics_cache(active_companies_count DESC);
CREATE INDEX idx_pac_person_hash ON person_analytics_cache(person_hash);
CREATE INDEX idx_pac_region ON person_analytics_cache(main_region);
CREATE INDEX idx_pac_roles ON person_analytics_cache USING GIN(roles);
