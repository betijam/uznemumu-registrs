from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Use production DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

print(f"Connecting to: {DATABASE_URL[:30]}...")

engine = create_engine(DATABASE_URL)

def check_production():
    with engine.connect() as conn:
        print("\n=== Checking Production Database ===\n")
        
        # Check if view exists
        view_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_matviews 
                WHERE schemaname = 'public' 
                AND matviewname = 'location_statistics'
            )
        """)).scalar()
        
        if not view_check:
            print("❌ Materialized view 'location_statistics' DOES NOT EXIST!")
            print("\nYou need to run the SQL from location_stats.sql in Neon console.")
            return
        
        print("✅ View exists\n")
        
        # Check actual data
        result = conn.execute(text("""
            SELECT 
                location_name,
                company_count,
                avg_salary
            FROM location_statistics
            WHERE location_name IN ('Jaunjelgava', 'Rīga', 'Mārupe')
            ORDER BY location_name
        """))
        
        print("Current values in production:\n")
        for row in result:
            status = "✅" if row.avg_salary < 5000 else "❌"
            print(f"{status} {row.location_name:20} | Avg Salary: €{row.avg_salary:>10,.2f}")
        
        # Check if tax_payments table exists
        print("\n=== Checking tax_payments table ===")
        tax_check = conn.execute(text("""
            SELECT COUNT(*) FROM tax_payments WHERE social_tax_vsaoi > 0
        """)).scalar()
        
        print(f"✅ tax_payments has {tax_check:,} records with VSAOI data")

if __name__ == "__main__":
    check_production()
