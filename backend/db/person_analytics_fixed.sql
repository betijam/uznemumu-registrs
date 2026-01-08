-- Person Analytics Materialized View (FIXED - matches person.py logic)
-- Calculates wealth (nominal + equity), turnover, and employees

-- GDPR Blacklist Table
CREATE TABLE IF NOT EXISTS hidden_persons (
    person_hash VARCHAR(64) PRIMARY KEY,
    hidden_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);

-- Drop existing view
DROP MATERIALIZED VIEW IF EXISTS person_analytics_cache CASCADE;

-- Main Analytics View
CREATE MATERIALIZED VIEW person_analytics_cache AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        CASE 
            WHEN equity IS NOT NULL AND equity = equity AND equity <> 'Infinity'::numeric AND equity <> '-Infinity'::numeric 
            THEN equity 
            ELSE 0 
        END as equity,
        CASE 
            WHEN turnover IS NOT NULL AND turnover = turnover AND turnover <> 'Infinity'::numeric AND turnover <> '-Infinity'::numeric 
            THEN turnover 
            ELSE 0 
        END as turnover,
        CASE 
            WHEN profit IS NOT NULL AND profit = profit AND profit <> 'Infinity'::numeric AND profit <> '-Infinity'::numeric 
            THEN profit 
            ELSE 0 
        END as profit,
        COALESCE(employees, 0) as employees
    FROM financial_reports
    WHERE year >= 2020
    ORDER BY company_regcode, year DESC
),
company_total_capital AS (
    SELECT 
        company_regcode,
        SUM(COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0)) as total_capital
    FROM persons
    WHERE role = 'member'
    GROUP BY company_regcode
),
person_companies AS (
    SELECT 
        p.person_hash,
        p.person_name,
        p.role,
        p.company_regcode as regcode,
        c.status,
        c.nace_code,
        p.number_of_shares,
        p.share_nominal_value,
        p.date_to,
        f.equity,
        f.turnover,
        f.profit,
        f.employees,
        -- Calculate ownership percentage from shares
        CASE 
            WHEN tc.total_capital > 0 AND p.role = 'member'
            THEN ((COALESCE(p.number_of_shares, 0) * COALESCE(p.share_nominal_value, 0)) / tc.total_capital) * 100
            ELSE 0
        END as ownership_percent
    FROM persons p
    JOIN companies c ON p.company_regcode = c.regcode
    LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
    LEFT JOIN company_total_capital tc ON c.regcode = tc.company_regcode
    WHERE p.person_hash IS NOT NULL
      AND p.person_hash NOT IN (SELECT person_hash FROM hidden_persons)
)
SELECT 
    person_hash,
    MAX(person_name) as full_name,
    
    -- Equity Wealth (Estimated Market Value share)
    ROUND(COALESCE(SUM(CASE 
        WHEN role = 'member' AND status = 'active' AND date_to IS NULL AND equity > 0 AND ownership_percent > 0
        THEN (ownership_percent / 100.0) * equity
        ELSE 0 
    END), 0)::numeric, 2) as net_worth,

    -- Nominal Wealth (Book Value)
    ROUND(COALESCE(SUM(CASE 
        WHEN role = 'member' AND status = 'active' AND date_to IS NULL
        THEN (COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0))
        ELSE 0 
    END), 0)::numeric, 2) as total_nominal_value,
    
    -- Power: Total managed turnover (Active Officers)
    ROUND(COALESCE(SUM(CASE 
        WHEN role != 'member' AND status = 'active' AND date_to IS NULL AND turnover > 0
        THEN turnover
        ELSE 0 
    END), 0)::numeric, 2) as managed_turnover,
    
    -- Managed Employees
    COALESCE(SUM(CASE 
        WHEN role != 'member' AND status = 'active' AND date_to IS NULL
        THEN employees
        ELSE 0 
    END), 0) as managed_employees,
    
    -- Activity: Count of active companies (Active Role + Active Company)
    COUNT(DISTINCT CASE WHEN status = 'active' AND date_to IS NULL THEN regcode END) as active_companies_count,
    
    -- Historical: Companies where not active
    COUNT(DISTINCT regcode) - COUNT(DISTINCT CASE WHEN status = 'active' AND date_to IS NULL THEN regcode END) as historical_companies_count,
    
    -- Primary sector
    MODE() WITHIN GROUP (ORDER BY LEFT(nace_code, 2)) as primary_nace
    
FROM person_companies
GROUP BY person_hash
HAVING COUNT(DISTINCT regcode) > 0;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pac_net_worth ON person_analytics_cache(net_worth DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_managed_turnover ON person_analytics_cache(managed_turnover DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_active_count ON person_analytics_cache(active_companies_count DESC);
CREATE INDEX IF NOT EXISTS idx_pac_person_hash ON person_analytics_cache(person_hash);
