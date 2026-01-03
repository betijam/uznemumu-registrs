-- Migration: Add Person Profile Optimizations
-- Date: 2026-01-03
-- Purpose: Add indexes and computed columns for person profile feature

-- Enable pg_trgm extension for fuzzy text search (if not already enabled)
-- This is safe to run multiple times
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. Add partial index for active persons (WHERE date_to IS NULL)
-- This speeds up queries filtering for current roles
CREATE INDEX IF NOT EXISTS idx_persons_person_code_active 
ON persons(person_code) 
WHERE date_to IS NULL;

-- 2. Add index for person lookups by name (for search functionality)
-- Using GIN index with pg_trgm for fuzzy matching
CREATE INDEX IF NOT EXISTS idx_persons_name_trgm 
ON persons USING gin (person_name gin_trgm_ops);

-- 3. Add index for company_regcode + role combination (frequent join pattern)
CREATE INDEX IF NOT EXISTS idx_persons_company_role 
ON persons(company_regcode, role) 
WHERE date_to IS NULL;

-- 4. Add index for birth_date (used in person matching fallback)
CREATE INDEX IF NOT EXISTS idx_persons_birth_date 
ON persons(birth_date) 
WHERE birth_date IS NOT NULL;

-- 5. Simple B-tree index on person_name as fallback (if GIN fails)
-- This provides basic alphabetical search capability
CREATE INDEX IF NOT EXISTS idx_persons_name_btree
ON persons(person_name);

-- Note: We're not adding person_id_hash column yet because:
-- 1. It would require regenerating ETL with new column
-- 2. Hash calculation is cheap and can be done on-the-fly
-- 3. We can add it later if lookup performance becomes an issue

-- Analyze tables to update query planner statistics
ANALYZE persons;
