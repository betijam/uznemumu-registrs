"""
Quick migration runner for company_computed_metrics table
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

def run_migration():
    engine = create_engine(DATABASE_URL)
    
    migration_file = os.path.join(os.path.dirname(__file__), "db", "computed_metrics_migration.sql")
    
    print(f"📊 Running computed metrics migration from {migration_file}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        
        print("✅ Computed metrics migration completed successfully!")
        print("\n📋 Created table:")
        print("  - company_computed_metrics")
        print("\n📋 Created indexes:")
        print("  - idx_computed_metrics_company")
        print("  - idx_computed_metrics_year")
        print("  - idx_computed_metrics_company_year")
        print("\n🎯 Next step: Run ETL to populate data")
        print("   python backend/etl/calculate_company_metrics.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL is set correctly")
        print("2. Ensure PostgreSQL is running")
        print("3. Check user has CREATE TABLE permissions")
        raise

if __name__ == "__main__":
    run_migration()
