-- Person Analytics Materialized View
-- Creates cached analytics for "Latvijas Biznesa Elite" dashboard
-- Refresh nightly via cron/scheduler

-- GDPR Blacklist Table (Right to be forgotten)
CREATE TABLE IF NOT EXISTS hidden_persons (
    person_hash VARCHAR(64) PRIMARY KEY,
    hidden_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);

-- Drop existing view if exists
DROP MATERIALIZED VIEW IF EXISTS person_analytics_cache CASCADE;

-- Main Analytics View
CREATE MATERIALIZED VIEW person_analytics_cache AS
WITH latest_financials AS (
    SELECT DISTINCT ON (company_regcode)
        company_regcode,
        year,
        equity,
        turnover,
        profit
    FROM financial_reports
    WHERE year >= 2020
    ORDER BY company_regcode, year DESC
),
person_companies AS (
    SELECT 
        p.person_hash,
        p.person_name,
        p.role,
        p.share_percent,
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
    
    -- Wealth: Equity share value (only for members/shareholders)
    ROUND(SUM(CASE 
        WHEN role = 'member' AND status = 'active'
        THEN (COALESCE(share_percent, 0) / 100.0) * COALESCE(equity, 0)
        ELSE 0 
    END)::numeric, 2) as net_worth,
    
    -- Power: Total managed turnover (for officers/board members)
    ROUND(SUM(CASE 
        WHEN role = 'officer' AND status = 'active'
        THEN COALESCE(turnover, 0)
        ELSE 0 
    END)::numeric, 2) as managed_turnover,
    
    -- Profit under management
    ROUND(SUM(CASE 
        WHEN role = 'officer' AND status = 'active'
        THEN COALESCE(profit, 0)
        ELSE 0 
    END)::numeric, 2) as managed_profit,
    
    -- Activity: Count of active companies (any role)
    COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) as active_companies_count,
    
    -- Total companies ever associated
    COUNT(DISTINCT regcode) as total_companies_count,
    
    -- Primary sector (most common NACE section)
    MODE() WITHIN GROUP (ORDER BY LEFT(nace_code, 2)) as primary_nace,
    
    -- Get main company name (largest by turnover)
    (SELECT c2.name FROM companies c2 
     JOIN persons p2 ON c2.regcode = p2.company_regcode 
     WHERE p2.person_hash = person_companies.person_hash 
       AND c2.status = 'active'
     ORDER BY (SELECT COALESCE(f2.turnover, 0) FROM latest_financials f2 WHERE f2.company_regcode = c2.regcode) DESC
     LIMIT 1) as main_company_name

FROM person_companies
GROUP BY person_hash
HAVING COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) > 0;

-- Create indexes for fast ranking queries
CREATE INDEX IF NOT EXISTS idx_pac_net_worth ON person_analytics_cache(net_worth DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_managed_turnover ON person_analytics_cache(managed_turnover DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_active_count ON person_analytics_cache(active_companies_count DESC);
CREATE INDEX IF NOT EXISTS idx_pac_person_hash ON person_analytics_cache(person_hash);

-- Refresh command (run via scheduler)
-- REFRESH MATERIALIZED VIEW person_analytics_cache;
