-- Migration: Add entity_type column to persons table
-- This allows us to identify FOREIGN_ENTITY members without additional queries

ALTER TABLE persons 
ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);

-- Add index for faster filtering
CREATE INDEX IF NOT EXISTS idx_persons_entity_type ON persons(entity_type);

-- Add comment
COMMENT ON COLUMN persons.entity_type IS 'Type of entity: PHYSICAL_PERSON, LEGAL_ENTITY, FOREIGN_ENTITY, etc.';
