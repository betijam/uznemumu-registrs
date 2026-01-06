-- Person Analytics Materialized View (FAST VERSION)
-- Simplified without correlated subquery for main_company_name

-- GDPR Blacklist Table
CREATE TABLE IF NOT EXISTS hidden_persons (
    person_hash VARCHAR(64) PRIMARY KEY,
    hidden_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);

-- Drop existing view if exists
DROP MATERIALIZED VIEW IF EXISTS person_analytics_cache CASCADE;

-- Main Analytics View (WITHOUT main_company_name for speed)
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
    
    -- Wealth: Equity share value
    ROUND(SUM(CASE 
        WHEN role = 'member' AND status = 'active'
        THEN (COALESCE(share_percent, 0) / 100.0) * COALESCE(equity, 0)
        ELSE 0 
    END)::numeric, 2) as net_worth,
    
    -- Power: Total managed turnover
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
    
    -- Activity: Count of active companies
    COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) as active_companies_count,
    
    -- Total companies ever
    COUNT(DISTINCT regcode) as total_companies_count,
    
    -- Primary sector
    MODE() WITHIN GROUP (ORDER BY LEFT(nace_code, 2)) as primary_nace,
    
    -- Placeholder for main_company (will be NULL for now)
    NULL::text as main_company_name

FROM person_companies
GROUP BY person_hash
HAVING COUNT(DISTINCT CASE WHEN status = 'active' THEN regcode END) > 0;

-- Create indexes for fast ranking queries
CREATE INDEX IF NOT EXISTS idx_pac_net_worth ON person_analytics_cache(net_worth DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_managed_turnover ON person_analytics_cache(managed_turnover DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_pac_active_count ON person_analytics_cache(active_companies_count DESC);
CREATE INDEX IF NOT EXISTS idx_pac_person_hash ON person_analytics_cache(person_hash);
