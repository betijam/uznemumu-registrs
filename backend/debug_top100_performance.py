
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(database_url)

def check_indexes():
    print("\n--- Checking Indexes on financial_reports ---")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM
                pg_indexes
            WHERE
                tablename = 'financial_reports';
        """)).fetchall()
        
        for row in result:
            print(f"{row.indexname}: {row.indexdef}")

def explain_analyze():
    print("\n--- Running EXPLAIN ANALYZE on Top 100 View Query ---")
    query = """
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT 
            regcode,
            name,
            turnover,
            profit,
            data_year
        FROM company_stats_materialized
        WHERE turnover IS NOT NULL
        ORDER BY turnover DESC
        LIMIT 100
    """
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text(query)).fetchall()
            for row in result:
                print(row[0])
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    check_indexes()
    explain_analyze()
