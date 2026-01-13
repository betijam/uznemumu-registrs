-- Performance Indexes for slow pages
-- Run this script in your Neon database console

-- ============================================================================
-- PERSONS TABLE INDEXES (for career timeline and person profile)
-- ============================================================================

-- Index for person lookups by code and name (primary lookup)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_persons_code_name 
ON persons(person_code, person_name);

-- Index for company capital calculations (member role lookups)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_persons_company_member 
ON persons(company_regcode, role) 
WHERE role = 'member';

-- Composite index for person career timeline
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_persons_career_lookup
ON persons(person_code, person_name, company_regcode);

-- ============================================================================
-- COMPANIES TABLE INDEXES
-- ============================================================================

-- Index for NACE code lookups (industry pages)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_nace_status 
ON companies(nace_code, status);

-- Index for ATVK (territory) lookups (regional pages)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_atvk_status 
ON companies(atvk, status);

-- ============================================================================
-- FINANCIAL_REPORTS TABLE INDEXES
-- ============================================================================

-- Composite index for financial data lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_reports_regcode_year 
ON financial_reports(company_regcode, year);

-- Index for turnover-based sorting/filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_reports_year_turnover 
ON financial_reports(year, turnover DESC NULLS LAST);

-- ============================================================================
-- MATERIALIZED VIEW INDEXES
-- ============================================================================

-- Index on industry_stats_materialized for faster lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_stats_code_year 
ON industry_stats_materialized(nace_code, data_year);

-- Index on territory_year_aggregates
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_territory_year_agg_lookup 
ON territory_year_aggregates(territory_id, year);

-- ============================================================================
-- ANALYZE TABLES (Update statistics for query planner)
-- ============================================================================

ANALYZE persons;
ANALYZE companies;
ANALYZE financial_reports;
ANALYZE industry_stats_materialized;
ANALYZE territory_year_aggregates;

-- ============================================================================
-- ADDRESS_DIMENSION INDEXES (for location/region pages)
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_address_city_name 
ON address_dimension(city_name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_address_municipality_name 
ON address_dimension(municipality_name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_address_parish_name 
ON address_dimension(parish_name);

-- ============================================================================
-- LOCATION_STATISTICS INDEXES (materialized view for locations)
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_location_stats_type_name 
ON location_statistics(location_type, location_name);

-- ============================================================================
-- COMPANY_STATS_MATERIALIZED INDEXES (for /explore page)
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_company_stats_regcode 
ON company_stats_materialized(regcode);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_company_stats_turnover 
ON company_stats_materialized(turnover DESC NULLS LAST);

-- ============================================================================
-- NACE SECTION INDEX (for industry page NACE filtering)
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_nace_section 
ON companies(nace_section);

-- ============================================================================
-- TAX_PAYMENTS INDEXES (for salary and tax calculations)
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tax_payments_regcode_year 
ON tax_payments(company_regcode, year);

-- ============================================================================
-- INDUSTRY_LEADERS_CACHE INDEX
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_leaders_nace 
ON industry_leaders_cache(nace_code);

-- Run ANALYZE again after creating indexes
ANALYZE address_dimension;
ANALYZE location_statistics;
ANALYZE company_stats_materialized;
ANALYZE tax_payments;
ANALYZE industry_leaders_cache;
