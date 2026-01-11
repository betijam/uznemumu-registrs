-- Check what tables exist for persons data
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%officer%' 
   OR table_name LIKE '%member%'
   OR table_name LIKE '%person%'
   OR table_name LIKE '%ubo%'
ORDER BY table_name;
