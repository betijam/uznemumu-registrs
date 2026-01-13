-- Populate entity_type column for existing data
-- This is a one-time migration script

-- 1. Mark all legal entities without regcode in companies table as FOREIGN_ENTITY
UPDATE persons p
SET entity_type = 'FOREIGN_ENTITY'
WHERE p.role = 'member' 
  AND p.legal_entity_regcode IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM companies c 
    WHERE c.regcode = p.legal_entity_regcode
  );

-- 2. Mark all legal entities WITH regcode in companies as LEGAL_ENTITY  
UPDATE persons p
SET entity_type = 'LEGAL_ENTITY'
WHERE p.role = 'member'
  AND p.legal_entity_regcode IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM companies c 
    WHERE c.regcode = p.legal_entity_regcode
  );

-- 3. Mark all physical persons (no legal_entity_regcode)
UPDATE persons p
SET entity_type = 'PHYSICAL_PERSON'
WHERE p.role IN ('member', 'officer', 'ubo')
  AND p.legal_entity_regcode IS NULL;

-- Verify counts
SELECT 
    entity_type,
    role,
    COUNT(*) as count
FROM persons
GROUP BY entity_type, role
ORDER BY entity_type, role;
