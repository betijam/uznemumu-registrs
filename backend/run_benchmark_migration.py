"""
Run benchmark database migration

This script creates the necessary tables for the benchmark/comparison tool:
- benchmark_sessions: Stores user comparison sessions
- industry_year_aggregates: Pre-computed industry statistics
- company_industry_rankings: Pre-computed company rankings
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

def run_migration():
    engine = create_engine(DATABASE_URL)
    
    migration_file = os.path.join(os.path.dirname(__file__), "db", "benchmark_migration.sql")
    
    print(f"📊 Running benchmark migration from {migration_file}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        with engine.connect() as conn:
            # Execute entire SQL file as one transaction
            # This preserves CREATE TABLE + INDEX order
            conn.execute(text(sql))
            conn.commit()
        
        print("✅ Benchmark migration completed successfully!")
        print("\n📋 Created tables:")
        print("  - benchmark_sessions")
        print("  - industry_year_aggregates")
        print("  - company_industry_rankings")
        print("\n📋 Created views:")
        print("  - v_industry_latest_stats")
        print("  - v_company_benchmark_data")
        print("\n🎯 Next step: Run ETL to populate data")
        print("   python backend/etl/calculate_benchmark_data.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL is set correctly")
        print("2. Ensure PostgreSQL is running")
        print("3. Check user has CREATE TABLE permissions")
        raise

if __name__ == "__main__":
    run_migration()

