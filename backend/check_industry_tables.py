from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def check_tables():
    tables = [
        'industry_stats_history',
        'industry_stats_materialized',
        'company_stats_materialized',
        'industry_leaders_cache'
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"✅ Table '{table}' exists and has {result} rows.")
            except Exception as e:
                print(f"❌ Table '{table}' does not exist or error: {e}")

if __name__ == "__main__":
    check_tables()
