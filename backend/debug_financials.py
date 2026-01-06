import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Debugging Financial Data ===\n")

with engine.connect() as conn:
    # Check raw financial data
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_reports,
            COUNT(DISTINCT company_regcode) as companies_with_data,
            SUM(CASE WHEN turnover IS NOT NULL THEN 1 ELSE 0 END) as reports_with_turnover,
            SUM(CASE WHEN profit IS NOT NULL THEN 1 ELSE 0 END) as reports_with_profit,
            MIN(turnover) as min_turnover,
            MAX(turnover) as max_turnover,
            AVG(turnover) as avg_turnover
        FROM financial_reports
        WHERE year >= 2020
    """))
    
    row = result.fetchone()
    print(f"Financial reports (2020+):")
    print(f"  Total reports: {row.total_reports:,}")
    print(f"  Companies: {row.companies_with_data:,}")
    print(f"  With turnover: {row.reports_with_turnover:,}")
    print(f"  Min turnover: {row.min_turnover}")
    print(f"  Max turnover: {row.max_turnover}")
    print(f"  Avg turnover: {row.avg_turnover}")
    
    # Check for infinity values
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM financial_reports
        WHERE year >= 2020
          AND (turnover = 'Infinity'::float OR turnover = '-Infinity'::float OR turnover = 'NaN'::float)
    """))
    inf_count = result.scalar()
    print(f"\n  Infinity/NaN turnover values: {inf_count}")
    
    # Check sample aggregation
    result = conn.execute(text("""
        SELECT 
            a.city_name,
            COUNT(DISTINCT c.regcode) as companies,
            SUM(f.turnover) as total_revenue,
            AVG(f.turnover) as avg_revenue
        FROM companies c
        JOIN address_dimension a ON c.addressid = a.address_id
        LEFT JOIN LATERAL (
            SELECT turnover FROM financial_reports
            WHERE company_regcode = c.regcode AND year >= 2020
            ORDER BY year DESC LIMIT 1
        ) f ON true
        WHERE a.city_name = 'Rīga' AND c.status = 'active'
        GROUP BY a.city_name
    """))
    
    row = result.fetchone()
    if row:
        print(f"\nRīga aggregation test:")
        print(f"  Companies: {row.companies}")
        print(f"  Total revenue: {row.total_revenue}")
        print(f"  Avg revenue: {row.avg_revenue}")
