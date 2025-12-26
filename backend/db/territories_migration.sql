-- Migration: Regional Economics Dashboard - Territories and Aggregates
-- Based on ATVK (Administrative Territorial Classification) system

-- ============================================================================
-- 1. TERRITORIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS territories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(7) UNIQUE NOT NULL,   -- ATVK code (7 characters)
    name TEXT NOT NULL,                 -- Territory name
    level SMALLINT NOT NULL,            -- 1=region, 2=municipality, 3=city/parish
    type VARCHAR(30) NOT NULL,          -- Type of territory
    parent_code VARCHAR(7),             -- Reference to parent territory
    valid_from DATE,
    valid_to DATE,
    
    CONSTRAINT territories_code_unique UNIQUE (code),
    CONSTRAINT territories_level_check CHECK (level IN (1, 2, 3))
);

CREATE INDEX IF NOT EXISTS idx_territories_level ON territories(level);
CREATE INDEX IF NOT EXISTS idx_territories_parent_code ON territories(parent_code);
CREATE INDEX IF NOT EXISTS idx_territories_type ON territories(type);
CREATE INDEX IF NOT EXISTS idx_territories_valid ON territories(valid_from, valid_to);

COMMENT ON TABLE territories IS 'ATVK administrative territories hierarchy (regions, municipalities, cities, parishes)';
COMMENT ON COLUMN territories.code IS 'ATVK 7-character code';
COMMENT ON COLUMN territories.level IS '1=region, 2=municipality, 3=city/parish';
COMMENT ON COLUMN territories.type IS 'REGIONS, NOVADS, VALSTSPILSĒTU_PAŠVALDĪBA, VALSTSPILSĒTA, PILSĒTA, PAGASTS';


-- ============================================================================
-- 1.5. ADD ATVK COLUMN TO COMPANIES TABLE
-- ============================================================================

-- Add atvk column if it doesn't exist
ALTER TABLE companies ADD COLUMN IF NOT EXISTS atvk VARCHAR(7);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_companies_atvk ON companies(atvk);

COMMENT ON COLUMN companies.atvk IS 'ATVK territorial code (7 characters)';


-- ============================================================================
-- 2. COMPANY-TERRITORY MAPPING VIEW
-- ============================================================================

CREATE OR REPLACE VIEW company_territories AS
SELECT
    c.regcode AS company_id,
    c.regcode,
    c.atvk AS company_atvk,
    c.name AS company_name,
    
    -- Municipality level (level 2)
    t_muni.id AS municipality_id,
    t_muni.code AS municipality_code,
    t_muni.name AS municipality_name,
    t_muni.type AS municipality_type,
    
    -- Region level (level 1)
    t_region.id AS region_id,
    t_region.code AS region_code,
    t_region.name AS region_name
    
FROM companies c
LEFT JOIN territories t ON t.code = c.atvk
LEFT JOIN territories t_muni ON (
    -- If company ATVK is already municipality level (level=2)
    (t.level = 2 AND t_muni.code = t.code)
    -- If company ATVK is city/parish (level=3), municipality = parent_code
    OR (t.level = 3 AND t_muni.code = t.parent_code)
)
LEFT JOIN territories t_region ON (
    -- Region from municipality's parent_code
    t_region.code = t_muni.parent_code AND t_region.level = 1
)
WHERE t_muni.level = 2;  -- Only municipality level

COMMENT ON VIEW company_territories IS 'Maps companies to their municipality and region via ATVK codes';


-- ============================================================================
-- 3. TERRITORY YEAR AGGREGATES
-- ============================================================================

CREATE TABLE IF NOT EXISTS territory_year_aggregates (
    id SERIAL PRIMARY KEY,
    territory_id INT REFERENCES territories(id) ON DELETE CASCADE,
    year INT NOT NULL,
    
    -- Economic indicators
    total_revenue NUMERIC(18,2),
    total_profit NUMERIC(18,2),
    total_employees INT,
    avg_salary NUMERIC(10,2),
    company_count INT,
    
    -- Growth rates (Year-over-Year %)
    revenue_growth_yoy NUMERIC(10,2),
    employee_growth_yoy NUMERIC(10,2),
    salary_growth_yoy NUMERIC(10,2),
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(territory_id, year)
);

CREATE INDEX IF NOT EXISTS idx_territory_year_agg_territory ON territory_year_aggregates(territory_id);
CREATE INDEX IF NOT EXISTS idx_territory_year_agg_year ON territory_year_aggregates(year);
CREATE INDEX IF NOT EXISTS idx_territory_year_agg_territory_year ON territory_year_aggregates(territory_id, year);

COMMENT ON TABLE territory_year_aggregates IS 'Pre-computed economic indicators by territory and year';


-- ============================================================================
-- 4. TERRITORY INDUSTRY YEAR AGGREGATES
-- ============================================================================

CREATE TABLE IF NOT EXISTS territory_industry_year_aggregates (
    id SERIAL PRIMARY KEY,
    territory_id INT REFERENCES territories(id) ON DELETE CASCADE,
    industry_code VARCHAR(10) NOT NULL,
    industry_name TEXT,
    year INT NOT NULL,
    
    total_revenue NUMERIC(18,2),
    total_profit NUMERIC(18,2),
    total_employees INT,
    company_count INT,
    
    computed_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(territory_id, industry_code, year)
);

CREATE INDEX IF NOT EXISTS idx_territory_industry_agg ON territory_industry_year_aggregates(territory_id, year);
CREATE INDEX IF NOT EXISTS idx_territory_industry_code ON territory_industry_year_aggregates(industry_code);

COMMENT ON TABLE territory_industry_year_aggregates IS 'Industry breakdown by territory';


-- ============================================================================
-- 5. HELPER VIEW: LATEST TERRITORY STATS
-- ============================================================================

CREATE OR REPLACE VIEW v_territory_latest_stats AS
SELECT 
    t.id AS territory_id,
    t.code,
    t.name,
    t.type,
    t.level,
    tya.year,
    tya.total_revenue,
    tya.total_profit,
    tya.total_employees,
    tya.avg_salary,
    tya.company_count,
    tya.revenue_growth_yoy,
    tya.employee_growth_yoy,
    tya.salary_growth_yoy
FROM territories t
LEFT JOIN LATERAL (
    SELECT *
    FROM territory_year_aggregates
    WHERE territory_id = t.id
    ORDER BY year DESC
    LIMIT 1
) tya ON true
WHERE t.level = 2;  -- Only municipalities

COMMENT ON VIEW v_territory_latest_stats IS 'Latest economic stats for each municipality';
