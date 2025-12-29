-- Optimised update for birth_date from person_code
-- Only updates where code matches format DDMMYY-*****
-- Uses Latvian logic: YY < 30 -> 20YY, else 19YY

UPDATE persons 
SET birth_date = 
    MAKE_DATE(
        CASE 
            WHEN CAST(SUBSTRING(person_code, 5, 2) AS INTEGER) < 30 
            THEN 2000 + CAST(SUBSTRING(person_code, 5, 2) AS INTEGER)
            ELSE 1900 + CAST(SUBSTRING(person_code, 5, 2) AS INTEGER)
        END,
        CAST(SUBSTRING(person_code, 3, 2) AS INTEGER),
        CAST(SUBSTRING(person_code, 1, 2) AS INTEGER)
    )
WHERE birth_date IS NULL 
  AND person_code ~ '^[0-9]{6}-'
  -- Basic validation to avoid date errors
  AND CAST(SUBSTRING(person_code, 3, 2) AS INTEGER) BETWEEN 1 AND 12
  AND CAST(SUBSTRING(person_code, 1, 2) AS INTEGER) BETWEEN 1 AND 31;
