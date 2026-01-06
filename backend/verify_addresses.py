import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Verifying Address Dimension ===\n")

with engine.connect() as conn:
    # Check total rows
    result = conn.execute(text("SELECT COUNT(*) FROM address_dimension"))
    total = result.scalar()
    print(f"Total addresses: {total:,}")
    
    # Check municipality distribution
    result = conn.execute(text("""
        SELECT municipality_name, COUNT(*) as cnt
        FROM address_dimension
        WHERE municipality_name IS NOT NULL
        GROUP BY municipality_name
        ORDER BY cnt DESC
        LIMIT 10
    """))
    print("\nTop 10 Municipalities by address count:")
    for row in result:
        print(f"  {row.municipality_name}: {row.cnt:,}")
    
    # Check city distribution
    result = conn.execute(text("""
        SELECT city_name, COUNT(*) as cnt
        FROM address_dimension
        WHERE city_name IS NOT NULL
        GROUP BY city_name
        ORDER BY cnt DESC
        LIMIT 10
    """))
    print("\nTop 10 Cities by address count:")
    for row in result:
        print(f"  {row.city_name}: {row.cnt:,}")
    
    # Check companies with addresses
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_companies,
            COUNT(a.address_id) as with_address,
            COUNT(a.municipality_name) as with_municipality,
            COUNT(a.city_name) as with_city
        FROM companies c
        LEFT JOIN address_dimension a ON c.addressid = a.address_id
    """))
    row = result.fetchone()
    print(f"\n=== Company Coverage ===")
    print(f"Total companies: {row.total_companies:,}")
    print(f"With address match: {row.with_address:,} ({row.with_address/row.total_companies*100:.1f}%)")
    print(f"With municipality: {row.with_municipality:,} ({row.with_municipality/row.total_companies*100:.1f}%)")
    print(f"With city: {row.with_city:,} ({row.with_city/row.total_companies*100:.1f}%)")
