-- Quick SQL to check foreign entity patterns
-- Run with: railway run psql < check_foreign.sql

\echo '========================================='
\echo 'CHECKING FOREIGN ENTITY IDENTIFICATION'
\echo '========================================='

\echo ''
\echo '1. Sample members with legal_entity_regcode:'
SELECT 
    person_name,
    legal_entity_regcode,
    entity_type
FROM persons
WHERE role = 'member' 
  AND legal_entity_regcode IS NOT NULL
LIMIT 10;

\echo ''
\echo '2. Foreign-looking company names in members:'
SELECT 
    person_name,
    legal_entity_regcode,
    entity_type,
    COUNT(*) OVER() as total_count
FROM persons
WHERE role = 'member' 
  AND legal_entity_regcode IS NOT NULL
  AND (
    person_name ILIKE '%gmbh%' OR
    person_name ILIKE '%uab%' OR
    person_name ILIKE '%osaühing%' OR
    person_name ILIKE '%osauhing%' OR
    person_name ILIKE '%ltd%' OR
    person_name ILIKE '%ab%' OR
    person_name ILIKE '%gruppe%'
  )
LIMIT 20;

\echo ''
\echo '3. Checking companies table for foreign branch types:'
SELECT 
    name,
    type,
    regcode
FROM companies
WHERE type ILIKE '%ārvalst%' OR type ILIKE '%filiale%'
LIMIT 10;

\echo ''
\echo '4. Cross-check: persons with foreign names vs companies table:'
SELECT 
    p.person_name,
    p.legal_entity_regcode,
    c.name as company_name,
    c.type as company_type
FROM persons p
LEFT JOIN companies c ON c.regcode = p.legal_entity_regcode
WHERE p.role = 'member' 
  AND p.legal_entity_regcode IS NOT NULL
  AND (
    p.person_name ILIKE '%gmbh%' OR
    p.person_name ILIKE '%uab%' OR
    p.person_name ILIKE '%osaühing%' OR
    p.person_name ILIKE '%osauhing%'
  )
LIMIT 10;
