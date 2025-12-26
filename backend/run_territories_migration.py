"""
Migration runner for territories and regional economics tables
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
    
    migration_file = os.path.join(os.path.dirname(__file__), "db", "territories_migration.sql")
    
    print(f"📊 Running territories migration from {migration_file}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        
        print("✅ Territories migration completed successfully!")
        print("\n📋 Created tables:")
        print("  - territories")
        print("  - territory_year_aggregates")
        print("  - territory_industry_year_aggregates")
        print("\n📋 Created views:")
        print("  - company_territories")
        print("  - v_territory_latest_stats")
        print("\n🎯 Next step: Import ATVK data")
        print("   python backend/etl/import_atvk_territories.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
