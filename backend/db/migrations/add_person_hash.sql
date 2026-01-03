-- Migration: Add person_hash column and index
-- Run this migration first, then use Python script to populate data

-- Step 1: Add person_hash column if it doesn't exist
ALTER TABLE persons ADD COLUMN IF NOT EXISTS person_hash VARCHAR(8);

-- Step 2: Create index for fast lookups (will speed up after data is populated)
CREATE INDEX IF NOT EXISTS idx_person_hash ON persons(person_hash);

-- Step 3: Verify the schema
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'persons' AND column_name = 'person_hash';

-- Note: Run update_person_hashes.py script to populate the hash values
-- The Python script uses batch updates for fast processing

