import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Creating Location Statistics Materialized View ===\n")

with open('db/location_stats.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()
    print("✅ Materialized view created")
    
    # Check row count
    result = conn.execute(text("SELECT COUNT(*) FROM location_statistics"))
    count = result.scalar()
    print(f"\nTotal locations: {count}")
    
    # Sample data
    result = conn.execute(text("""
        SELECT location_type, location_name, company_count, total_revenue, avg_salary
        FROM location_statistics
        ORDER BY total_revenue DESC NULLS LAST
        LIMIT 5
    """))
    
    print("\nTop 5 locations by revenue:")
    for row in result:
        print(f"  {row.location_name} ({row.location_type}): {row.company_count} companies, €{row.total_revenue:,.0f}")
