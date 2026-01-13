-- Update entity_type for foreign entities based on companies.type
-- Foreign entities are identified by companies.type containing 'ārvalst' or 'filiāle'

UPDATE persons p
SET entity_type = 'FOREIGN_ENTITY'
FROM companies c
WHERE p.legal_entity_regcode = c.regcode
  AND p.role = 'member'
  AND (
    c.type ILIKE '%ārvalst%' OR
    c.type ILIKE '%filiale%' OR
    c.type ILIKE '%filiāle%'
  );

-- Verify the update
SELECT 
    entity_type,
    COUNT(*) as count
FROM persons
WHERE role = 'member' AND legal_entity_regcode IS NOT NULL
GROUP BY entity_type;

-- Show sample of foreign entities
SELECT 
    p.person_name,
    p.legal_entity_regcode,
    c.name as company_name,
    c.type as company_type,
    p.entity_type
FROM persons p
JOIN companies c ON c.regcode = p.legal_entity_regcode
WHERE p.entity_type = 'FOREIGN_ENTITY'
LIMIT 10;
