-- Migration: Add birth_date column to persons table
-- This extracts birth date from the masked person code (e.g., 290800-***** -> 2000-08-29)

ALTER TABLE persons ADD COLUMN IF NOT EXISTS birth_date DATE;

-- Update birth_date from existing person_code data
-- Format: DDMMYY-***** where first 6 digits represent birth date
UPDATE persons 
SET birth_date = 
    CASE 
        WHEN person_code IS NOT NULL 
         AND person_code ~ '^[0-9]{6}-' 
        THEN 
            -- Extract DDMMYY and convert to date
            -- YY < 30 -> 20YY, YY >= 30 -> 19YY (standard Latvian ID assumption)
            MAKE_DATE(
                CASE 
                    WHEN CAST(SUBSTRING(person_code, 5, 2) AS INTEGER) < 30 
                    THEN 2000 + CAST(SUBSTRING(person_code, 5, 2) AS INTEGER)
                    ELSE 1900 + CAST(SUBSTRING(person_code, 5, 2) AS INTEGER)
                END,
                CAST(SUBSTRING(person_code, 3, 2) AS INTEGER),  -- Month
                CAST(SUBSTRING(person_code, 1, 2) AS INTEGER)   -- Day
            )
        ELSE NULL
    END
WHERE birth_date IS NULL;

-- Create index for birth_date queries
CREATE INDEX IF NOT EXISTS idx_person_birth_date ON persons(birth_date);
