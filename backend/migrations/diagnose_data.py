import os
import sys
from sqlalchemy import create_engine, text

# Setup paths and environment
try:
    from dotenv import load_dotenv
    # Go up 3 levels: backend/migrations -> backend -> root
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    print(f"Looking for .env at: {env_path}")
    load_dotenv(env_path)
    DATABASE_URL = os.getenv("DATABASE_URL")
except ImportError:
    print("python-dotenv not installed.")
    DATABASE_URL = None

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found!")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

safe_url = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '...'
print(f"Connecting to DB: ...@{safe_url}")

engine = create_engine(DATABASE_URL)

def run_diagnostics():
    print("\n--- DIAGNOSTICS START ---")
    
    with engine.connect() as conn:
        # 1. Check industry_stats_materialized existence and count
        print("\n1. Checking 'industry_stats_materialized':")
        try:
            count = conn.execute(text("SELECT COUNT(*) FROM industry_stats_materialized")).scalar()
            print(f"   Total rows: {count}")
            
            if count > 0:
                # Check Level 1 (Sections)
                l1_count = conn.execute(text("SELECT COUNT(*) FROM industry_stats_materialized WHERE nace_level = 1")).scalar()
                print(f"   Level 1 rows (Sections): {l1_count}")
                
                # Check Data Validity
                sample = conn.execute(text("SELECT nace_code, data_year, total_turnover FROM industry_stats_materialized LIMIT 1")).fetchone()
                print(f"   Sample row: {sample}")
                
                # Check for NULL years
                null_year = conn.execute(text("SELECT COUNT(*) FROM industry_stats_materialized WHERE data_year IS NULL")).scalar()
                print(f"   Rows with NULL year: {null_year}")
            else:
                print("   TABLE IS EMPTY!")
        except Exception as e:
            print(f"   ERROR accessing table: {e}")

        # 2. Check source tables
        print("\n2. Checking source tables:")
        try:
            companies_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            print(f"   'companies' count: {companies_count}")
            
            reports_count = conn.execute(text("SELECT COUNT(*) FROM financial_reports")).scalar()
            print(f"   'financial_reports' count: {reports_count}")
            
            if reports_count > 0:
                latest_year = conn.execute(text("SELECT MAX(year) FROM financial_reports")).scalar()
                print(f"   Latest financial report year: {latest_year}")
        except Exception as e:
            print(f"   ERROR accessing source tables: {e}")

    print("\n--- DIAGNOSTICS END ---")

if __name__ == "__main__":
    run_diagnostics()
