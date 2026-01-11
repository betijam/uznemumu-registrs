-- Check all column names in financial_reports table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'financial_reports'
AND column_name LIKE '%interest%' 
   OR column_name LIKE '%deprec%' 
   OR column_name LIKE '%tax%'
   OR column_name LIKE '%cash%'
   OR column_name LIKE '%cfo%'
   OR column_name LIKE '%cfi%'
   OR column_name LIKE '%cff%'
ORDER BY column_name;
