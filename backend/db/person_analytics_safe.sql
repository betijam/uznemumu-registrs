-- Person Analytics Materialized View (SAFE VERSION - handles NaN/Infinity)
-- Filters out invalid numeric values that corrupt aggregations

-- GDPR Blacklist Table
CREATE TABLE IF NOT EXISTS hidden_persons (
    person_hash VARCHAR(64) PRIMARY KEY,
    hidden_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);

-- Drop existing view
DROP MATERIALIZED VIEW IF EXISTS person_analytics_cache CASCADE;

-- Main Analytics View with NaN/Infinity protection
CREATE MATERIALIZED VIEW person_analytics_cache AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        -- Filter out NaN, Infinity, and NULL
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
        END as profit
    FROM financial_reports
    WHERE year >= 2020
    ORDER BY company_regcode, year DESC
),
person_companies AS (
    SELECT 
        p.person_hash,
        p.person_name,
        p.role,
        COALESCE(p.share_percent, 0) as share_percent,
        c.regcode,
        c.status,
        c.nace_code,
        f.equity,
        f.turnover,
        f.profit
    FROM persons p
    JOIN companies c ON p.company_regcode = c.regcode
    LEFT JOIN latest_financials f ON c.regcode = f.company_regcode
    WHERE p.person_hash IS NOT NULL
      AND p.person_hash NOT IN (SELECT person_hash FROM hidden_persons)
)
SELECT 
    person_hash,
    MAX(person_name) as full_name,
    
    -- Wealth: Equity share value (safe aggregation)
    ROUND(COALESCE(SUM(CASE 
        WHEN role = 'member' AND status = 'active' AND equity > 0
        THEN (share_percent / 100.0) * equity
        ELSE 0 
    END), 0)::numeric, 2) as net_worth,
    
    -- Power: Total managed turnover (safe aggregation)
    ROUND(COALESCE(SUM(CASE 
        WHEN role = 'officer' AND status = 'active' AND turnover > 0
        THEN turnover
        ELSE 0 
    END), 0)::numeric, 2) as managed_turnover,
    
    -- Profit under management (safe aggregation)
    ROUND(COALESCE(SUM(CASE 
        WHEN role = 'officer' AND status = 'active' AND profit <> 0
        THEN profit
        ELSE 0 
    END), 0)::numeric, 2) as managed_profit,
    
    -- Activity: Count of active companies
    COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) as active_companies_count,
    
    -- Total companies ever
    COUNT(DISTINCT regcode) as total_companies_count,
    
    -- Primary sector
    MODE() WITHIN GROUP (ORDER BY LEFT(nace_code, 2)) as primary_nace,
    
    -- Placeholder for main_company
    NULL::text as main_company_name

FROM person_companies
GROUP BY person_hash
HAVING COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) > 0;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pac_net_worth ON person_analytics_cache(net_worth DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_managed_turnover ON person_analytics_cache(managed_turnover DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_active_count ON person_analytics_cache(active_companies_count DESC);
CREATE INDEX IF NOT EXISTS idx_pac_person_hash ON person_analytics_cache(person_hash);
