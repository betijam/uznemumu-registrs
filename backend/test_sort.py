from etl.loader import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Test the actual query with NaN filter
    result = conn.execute(text("""
        SELECT 
            c.regcode, c.name, s.turnover
        FROM companies c
        LEFT JOIN company_stats_materialized s ON s.regcode = c.regcode AND s.year = 2024
        WHERE s.turnover IS NOT NULL 
          AND s.turnover::text != 'NaN'
          AND s.turnover > 0
        ORDER BY s.turnover DESC NULLS LAST
        LIMIT 10
    """)).fetchall()
    
    print("TOP 10 by turnover (with NULL + NaN + >0 filter):")
    for i, r in enumerate(result, 1):
        t = f"{r.turnover:,.0f}" if r.turnover else "NULL"
        print(f"  {i}. {r.name[:50]:<50} | {t} EUR")
