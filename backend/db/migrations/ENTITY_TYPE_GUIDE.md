# Entity Type Migration Guide

## Overview
The `entity_type` column in the `persons` table is used to identify foreign entities that don't have profile pages in our system.

## Values
- `PHYSICAL_PERSON` - Natural person (always has profile via person page)
- `LEGAL_ENTITY` - Latvian legal entity (has company profile page)
- `FOREIGN_ENTITY` - Foreign company/entity (NO profile page, show tooltip)

## How to populate from CSV

The `entity_type` data should be extracted from the original CSV files during ETL:

### Members CSV
Look for column that indicates entity type (e.g., `entity_type`, `type`, or similar)

### Officers CSV  
Similar column indicating if it's a foreign entity

## ETL Update Required

Update the ETL script to:
1. Read `entity_type` from CSV
2. Map values to our enum (PHYSICAL_PERSON, LEGAL_ENTITY, FOREIGN_ENTITY)
3. Insert into `persons.entity_type` column

## Example SQL Update (if CSV not available)

```sql
-- Mark all legal entities without regcode in companies table as FOREIGN_ENTITY
UPDATE persons p
SET entity_type = 'FOREIGN_ENTITY'
WHERE p.role = 'member' 
  AND p.legal_entity_regcode IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM companies c 
    WHERE c.regcode = p.legal_entity_regcode
  );

-- Mark all legal entities WITH regcode in companies as LEGAL_ENTITY  
UPDATE persons p
SET entity_type = 'LEGAL_ENTITY'
WHERE p.role = 'member'
  AND p.legal_entity_regcode IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM companies c 
    WHERE c.regcode = p.legal_entity_regcode
  );

-- Mark all physical persons
UPDATE persons p
SET entity_type = 'PHYSICAL_PERSON'
WHERE p.role IN ('member', 'officer', 'ubo')
  AND p.legal_entity_regcode IS NULL;
```

## Performance Impact
✅ **MUCH FASTER** - No additional SQL query needed per company
✅ Single column read from existing table
✅ Indexed for fast filtering
