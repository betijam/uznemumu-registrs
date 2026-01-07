from etl.loader import engine
from sqlalchemy import text

conn = engine.connect()

# Check Level 1 industries
r = conn.execute(text("SELECT nace_code, nace_name, nace_level FROM industry_stats_materialized WHERE nace_level = 1 ORDER BY nace_code LIMIT 15")).fetchall()
print('Level 1 industries in materialized view:')
for row in r:
    print(row)

# Check undefined NACE count
r2 = conn.execute(text("SELECT nace_text, COUNT(*) as cnt FROM companies WHERE nace_text ILIKE '%nenoteikt%' OR nace_text IS NULL GROUP BY nace_text")).fetchall()
print('\nCompanies with undefined NACE:')
for row in r2:
    print(row)
